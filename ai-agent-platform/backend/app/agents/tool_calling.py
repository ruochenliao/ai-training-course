"""
# Copyright (c) 2025 左岚. All rights reserved.

工具调用智能体

负责调用各种外部工具和API来完成特定任务。
"""

# # Standard library imports
import json
import logging
from typing import Any, Callable, Dict, List, Optional

# # Local folder imports
from .base import AgentConfig, AgentMessage, BaseAgent
from .llm_interface import llm_manager

logger = logging.getLogger(__name__)


class Tool:
    """工具定义"""
    
    def __init__(self, name: str, description: str, parameters: Dict[str, Any], 
                 function: Callable, required_params: List[str] = None):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.function = function
        self.required_params = required_params or []
    
    async def execute(self, **kwargs) -> Any:
        """执行工具"""
        # 验证必需参数
        for param in self.required_params:
            if param not in kwargs:
                raise ValueError(f"缺少必需参数: {param}")
        
        # 执行工具函数
        try:
            if asyncio.iscoroutinefunction(self.function):
                return await self.function(**kwargs)
            else:
                return self.function(**kwargs)
        except Exception as e:
            logger.error(f"工具执行失败 {self.name}: {e}")
            raise
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }


class ToolRegistry:
    """工具注册表"""
    
    def __init__(self):
        self.tools: Dict[str, Tool] = {}
    
    def register(self, tool: Tool):
        """注册工具"""
        self.tools[tool.name] = tool
        logger.info(f"注册工具: {tool.name}")
    
    def unregister(self, name: str):
        """注销工具"""
        if name in self.tools:
            del self.tools[name]
            logger.info(f"注销工具: {name}")
    
    def get(self, name: str) -> Optional[Tool]:
        """获取工具"""
        return self.tools.get(name)
    
    def list_tools(self) -> List[str]:
        """列出所有工具名称"""
        return list(self.tools.keys())
    
    def get_tools_schema(self) -> List[Dict[str, Any]]:
        """获取工具模式定义"""
        return [tool.to_dict() for tool in self.tools.values()]


# 全局工具注册表
tool_registry = ToolRegistry()


class ToolCallingAgent(BaseAgent):
    """工具调用智能体"""
    
    def __init__(self, config: AgentConfig = None):
        if config is None:
            config = AgentConfig(
                name="ToolCallingAgent",
                description="负责调用各种外部工具和API来完成特定任务",
                model="gpt-4o",
                temperature=0.3,
                system_prompt=self._get_system_prompt()
            )
        super().__init__(config)
        
        # 注册基础工具
        self._register_basic_tools()
    
    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        tools_schema = tool_registry.get_tools_schema()
        
        return f"""你是一个专业的工具调用助手，能够根据用户需求选择和调用合适的工具。

可用工具：
{json.dumps(tools_schema, ensure_ascii=False, indent=2)}

工具调用规则：
1. 仔细分析用户需求，确定需要使用哪些工具
2. 按照工具的参数要求准备调用参数
3. 可以组合使用多个工具来完成复杂任务
4. 如果工具执行失败，尝试其他方案或报告错误

请根据用户请求返回工具调用计划，格式如下：
{{
    "tools_to_call": [
        {{
            "tool_name": "工具名称",
            "parameters": {{
                "param1": "value1",
                "param2": "value2"
            }},
            "reasoning": "调用理由"
        }}
    ],
    "execution_order": "sequential|parallel",
    "expected_outcome": "预期结果描述"
}}

如果不需要调用工具，返回：
{{
    "tools_to_call": [],
    "response": "直接回复内容"
}}"""
    
    def _register_basic_tools(self):
        """注册基础工具"""
        # # Standard library imports
        import asyncio

        # 计算器工具
        def calculator(expression: str) -> str:
            """计算数学表达式"""
            try:
                # 安全的数学表达式计算
                allowed_chars = set('0123456789+-*/().,')
                if not all(c in allowed_chars for c in expression.replace(' ', '')):
                    return "错误：包含不允许的字符"
                
                result = eval(expression)
                return str(result)
            except Exception as e:
                return f"计算错误: {str(e)}"
        
        calculator_tool = Tool(
            name="calculator",
            description="计算数学表达式",
            parameters={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "要计算的数学表达式"
                    }
                },
                "required": ["expression"]
            },
            function=calculator,
            required_params=["expression"]
        )
        tool_registry.register(calculator_tool)
        
        # 文本处理工具
        def text_processor(text: str, operation: str) -> str:
            """处理文本"""
            operations = {
                "upper": lambda x: x.upper(),
                "lower": lambda x: x.lower(),
                "reverse": lambda x: x[::-1],
                "length": lambda x: str(len(x)),
                "words": lambda x: str(len(x.split()))
            }
            
            if operation not in operations:
                return f"不支持的操作: {operation}"
            
            try:
                return operations[operation](text)
            except Exception as e:
                return f"处理错误: {str(e)}"
        
        text_tool = Tool(
            name="text_processor",
            description="处理文本内容",
            parameters={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "要处理的文本"
                    },
                    "operation": {
                        "type": "string",
                        "enum": ["upper", "lower", "reverse", "length", "words"],
                        "description": "处理操作类型"
                    }
                },
                "required": ["text", "operation"]
            },
            function=text_processor,
            required_params=["text", "operation"]
        )
        tool_registry.register(text_tool)
    
    async def process_message(self, message: AgentMessage) -> AgentMessage:
        """处理工具调用请求"""
        try:
            # 分析需要调用的工具
            tool_plan = await self._analyze_tool_requirements(message.content)
            
            if not tool_plan.get("tools_to_call"):
                # 不需要调用工具，直接回复
                response_content = tool_plan.get("response", "无需调用工具")
            else:
                # 执行工具调用
                results = await self._execute_tools(tool_plan["tools_to_call"])
                response_content = await self._generate_final_response(
                    message.content, tool_plan, results
                )
            
            response = AgentMessage(
                id=f"tool_response_{message.id}",
                sender=self.name,
                receiver=message.sender,
                content=response_content,
                message_type="tool_result",
                metadata={
                    "original_message_id": message.id,
                    "tools_used": tool_plan.get("tools_to_call", [])
                }
            )
            
            return response
            
        except Exception as e:
            logger.error(f"工具调用处理失败: {e}")
            error_response = AgentMessage(
                id=f"tool_error_{message.id}",
                sender=self.name,
                receiver=message.sender,
                content=f"工具调用失败: {str(e)}",
                message_type="error"
            )
            return error_response
    
    async def _analyze_tool_requirements(self, user_request: str) -> Dict[str, Any]:
        """分析工具需求"""
        prompt = f"""
用户请求：{user_request}

请分析这个请求并制定工具调用计划。
"""
        
        response = await llm_manager.generate(
            prompt=prompt,
            model=self.model,
            temperature=self.temperature,
            max_tokens=1000
        )
        
        try:
            tool_plan = json.loads(response.content)
            return tool_plan
        except json.JSONDecodeError as e:
            logger.error(f"工具计划解析失败: {e}")
            return {"tools_to_call": [], "response": "无法解析工具调用计划"}
    
    async def _execute_tools(self, tools_to_call: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """执行工具调用"""
        results = []
        
        for tool_call in tools_to_call:
            tool_name = tool_call["tool_name"]
            parameters = tool_call["parameters"]
            
            try:
                tool = tool_registry.get(tool_name)
                if not tool:
                    result = {
                        "tool_name": tool_name,
                        "success": False,
                        "error": f"工具不存在: {tool_name}"
                    }
                else:
                    output = await tool.execute(**parameters)
                    result = {
                        "tool_name": tool_name,
                        "success": True,
                        "output": output,
                        "parameters": parameters
                    }
                
                results.append(result)
                logger.info(f"工具执行完成: {tool_name}")
                
            except Exception as e:
                result = {
                    "tool_name": tool_name,
                    "success": False,
                    "error": str(e),
                    "parameters": parameters
                }
                results.append(result)
                logger.error(f"工具执行失败: {tool_name}, 错误: {e}")
        
        return results
    
    async def _generate_final_response(self, user_request: str, 
                                     tool_plan: Dict[str, Any], 
                                     results: List[Dict[str, Any]]) -> str:
        """生成最终响应"""
        prompt = f"""
用户请求：{user_request}

工具调用计划：
{json.dumps(tool_plan, ensure_ascii=False, indent=2)}

工具执行结果：
{json.dumps(results, ensure_ascii=False, indent=2)}

请根据工具执行结果，为用户生成一个清晰、有用的回复。
"""
        
        response = await llm_manager.generate(
            prompt=prompt,
            model=self.model,
            temperature=0.7,
            max_tokens=1000
        )
        
        return response.content
    
    async def generate_response(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """生成响应"""
        response = await llm_manager.generate(
            prompt=prompt,
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        return response.content
    
    def register_tool(self, tool: Tool):
        """注册新工具"""
        tool_registry.register(tool)
        # 更新系统提示词
        self.system_prompt = self._get_system_prompt()
    
    def unregister_tool(self, tool_name: str):
        """注销工具"""
        tool_registry.unregister(tool_name)
        # 更新系统提示词
        self.system_prompt = self._get_system_prompt()
    
    def list_available_tools(self) -> List[str]:
        """列出可用工具"""
        return tool_registry.list_tools()
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """获取工具信息"""
        tool = tool_registry.get(tool_name)
        if tool:
            return tool.to_dict()
        return None
