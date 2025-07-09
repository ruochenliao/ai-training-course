"""
文档操作服务
基于ChromaVectorDBManager的高级文档操作接口
提供便捷的文档管理、搜索和批量操作功能
"""
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass

from .chroma_manager import (
    ChromaVectorDBManager,
    ChromaConfig,
    CollectionType,
    DocumentMetadata,
    SearchResult,
    MetadataManager,
    CollectionNamingStrategy
)

logger = logging.getLogger(__name__)


@dataclass
class DocumentInfo:
    """文档信息"""
    file_id: str
    file_name: str
    file_type: str
    file_size: int
    content: str
    knowledge_base_id: str
    knowledge_type: str
    is_public: bool
    owner_id: str
    extra_metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.extra_metadata is None:
            self.extra_metadata = {}


@dataclass
class SearchQuery:
    """搜索查询"""
    query_text: str
    collection_name: str = None
    knowledge_type: str = None
    knowledge_base_id: str = None
    file_id: str = None
    owner_id: str = None
    is_public: bool = None
    file_type: str = None
    n_results: int = 10
    custom_filters: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.custom_filters is None:
            self.custom_filters = {}


class DocumentOperationService:
    """
    文档操作服务
    提供高级的文档管理、搜索和批量操作功能
    """
    
    def __init__(self, config: ChromaConfig = None):
        """
        初始化文档操作服务
        
        Args:
            config: ChromaDB配置
        """
        self.db_manager = ChromaVectorDBManager(config)
        self.initialized = False
        
        # 操作统计
        self.operation_stats = {
            "documents_added": 0,
            "documents_deleted": 0,
            "searches_performed": 0,
            "collections_created": 0,
            "batch_operations": 0,
            "errors": 0
        }
        
        logger.info("文档操作服务初始化完成")
    
    async def initialize(self) -> bool:
        """
        初始化服务
        
        Returns:
            是否初始化成功
        """
        try:
            success = await self.db_manager.initialize()
            self.initialized = success
            
            if success:
                logger.info("文档操作服务初始化成功")
            else:
                logger.error("文档操作服务初始化失败")
            
            return success
            
        except Exception as e:
            logger.error(f"文档操作服务初始化异常: {e}")
            return False
    
    async def add_document(
        self,
        document: DocumentInfo,
        collection_type: CollectionType = CollectionType.PRIVATE,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        auto_create_collection: bool = True
    ) -> Tuple[bool, List[str]]:
        """
        添加文档
        
        Args:
            document: 文档信息
            collection_type: 集合类型
            chunk_size: 分块大小
            chunk_overlap: 分块重叠
            auto_create_collection: 是否自动创建集合
            
        Returns:
            (是否成功, 文档块ID列表)
        """
        try:
            if not self.initialized:
                raise RuntimeError("服务未初始化")
            
            # 生成集合名称
            user_id = document.owner_id if collection_type == CollectionType.PRIVATE else None
            collection_name = CollectionNamingStrategy.get_collection_name(
                document.knowledge_type, collection_type, user_id
            )
            
            # 自动创建集合（如果需要）
            if auto_create_collection:
                try:
                    await self.db_manager.create_collection(
                        document.knowledge_type, collection_type, user_id
                    )
                except Exception as e:
                    logger.warning(f"创建集合失败，可能已存在: {e}")
            
            # 创建文档元数据
            file_hash = MetadataManager.create_file_metadata(
                document.file_id,
                document.knowledge_base_id,
                document.file_type,
                document.file_name,
                document.file_size,
                document.content,
                document.is_public,
                document.owner_id,
                document.knowledge_type,
                document.extra_metadata
            )
            
            metadata = DocumentMetadata(
                file_id=document.file_id,
                knowledge_base_id=document.knowledge_base_id,
                file_type=document.file_type,
                file_name=document.file_name,
                file_size=document.file_size,
                file_hash=file_hash,
                chunk_index=0,  # 将在add_document中更新
                total_chunks=1,  # 将在add_document中更新
                byte_length=len(document.content.encode('utf-8')),
                chunk_hash="",  # 将在add_document中更新
                is_public=document.is_public,
                owner_id=document.owner_id,
                knowledge_type=document.knowledge_type,
                extra_metadata=document.extra_metadata
            )
            
            # 添加文档
            chunk_ids = await self.db_manager.add_document(
                collection_name,
                document.content,
                metadata,
                chunk_size,
                chunk_overlap
            )
            
            self.operation_stats["documents_added"] += 1
            logger.info(f"文档添加成功: {document.file_id}, 分块数: {len(chunk_ids)}")
            
            return True, chunk_ids
            
        except Exception as e:
            self.operation_stats["errors"] += 1
            logger.error(f"添加文档失败: {e}")
            return False, []
    
    async def search_documents(
        self,
        query: SearchQuery,
        user_id: str = None
    ) -> List[SearchResult]:
        """
        搜索文档
        
        Args:
            query: 搜索查询
            user_id: 用户ID（用于私有集合搜索）
            
        Returns:
            搜索结果列表
        """
        try:
            if not self.initialized:
                raise RuntimeError("服务未初始化")
            
            # 确定集合名称
            if query.collection_name:
                collection_name = query.collection_name
            elif query.knowledge_type:
                # 根据知识类型和用户ID确定集合
                if user_id:
                    # 优先搜索私有集合
                    collection_name = CollectionNamingStrategy.get_collection_name(
                        query.knowledge_type, CollectionType.PRIVATE, user_id
                    )
                else:
                    # 搜索公共集合
                    collection_name = CollectionNamingStrategy.get_collection_name(
                        query.knowledge_type, CollectionType.PUBLIC
                    )
            else:
                raise ValueError("必须提供collection_name或knowledge_type")
            
            # 构建过滤条件
            where_filters = MetadataManager.build_search_filter(
                knowledge_base_id=query.knowledge_base_id,
                file_id=query.file_id,
                owner_id=query.owner_id,
                is_public=query.is_public,
                knowledge_type=query.knowledge_type,
                file_type=query.file_type,
                custom_filters=query.custom_filters
            )
            
            # 执行搜索
            results = await self.db_manager.search(
                collection_name,
                query.query_text,
                query.n_results,
                where_filters if where_filters else None
            )
            
            self.operation_stats["searches_performed"] += 1
            logger.info(f"搜索完成: 集合={collection_name}, 查询='{query.query_text}', 结果数={len(results)}")
            
            return results
            
        except Exception as e:
            self.operation_stats["errors"] += 1
            logger.error(f"搜索文档失败: {e}")
            return []
    
    async def search_multiple_collections(
        self,
        query_text: str,
        knowledge_type: str,
        user_id: str,
        n_results: int = 10,
        search_public: bool = True,
        search_private: bool = True,
        merge_results: bool = True
    ) -> Union[List[SearchResult], Dict[str, List[SearchResult]]]:
        """
        在多个集合中搜索
        
        Args:
            query_text: 查询文本
            knowledge_type: 知识类型
            user_id: 用户ID
            n_results: 每个集合的结果数量
            search_public: 是否搜索公共集合
            search_private: 是否搜索私有集合
            merge_results: 是否合并结果
            
        Returns:
            搜索结果（合并或分组）
        """
        try:
            results = {}
            
            # 搜索私有集合
            if search_private:
                try:
                    private_query = SearchQuery(
                        query_text=query_text,
                        knowledge_type=knowledge_type,
                        n_results=n_results
                    )
                    private_results = await self.search_documents(private_query, user_id)
                    results["private"] = private_results
                except Exception as e:
                    logger.warning(f"搜索私有集合失败: {e}")
                    results["private"] = []
            
            # 搜索公共集合
            if search_public:
                try:
                    public_query = SearchQuery(
                        query_text=query_text,
                        knowledge_type=knowledge_type,
                        n_results=n_results
                    )
                    public_results = await self.search_documents(public_query)
                    results["public"] = public_results
                except Exception as e:
                    logger.warning(f"搜索公共集合失败: {e}")
                    results["public"] = []
            
            if merge_results:
                # 合并结果并按分数排序
                all_results = []
                for collection_results in results.values():
                    all_results.extend(collection_results)
                
                # 按分数降序排序
                all_results.sort(key=lambda x: x.score, reverse=True)
                
                # 限制结果数量
                return all_results[:n_results]
            else:
                return results
                
        except Exception as e:
            self.operation_stats["errors"] += 1
            logger.error(f"多集合搜索失败: {e}")
            return [] if merge_results else {}
    
    async def delete_document(
        self,
        file_id: str,
        knowledge_type: str,
        collection_type: CollectionType,
        user_id: str = None
    ) -> bool:
        """
        删除文档
        
        Args:
            file_id: 文件ID
            knowledge_type: 知识类型
            collection_type: 集合类型
            user_id: 用户ID（私有集合需要）
            
        Returns:
            是否删除成功
        """
        try:
            if not self.initialized:
                raise RuntimeError("服务未初始化")
            
            # 生成集合名称
            user_id_param = user_id if collection_type == CollectionType.PRIVATE else None
            collection_name = CollectionNamingStrategy.get_collection_name(
                knowledge_type, collection_type, user_id_param
            )
            
            # 删除文档
            success = await self.db_manager.delete_file(collection_name, file_id)
            
            if success:
                self.operation_stats["documents_deleted"] += 1
                logger.info(f"文档删除成功: {file_id}")
            
            return success
            
        except Exception as e:
            self.operation_stats["errors"] += 1
            logger.error(f"删除文档失败: {file_id}, 错误: {e}")
            return False

    async def delete_knowledge_base(
        self,
        knowledge_base_id: str,
        knowledge_type: str,
        collection_type: CollectionType,
        user_id: str = None
    ) -> bool:
        """
        删除知识库

        Args:
            knowledge_base_id: 知识库ID
            knowledge_type: 知识类型
            collection_type: 集合类型
            user_id: 用户ID（私有集合需要）

        Returns:
            是否删除成功
        """
        try:
            if not self.initialized:
                raise RuntimeError("服务未初始化")

            # 生成集合名称
            user_id_param = user_id if collection_type == CollectionType.PRIVATE else None
            collection_name = CollectionNamingStrategy.get_collection_name(
                knowledge_type, collection_type, user_id_param
            )

            # 删除知识库
            success = await self.db_manager.delete_knowledge_base(collection_name, knowledge_base_id)

            if success:
                logger.info(f"知识库删除成功: {knowledge_base_id}")

            return success

        except Exception as e:
            self.operation_stats["errors"] += 1
            logger.error(f"删除知识库失败: {knowledge_base_id}, 错误: {e}")
            return False

    async def batch_add_documents(
        self,
        documents: List[DocumentInfo],
        collection_type: CollectionType = CollectionType.PRIVATE,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        max_concurrent: int = 5
    ) -> Dict[str, Any]:
        """
        批量添加文档

        Args:
            documents: 文档列表
            collection_type: 集合类型
            chunk_size: 分块大小
            chunk_overlap: 分块重叠
            max_concurrent: 最大并发数

        Returns:
            批量操作结果
        """
        try:
            if not self.initialized:
                raise RuntimeError("服务未初始化")

            # 创建信号量限制并发
            semaphore = asyncio.Semaphore(max_concurrent)

            async def add_single_document(doc: DocumentInfo):
                async with semaphore:
                    return await self.add_document(
                        doc, collection_type, chunk_size, chunk_overlap
                    )

            # 并发添加文档
            tasks = [add_single_document(doc) for doc in documents]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 统计结果
            successful = 0
            failed = 0
            total_chunks = 0
            errors = []

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    failed += 1
                    errors.append({
                        "document_id": documents[i].file_id,
                        "error": str(result)
                    })
                else:
                    success, chunk_ids = result
                    if success:
                        successful += 1
                        total_chunks += len(chunk_ids)
                    else:
                        failed += 1
                        errors.append({
                            "document_id": documents[i].file_id,
                            "error": "添加失败"
                        })

            self.operation_stats["batch_operations"] += 1

            batch_result = {
                "total_documents": len(documents),
                "successful": successful,
                "failed": failed,
                "total_chunks": total_chunks,
                "errors": errors,
                "timestamp": datetime.now().isoformat()
            }

            logger.info(f"批量添加文档完成: 总数={len(documents)}, 成功={successful}, 失败={failed}")

            return batch_result

        except Exception as e:
            self.operation_stats["errors"] += 1
            logger.error(f"批量添加文档失败: {e}")
            return {
                "total_documents": len(documents),
                "successful": 0,
                "failed": len(documents),
                "total_chunks": 0,
                "errors": [{"error": str(e)}],
                "timestamp": datetime.now().isoformat()
            }

    async def batch_delete_documents(
        self,
        file_ids: List[str],
        knowledge_type: str,
        collection_type: CollectionType,
        user_id: str = None,
        max_concurrent: int = 5
    ) -> Dict[str, Any]:
        """
        批量删除文档

        Args:
            file_ids: 文件ID列表
            knowledge_type: 知识类型
            collection_type: 集合类型
            user_id: 用户ID（私有集合需要）
            max_concurrent: 最大并发数

        Returns:
            批量操作结果
        """
        try:
            if not self.initialized:
                raise RuntimeError("服务未初始化")

            # 创建信号量限制并发
            semaphore = asyncio.Semaphore(max_concurrent)

            async def delete_single_document(file_id: str):
                async with semaphore:
                    return await self.delete_document(
                        file_id, knowledge_type, collection_type, user_id
                    )

            # 并发删除文档
            tasks = [delete_single_document(file_id) for file_id in file_ids]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 统计结果
            successful = 0
            failed = 0
            errors = []

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    failed += 1
                    errors.append({
                        "file_id": file_ids[i],
                        "error": str(result)
                    })
                elif result:
                    successful += 1
                else:
                    failed += 1
                    errors.append({
                        "file_id": file_ids[i],
                        "error": "删除失败"
                    })

            self.operation_stats["batch_operations"] += 1

            batch_result = {
                "total_files": len(file_ids),
                "successful": successful,
                "failed": failed,
                "errors": errors,
                "timestamp": datetime.now().isoformat()
            }

            logger.info(f"批量删除文档完成: 总数={len(file_ids)}, 成功={successful}, 失败={failed}")

            return batch_result

        except Exception as e:
            self.operation_stats["errors"] += 1
            logger.error(f"批量删除文档失败: {e}")
            return {
                "total_files": len(file_ids),
                "successful": 0,
                "failed": len(file_ids),
                "errors": [{"error": str(e)}],
                "timestamp": datetime.now().isoformat()
            }

    async def get_collection_info(
        self,
        knowledge_type: str,
        collection_type: CollectionType,
        user_id: str = None
    ) -> Dict[str, Any]:
        """
        获取集合信息

        Args:
            knowledge_type: 知识类型
            collection_type: 集合类型
            user_id: 用户ID（私有集合需要）

        Returns:
            集合信息
        """
        try:
            if not self.initialized:
                raise RuntimeError("服务未初始化")

            # 生成集合名称
            user_id_param = user_id if collection_type == CollectionType.PRIVATE else None
            collection_name = CollectionNamingStrategy.get_collection_name(
                knowledge_type, collection_type, user_id_param
            )

            # 获取集合统计
            stats = await self.db_manager.get_collection_stats(collection_name)

            return stats

        except Exception as e:
            logger.error(f"获取集合信息失败: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def list_all_collections(self) -> List[Dict[str, Any]]:
        """
        列出所有集合

        Returns:
            集合信息列表
        """
        try:
            if not self.initialized:
                raise RuntimeError("服务未初始化")

            return await self.db_manager.list_collections()

        except Exception as e:
            logger.error(f"列出集合失败: {e}")
            return []

    async def health_check(self) -> Dict[str, Any]:
        """
        执行健康检查

        Returns:
            健康状态信息
        """
        try:
            # 获取数据库管理器健康状态
            db_health = await self.db_manager.health_check()

            # 组合服务健康状态
            service_health = {
                "service_status": "healthy" if self.initialized else "not_initialized",
                "initialized": self.initialized,
                "operation_stats": self.operation_stats.copy(),
                "db_manager_health": db_health,
                "timestamp": datetime.now().isoformat()
            }

            # 判断整体健康状态
            if not self.initialized or db_health.get("status") != "healthy":
                service_health["service_status"] = "unhealthy"

            return service_health

        except Exception as e:
            return {
                "service_status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def close(self) -> None:
        """关闭服务，释放资源"""
        try:
            await self.db_manager.close()
            self.initialized = False
            logger.info("文档操作服务已关闭")

        except Exception as e:
            logger.error(f"关闭文档操作服务失败: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """
        获取服务统计信息

        Returns:
            统计信息
        """
        return {
            "initialized": self.initialized,
            "operation_stats": self.operation_stats.copy(),
            "db_manager_stats": self.db_manager.get_stats() if self.db_manager else None,
            "timestamp": datetime.now().isoformat()
        }
