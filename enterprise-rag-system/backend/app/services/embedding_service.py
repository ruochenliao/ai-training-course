"""
嵌入模型服务 - 集成通义千问3-8B嵌入模型
"""

import asyncio
from dataclasses import dataclass
from typing import List, Dict, Any, Union

import httpx
import numpy as np
from loguru import logger

from app import qwen_model_manager
from app.core import AIServiceException
from app.core import settings


@dataclass
class EmbeddingRequest:
    """嵌入请求"""
    input: Union[str, List[str]]
    model: str = "text-embedding-v1"
    encoding_format: str = "float"


@dataclass
class EmbeddingResponse:
    """嵌入响应"""
    object: str
    data: List[Dict[str, Any]]
    model: str
    usage: Dict[str, int]


class EmbeddingService:
    """嵌入模型服务类 - 支持通义千问3-8B本地模型和API"""

    def __init__(self):
        self.api_base = settings.EMBEDDING_API_BASE
        self.api_key = settings.EMBEDDING_API_KEY
        self.model_name = settings.EMBEDDING_MODEL_NAME
        self.dimension = settings.EMBEDDING_DIMENSION

        # HTTP客户端配置
        self.timeout = httpx.Timeout(60.0, connect=10.0)
        self.limits = httpx.Limits(max_keepalive_connections=20, max_connections=100)

        # 批处理配置
        self.max_batch_size = settings.EMBEDDING_BATCH_SIZE
        self.max_text_length = settings.EMBEDDING_MAX_LENGTH

        # 通义千问模型服务
        self.qwen_service = None
        self._initialized = False
    
    async def initialize(self):
        """初始化嵌入服务"""
        if self._initialized:
            return

        try:
            self.qwen_service = await qwen_model_manager.get_embedding_service()
            self._initialized = True
            logger.info("嵌入服务初始化完成")
        except Exception as e:
            logger.error(f"嵌入服务初始化失败: {e}")
            # 继续使用API模式

    async def create_embeddings(
        self,
        texts: Union[str, List[str]],
        model: str = None,
        normalize: bool = True
    ) -> Union[List[float], List[List[float]]]:
        """创建嵌入向量 - 优先使用通义千问本地模型"""
        try:
            # 确保服务已初始化
            if not self._initialized:
                await self.initialize()

            # 标准化输入
            if isinstance(texts, str):
                texts = [texts]
                single_input = True
            else:
                single_input = False

            # 文本预处理
            processed_texts = self._preprocess_texts(texts)

            # 优先使用通义千问本地模型
            if self.qwen_service:
                try:
                    all_embeddings = await self.qwen_service.embed_texts(processed_texts)
                    if all_embeddings:
                        # 返回结果
                        if single_input:
                            return all_embeddings[0]
                        else:
                            return all_embeddings
                except Exception as e:
                    logger.warning(f"通义千问模型调用失败，回退到API: {e}")

            # 回退到原有API方式
            all_embeddings = []
            for batch in self._create_batches(processed_texts):
                batch_embeddings = await self._create_batch_embeddings(batch, model)
                all_embeddings.extend(batch_embeddings)

            # 归一化
            if normalize:
                all_embeddings = self._normalize_embeddings(all_embeddings)

            # 返回结果
            if single_input:
                return all_embeddings[0]
            else:
                return all_embeddings

        except Exception as e:
            logger.error(f"创建嵌入向量失败: {e}")
            raise AIServiceException(f"创建嵌入向量失败: {e}")
    
    async def _create_batch_embeddings(
        self, 
        texts: List[str], 
        model: str = None
    ) -> List[List[float]]:
        """批量创建嵌入向量"""
        try:
            request_data = {
                "model": model or self.model_name,
                "input": texts,
                "encoding_format": "float"
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=self.timeout, limits=self.limits) as client:
                response = await client.post(
                    f"{self.api_base}/embeddings",
                    json=request_data,
                    headers=headers
                )
                
                if response.status_code != 200:
                    error_msg = f"嵌入API错误: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    raise AIServiceException(error_msg)
                
                result = response.json()
                
                # 提取嵌入向量
                embeddings = []
                for item in result["data"]:
                    embeddings.append(item["embedding"])
                
                return embeddings
                
        except Exception as e:
            logger.error(f"批量创建嵌入向量失败: {e}")
            raise AIServiceException(f"批量创建嵌入向量失败: {e}")
    
    def _preprocess_texts(self, texts: List[str]) -> List[str]:
        """预处理文本"""
        processed = []
        
        for text in texts:
            # 清理文本
            cleaned_text = text.strip()
            
            # 截断过长的文本
            if len(cleaned_text) > self.max_text_length:
                cleaned_text = cleaned_text[:self.max_text_length]
                logger.warning(f"文本被截断到 {self.max_text_length} 字符")
            
            # 跳过空文本
            if not cleaned_text:
                cleaned_text = " "  # 用空格替代空文本
            
            processed.append(cleaned_text)
        
        return processed
    
    def _create_batches(self, texts: List[str]) -> List[List[str]]:
        """创建批次"""
        batches = []
        
        for i in range(0, len(texts), self.max_batch_size):
            batch = texts[i:i + self.max_batch_size]
            batches.append(batch)
        
        return batches
    
    def _normalize_embeddings(self, embeddings: List[List[float]]) -> List[List[float]]:
        """归一化嵌入向量"""
        normalized = []
        
        for embedding in embeddings:
            # 转换为numpy数组
            vec = np.array(embedding)
            
            # L2归一化
            norm = np.linalg.norm(vec)
            if norm > 0:
                normalized_vec = vec / norm
            else:
                normalized_vec = vec
            
            normalized.append(normalized_vec.tolist())
        
        return normalized
    
    async def compute_similarity(
        self, 
        text1: str, 
        text2: str,
        similarity_type: str = "cosine"
    ) -> float:
        """计算文本相似度"""
        try:
            # 获取嵌入向量
            embeddings = await self.create_embeddings([text1, text2])
            
            vec1 = np.array(embeddings[0])
            vec2 = np.array(embeddings[1])
            
            if similarity_type == "cosine":
                # 余弦相似度
                similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
            elif similarity_type == "euclidean":
                # 欧几里得距离（转换为相似度）
                distance = np.linalg.norm(vec1 - vec2)
                similarity = 1 / (1 + distance)
            elif similarity_type == "dot":
                # 点积相似度
                similarity = np.dot(vec1, vec2)
            else:
                raise ValueError(f"不支持的相似度类型: {similarity_type}")
            
            return float(similarity)
            
        except Exception as e:
            logger.error(f"计算文本相似度失败: {e}")
            raise AIServiceException(f"计算文本相似度失败: {e}")
    
    async def find_most_similar(
        self, 
        query_text: str, 
        candidate_texts: List[str],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """找到最相似的文本"""
        try:
            # 获取所有文本的嵌入向量
            all_texts = [query_text] + candidate_texts
            embeddings = await self.create_embeddings(all_texts)
            
            query_embedding = np.array(embeddings[0])
            candidate_embeddings = [np.array(emb) for emb in embeddings[1:]]
            
            # 计算相似度
            similarities = []
            for i, candidate_embedding in enumerate(candidate_embeddings):
                similarity = np.dot(query_embedding, candidate_embedding)
                similarities.append({
                    "index": i,
                    "text": candidate_texts[i],
                    "similarity": float(similarity)
                })
            
            # 排序并返回top_k
            similarities.sort(key=lambda x: x["similarity"], reverse=True)
            return similarities[:top_k]
            
        except Exception as e:
            logger.error(f"查找最相似文本失败: {e}")
            raise AIServiceException(f"查找最相似文本失败: {e}")
    
    async def cluster_texts(
        self, 
        texts: List[str], 
        num_clusters: int = 5
    ) -> Dict[str, Any]:
        """文本聚类"""
        try:
            # 获取嵌入向量
            embeddings = await self.create_embeddings(texts)
            embeddings_array = np.array(embeddings)
            
            # 使用K-means聚类
            from sklearn.cluster import KMeans
            
            kmeans = KMeans(n_clusters=num_clusters, random_state=42)
            cluster_labels = kmeans.fit_predict(embeddings_array)
            
            # 组织结果
            clusters = {}
            for i, label in enumerate(cluster_labels):
                if label not in clusters:
                    clusters[label] = []
                clusters[label].append({
                    "index": i,
                    "text": texts[i],
                    "embedding": embeddings[i]
                })
            
            # 计算聚类中心
            cluster_centers = kmeans.cluster_centers_.tolist()
            
            return {
                "clusters": clusters,
                "cluster_centers": cluster_centers,
                "num_clusters": num_clusters,
                "inertia": float(kmeans.inertia_)
            }
            
        except Exception as e:
            logger.error(f"文本聚类失败: {e}")
            raise AIServiceException(f"文本聚类失败: {e}")
    
    async def semantic_search(
        self, 
        query: str, 
        documents: List[Dict[str, Any]],
        top_k: int = 10,
        score_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """语义搜索"""
        try:
            # 提取文档文本
            doc_texts = [doc.get("content", "") for doc in documents]
            
            # 获取查询和文档的嵌入向量
            all_texts = [query] + doc_texts
            embeddings = await self.create_embeddings(all_texts)
            
            query_embedding = np.array(embeddings[0])
            doc_embeddings = [np.array(emb) for emb in embeddings[1:]]
            
            # 计算相似度分数
            results = []
            for i, doc_embedding in enumerate(doc_embeddings):
                similarity = np.dot(query_embedding, doc_embedding)
                
                if similarity >= score_threshold:
                    result = {
                        **documents[i],
                        "similarity_score": float(similarity),
                        "rank": len(results) + 1
                    }
                    results.append(result)
            
            # 按相似度排序
            results.sort(key=lambda x: x["similarity_score"], reverse=True)
            
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"语义搜索失败: {e}")
            raise AIServiceException(f"语义搜索失败: {e}")
    
    async def check_model_health(self) -> Dict[str, Any]:
        """检查模型健康状态"""
        try:
            test_text = "This is a test sentence for health check."
            
            start_time = asyncio.get_event_loop().time()
            embedding = await self.create_embeddings(test_text)
            end_time = asyncio.get_event_loop().time()
            
            return {
                "status": "healthy",
                "model": self.model_name,
                "dimension": len(embedding),
                "response_time": end_time - start_time
            }
            
        except Exception as e:
            logger.error(f"嵌入模型健康检查失败: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "model_name": self.model_name,
            "dimension": self.dimension,
            "max_batch_size": self.max_batch_size,
            "max_text_length": self.max_text_length,
            "api_base": self.api_base
        }

    # 兼容性方法，供智能体服务使用
    async def embed_text(self, text: str) -> List[float]:
        """单个文本嵌入（兼容性方法）"""
        return await self.create_embeddings(text)

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """批量文本嵌入（兼容性方法）"""
        return await self.create_embeddings(texts)

    async def embed_query(self, query: str) -> List[float]:
        """查询嵌入（兼容性方法）"""
        return await self.create_embeddings(query)


# 全局嵌入服务实例
embedding_service = EmbeddingService()
