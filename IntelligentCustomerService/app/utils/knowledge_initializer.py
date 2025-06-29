"""
知识库初始化工具
用于初始化和管理个人知识库和公共知识库
"""
import asyncio
import logging
from typing import Dict, Any

from ..services.memory.factory import MemoryServiceFactory
from ..utils.model_downloader import get_model_downloader

logger = logging.getLogger(__name__)


class KnowledgeInitializer:
    """知识库初始化器"""
    
    def __init__(self):
        self.memory_factory = MemoryServiceFactory()
        self.model_downloader = get_model_downloader()
    
    async def initialize_system(self, download_models: bool = True) -> Dict[str, Any]:
        """
        初始化整个知识库系统
        
        Args:
            download_models: 是否下载模型
            
        Returns:
            初始化结果
        """
        results = {
            "models": {"status": "skipped"},
            "public_knowledge": {"status": "unknown"},
            "system_ready": False
        }
        
        try:
            logger.info("🚀 开始初始化知识库系统...")
            
            # 第一步：下载模型（如果需要）
            if download_models:
                logger.info("📥 检查和下载模型...")
                model_results = await self._ensure_models_available()
                results["models"] = model_results
            
            # 第二步：初始化公共知识库
            logger.info("📚 初始化公共知识库...")
            public_results = await self._initialize_public_knowledge()
            results["public_knowledge"] = public_results
            
            # 第三步：验证系统状态
            logger.info("✅ 验证系统状态...")
            system_status = await self._validate_system_status()
            results["system_status"] = system_status
            results["system_ready"] = system_status.get("ready", False)
            
            if results["system_ready"]:
                logger.info("🎉 知识库系统初始化完成！")
            else:
                logger.warning("⚠️ 知识库系统初始化完成，但存在一些问题")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ 知识库系统初始化失败: {e}")
            results["error"] = str(e)
            return results
    
    async def _ensure_models_available(self) -> Dict[str, Any]:
        """确保模型可用"""
        try:
            # 检查模型状态
            model_info = self.model_downloader.get_model_info()
            
            download_needed = []
            for model_type, info in model_info["models"].items():
                if not info["is_cached"]:
                    download_needed.append(model_type)
            
            if download_needed:
                logger.info(f"需要下载的模型: {download_needed}")
                
                # 下载缺失的模型
                download_results = {}
                for model_type in download_needed:
                    try:
                        logger.info(f"下载模型: {model_type}")
                        model_path = await self.model_downloader.download_model_async(model_type)
                        download_results[model_type] = {
                            "status": "success",
                            "path": model_path
                        }
                    except Exception as e:
                        logger.error(f"下载模型失败 {model_type}: {e}")
                        download_results[model_type] = {
                            "status": "failed",
                            "error": str(e)
                        }
                
                return {
                    "status": "completed",
                    "download_needed": download_needed,
                    "download_results": download_results
                }
            else:
                logger.info("所有模型已缓存，无需下载")
                return {
                    "status": "already_available",
                    "models": list(model_info["models"].keys())
                }
                
        except Exception as e:
            logger.error(f"检查模型状态失败: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def _initialize_public_knowledge(self) -> Dict[str, Any]:
        """初始化公共知识库"""
        try:
            # 获取公共记忆服务
            public_memory = self.memory_factory.get_public_memory_service()
            
            # 触发默认知识库初始化
            await public_memory._ensure_knowledge_initialized()
            
            # 获取统计信息
            stats = await public_memory.get_knowledge_stats()
            
            return {
                "status": "success",
                "stats": stats
            }
            
        except Exception as e:
            logger.error(f"初始化公共知识库失败: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def _validate_system_status(self) -> Dict[str, Any]:
        """验证系统状态"""
        try:
            status = {
                "ready": False,
                "components": {}
            }
            
            # 验证模型状态
            try:
                from ..config.vector_db_config import model_manager
                
                # 测试嵌入模型
                embedding_model = model_manager.get_embedding_model()
                if embedding_model:
                    test_embedding = embedding_model.encode("测试文本")
                    status["components"]["embedding_model"] = {
                        "status": "ok" if test_embedding is not None else "error",
                        "dimension": len(test_embedding) if test_embedding is not None else 0
                    }
                else:
                    status["components"]["embedding_model"] = {"status": "not_loaded"}
                
                # 测试重排模型（可选）
                try:
                    reranker_model = model_manager.get_reranker_model()
                    if reranker_model:
                        test_scores = reranker_model.predict([("查询", "文档")])
                        status["components"]["reranker_model"] = {
                            "status": "ok" if test_scores is not None else "error"
                        }
                    else:
                        status["components"]["reranker_model"] = {"status": "disabled"}
                except Exception:
                    status["components"]["reranker_model"] = {"status": "disabled"}
                
            except Exception as e:
                status["components"]["models"] = {"status": "error", "error": str(e)}
            
            # 验证公共知识库
            try:
                public_memory = self.memory_factory.get_public_memory_service()
                test_results = await public_memory.retrieve_memories("测试查询", limit=1)
                status["components"]["public_knowledge"] = {
                    "status": "ok",
                    "test_results_count": len(test_results)
                }
            except Exception as e:
                status["components"]["public_knowledge"] = {"status": "error", "error": str(e)}
            
            # 判断整体状态
            component_statuses = [comp.get("status") for comp in status["components"].values()]
            status["ready"] = "ok" in component_statuses and "error" not in component_statuses
            
            return status
            
        except Exception as e:
            logger.error(f"验证系统状态失败: {e}")
            return {
                "ready": False,
                "error": str(e)
            }
    
    async def add_sample_knowledge(self, category: str = "sample") -> Dict[str, Any]:
        """添加示例知识"""
        try:
            public_memory = self.memory_factory.get_public_memory_service()
            
            sample_knowledge = [
                {
                    "content": "人工智能（AI）是计算机科学的一个分支，致力于创建能够执行通常需要人类智能的任务的系统。",
                    "title": "人工智能简介",
                    "tags": ["AI", "人工智能", "技术"],
                    "priority": 3
                },
                {
                    "content": "机器学习是人工智能的一个子集，它使计算机能够在没有明确编程的情况下学习和改进。",
                    "title": "机器学习概念",
                    "tags": ["机器学习", "ML", "算法"],
                    "priority": 3
                },
                {
                    "content": "深度学习是机器学习的一个分支，使用多层神经网络来模拟人脑的工作方式。",
                    "title": "深度学习基础",
                    "tags": ["深度学习", "神经网络", "DL"],
                    "priority": 3
                }
            ]
            
            added_ids = []
            for item in sample_knowledge:
                metadata = {
                    "category": category,
                    "title": item["title"],
                    "tags": item["tags"],
                    "priority": item["priority"],
                    "source": "sample_data"
                }
                
                knowledge_id = await public_memory.add_memory(item["content"], metadata)
                added_ids.append(knowledge_id)
            
            return {
                "status": "success",
                "added_count": len(added_ids),
                "knowledge_ids": added_ids
            }
            
        except Exception as e:
            logger.error(f"添加示例知识失败: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }


# 全局初始化器实例
_knowledge_initializer = None

def get_knowledge_initializer() -> KnowledgeInitializer:
    """获取全局知识库初始化器实例"""
    global _knowledge_initializer
    if _knowledge_initializer is None:
        _knowledge_initializer = KnowledgeInitializer()
    return _knowledge_initializer


async def quick_initialize_knowledge_system(download_models: bool = True) -> Dict[str, Any]:
    """快速初始化知识库系统"""
    initializer = get_knowledge_initializer()
    return await initializer.initialize_system(download_models)


if __name__ == "__main__":
    # 命令行运行时的初始化
    async def main():
        print("🚀 开始初始化知识库系统...")
        results = await quick_initialize_knowledge_system(download_models=True)
        print(f"📊 初始化结果: {results}")
        
        if results.get("system_ready"):
            print("✅ 系统初始化成功！")
        else:
            print("❌ 系统初始化失败或存在问题")
    
    asyncio.run(main())
