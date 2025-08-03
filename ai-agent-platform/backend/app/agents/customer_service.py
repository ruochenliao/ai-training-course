"""
客服智能体

专门处理客户服务相关问题，包括咨询、投诉、售后等。
"""

import logging
from typing import Dict, Any, List, Optional
import json
from datetime import datetime
from enum import Enum

from .base import BaseAgent, AgentMessage, AgentConfig
from .llm_interface import llm_manager
from ..rag.rag_agent import RAGAgent

logger = logging.getLogger(__name__)


class ServiceType(Enum):
    """服务类型"""
    CONSULTATION = "consultation"  # 咨询
    COMPLAINT = "complaint"  # 投诉
    AFTER_SALES = "after_sales"  # 售后
    TECHNICAL_SUPPORT = "technical_support"  # 技术支持
    BILLING = "billing"  # 账单问题
    GENERAL = "general"  # 一般问题


class Priority(Enum):
    """优先级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class CustomerServiceTicket:
    """客服工单"""
    
    def __init__(self, ticket_id: str, user_id: str, service_type: ServiceType,
                 title: str, description: str, priority: Priority = Priority.MEDIUM):
        self.ticket_id = ticket_id
        self.user_id = user_id
        self.service_type = service_type
        self.title = title
        self.description = description
        self.priority = priority
        self.status = "open"
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.responses: List[Dict[str, Any]] = []
        self.tags: List[str] = []
        self.assigned_agent = None
    
    def add_response(self, content: str, sender: str, response_type: str = "reply"):
        """添加回复"""
        response = {
            "id": f"resp_{len(self.responses) + 1}",
            "content": content,
            "sender": sender,
            "type": response_type,
            "timestamp": datetime.now().isoformat()
        }
        self.responses.append(response)
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "ticket_id": self.ticket_id,
            "user_id": self.user_id,
            "service_type": self.service_type.value,
            "title": self.title,
            "description": self.description,
            "priority": self.priority.value,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "responses": self.responses,
            "tags": self.tags,
            "assigned_agent": self.assigned_agent
        }


class CustomerServiceAgent(BaseAgent):
    """客服智能体"""
    
    def __init__(self, config: AgentConfig = None, rag_agent: RAGAgent = None):
        if config is None:
            config = AgentConfig(
                name="CustomerServiceAgent",
                description="专业的客户服务智能体，处理咨询、投诉、售后等问题",
                model="gpt-4o",
                temperature=0.7,
                system_prompt=self._get_system_prompt()
            )
        
        super().__init__(config)
        
        # RAG智能体用于知识库查询
        self.rag_agent = rag_agent
        
        # 工单管理
        self.tickets: Dict[str, CustomerServiceTicket] = {}
        
        # 常见问题缓存
        self.faq_cache: Dict[str, str] = {}
        
        # 服务统计
        self.stats = {
            "total_conversations": 0,
            "resolved_issues": 0,
            "average_response_time": 0,
            "satisfaction_score": 0
        }
    
    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是一个专业、友好的客户服务代表。你的目标是帮助客户解决问题，提供优质的服务体验。

服务原则：
1. 友好专业：始终保持礼貌、耐心和专业的态度
2. 积极倾听：仔细理解客户的问题和需求
3. 快速响应：及时回复客户的询问
4. 解决导向：专注于解决客户的实际问题
5. 超越期望：尽可能提供额外的帮助和建议

服务能力：
- 产品咨询和介绍
- 技术支持和故障排除
- 订单和账单查询
- 投诉处理和问题解决
- 售后服务和退换货
- 使用指导和培训

沟通风格：
- 使用温暖、友好的语调
- 避免使用过于技术性的术语
- 提供清晰、具体的解决方案
- 主动询问是否还有其他需要帮助的地方
- 在适当时候表达同理心

如果遇到无法解决的问题，会及时转接给人工客服或相关专家。"""
    
    async def process_message(self, message: AgentMessage) -> AgentMessage:
        """处理客服消息"""
        try:
            # 分析消息类型和意图
            analysis = await self._analyze_customer_intent(message.content)
            
            # 根据意图类型处理
            if analysis["service_type"] == ServiceType.CONSULTATION.value:
                response_content = await self._handle_consultation(message.content, analysis)
            elif analysis["service_type"] == ServiceType.COMPLAINT.value:
                response_content = await self._handle_complaint(message.content, analysis)
            elif analysis["service_type"] == ServiceType.TECHNICAL_SUPPORT.value:
                response_content = await self._handle_technical_support(message.content, analysis)
            else:
                response_content = await self._handle_general_inquiry(message.content, analysis)
            
            # 创建工单（如果需要）
            if analysis.get("create_ticket", False):
                ticket = await self._create_ticket(message, analysis)
                response_content += f"\n\n我已为您创建工单 #{ticket.ticket_id}，我们会尽快处理您的问题。"
            
            # 更新统计
            self.stats["total_conversations"] += 1
            
            response = AgentMessage(
                id=f"cs_response_{message.id}",
                sender=self.name,
                receiver=message.sender,
                content=response_content,
                message_type="customer_service_response",
                metadata={
                    "original_message_id": message.id,
                    "service_type": analysis["service_type"],
                    "intent": analysis.get("intent", ""),
                    "priority": analysis.get("priority", "medium")
                }
            )
            
            return response
            
        except Exception as e:
            logger.error(f"客服消息处理失败: {e}")
            error_response = AgentMessage(
                id=f"cs_error_{message.id}",
                sender=self.name,
                receiver=message.sender,
                content="抱歉，我遇到了一些技术问题。请稍后再试，或联系人工客服获得帮助。",
                message_type="error"
            )
            return error_response
    
    async def _analyze_customer_intent(self, message: str) -> Dict[str, Any]:
        """分析客户意图"""
        try:
            prompt = f"""
请分析以下客户消息的意图和服务类型。

客户消息：{message}

请返回JSON格式的分析结果：
{{
    "service_type": "consultation|complaint|after_sales|technical_support|billing|general",
    "intent": "具体意图描述",
    "priority": "low|medium|high|urgent",
    "emotion": "positive|neutral|negative|angry",
    "keywords": ["关键词1", "关键词2"],
    "create_ticket": true/false,
    "requires_human": true/false
}}

分析要点：
1. 识别服务类型（咨询、投诉、售后、技术支持、账单、一般）
2. 判断优先级（紧急程度）
3. 识别情感倾向
4. 提取关键词
5. 判断是否需要创建工单
6. 判断是否需要人工介入
"""
            
            response = await llm_manager.generate(
                prompt=prompt,
                model=self.model,
                temperature=0.3,
                max_tokens=500
            )
            
            try:
                analysis = json.loads(response.content)
                return analysis
            except json.JSONDecodeError:
                # 返回默认分析
                return {
                    "service_type": "general",
                    "intent": "一般咨询",
                    "priority": "medium",
                    "emotion": "neutral",
                    "keywords": [],
                    "create_ticket": False,
                    "requires_human": False
                }
                
        except Exception as e:
            logger.error(f"意图分析失败: {e}")
            return {
                "service_type": "general",
                "intent": "分析失败",
                "priority": "medium",
                "emotion": "neutral",
                "keywords": [],
                "create_ticket": False,
                "requires_human": False
            }
    
    async def _handle_consultation(self, message: str, analysis: Dict[str, Any]) -> str:
        """处理咨询问题"""
        try:
            # 先尝试从知识库获取答案
            if self.rag_agent:
                rag_result = await self.rag_agent.query(
                    query=message,
                    kb_filter={"category": "product_info"}
                )
                
                if rag_result["confidence"] > 0.6:
                    return f"根据我们的产品资料，{rag_result['answer']}\n\n如果您还有其他问题，请随时告诉我！"
            
            # 使用LLM生成回答
            prompt = f"""
客户咨询：{message}

请作为专业的客服代表回答客户的咨询问题。

回答要求：
1. 友好、专业的语调
2. 提供具体、有用的信息
3. 如果需要更多信息，主动询问
4. 结尾询问是否还有其他需要帮助的地方

回答：
"""
            
            response = await llm_manager.generate(
                prompt=prompt,
                model=self.model,
                temperature=0.7,
                max_tokens=800
            )
            
            return response.content
            
        except Exception as e:
            logger.error(f"处理咨询失败: {e}")
            return "感谢您的咨询。我正在为您查找相关信息，请稍等片刻。"
    
    async def _handle_complaint(self, message: str, analysis: Dict[str, Any]) -> str:
        """处理投诉问题"""
        try:
            prompt = f"""
客户投诉：{message}

请作为专业的客服代表处理客户投诉。

处理要求：
1. 首先表达同理心和歉意
2. 认真倾听客户的问题
3. 提供具体的解决方案
4. 承诺跟进和改进
5. 语调要诚恳、负责任

回答：
"""
            
            response = await llm_manager.generate(
                prompt=prompt,
                model=self.model,
                temperature=0.6,
                max_tokens=800
            )
            
            return response.content
            
        except Exception as e:
            logger.error(f"处理投诉失败: {e}")
            return "非常抱歉给您带来了不便。我会认真处理您的投诉，并尽快为您解决问题。"
    
    async def _handle_technical_support(self, message: str, analysis: Dict[str, Any]) -> str:
        """处理技术支持问题"""
        try:
            # 尝试从技术知识库获取答案
            if self.rag_agent:
                rag_result = await self.rag_agent.query(
                    query=message,
                    kb_filter={"category": "technical_support"}
                )
                
                if rag_result["confidence"] > 0.7:
                    return f"根据技术文档，{rag_result['answer']}\n\n如果问题仍未解决，请提供更多详细信息，我会进一步协助您。"
            
            prompt = f"""
技术支持请求：{message}

请作为技术支持专家回答客户的技术问题。

回答要求：
1. 提供清晰的步骤说明
2. 使用易懂的语言解释技术概念
3. 如果需要更多信息，具体说明需要什么
4. 提供替代解决方案
5. 必要时建议联系技术专家

回答：
"""
            
            response = await llm_manager.generate(
                prompt=prompt,
                model=self.model,
                temperature=0.5,
                max_tokens=1000
            )
            
            return response.content
            
        except Exception as e:
            logger.error(f"处理技术支持失败: {e}")
            return "我正在为您查找技术解决方案。如果问题比较复杂，我可以为您转接技术专家。"
    
    async def _handle_general_inquiry(self, message: str, analysis: Dict[str, Any]) -> str:
        """处理一般询问"""
        try:
            prompt = f"""
客户询问：{message}

请作为友好的客服代表回答客户的问题。

回答要求：
1. 保持友好、专业的态度
2. 尽可能提供有用的信息
3. 如果不确定，诚实说明并提供其他帮助方式
4. 主动询问是否还有其他需要

回答：
"""
            
            response = await llm_manager.generate(
                prompt=prompt,
                model=self.model,
                temperature=0.7,
                max_tokens=600
            )
            
            return response.content
            
        except Exception as e:
            logger.error(f"处理一般询问失败: {e}")
            return "感谢您的询问。我会尽力为您提供帮助。请告诉我更多详细信息，这样我能更好地协助您。"
    
    async def _create_ticket(self, message: AgentMessage, analysis: Dict[str, Any]) -> CustomerServiceTicket:
        """创建客服工单"""
        try:
            ticket_id = f"CS{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # 确定服务类型
            service_type = ServiceType(analysis.get("service_type", "general"))
            
            # 确定优先级
            priority = Priority(analysis.get("priority", "medium"))
            
            # 生成工单标题
            title = analysis.get("intent", "客户咨询")[:50]
            
            ticket = CustomerServiceTicket(
                ticket_id=ticket_id,
                user_id=message.sender,
                service_type=service_type,
                title=title,
                description=message.content,
                priority=priority
            )
            
            # 添加标签
            ticket.tags = analysis.get("keywords", [])
            
            # 存储工单
            self.tickets[ticket_id] = ticket
            
            logger.info(f"创建客服工单: {ticket_id}")
            return ticket
            
        except Exception as e:
            logger.error(f"创建工单失败: {e}")
            raise
    
    async def generate_response(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """生成响应"""
        response = await llm_manager.generate(
            prompt=prompt,
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        return response.content
    
    def get_ticket(self, ticket_id: str) -> Optional[CustomerServiceTicket]:
        """获取工单"""
        return self.tickets.get(ticket_id)
    
    def list_tickets(self, status: str = None) -> List[CustomerServiceTicket]:
        """列出工单"""
        tickets = list(self.tickets.values())
        if status:
            tickets = [t for t in tickets if t.status == status]
        return tickets
    
    def get_stats(self) -> Dict[str, Any]:
        """获取服务统计"""
        return {
            **self.stats,
            "total_tickets": len(self.tickets),
            "open_tickets": len([t for t in self.tickets.values() if t.status == "open"]),
            "resolved_tickets": len([t for t in self.tickets.values() if t.status == "resolved"])
        }
