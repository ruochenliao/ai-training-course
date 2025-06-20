"""
搜索工具集
基于MCP协议的搜索和检索工具实现
"""

import asyncio
from typing import Dict, Any, List, Optional
import httpx
from datetime import datetime
import json

from loguru import logger
from app.services.mcp_service import MCPTool, MCPContext
from app.services.enhanced_document_service import enhanced_document_service
from app.services.memory.factory import MemoryServiceFactory


class SearchTools:
    """搜索工具集"""
    
    def __init__(self):
        """初始化搜索工具"""
        self.client = httpx.AsyncClient(timeout=30.0)
        self.memory_factory = MemoryServiceFactory()
        
    async def get_tools(self) -> List[MCPTool]:
        """获取所有搜索工具"""
        return [
            MCPTool(
                name="search_documents",
                description="在用户上传的文档中搜索相关内容",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "搜索查询"
                        },
                        "conversation_id": {
                            "type": "string",
                            "description": "对话ID，用于限制搜索范围"
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "返回结果数量",
                            "default": 5
                        },
                        "similarity_threshold": {
                            "type": "number",
                            "description": "相似度阈值",
                            "default": 0.7
                        }
                    },
                    "required": ["query"]
                },
                handler=self.search_documents,
                category="search"
            ),
            
            MCPTool(
                name="search_knowledge_base",
                description="在知识库中搜索相关信息",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "搜索查询"
                        },
                        "knowledge_type": {
                            "type": "string",
                            "description": "知识库类型",
                            "enum": ["private", "public"],
                            "default": "public"
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "返回结果数量",
                            "default": 5
                        }
                    },
                    "required": ["query"]
                },
                handler=self.search_knowledge_base,
                category="search"
            ),
            
            MCPTool(
                name="search_chat_history",
                description="在聊天历史中搜索相关对话",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "搜索查询"
                        },
                        "user_id": {
                            "type": "string",
                            "description": "用户ID"
                        },
                        "days_back": {
                            "type": "integer",
                            "description": "搜索多少天内的历史",
                            "default": 30
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "返回结果数量",
                            "default": 5
                        }
                    },
                    "required": ["query", "user_id"]
                },
                handler=self.search_chat_history,
                category="search"
            ),
            
            MCPTool(
                name="web_search",
                description="在互联网上搜索信息",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "搜索查询"
                        },
                        "num_results": {
                            "type": "integer",
                            "description": "返回结果数量",
                            "default": 5
                        },
                        "language": {
                            "type": "string",
                            "description": "搜索语言",
                            "default": "zh-CN"
                        }
                    },
                    "required": ["query"]
                },
                handler=self.web_search,
                category="search"
            ),
            
            MCPTool(
                name="semantic_search",
                description="基于语义相似度的智能搜索",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "搜索查询"
                        },
                        "search_scope": {
                            "type": "array",
                            "description": "搜索范围",
                            "items": {
                                "type": "string",
                                "enum": ["documents", "knowledge", "chat_history", "web"]
                            },
                            "default": ["documents", "knowledge"]
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "每个范围返回的结果数量",
                            "default": 3
                        }
                    },
                    "required": ["query"]
                },
                handler=self.semantic_search,
                category="search"
            ),
            
            MCPTool(
                name="search_similar_questions",
                description="搜索相似的问题和答案",
                parameters={
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": "用户问题"
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "返回结果数量",
                            "default": 5
                        }
                    },
                    "required": ["question"]
                },
                handler=self.search_similar_questions,
                category="search"
            )
        ]
    
    async def search_documents(self, params: Dict[str, Any], context: Optional[MCPContext] = None) -> Dict[str, Any]:
        """搜索文档"""
        try:
            query = params["query"]
            conversation_id = params.get("conversation_id")
            top_k = params.get("top_k", 5)
            similarity_threshold = params.get("similarity_threshold", 0.7)
            
            # 获取用户ID
            user_id = context.user_id if context else None
            if not user_id:
                return {"error": "需要用户ID进行文档搜索"}
            
            # 调用文档搜索服务
            results = await enhanced_document_service.search_documents(
                query=query,
                user_id=int(user_id),
                conversation_id=conversation_id,
                top_k=top_k,
                similarity_threshold=similarity_threshold
            )
            
            return {
                "query": query,
                "results": results,
                "total": len(results),
                "search_type": "documents"
            }
            
        except Exception as e:
            logger.error(f"文档搜索失败: {e}")
            return {"error": str(e), "results": []}
    
    async def search_knowledge_base(self, params: Dict[str, Any], context: Optional[MCPContext] = None) -> Dict[str, Any]:
        """搜索知识库"""
        try:
            query = params["query"]
            knowledge_type = params.get("knowledge_type", "public")
            top_k = params.get("top_k", 5)
            
            # 获取用户ID
            user_id = context.user_id if context else "default"
            
            # 获取对应的记忆服务
            if knowledge_type == "private":
                memory_service = self.memory_factory.get_private_memory_service(user_id)
            else:
                memory_service = self.memory_factory.get_public_memory_service()
            
            # 执行搜索
            results = await memory_service.search(query, top_k=top_k)
            
            # 格式化结果
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "content": result.get("content", ""),
                    "metadata": result.get("metadata", {}),
                    "score": result.get("score", 0.0),
                    "source": f"{knowledge_type}_knowledge_base"
                })
            
            return {
                "query": query,
                "results": formatted_results,
                "total": len(formatted_results),
                "search_type": f"{knowledge_type}_knowledge_base"
            }
            
        except Exception as e:
            logger.error(f"知识库搜索失败: {e}")
            return {"error": str(e), "results": []}
    
    async def search_chat_history(self, params: Dict[str, Any], context: Optional[MCPContext] = None) -> Dict[str, Any]:
        """搜索聊天历史"""
        try:
            query = params["query"]
            user_id = params["user_id"]
            days_back = params.get("days_back", 30)
            top_k = params.get("top_k", 5)
            
            # 获取聊天记忆服务
            chat_memory = self.memory_factory.get_chat_memory_service(user_id)
            
            # 执行搜索
            results = await chat_memory.search(query, top_k=top_k)
            
            # 格式化结果
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "content": result.get("content", ""),
                    "metadata": result.get("metadata", {}),
                    "score": result.get("score", 0.0),
                    "timestamp": result.get("metadata", {}).get("timestamp"),
                    "source": "chat_history"
                })
            
            return {
                "query": query,
                "results": formatted_results,
                "total": len(formatted_results),
                "search_type": "chat_history"
            }
            
        except Exception as e:
            logger.error(f"聊天历史搜索失败: {e}")
            return {"error": str(e), "results": []}
    
    async def web_search(self, params: Dict[str, Any], context: Optional[MCPContext] = None) -> Dict[str, Any]:
        """网络搜索"""
        try:
            query = params["query"]
            num_results = params.get("num_results", 5)
            language = params.get("language", "zh-CN")
            
            # 这里可以集成真实的搜索API，如Google、Bing等
            # 目前返回模拟结果
            mock_results = [
                {
                    "title": f"关于'{query}'的搜索结果 1",
                    "url": f"https://example.com/search1?q={query}",
                    "snippet": f"这是关于{query}的详细信息，包含了相关的技术细节和解决方案。",
                    "source": "web_search",
                    "timestamp": datetime.now().isoformat()
                },
                {
                    "title": f"关于'{query}'的搜索结果 2",
                    "url": f"https://example.com/search2?q={query}",
                    "snippet": f"更多关于{query}的信息，提供了实用的建议和最佳实践。",
                    "source": "web_search",
                    "timestamp": datetime.now().isoformat()
                }
            ]
            
            return {
                "query": query,
                "results": mock_results[:num_results],
                "total": len(mock_results[:num_results]),
                "search_type": "web_search",
                "language": language
            }
            
        except Exception as e:
            logger.error(f"网络搜索失败: {e}")
            return {"error": str(e), "results": []}
    
    async def semantic_search(self, params: Dict[str, Any], context: Optional[MCPContext] = None) -> Dict[str, Any]:
        """语义搜索"""
        try:
            query = params["query"]
            search_scope = params.get("search_scope", ["documents", "knowledge"])
            top_k = params.get("top_k", 3)
            
            all_results = []
            
            # 在不同范围内搜索
            for scope in search_scope:
                if scope == "documents":
                    doc_results = await self.search_documents(
                        {"query": query, "top_k": top_k}, context
                    )
                    all_results.extend(doc_results.get("results", []))
                
                elif scope == "knowledge":
                    kb_results = await self.search_knowledge_base(
                        {"query": query, "top_k": top_k}, context
                    )
                    all_results.extend(kb_results.get("results", []))
                
                elif scope == "chat_history" and context:
                    chat_results = await self.search_chat_history(
                        {"query": query, "user_id": context.user_id, "top_k": top_k}, context
                    )
                    all_results.extend(chat_results.get("results", []))
                
                elif scope == "web":
                    web_results = await self.web_search(
                        {"query": query, "num_results": top_k}, context
                    )
                    all_results.extend(web_results.get("results", []))
            
            # 按相似度排序
            all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
            
            return {
                "query": query,
                "results": all_results[:top_k * len(search_scope)],
                "total": len(all_results),
                "search_type": "semantic_search",
                "search_scope": search_scope
            }
            
        except Exception as e:
            logger.error(f"语义搜索失败: {e}")
            return {"error": str(e), "results": []}
    
    async def search_similar_questions(self, params: Dict[str, Any], context: Optional[MCPContext] = None) -> Dict[str, Any]:
        """搜索相似问题"""
        try:
            question = params["question"]
            top_k = params.get("top_k", 5)
            
            # 这里可以集成FAQ数据库或者使用机器学习模型
            # 目前返回模拟的相似问题
            mock_similar_questions = [
                {
                    "question": f"与'{question}'相关的常见问题1",
                    "answer": "这是一个详细的答案，解释了相关的概念和解决方案。",
                    "similarity_score": 0.85,
                    "category": "常见问题",
                    "source": "faq_database"
                },
                {
                    "question": f"关于'{question}'的另一个问题",
                    "answer": "这里提供了另一种角度的解答和建议。",
                    "similarity_score": 0.78,
                    "category": "技术支持",
                    "source": "faq_database"
                }
            ]
            
            return {
                "original_question": question,
                "similar_questions": mock_similar_questions[:top_k],
                "total": len(mock_similar_questions[:top_k]),
                "search_type": "similar_questions"
            }
            
        except Exception as e:
            logger.error(f"搜索相似问题失败: {e}")
            return {"error": str(e), "similar_questions": []}
    
    async def close(self):
        """关闭HTTP客户端"""
        await self.client.aclose()


# 全局搜索工具实例
search_tools = SearchTools()
