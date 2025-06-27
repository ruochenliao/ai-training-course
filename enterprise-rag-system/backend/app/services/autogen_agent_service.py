"""
AutoGen智能体协作服务 - 企业级RAG系统
严格按照技术栈要求：AutoGen (microsoft/autogen) 多智能体协作和答案融合
"""
import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

import autogen
from app.core.config import settings
from app.services.bge_reranker_service import bge_reranker_service
from app.services.deepseek_llm_service import deepseek_llm_service
from app.services.milvus_vector_service import milvus_service
from app.services.neo4j_graph_service import neo4j_service
from app.services.qwen_multimodal_service import qwen_multimodal_service
from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager
from loguru import logger


class AutoGenAgentService:
    """AutoGen智能体协作服务"""
    
    def __init__(self):
        self.agents = {}
        self.group_chats = {}
        self.conversation_history = {}
        
        # LLM配置
        self.llm_config = {
            "config_list": [
                {
                    "model": "deepseek-chat",
                    "api_key": settings.DEEPSEEK_API_KEY,
                    "base_url": "https://api.deepseek.com/v1",
                    "api_type": "openai"
                }
            ],
            "temperature": 0.7,
            "timeout": 60,
            "cache_seed": None  # 禁用缓存以确保实时性
        }
        
        # 智能体配置
        self.agent_configs = {
            "retrieval_agent": {
                "name": "检索智能体",
                "system_message": """你是一个专业的信息检索智能体，负责从知识库中检索相关信息。
你的职责：
1. 分析用户查询，确定检索策略（语义、图谱、混合）
2. 执行多源检索，获取相关文档片段
3. 评估检索结果的相关性和质量
4. 为其他智能体提供结构化的检索结果

请始终以JSON格式返回检索结果，包含相关性评分。""",
                "max_consecutive_auto_reply": 3
            },
            "fusion_agent": {
                "name": "融合智能体",
                "system_message": """你是一个信息融合智能体，负责整合多个检索结果并生成综合答案。
你的职责：
1. 接收检索智能体提供的多源信息
2. 分析信息的一致性和互补性
3. 识别信息冲突并进行权重评估
4. 融合信息生成连贯、准确的综合答案
5. 标注信息来源和置信度

请确保答案逻辑清晰，引用具体来源。""",
                "max_consecutive_auto_reply": 2
            },
            "validation_agent": {
                "name": "验证智能体",
                "system_message": """你是一个质量验证智能体，负责事实核查和一致性验证。
你的职责：
1. 验证融合答案的事实准确性
2. 检查逻辑一致性和完整性
3. 识别潜在的错误或遗漏
4. 评估答案质量并提供改进建议
5. 确保最终答案符合用户需求

如果发现问题，请明确指出并建议修正方案。""",
                "max_consecutive_auto_reply": 2
            }
        }
    
    async def initialize_agents(self):
        """初始化智能体"""
        try:
            # 创建检索智能体
            self.agents["retrieval_agent"] = AssistantAgent(
                name=self.agent_configs["retrieval_agent"]["name"],
                system_message=self.agent_configs["retrieval_agent"]["system_message"],
                llm_config=self.llm_config,
                max_consecutive_auto_reply=self.agent_configs["retrieval_agent"]["max_consecutive_auto_reply"]
            )
            
            # 注册检索函数
            self.agents["retrieval_agent"].register_function(
                function_map={
                    "search_knowledge_base": self._search_knowledge_base,
                    "search_entities": self._search_entities,
                    "get_entity_relations": self._get_entity_relations
                }
            )
            
            # 创建融合智能体
            self.agents["fusion_agent"] = AssistantAgent(
                name=self.agent_configs["fusion_agent"]["name"],
                system_message=self.agent_configs["fusion_agent"]["system_message"],
                llm_config=self.llm_config,
                max_consecutive_auto_reply=self.agent_configs["fusion_agent"]["max_consecutive_auto_reply"]
            )
            
            # 创建验证智能体
            self.agents["validation_agent"] = AssistantAgent(
                name=self.agent_configs["validation_agent"]["name"],
                system_message=self.agent_configs["validation_agent"]["system_message"],
                llm_config=self.llm_config,
                max_consecutive_auto_reply=self.agent_configs["validation_agent"]["max_consecutive_auto_reply"]
            )
            
            # 创建用户代理
            self.agents["user_proxy"] = UserProxyAgent(
                name="用户代理",
                human_input_mode="NEVER",
                max_consecutive_auto_reply=0,
                code_execution_config=False
            )
            
            logger.info("AutoGen智能体初始化完成")
            
        except Exception as e:
            logger.error(f"智能体初始化失败: {e}")
            raise
    
    async def _search_knowledge_base(
        self,
        knowledge_base_id: int,
        query: str,
        search_type: str = "hybrid",
        top_k: int = 10
    ) -> Dict[str, Any]:
        """搜索知识库"""
        try:
            if search_type == "semantic":
                results = await milvus_service.search_vectors(
                    f"kb_{knowledge_base_id}", query, top_k
                )
            elif search_type == "graph":
                entities = await neo4j_service.search_entities(
                    knowledge_base_id, query, None, top_k
                )
                results = []
                for entity in entities:
                    contexts = await neo4j_service.get_entity_context(
                        entity["name"], knowledge_base_id, 3
                    )
                    for context in contexts:
                        results.append({
                            "content": context["content"],
                            "score": entity["confidence"],
                            "source": "graph",
                            "entity": entity["name"]
                        })
            else:  # hybrid
                # 并行执行语义和图谱检索
                semantic_results = await milvus_service.search_vectors(
                    f"kb_{knowledge_base_id}", query, top_k // 2
                )
                
                entities = await neo4j_service.search_entities(
                    knowledge_base_id, query, None, top_k // 2
                )
                
                graph_results = []
                for entity in entities:
                    contexts = await neo4j_service.get_entity_context(
                        entity["name"], knowledge_base_id, 2
                    )
                    for context in contexts:
                        graph_results.append({
                            "content": context["content"],
                            "score": entity["confidence"],
                            "source": "graph",
                            "entity": entity["name"]
                        })
                
                # 合并结果
                all_results = []
                for result in semantic_results:
                    all_results.append({
                        "content": result["content"],
                        "score": result["score"],
                        "source": "semantic",
                        "document_id": result["document_id"]
                    })
                
                all_results.extend(graph_results)
                
                # 重排序
                if all_results:
                    passages = [r["content"] for r in all_results]
                    reranked = await bge_reranker_service.rerank_and_sort(
                        query, passages, top_k
                    )
                    
                    results = []
                    for idx, passage, score in reranked:
                        original_result = all_results[idx]
                        original_result["rerank_score"] = score
                        results.append(original_result)
                else:
                    results = []
            
            return {
                "success": True,
                "results": results,
                "total_count": len(results),
                "search_type": search_type
            }
            
        except Exception as e:
            logger.error(f"知识库搜索失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "results": []
            }
    
    async def _search_entities(
        self,
        knowledge_base_id: int,
        query: str,
        entity_types: Optional[List[str]] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """搜索实体"""
        try:
            entities = await neo4j_service.search_entities(
                knowledge_base_id, query, entity_types, limit
            )
            
            return {
                "success": True,
                "entities": entities,
                "total_count": len(entities)
            }
            
        except Exception as e:
            logger.error(f"实体搜索失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "entities": []
            }
    
    async def _get_entity_relations(
        self,
        knowledge_base_id: int,
        entity_name: str,
        max_hops: int = 2,
        limit: int = 10
    ) -> Dict[str, Any]:
        """获取实体关系"""
        try:
            related_entities = await neo4j_service.find_related_entities(
                entity_name, knowledge_base_id, max_hops, limit
            )
            
            return {
                "success": True,
                "entity_name": entity_name,
                "related_entities": related_entities,
                "total_count": len(related_entities)
            }
            
        except Exception as e:
            logger.error(f"获取实体关系失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "related_entities": []
            }

    async def create_group_chat(
        self,
        conversation_id: str,
        knowledge_base_id: int,
        agents: Optional[List[str]] = None
    ) -> str:
        """创建群聊"""
        try:
            if not self.agents:
                await self.initialize_agents()

            # 选择参与的智能体
            if agents is None:
                agents = ["retrieval_agent", "fusion_agent", "validation_agent"]

            selected_agents = [self.agents[agent_name] for agent_name in agents if agent_name in self.agents]
            selected_agents.append(self.agents["user_proxy"])

            # 创建群聊
            group_chat = GroupChat(
                agents=selected_agents,
                messages=[],
                max_round=10,
                speaker_selection_method="round_robin"
            )

            # 创建群聊管理器
            manager = GroupChatManager(
                groupchat=group_chat,
                llm_config=self.llm_config
            )

            # 存储群聊信息
            chat_id = f"{conversation_id}_{knowledge_base_id}"
            self.group_chats[chat_id] = {
                "group_chat": group_chat,
                "manager": manager,
                "knowledge_base_id": knowledge_base_id,
                "created_at": datetime.now(),
                "agents": agents
            }

            logger.info(f"群聊创建成功: {chat_id}")
            return chat_id

        except Exception as e:
            logger.error(f"创建群聊失败: {e}")
            raise

    async def process_query(
        self,
        chat_id: str,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """处理查询"""
        try:
            if chat_id not in self.group_chats:
                raise ValueError(f"群聊不存在: {chat_id}")

            chat_info = self.group_chats[chat_id]
            manager = chat_info["manager"]
            knowledge_base_id = chat_info["knowledge_base_id"]

            # 构建查询消息
            query_message = f"""
用户查询: {query}
知识库ID: {knowledge_base_id}
"""

            if context:
                query_message += f"上下文信息: {json.dumps(context, ensure_ascii=False)}\n"

            query_message += """
请按照以下步骤协作处理:
1. 检索智能体: 执行多源检索，获取相关信息
2. 融合智能体: 整合检索结果，生成综合答案
3. 验证智能体: 验证答案质量，提供最终结果
"""

            # 启动群聊
            start_time = datetime.now()

            # 使用异步方式启动对话
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                self._run_group_chat,
                manager,
                query_message
            )

            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds() * 1000

            # 提取最终答案
            final_answer = self._extract_final_answer(chat_info["group_chat"].messages)

            # 记录对话历史
            if chat_id not in self.conversation_history:
                self.conversation_history[chat_id] = []

            self.conversation_history[chat_id].append({
                "query": query,
                "answer": final_answer,
                "processing_time_ms": processing_time,
                "timestamp": start_time.isoformat(),
                "messages": chat_info["group_chat"].messages[-10:]  # 保留最近10条消息
            })

            return {
                "success": True,
                "answer": final_answer,
                "processing_time_ms": processing_time,
                "agents_involved": chat_info["agents"],
                "message_count": len(chat_info["group_chat"].messages)
            }

        except Exception as e:
            logger.error(f"处理查询失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "answer": "抱歉，处理您的查询时出现了错误。"
            }

    def _run_group_chat(self, manager, message: str):
        """运行群聊（同步方法）"""
        return self.agents["user_proxy"].initiate_chat(
            manager,
            message=message
        )

    def _extract_final_answer(self, messages: List[Dict[str, Any]]) -> str:
        """提取最终答案"""
        try:
            # 从消息中提取验证智能体的最后回复作为最终答案
            for message in reversed(messages):
                if message.get("name") == "验证智能体":
                    content = message.get("content", "")
                    if content and "最终答案" in content:
                        return content

            # 如果没有找到验证智能体的回复，使用融合智能体的回复
            for message in reversed(messages):
                if message.get("name") == "融合智能体":
                    return message.get("content", "")

            # 如果都没有，使用最后一条非用户消息
            for message in reversed(messages):
                if message.get("name") != "用户代理":
                    return message.get("content", "")

            return "抱歉，无法生成有效的答案。"

        except Exception as e:
            logger.error(f"提取最终答案失败: {e}")
            return "抱歉，处理答案时出现错误。"

    async def get_conversation_history(self, chat_id: str) -> List[Dict[str, Any]]:
        """获取对话历史"""
        return self.conversation_history.get(chat_id, [])

    async def clear_conversation_history(self, chat_id: str):
        """清除对话历史"""
        if chat_id in self.conversation_history:
            del self.conversation_history[chat_id]

        if chat_id in self.group_chats:
            self.group_chats[chat_id]["group_chat"].messages = []

    async def get_agent_stats(self) -> Dict[str, Any]:
        """获取智能体统计信息"""
        return {
            "total_agents": len(self.agents),
            "active_group_chats": len(self.group_chats),
            "total_conversations": sum(len(history) for history in self.conversation_history.values()),
            "agent_configs": self.agent_configs,
            "llm_config": {
                "model": self.llm_config["config_list"][0]["model"],
                "temperature": self.llm_config["temperature"]
            }
        }

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            if not self.agents:
                await self.initialize_agents()

            # 检查DeepSeek LLM服务
            llm_health = await deepseek_llm_service.health_check()

            return {
                "status": "healthy" if llm_health["status"] == "healthy" else "unhealthy",
                "agents_initialized": len(self.agents) > 0,
                "total_agents": len(self.agents),
                "llm_service": llm_health,
                "framework": "AutoGen"
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "agents_initialized": False
            }


# 全局AutoGen智能体服务实例
autogen_service = AutoGenAgentService()


# 便捷函数
async def create_agent_conversation(
    conversation_id: str,
    knowledge_base_id: int
) -> str:
    """创建智能体对话的便捷函数"""
    return await autogen_service.create_group_chat(conversation_id, knowledge_base_id)


async def ask_agents(
    chat_id: str,
    query: str,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """向智能体提问的便捷函数"""
    return await autogen_service.process_query(chat_id, query, context)
