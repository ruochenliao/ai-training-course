"""
路由智能体

负责分析用户请求并将其路由到合适的专业智能体。
"""

import json
import logging
from typing import Dict, Any, List, Optional
from .base import BaseAgent, AgentMessage, AgentConfig
from .llm_interface import llm_manager

logger = logging.getLogger(__name__)


class RouterAgent(BaseAgent):
    """路由智能体"""
    
    def __init__(self, config: AgentConfig = None):
        if config is None:
            config = AgentConfig(
                name="RouterAgent",
                description="负责分析用户请求并路由到合适的专业智能体",
                model="gpt-4o",
                temperature=0.3,
                system_prompt=self._get_system_prompt()
            )
        super().__init__(config)
        
        # 可用的智能体类型
        self.available_agents = {
            "customer_service": {
                "name": "智能客服",
                "description": "处理客户咨询、投诉、售后等问题",
                "capabilities": ["客户服务", "问题解答", "投诉处理", "产品咨询"]
            },
            "text2sql": {
                "name": "数据分析",
                "description": "将自然语言转换为SQL查询，进行数据分析",
                "capabilities": ["数据查询", "SQL生成", "数据分析", "报表生成"]
            },
            "knowledge_qa": {
                "name": "知识库问答",
                "description": "基于企业知识库回答专业问题",
                "capabilities": ["知识检索", "专业问答", "文档查询", "技术支持"]
            },
            "content_creation": {
                "name": "文案创作",
                "description": "创作各类文案、文章、营销内容",
                "capabilities": ["文案写作", "内容创作", "营销文案", "文章撰写"]
            }
        }
    
    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是一个智能路由助手，负责分析用户的请求并将其路由到最合适的专业智能体。

可用的智能体类型：
1. customer_service (智能客服) - 处理客户咨询、投诉、售后等问题
2. text2sql (数据分析) - 将自然语言转换为SQL查询，进行数据分析
3. knowledge_qa (知识库问答) - 基于企业知识库回答专业问题
4. content_creation (文案创作) - 创作各类文案、文章、营销内容

请分析用户的请求，并返回以下JSON格式的路由决策：
{
    "agent_type": "选择的智能体类型",
    "confidence": 0.95,
    "reasoning": "选择理由",
    "extracted_intent": "提取的用户意图",
    "parameters": {
        "key": "value"
    }
}

分析要点：
1. 仔细理解用户的真实意图
2. 考虑请求的复杂度和专业性
3. 选择最匹配的智能体类型
4. 提供清晰的选择理由
5. 提取关键参数供后续处理

如果请求不明确或需要澄清，返回：
{
    "agent_type": "clarification",
    "confidence": 0.0,
    "reasoning": "需要澄清的原因",
    "clarification_questions": ["问题1", "问题2"]
}"""
    
    async def process_message(self, message: AgentMessage) -> AgentMessage:
        """处理路由请求"""
        try:
            # 分析用户请求
            routing_decision = await self._analyze_request(message.content)
            
            # 构建响应
            response_content = json.dumps(routing_decision, ensure_ascii=False, indent=2)
            
            response = AgentMessage(
                id=f"router_response_{message.id}",
                sender=self.name,
                receiver=message.sender,
                content=response_content,
                message_type="routing_decision",
                metadata={
                    "original_message_id": message.id,
                    "routing_decision": routing_decision
                }
            )
            
            return response
            
        except Exception as e:
            logger.error(f"路由处理失败: {e}")
            error_response = AgentMessage(
                id=f"router_error_{message.id}",
                sender=self.name,
                receiver=message.sender,
                content=f"路由分析失败: {str(e)}",
                message_type="error"
            )
            return error_response
    
    async def _analyze_request(self, user_request: str) -> Dict[str, Any]:
        """分析用户请求"""
        # 构建分析提示
        prompt = f"""
用户请求：{user_request}

请分析这个请求并返回路由决策。
"""
        
        # 调用LLM分析
        response = await llm_manager.generate(
            prompt=prompt,
            model=self.model,
            temperature=self.temperature,
            max_tokens=1000
        )
        
        try:
            # 解析JSON响应
            routing_decision = json.loads(response.content)
            
            # 验证响应格式
            if not self._validate_routing_decision(routing_decision):
                raise ValueError("路由决策格式无效")
            
            return routing_decision
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            # 返回默认路由决策
            return {
                "agent_type": "customer_service",
                "confidence": 0.5,
                "reasoning": "无法解析LLM响应，使用默认客服路由",
                "extracted_intent": user_request,
                "parameters": {}
            }
    
    def _validate_routing_decision(self, decision: Dict[str, Any]) -> bool:
        """验证路由决策格式"""
        required_fields = ["agent_type", "confidence", "reasoning"]
        
        # 检查必需字段
        for field in required_fields:
            if field not in decision:
                return False
        
        # 检查智能体类型是否有效
        agent_type = decision["agent_type"]
        if agent_type not in self.available_agents and agent_type != "clarification":
            return False
        
        # 检查置信度范围
        confidence = decision.get("confidence", 0)
        if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
            return False
        
        return True
    
    async def generate_response(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """生成响应"""
        response = await llm_manager.generate(
            prompt=prompt,
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        return response.content
    
    def get_available_agents(self) -> Dict[str, Dict[str, Any]]:
        """获取可用智能体列表"""
        return self.available_agents
    
    def add_agent_type(self, agent_type: str, info: Dict[str, Any]):
        """添加新的智能体类型"""
        self.available_agents[agent_type] = info
        logger.info(f"添加智能体类型: {agent_type}")
    
    def remove_agent_type(self, agent_type: str):
        """移除智能体类型"""
        if agent_type in self.available_agents:
            del self.available_agents[agent_type]
            logger.info(f"移除智能体类型: {agent_type}")
    
    async def get_routing_suggestions(self, user_request: str) -> List[Dict[str, Any]]:
        """获取路由建议（返回多个可能的选择）"""
        prompt = f"""
用户请求：{user_request}

请为这个请求提供3个最可能的智能体路由选择，按置信度排序。
返回JSON数组格式：
[
    {{
        "agent_type": "智能体类型",
        "confidence": 0.95,
        "reasoning": "选择理由"
    }},
    ...
]
"""
        
        response = await llm_manager.generate(
            prompt=prompt,
            model=self.model,
            temperature=0.5,
            max_tokens=1000
        )
        
        try:
            suggestions = json.loads(response.content)
            return suggestions if isinstance(suggestions, list) else []
        except json.JSONDecodeError:
            return []
    
    def get_agent_capabilities(self, agent_type: str) -> List[str]:
        """获取指定智能体的能力列表"""
        if agent_type in self.available_agents:
            return self.available_agents[agent_type].get("capabilities", [])
        return []
    
    async def explain_routing(self, user_request: str, agent_type: str) -> str:
        """解释为什么选择特定的智能体"""
        agent_info = self.available_agents.get(agent_type, {})
        
        prompt = f"""
用户请求：{user_request}
选择的智能体：{agent_info.get('name', agent_type)}
智能体描述：{agent_info.get('description', '')}
智能体能力：{', '.join(agent_info.get('capabilities', []))}

请用简洁明了的语言解释为什么选择这个智能体来处理用户的请求。
"""
        
        response = await llm_manager.generate(
            prompt=prompt,
            model=self.model,
            temperature=0.7,
            max_tokens=500
        )
        
        return response.content
