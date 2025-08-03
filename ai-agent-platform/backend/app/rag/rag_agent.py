"""
RAG智能体

整合文档处理、检索和生成功能的完整RAG系统。
"""

import logging
from typing import List, Dict, Any, Optional
import json
from datetime import datetime

from ..agents.base import BaseAgent, AgentMessage, AgentConfig
from .vectorstore import VectorStore, Document
from .processor import DocumentProcessor, ChunkStrategy
from .retriever import DocumentRetriever
from .generator import ResponseGenerator, GenerationStrategy, CitationStyle
from .embeddings import embedding_manager

logger = logging.getLogger(__name__)


class RAGConfig:
    """RAG配置"""
    
    def __init__(self, 
                 vector_store_type: str = "memory",
                 embedding_model: str = "openai",
                 chunk_strategy: ChunkStrategy = ChunkStrategy.FIXED_SIZE,
                 chunk_size: int = 1000,
                 chunk_overlap: int = 200,
                 retrieval_top_k: int = 5,
                 generation_strategy: GenerationStrategy = GenerationStrategy.ABSTRACTIVE,
                 citation_style: CitationStyle = CitationStyle.NUMBERED,
                 enable_query_expansion: bool = True,
                 enable_reranking: bool = True):
        self.vector_store_type = vector_store_type
        self.embedding_model = embedding_model
        self.chunk_strategy = chunk_strategy
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.retrieval_top_k = retrieval_top_k
        self.generation_strategy = generation_strategy
        self.citation_style = citation_style
        self.enable_query_expansion = enable_query_expansion
        self.enable_reranking = enable_reranking


class RAGAgent(BaseAgent):
    """RAG智能体"""
    
    def __init__(self, config: AgentConfig = None, rag_config: RAGConfig = None):
        if config is None:
            config = AgentConfig(
                name="RAGAgent",
                description="基于检索增强生成的知识库问答智能体",
                model="gpt-4o",
                temperature=0.7,
                system_prompt=self._get_system_prompt()
            )
        
        super().__init__(config)
        
        # RAG配置
        self.rag_config = rag_config or RAGConfig()
        
        # 初始化组件
        self.vector_store = None
        self.document_processor = DocumentProcessor()
        self.retriever = None
        self.generator = ResponseGenerator(model_name=self.model)
        
        # 知识库管理
        self.knowledge_bases: Dict[str, str] = {}  # kb_id -> kb_name
        self.document_count = 0
    
    async def initialize(self):
        """初始化RAG系统"""
        try:
            # 初始化向量存储
            self.vector_store = VectorStore(
                store_type=self.rag_config.vector_store_type,
                dimension=embedding_manager.get_dimension(self.rag_config.embedding_model)
            )
            await self.vector_store.initialize()
            
            # 初始化检索器
            self.retriever = DocumentRetriever(self.vector_store)
            
            # 配置文档处理器
            if self.rag_config.chunk_strategy == ChunkStrategy.FIXED_SIZE:
                self.document_processor.configure_chunker(
                    ChunkStrategy.FIXED_SIZE,
                    chunk_size=self.rag_config.chunk_size,
                    overlap=self.rag_config.chunk_overlap
                )
            
            logger.info("RAG系统初始化完成")
            
        except Exception as e:
            logger.error(f"RAG系统初始化失败: {e}")
            raise
    
    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是一个专业的知识库问答助手，基于RAG（检索增强生成）技术为用户提供准确的答案。

你的能力包括：
1. 理解用户的问题并检索相关文档
2. 基于检索到的文档生成准确、有用的回答
3. 提供信息来源和引用
4. 处理复杂的多步骤问题

回答原则：
1. 基于事实：只基于检索到的文档内容回答
2. 准确引用：明确标注信息来源
3. 承认限制：如果没有相关信息，诚实说明
4. 结构清晰：组织好回答的逻辑结构
5. 用户友好：使用易懂的语言

请根据用户的问题，检索相关文档并生成高质量的回答。"""
    
    async def process_message(self, message: AgentMessage) -> AgentMessage:
        """处理RAG查询"""
        try:
            # 解析查询参数
            query = message.content
            metadata = message.metadata or {}
            
            # 获取知识库过滤器
            kb_filter = self._get_kb_filter(metadata)
            
            # 执行RAG查询
            response = await self.query(
                query=query,
                kb_filter=kb_filter,
                top_k=metadata.get("top_k", self.rag_config.retrieval_top_k)
            )
            
            # 构建响应消息
            response_message = AgentMessage(
                id=f"rag_response_{message.id}",
                sender=self.name,
                receiver=message.sender,
                content=response["answer"],
                message_type="rag_response",
                metadata={
                    "original_message_id": message.id,
                    "sources": response["sources"],
                    "confidence": response["confidence"],
                    "generation_metadata": response["metadata"]
                }
            )
            
            return response_message
            
        except Exception as e:
            logger.error(f"RAG查询处理失败: {e}")
            error_response = AgentMessage(
                id=f"rag_error_{message.id}",
                sender=self.name,
                receiver=message.sender,
                content=f"知识库查询失败: {str(e)}",
                message_type="error"
            )
            return error_response
    
    async def query(self, query: str, kb_filter: Dict[str, Any] = None, 
                   top_k: int = None) -> Dict[str, Any]:
        """执行RAG查询"""
        try:
            if not self.vector_store or not self.retriever:
                await self.initialize()
            
            top_k = top_k or self.rag_config.retrieval_top_k
            
            # 检索相关文档
            search_results = await self.retriever.retrieve(
                query=query,
                top_k=top_k,
                expand_query=self.rag_config.enable_query_expansion,
                rerank=self.rag_config.enable_reranking,
                filters=kb_filter
            )
            
            # 生成回答
            generated_response = await self.generator.generate(
                query=query,
                search_results=search_results,
                strategy=self.rag_config.generation_strategy,
                citation_style=self.rag_config.citation_style
            )
            
            return {
                "answer": generated_response.answer,
                "sources": generated_response.sources,
                "confidence": generated_response.confidence,
                "metadata": generated_response.metadata,
                "retrieved_count": len(search_results)
            }
            
        except Exception as e:
            logger.error(f"RAG查询失败: {e}")
            return {
                "answer": "抱歉，查询过程中出现错误。",
                "sources": [],
                "confidence": 0.0,
                "metadata": {"error": str(e)},
                "retrieved_count": 0
            }
    
    async def add_document(self, content: str, metadata: Dict[str, Any] = None,
                          kb_id: str = "default") -> Dict[str, Any]:
        """添加文档到知识库"""
        try:
            if not self.vector_store:
                await self.initialize()
            
            # 添加知识库信息到元数据
            doc_metadata = metadata or {}
            doc_metadata["knowledge_base_id"] = kb_id
            doc_metadata["added_at"] = datetime.now().isoformat()
            
            # 处理文档并生成嵌入
            documents = await self.document_processor.process_and_embed(
                text=content,
                strategy=self.rag_config.chunk_strategy,
                metadata=doc_metadata,
                model_name=self.rag_config.embedding_model
            )
            
            # 存储到向量数据库
            doc_ids = await self.vector_store.add_documents(documents)
            
            # 更新统计
            self.document_count += len(documents)
            if kb_id not in self.knowledge_bases:
                self.knowledge_bases[kb_id] = f"知识库_{kb_id}"
            
            logger.info(f"添加文档成功: {len(documents)} 个块, 知识库: {kb_id}")
            
            return {
                "success": True,
                "document_ids": doc_ids,
                "chunk_count": len(documents),
                "knowledge_base_id": kb_id
            }
            
        except Exception as e:
            logger.error(f"添加文档失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def add_file(self, file_path: str, metadata: Dict[str, Any] = None,
                      kb_id: str = "default") -> Dict[str, Any]:
        """添加文件到知识库"""
        try:
            if not self.vector_store:
                await self.initialize()
            
            # 处理文件
            chunks = self.document_processor.process_file(
                file_path=file_path,
                strategy=self.rag_config.chunk_strategy,
                metadata=metadata
            )
            
            # 生成嵌入
            texts = [chunk.content for chunk in chunks]
            embeddings = await embedding_manager.embed_texts(
                texts, self.rag_config.embedding_model
            )
            
            # 创建文档对象
            documents = []
            for chunk, embedding in zip(chunks, embeddings):
                chunk.metadata["knowledge_base_id"] = kb_id
                chunk.metadata["added_at"] = datetime.now().isoformat()
                doc = chunk.to_document(embedding=embedding)
                documents.append(doc)
            
            # 存储到向量数据库
            doc_ids = await self.vector_store.add_documents(documents)
            
            # 更新统计
            self.document_count += len(documents)
            if kb_id not in self.knowledge_bases:
                self.knowledge_bases[kb_id] = f"知识库_{kb_id}"
            
            logger.info(f"添加文件成功: {file_path}, {len(documents)} 个块")
            
            return {
                "success": True,
                "document_ids": doc_ids,
                "chunk_count": len(documents),
                "knowledge_base_id": kb_id,
                "file_path": file_path
            }
            
        except Exception as e:
            logger.error(f"添加文件失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def delete_document(self, doc_id: str) -> bool:
        """删除文档"""
        try:
            if not self.vector_store:
                await self.initialize()
            
            success = await self.vector_store.delete_document(doc_id)
            if success:
                self.document_count = max(0, self.document_count - 1)
            
            return success
            
        except Exception as e:
            logger.error(f"删除文档失败: {e}")
            return False
    
    async def get_knowledge_bases(self) -> List[Dict[str, Any]]:
        """获取知识库列表"""
        try:
            kb_list = []
            for kb_id, kb_name in self.knowledge_bases.items():
                # 统计该知识库的文档数量
                count = await self.vector_store.count_documents({"knowledge_base_id": kb_id})
                
                kb_list.append({
                    "id": kb_id,
                    "name": kb_name,
                    "document_count": count,
                    "created_at": datetime.now().isoformat()  # 简化处理
                })
            
            return kb_list
            
        except Exception as e:
            logger.error(f"获取知识库列表失败: {e}")
            return []
    
    async def search_documents(self, query: str, kb_id: str = None, 
                              top_k: int = 10) -> List[Dict[str, Any]]:
        """搜索文档"""
        try:
            if not self.retriever:
                await self.initialize()
            
            # 构建过滤器
            filters = {}
            if kb_id:
                filters["knowledge_base_id"] = kb_id
            
            # 执行搜索
            results = await self.retriever.retrieve(
                query=query,
                top_k=top_k,
                filters=filters
            )
            
            # 转换结果格式
            search_results = []
            for result in results:
                search_results.append({
                    "id": result.document.id,
                    "content": result.document.content,
                    "score": result.score,
                    "rank": result.rank,
                    "metadata": result.document.metadata
                })
            
            return search_results
            
        except Exception as e:
            logger.error(f"搜索文档失败: {e}")
            return []
    
    def _get_kb_filter(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """获取知识库过滤器"""
        filters = {}
        
        # 知识库ID过滤
        if "knowledge_base_id" in metadata:
            filters["knowledge_base_id"] = metadata["knowledge_base_id"]
        
        # 其他过滤条件
        for key in ["document_type", "author", "category"]:
            if key in metadata:
                filters[key] = metadata[key]
        
        return filters
    
    async def generate_response(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """生成响应"""
        # 如果是简单的生成任务，直接调用基类方法
        if not context or "query" not in context:
            return await super().generate_response(prompt, context)
        
        # 如果是RAG查询，使用RAG流程
        result = await self.query(context["query"])
        return result["answer"]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "document_count": self.document_count,
            "knowledge_base_count": len(self.knowledge_bases),
            "knowledge_bases": list(self.knowledge_bases.keys()),
            "config": {
                "vector_store_type": self.rag_config.vector_store_type,
                "embedding_model": self.rag_config.embedding_model,
                "chunk_strategy": self.rag_config.chunk_strategy.value,
                "retrieval_top_k": self.rag_config.retrieval_top_k
            }
        }
