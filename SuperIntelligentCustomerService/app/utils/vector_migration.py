"""
向量数据库迁移工具
用于将现有的多个向量数据库迁移到统一的向量数据库架构
"""
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# 尝试导入 chromadb
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    print("未找到 ChromaDB 库。迁移功能将被禁用。")

from ..services.unified_vector_service import (
    VectorCollectionType,
    VectorDocument,
    get_unified_vector_service
)
from ..services.vector_db import get_vector_db
from ..settings.config import settings

logger = logging.getLogger(__name__)


class VectorMigrationTool:
    """向量数据库迁移工具"""
    
    def __init__(self):
        """初始化迁移工具"""
        self.unified_service = get_unified_vector_service()
        self.old_vector_service = get_vector_db()
        self.migration_log = []
        
        # 迁移统计
        self.stats = {
            "total_collections": 0,
            "migrated_collections": 0,
            "total_documents": 0,
            "migrated_documents": 0,
            "failed_documents": 0,
            "start_time": None,
            "end_time": None
        }
    
    async def migrate_all(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        迁移所有向量数据
        
        Args:
            dry_run: 是否为试运行（不实际迁移数据）
            
        Returns:
            迁移结果统计
        """
        logger.info(f"开始向量数据库迁移 (dry_run={dry_run})")
        self.stats["start_time"] = datetime.now()
        
        try:
            # 1. 迁移主向量数据库
            await self._migrate_main_vector_db(dry_run)
            
            # 2. 迁移知识库向量数据
            await self._migrate_knowledge_vectors(dry_run)
            
            # 3. 迁移记忆向量数据
            await self._migrate_memory_vectors(dry_run)
            
            # 4. 清理旧数据（仅在非试运行模式下）
            if not dry_run:
                await self._cleanup_old_data()
            
            self.stats["end_time"] = datetime.now()
            
            logger.info("向量数据库迁移完成")
            return self._generate_migration_report()
            
        except Exception as e:
            logger.error(f"迁移过程中发生错误: {e}")
            self.stats["end_time"] = datetime.now()
            return self._generate_migration_report(error=str(e))
    
    async def _migrate_main_vector_db(self, dry_run: bool = False):
        """迁移主向量数据库"""
        logger.info("开始迁移主向量数据库")
        
        if not self.old_vector_service or not self.old_vector_service.chroma_client:
            logger.warning("旧向量数据库服务不可用，跳过主向量数据库迁移")
            return
        
        try:
            # 获取所有旧集合
            old_collections = self.old_vector_service.chroma_client.list_collections()
            self.stats["total_collections"] += len(old_collections)
            
            for collection in old_collections:
                await self._migrate_collection(collection, dry_run)
                
        except Exception as e:
            logger.error(f"迁移主向量数据库失败: {e}")
            self._log_migration_error("main_vector_db", str(e))
    
    async def _migrate_collection(self, old_collection, dry_run: bool = False):
        """迁移单个集合"""
        collection_name = old_collection.name
        logger.info(f"迁移集合: {collection_name}")
        
        try:
            # 获取集合中的所有文档
            results = old_collection.get(include=['metadatas', 'documents'])
            
            if not results or not results.get('ids'):
                logger.info(f"集合 {collection_name} 为空，跳过")
                return
            
            documents = []
            for i, doc_id in enumerate(results['ids']):
                content = results['documents'][i] if results.get('documents') else ""
                metadata = results['metadatas'][i] if results.get('metadatas') else {}
                
                # 确定新的集合类型
                new_collection_type = self._determine_collection_type(collection_name, metadata)
                
                # 创建向量文档
                vector_doc = VectorDocument(
                    id=doc_id,
                    content=content,
                    metadata=metadata
                )
                documents.append((vector_doc, new_collection_type))
            
            self.stats["total_documents"] += len(documents)
            
            if not dry_run:
                # 按集合类型分组并迁移
                await self._migrate_documents_by_type(documents)
            
            self.stats["migrated_collections"] += 1
            self._log_migration_success(collection_name, len(documents))
            
        except Exception as e:
            logger.error(f"迁移集合 {collection_name} 失败: {e}")
            self._log_migration_error(collection_name, str(e))
    
    def _determine_collection_type(self, collection_name: str, metadata: Dict[str, Any]) -> VectorCollectionType:
        """根据集合名称和元数据确定新的集合类型"""
        # 检查元数据中的类型信息
        if metadata.get("knowledge_type"):
            knowledge_type = metadata["knowledge_type"]
            if knowledge_type == "customer_service":
                return VectorCollectionType.CUSTOMER_SERVICE
            elif "knowledge" in knowledge_type.lower():
                return VectorCollectionType.KNOWLEDGE_BASE
        
        # 根据集合名称判断
        name_lower = collection_name.lower()
        
        if name_lower.startswith("kb_") or "knowledge" in name_lower:
            return VectorCollectionType.KNOWLEDGE_BASE
        elif "chat" in name_lower or "conversation" in name_lower:
            return VectorCollectionType.CHAT_MEMORY
        elif "private" in name_lower:
            return VectorCollectionType.PRIVATE_MEMORY
        elif "public" in name_lower:
            return VectorCollectionType.PUBLIC_MEMORY
        elif "customer" in name_lower or "service" in name_lower:
            return VectorCollectionType.CUSTOMER_SERVICE
        else:
            # 默认为知识库类型
            return VectorCollectionType.KNOWLEDGE_BASE
    
    async def _migrate_documents_by_type(self, documents: List[tuple]):
        """按类型迁移文档"""
        # 按集合类型分组
        type_groups = {}
        for doc, collection_type in documents:
            if collection_type not in type_groups:
                type_groups[collection_type] = []
            type_groups[collection_type].append(doc)
        
        # 迁移每个类型的文档
        for collection_type, docs in type_groups.items():
            try:
                # 确定标识符
                identifier = self._extract_identifier(docs[0].metadata, collection_type)
                is_public = docs[0].metadata.get("is_public", False)
                owner_id = docs[0].metadata.get("owner_id")
                
                if owner_id and isinstance(owner_id, str):
                    try:
                        owner_id = int(owner_id)
                    except ValueError:
                        owner_id = None
                
                # 添加文档到新的统一服务
                result_ids = await self.unified_service.add_documents(
                    collection_type=collection_type,
                    documents=docs,
                    identifier=identifier,
                    is_public=is_public,
                    owner_id=owner_id
                )
                
                self.stats["migrated_documents"] += len(result_ids)
                logger.info(f"成功迁移 {len(result_ids)} 个文档到 {collection_type.value}")
                
            except Exception as e:
                logger.error(f"迁移文档到 {collection_type.value} 失败: {e}")
                self.stats["failed_documents"] += len(docs)
    
    def _extract_identifier(self, metadata: Dict[str, Any], collection_type: VectorCollectionType) -> Optional[str]:
        """从元数据中提取标识符"""
        if collection_type == VectorCollectionType.KNOWLEDGE_BASE:
            return metadata.get("knowledge_base_id") or metadata.get("file_id")
        elif collection_type == VectorCollectionType.CHAT_MEMORY:
            return metadata.get("user_id") or metadata.get("session_id")
        elif collection_type == VectorCollectionType.PRIVATE_MEMORY:
            return metadata.get("memory_type", "general")
        elif collection_type == VectorCollectionType.PUBLIC_MEMORY:
            return metadata.get("memory_type", "general")
        elif collection_type == VectorCollectionType.CUSTOMER_SERVICE:
            return metadata.get("service_type", "general")
        
        return None
    
    async def _migrate_knowledge_vectors(self, dry_run: bool = False):
        """迁移知识库向量数据"""
        logger.info("开始迁移知识库向量数据")
        
        # 这里可以添加从其他知识库向量服务迁移的逻辑
        # 由于KnowledgeVectorService使用的是autogen的ChromaDB，
        # 可能需要特殊处理
        
        try:
            # 查找知识库向量数据目录
            vector_dirs = [
                Path(settings.BASE_DIR) / "data" / "vector_db",
                Path(settings.BASE_DIR) / "vector_db_data"
            ]
            
            for vector_dir in vector_dirs:
                if vector_dir.exists():
                    await self._migrate_directory_collections(vector_dir, dry_run)
                    
        except Exception as e:
            logger.error(f"迁移知识库向量数据失败: {e}")
            self._log_migration_error("knowledge_vectors", str(e))
    
    async def _migrate_memory_vectors(self, dry_run: bool = False):
        """迁移记忆向量数据"""
        logger.info("开始迁移记忆向量数据")
        
        # 这里可以添加从VectorMemoryService迁移的逻辑
        pass
    
    async def _migrate_directory_collections(self, directory: Path, dry_run: bool = False):
        """迁移目录中的集合"""
        logger.info(f"迁移目录: {directory}")
        
        # 这里需要根据具体的存储格式来实现
        # ChromaDB的持久化存储通常包含多个文件
        pass
    
    async def _cleanup_old_data(self):
        """清理旧数据"""
        logger.info("开始清理旧数据")
        
        # 这里可以添加清理旧向量数据库的逻辑
        # 注意：只有在确认迁移成功后才执行清理
        pass
    
    def _log_migration_success(self, collection_name: str, document_count: int):
        """记录迁移成功"""
        message = f"成功迁移集合 {collection_name}，文档数量: {document_count}"
        self.migration_log.append({
            "type": "success",
            "collection": collection_name,
            "document_count": document_count,
            "timestamp": datetime.now().isoformat(),
            "message": message
        })
        logger.info(message)
    
    def _log_migration_error(self, collection_name: str, error: str):
        """记录迁移错误"""
        message = f"迁移集合 {collection_name} 失败: {error}"
        self.migration_log.append({
            "type": "error",
            "collection": collection_name,
            "error": error,
            "timestamp": datetime.now().isoformat(),
            "message": message
        })
        logger.error(message)
    
    def _generate_migration_report(self, error: Optional[str] = None) -> Dict[str, Any]:
        """生成迁移报告"""
        duration = None
        if self.stats["start_time"] and self.stats["end_time"]:
            duration = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()
        
        report = {
            "migration_stats": self.stats.copy(),
            "duration_seconds": duration,
            "migration_log": self.migration_log,
            "success": error is None,
            "error": error
        }
        
        return report


async def run_migration(dry_run: bool = True) -> Dict[str, Any]:
    """运行向量数据库迁移"""
    migration_tool = VectorMigrationTool()
    return await migration_tool.migrate_all(dry_run=dry_run)


if __name__ == "__main__":
    # 命令行运行迁移
    import sys
    
    dry_run = "--dry-run" in sys.argv or "-d" in sys.argv
    
    async def main():
        result = await run_migration(dry_run=dry_run)
        print(f"迁移完成: {result}")
    
    asyncio.run(main())
