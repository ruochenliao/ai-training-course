"""
公共记忆服务
存储FAQ、政策信息等公共知识库
使用ChromaDB向量数据库实现高质量的语义检索和重排
基于AutoGen的ChromaDBVectorMemory实现模式
"""
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

try:
    import chromadb
    from chromadb.config import Settings
    from sentence_transformers import SentenceTransformer, CrossEncoder
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    chromadb = None
    SentenceTransformer = None
    CrossEncoder = None

    class MockChromaDB:
        """ChromaDB不可用时的占位符"""
        pass

from .base import MemoryItem

logger = logging.getLogger(__name__)


class PublicMemoryService:
    """公共知识库服务 - 基于ChromaDB向量数据库和重排模型实现"""

    def __init__(self):
        if not CHROMADB_AVAILABLE:
            raise ImportError("ChromaDB不可用，请安装: pip install chromadb sentence-transformers")

        self._init_vector_db()

        # 初始化默认知识库内容（延迟到第一次使用时）
        self._knowledge_initialized = False

    def _init_vector_db(self):
        """初始化向量数据库"""
        try:
            # 设置ChromaDB持久化路径
            self.chroma_path = os.path.join(
                str(Path.home()),
                ".chromadb_intelligent_customer_service",
                "public_memory"
            )
            os.makedirs(self.chroma_path, exist_ok=True)

            # 初始化ChromaDB客户端
            self.chroma_client = chromadb.PersistentClient(
                path=self.chroma_path,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )

            # 创建或获取集合
            self.collection_name = "public_knowledge_base"
            try:
                self.collection = self.chroma_client.get_collection(self.collection_name)
            except Exception:  # 捕获所有异常，包括NotFoundError
                self.collection = self.chroma_client.create_collection(
                    name=self.collection_name,
                    metadata={"type": "public_knowledge", "version": "1.0"}
                )

            # 初始化嵌入模型和重排模型 - 使用全局模型管理器
            from ...config.vector_db_config import model_manager

            # 获取嵌入模型
            self.embedding_model = model_manager.get_embedding_model()
            logger.info("嵌入模型初始化成功")

            # 获取重排模型（可选）
            try:
                self.reranker_model = model_manager.get_reranker_model()
                self.use_reranker = self.reranker_model is not None
                if self.use_reranker:
                    logger.info("重排模型初始化成功")
                else:
                    logger.info("重排模型未启用")
            except Exception as e:
                logger.warning(f"重排模型初始化失败，将使用基础排序: {e}")
                self.reranker_model = None
                self.use_reranker = False

            logger.info(f"公共知识库向量数据库初始化成功: {self.chroma_path}")

        except Exception as e:
            logger.error(f"向量数据库初始化失败: {e}")
            raise

    async def _ensure_knowledge_initialized(self):
        """确保知识库已初始化"""
        if not self._knowledge_initialized:
            await self._init_default_knowledge()
            self._knowledge_initialized = True
    
    async def _init_default_knowledge(self):
        """初始化默认知识库内容"""
        default_knowledge = [
            {
                "category": "policy",
                "title": "退货政策",
                "content": "我们提供30天无理由退货服务。商品需保持原包装完整，未使用状态。退货运费由买家承担，质量问题除外。具体退货流程：1. 联系客服申请退货；2. 获得退货授权码；3. 按要求包装商品；4. 选择物流方式寄回；5. 商品验收后3-5个工作日退款到账。",
                "tags": ["退货", "政策", "售后", "流程"],
                "priority": 5
            },
            {
                "category": "policy",
                "title": "换货政策",
                "content": "商品质量问题可在7天内申请换货。换货商品需保持原包装，我们承担换货运费。换货流程：1. 拍照记录质量问题；2. 联系客服说明情况；3. 客服确认后安排换货；4. 同时寄出新商品和回收旧商品；5. 通常3-5个工作日完成换货。",
                "tags": ["换货", "政策", "售后", "质量问题"],
                "priority": 5
            },
            {
                "category": "shipping",
                "title": "配送时间",
                "content": "一般商品1-3个工作日发货，偏远地区可能需要5-7个工作日。急需商品可选择加急配送。配送时间说明：现货商品当天下单次日发货；预售商品按预售周期发货；大件商品需要预约配送时间；节假日期间配送时间会有调整。",
                "tags": ["配送", "时间", "物流", "发货"],
                "priority": 4
            },
            {
                "category": "payment",
                "title": "支付方式",
                "content": "支持微信支付、支付宝、银行卡支付。企业客户可申请月结账期。支付安全保障：采用SSL加密传输；支持多种安全认证；资金由第三方托管；支持分期付款和优惠券使用。",
                "tags": ["支付", "方式", "结算", "安全"],
                "priority": 4
            },
            {
                "category": "service",
                "title": "客服时间",
                "content": "客服工作时间：周一至周日 9:00-21:00。节假日可能有调整，具体以公告为准。联系方式：在线客服、客服热线400-xxx-xxxx、邮箱service@company.com。紧急问题可通过微信公众号联系。",
                "tags": ["客服", "时间", "服务", "联系方式"],
                "priority": 3
            },
            {
                "category": "warranty",
                "title": "质保服务",
                "content": "电子产品提供1年质保，家电产品提供3年质保。质保期内免费维修，超出质保期收取成本费。质保范围包括：产品功能故障、零部件损坏、软件问题等。不包括：人为损坏、自然老化、意外事故等。",
                "tags": ["质保", "维修", "服务", "保修"],
                "priority": 4
            },
            {
                "category": "promotion",
                "title": "优惠券使用",
                "content": "优惠券有使用期限，过期作废。部分商品不支持优惠券，具体以商品页面说明为准。使用规则：每单限用一张；不可与其他优惠叠加；满减券需达到最低消费金额；折扣券按商品原价计算。",
                "tags": ["优惠券", "促销", "使用规则", "折扣"],
                "priority": 3
            },
            {
                "category": "account",
                "title": "会员等级",
                "content": "根据累计消费金额划分会员等级：普通会员（0-999元）、银卡会员（1000-4999元）、金卡会员（5000-19999元）、钻石会员（20000元以上）。不同等级享受不同折扣和服务：专属客服、生日礼品、积分倍率、优先发货等。",
                "tags": ["会员", "等级", "权益", "折扣"],
                "priority": 3
            }
        ]

        await self._init_default_knowledge_vector(default_knowledge)

    async def _init_default_knowledge_vector(self, knowledge_items: List[Dict[str, Any]]):
        """使用向量数据库初始化默认知识"""
        try:
            # 检查是否已经初始化过
            existing_count = self.collection.count()
            if existing_count > 0:
                logger.info(f"公共知识库已存在 {existing_count} 条记录，跳过初始化")
                return

            # 批量添加知识项
            ids = []
            documents = []
            embeddings = []
            metadatas = []

            for item in knowledge_items:
                memory_id = f"public_{item['category']}_{item['title'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

                # 生成嵌入向量
                embedding = self.embedding_model.encode(item["content"]).tolist()

                # 准备元数据
                metadata = {
                    "category": item["category"],
                    "title": item["title"],
                    "tags": json.dumps(item["tags"]),
                    "priority": item.get("priority", 1),
                    "is_active": True,
                    "created_at": datetime.now().isoformat(),
                    "content_type": "knowledge_base"
                }

                ids.append(memory_id)
                documents.append(item["content"])
                embeddings.append(embedding)
                metadatas.append(metadata)

            # 批量插入到ChromaDB
            self.collection.add(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas
            )

            logger.info(f"成功初始化 {len(knowledge_items)} 条默认公共知识")

        except Exception as e:
            logger.error(f"向量知识库初始化失败: {e}")


    
    async def add_memory(self, content: str, metadata: Dict[str, Any] = None) -> str:
        """添加公共知识"""
        # 确保知识库已初始化
        await self._ensure_knowledge_initialized()
        metadata = metadata or {}
        memory_id = f"public_{metadata.get('category', 'general')}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        return await self._add_memory_vector(memory_id, content, metadata)

    async def _add_memory_vector(self, memory_id: str, content: str, metadata: Dict[str, Any]) -> str:
        """使用向量数据库添加公共知识"""
        try:
            # 生成嵌入向量
            embedding = self.embedding_model.encode(content).tolist()

            # 准备元数据
            doc_metadata = {
                "category": metadata.get("category", "general"),
                "title": metadata.get("title", content[:50] + "..." if len(content) > 50 else content),
                "tags": json.dumps(metadata.get("tags", [])),
                "priority": metadata.get("priority", 1),
                "is_active": metadata.get("is_active", True),
                "created_at": datetime.now().isoformat(),
                "content_type": "knowledge_base",
                **metadata
            }

            # 添加到ChromaDB
            self.collection.add(
                ids=[memory_id],
                documents=[content],
                embeddings=[embedding],
                metadatas=[doc_metadata]
            )

            logger.debug(f"向量知识添加成功: {memory_id}")
            return memory_id

        except Exception as e:
            logger.error(f"向量知识添加失败: {e}")
            raise


    
    async def retrieve_memories(self, query: str, limit: int = 5) -> List[MemoryItem]:
        """检索相关公共知识，使用向量检索+重排模型"""
        # 确保知识库已初始化
        await self._ensure_knowledge_initialized()
        return await self._retrieve_memories_vector(query, limit)

    async def _retrieve_memories_vector(self, query: str, limit: int = 5) -> List[MemoryItem]:
        """使用向量数据库和重排模型检索记忆"""
        try:
            # 生成查询嵌入
            query_embedding = self.embedding_model.encode(query).tolist()

            # 第一阶段：向量检索，获取更多候选结果
            retrieval_limit = min(limit * 3, 20)  # 获取3倍数量用于重排

            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=retrieval_limit,
                include=["documents", "metadatas", "distances"],
                where={"is_active": True}  # 只检索激活的知识
            )

            if not results["ids"] or not results["ids"][0]:
                return []

            # 准备候选结果
            candidates = []
            for i, doc_id in enumerate(results["ids"][0]):
                try:
                    content = results["documents"][0][i]
                    metadata = results["metadatas"][0][i]
                    distance = results["distances"][0][i]

                    # 转换距离为相似度分数
                    similarity_score = 1.0 / (1.0 + distance)

                    # 解析标签
                    if "tags" in metadata:
                        try:
                            metadata["tags"] = json.loads(metadata["tags"])
                        except (json.JSONDecodeError, TypeError):
                            metadata["tags"] = []

                    candidates.append({
                        "id": doc_id,
                        "content": content,
                        "metadata": metadata,
                        "similarity_score": similarity_score,
                        "distance": distance
                    })

                except Exception as e:
                    logger.warning(f"Failed to process vector result: {e}")
                    continue

            # 第二阶段：重排（如果可用）
            if self.use_reranker and len(candidates) > 1:
                candidates = await self._rerank_candidates(query, candidates)

            # 转换为MemoryItem对象
            memories = []
            for candidate in candidates[:limit]:
                metadata = candidate["metadata"]
                metadata["relevance_score"] = candidate.get("rerank_score", candidate["similarity_score"])
                metadata["similarity_score"] = candidate["similarity_score"]
                metadata["distance"] = candidate["distance"]

                memory = MemoryItem(
                    id=candidate["id"],
                    content=candidate["content"],
                    metadata=metadata,
                    created_at=datetime.fromisoformat(metadata.get("created_at", datetime.now().isoformat())),
                    updated_at=datetime.now()
                )
                memories.append(memory)

            return memories

        except Exception as e:
            logger.error(f"向量检索失败: {e}")
            return []

    async def _rerank_candidates(self, query: str, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """使用重排模型对候选结果进行精确排序"""
        try:
            # 准备查询-文档对
            query_doc_pairs = []
            for candidate in candidates:
                # 组合标题和内容进行重排
                title = candidate["metadata"].get("title", "")
                content = candidate["content"]
                doc_text = f"{title}\n{content}" if title else content
                query_doc_pairs.append([query, doc_text])

            # 使用重排模型计算分数
            rerank_scores = self.reranker_model.predict(query_doc_pairs)

            # 更新候选结果的分数
            for i, candidate in enumerate(candidates):
                candidate["rerank_score"] = float(rerank_scores[i])

                # 结合原始相似度和重排分数
                combined_score = 0.3 * candidate["similarity_score"] + 0.7 * candidate["rerank_score"]

                # 考虑优先级加权
                priority = candidate["metadata"].get("priority", 1)
                priority_bonus = priority * 0.1
                candidate["final_score"] = combined_score + priority_bonus

            # 按最终分数排序
            candidates.sort(key=lambda x: x.get("final_score", x.get("rerank_score", 0)), reverse=True)

            logger.debug(f"重排完成，处理了 {len(candidates)} 个候选结果")
            return candidates

        except Exception as e:
            logger.error(f"重排失败: {e}")
            # 回退到原始排序
            candidates.sort(key=lambda x: x["similarity_score"], reverse=True)
            return candidates


    
    async def get_by_category(self, category: str, limit: int = 10) -> List[MemoryItem]:
        """按分类获取知识"""
        try:
            # 确保知识库已初始化
            await self._ensure_knowledge_initialized()

            # 从ChromaDB按分类检索
            results = self.collection.get(
                where={"category": category, "is_active": True},
                include=["documents", "metadatas"],
                limit=limit
            )

            memories = []
            if results["ids"]:
                for i, doc_id in enumerate(results["ids"]):
                    try:
                        content = results["documents"][i]
                        metadata = results["metadatas"][i]

                        # 解析标签
                        if "tags" in metadata:
                            try:
                                metadata["tags"] = json.loads(metadata["tags"])
                            except (json.JSONDecodeError, TypeError):
                                metadata["tags"] = []

                        memory = MemoryItem(
                            id=doc_id,
                            content=content,
                            metadata=metadata,
                            created_at=datetime.fromisoformat(metadata.get("created_at", datetime.now().isoformat())),
                            updated_at=datetime.now()
                        )
                        memories.append(memory)

                    except Exception as e:
                        logger.warning(f"Failed to parse public memory: {e}")
                        continue

            # 按优先级和创建时间排序
            memories.sort(key=lambda x: (x.metadata.get("priority", 1), x.created_at), reverse=True)
            return memories[:limit]

        except Exception as e:
            logger.error(f"按分类获取知识失败: {e}")
            return []
    
    def _generate_summary(self, content: str, max_length: int = 150) -> str:
        """生成内容摘要"""
        if len(content) <= max_length:
            return content
        
        # 尝试在句号处截断
        truncated = content[:max_length]
        last_period = truncated.rfind('。')
        
        if last_period > max_length * 0.7:  # 如果句号位置合理
            return truncated[:last_period + 1]
        else:
            return truncated.strip() + "..."
    
    async def update_memory(self, memory_id: str, content: str = None, metadata: Dict[str, Any] = None) -> bool:
        """更新公共知识"""
        try:
            # ChromaDB不支持直接更新，需要删除后重新添加
            if content is not None or metadata is not None:
                # 先获取现有记录
                existing_results = self.collection.get(
                    ids=[memory_id],
                    include=["documents", "metadatas"]
                )

                if not existing_results["ids"]:
                    logger.warning(f"记忆ID不存在: {memory_id}")
                    return False

                # 获取现有内容和元数据
                existing_content = existing_results["documents"][0]
                existing_metadata = existing_results["metadatas"][0]

                # 更新内容和元数据
                updated_content = content if content is not None else existing_content
                updated_metadata = existing_metadata.copy()
                if metadata is not None:
                    updated_metadata.update(metadata)
                    # 更新时间戳
                    updated_metadata["updated_at"] = datetime.now().isoformat()

                # 删除旧记录
                self.collection.delete(ids=[memory_id])

                # 重新添加更新后的记录
                await self._add_memory_vector(memory_id, updated_content, updated_metadata)
                return True

            return False

        except Exception as e:
            logger.error(f"更新公共知识失败: {e}")
            return False
    
    async def delete_memory(self, memory_id: str) -> bool:
        """删除公共知识"""
        try:
            self.collection.delete(ids=[memory_id])
            return True
        except Exception as e:
            logger.error(f"向量知识删除失败: {e}")
            return False

    async def close(self):
        """关闭记忆服务，清理资源"""
        try:
            # ChromaDB客户端会自动处理连接关闭
            pass
        except Exception as e:
            logger.error(f"关闭向量数据库失败: {e}")

    def _generate_summary(self, content: str, max_length: int = 150) -> str:
        """生成内容摘要"""
        if len(content) <= max_length:
            return content

        # 尝试在句号处截断
        truncated = content[:max_length]
        last_period = truncated.rfind('。')

        if last_period > max_length * 0.7:  # 如果句号位置合理
            return truncated[:last_period + 1]
        else:
            return truncated.strip() + "..."

    async def get_all_categories(self) -> List[str]:
        """获取所有知识分类"""
        try:
            # 确保知识库已初始化
            await self._ensure_knowledge_initialized()

            # 获取所有记录的元数据
            results = self.collection.get(
                where={"is_active": True},
                include=["metadatas"]
            )

            categories = set()
            if results["metadatas"]:
                for metadata in results["metadatas"]:
                    category = metadata.get("category")
                    if category:
                        categories.add(category)

            return sorted(list(categories))

        except Exception as e:
            logger.error(f"获取知识分类失败: {e}")
            return []

    async def get_knowledge_stats(self) -> Dict[str, Any]:
        """获取知识库统计信息"""
        try:
            # 确保知识库已初始化
            await self._ensure_knowledge_initialized()

            # 获取所有记录
            results = self.collection.get(
                include=["metadatas"]
            )

            total_count = len(results["ids"]) if results["ids"] else 0
            active_count = 0
            category_stats = {}

            if results["metadatas"]:
                for metadata in results["metadatas"]:
                    if metadata.get("is_active", True):
                        active_count += 1

                    category = metadata.get("category", "unknown")
                    category_stats[category] = category_stats.get(category, 0) + 1

            return {
                "total_count": total_count,
                "active_count": active_count,
                "inactive_count": total_count - active_count,
                "categories": category_stats,
                "last_updated": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"获取知识库统计失败: {e}")
            return {
                "total_count": 0,
                "active_count": 0,
                "inactive_count": 0,
                "categories": {},
                "last_updated": datetime.now().isoformat()
            }
