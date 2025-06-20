"""
工具调用智能体
负责识别用户需求并调用相应的工具来完成任务
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Callable, Union
from datetime import datetime
import inspect

from autogen_core import CancellationToken

from .base_agent import BaseAgent
from ..core.model_manager import model_manager, ModelType

logger = logging.getLogger(__name__)


class ToolDefinition:
    """工具定义类"""
    
    def __init__(
        self,
        name: str,
        description: str,
        function: Callable,
        parameters: Dict[str, Any],
        category: str = "general",
        requires_auth: bool = False,
        timeout: int = 30
    ):
        self.name = name
        self.description = description
        self.function = function
        self.parameters = parameters
        self.category = category
        self.requires_auth = requires_auth
        self.timeout = timeout
        self.usage_count = 0
        self.error_count = 0
        self.created_at = datetime.now()
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """执行工具函数"""
        try:
            self.usage_count += 1
            
            # 参数验证
            validated_params = self._validate_parameters(kwargs)
            
            # 执行函数
            if inspect.iscoroutinefunction(self.function):
                result = await asyncio.wait_for(
                    self.function(**validated_params),
                    timeout=self.timeout
                )
            else:
                result = await asyncio.wait_for(
                    asyncio.to_thread(self.function, **validated_params),
                    timeout=self.timeout
                )
            
            return {
                "success": True,
                "result": result,
                "tool_name": self.name,
                "execution_time": datetime.now().isoformat()
            }
            
        except asyncio.TimeoutError:
            self.error_count += 1
            return {
                "success": False,
                "error": f"工具执行超时 (>{self.timeout}秒)",
                "tool_name": self.name
            }
        except Exception as e:
            self.error_count += 1
            logger.error(f"工具 {self.name} 执行失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "tool_name": self.name
            }
    
    def _validate_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """验证参数"""
        validated = {}
        
        for param_name, param_info in self.parameters.items():
            if param_name in params:
                validated[param_name] = params[param_name]
            elif param_info.get('required', False):
                raise ValueError(f"缺少必需参数: {param_name}")
            elif 'default' in param_info:
                validated[param_name] = param_info['default']
        
        return validated
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "category": self.category,
            "requires_auth": self.requires_auth,
            "usage_count": self.usage_count,
            "error_count": self.error_count,
            "success_rate": (self.usage_count - self.error_count) / max(self.usage_count, 1)
        }


class ToolRegistry:
    """工具注册表"""
    
    def __init__(self):
        self.tools: Dict[str, ToolDefinition] = {}
        self.categories: Dict[str, List[str]] = {}
    
    def register_tool(
        self,
        name: str,
        description: str,
        function: Callable,
        parameters: Dict[str, Any],
        category: str = "general",
        requires_auth: bool = False,
        timeout: int = 30
    ):
        """注册工具"""
        tool = ToolDefinition(
            name=name,
            description=description,
            function=function,
            parameters=parameters,
            category=category,
            requires_auth=requires_auth,
            timeout=timeout
        )
        
        self.tools[name] = tool
        
        if category not in self.categories:
            self.categories[category] = []
        self.categories[category].append(name)
        
        logger.info(f"注册工具: {name} (类别: {category})")
    
    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """获取工具"""
        return self.tools.get(name)
    
    def list_tools(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出工具"""
        if category:
            tool_names = self.categories.get(category, [])
            return [self.tools[name].to_dict() for name in tool_names if name in self.tools]
        else:
            return [tool.to_dict() for tool in self.tools.values()]
    
    def get_tools_for_llm(self) -> List[Dict[str, Any]]:
        """获取适用于LLM的工具定义"""
        llm_tools = []
        
        for tool in self.tools.values():
            llm_tool = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
            
            # 转换参数格式
            for param_name, param_info in tool.parameters.items():
                llm_tool["function"]["parameters"]["properties"][param_name] = {
                    "type": param_info.get("type", "string"),
                    "description": param_info.get("description", "")
                }
                
                if param_info.get("required", False):
                    llm_tool["function"]["parameters"]["required"].append(param_name)
            
            llm_tools.append(llm_tool)
        
        return llm_tools


class ToolAgent(BaseAgent):
    """
    工具调用智能体
    
    主要职责：
    - 识别用户请求中的工具调用需求
    - 选择合适的工具执行任务
    - 管理工具执行过程和结果
    - 提供工具执行监控和日志
    - 处理工具权限和安全控制
    """
    
    def __init__(
        self,
        name: str = "ToolAgent",
        system_message: str = None,
        model_config: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """
        初始化工具调用智能体
        
        Args:
            name: 智能体名称
            system_message: 系统提示词
            model_config: 模型配置
            **kwargs: 其他配置参数
        """
        if system_message is None:
            system_message = self._get_default_system_message()
        
        super().__init__(
            name=name,
            system_message=system_message,
            model_config=model_config,
            **kwargs
        )
        
        # 工具配置
        self.enabled_tools = model_config.get('enabled_tools', []) if model_config else []
        self.max_tool_calls = model_config.get('max_tool_calls', 5) if model_config else 5
        self.tool_timeout = model_config.get('tool_timeout', 30) if model_config else 30
        self.require_confirmation = model_config.get('require_confirmation', False) if model_config else False
        
        # 工具注册表
        self.tool_registry = ToolRegistry()
        
        # 执行统计
        self.total_tool_calls = 0
        self.successful_calls = 0
        self.failed_calls = 0
        
        logger.info(f"工具调用智能体 {self.name} 初始化完成")
    
    def _get_default_system_message(self) -> str:
        """获取默认系统提示词"""
        return """你是一个专业的工具调用助手。你的主要职责是：

1. 理解用户的请求和需求
2. 识别需要调用的工具来完成任务
3. 选择合适的工具并准确调用
4. 解释工具执行结果并提供有用的回答
5. 在工具执行失败时提供替代方案

你可以调用多种工具来帮助用户完成任务，包括但不限于：
- 电商相关工具（商品查询、订单管理等）
- 搜索工具（信息检索、数据查找等）
- 文件处理工具（文档解析、格式转换等）

请根据用户需求选择最合适的工具，并确保参数正确。如果不确定如何使用某个工具，请先询问用户提供更多信息。"""
    
    async def initialize_tools(self):
        """初始化工具"""
        try:
            # 注册基础工具
            await self._register_basic_tools()
            
            # 注册电商工具
            await self._register_ecommerce_tools()
            
            # 注册搜索工具
            await self._register_search_tools()
            
            # 注册文件工具
            await self._register_file_tools()
            
            logger.info(f"工具调用智能体 {self.name} 工具初始化完成，共注册 {len(self.tool_registry.tools)} 个工具")
            
        except Exception as e:
            logger.error(f"工具初始化失败: {str(e)}")
            raise
    
    async def _handle_message(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        cancellation_token: Optional[CancellationToken] = None
    ) -> str:
        """
        处理工具调用请求的核心逻辑
        
        Args:
            message: 用户请求
            context: 上下文信息
            cancellation_token: 取消令牌
            
        Returns:
            工具执行结果
        """
        try:
            # 确保工具已初始化
            if not self.tool_registry.tools:
                await self.initialize_tools()
            
            # 分析是否需要工具调用
            tool_analysis = await self._analyze_tool_needs(message, context)
            
            if not tool_analysis.get('needs_tools', False):
                return "根据您的请求，我认为不需要调用特殊工具。请提供更具体的任务需求。"
            
            # 使用LLM识别需要调用的工具
            tool_calls = await self._identify_tool_calls(message, context)
            
            if not tool_calls:
                return "我理解您的需求，但无法确定需要调用哪些工具。请提供更详细的信息。"
            
            # 执行工具调用
            execution_results = await self._execute_tool_calls(tool_calls, context)
            
            # 生成基于工具结果的回答
            response = await self._generate_tool_response(message, execution_results, context)
            
            return response
            
        except Exception as e:
            logger.error(f"工具调用处理失败: {str(e)}")
            return f"抱歉，在执行工具调用时遇到了问题：{str(e)}"
    
    async def _analyze_tool_needs(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """分析是否需要工具调用"""
        analysis = {
            'needs_tools': False,
            'confidence': 0.0,
            'suggested_categories': [],
            'keywords': []
        }
        
        message_lower = message.lower()
        
        # 检查工具调用关键词
        tool_keywords = {
            'ecommerce': ['商品', '订单', '购买', '支付', '退款', '库存', '价格'],
            'search': ['搜索', '查找', '检索', '查询'],
            'file': ['文件', '文档', '上传', '下载', '解析', '转换'],
            'general': ['执行', '调用', '运行', '处理']
        }
        
        for category, keywords in tool_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                analysis['needs_tools'] = True
                analysis['suggested_categories'].append(category)
                analysis['keywords'].extend([kw for kw in keywords if kw in message_lower])
        
        # 计算置信度
        if analysis['needs_tools']:
            analysis['confidence'] = min(len(analysis['keywords']) * 0.2, 1.0)
        
        return analysis
    
    async def _identify_tool_calls(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """使用LLM识别需要调用的工具"""
        try:
            llm_service = model_manager.get_default_model(ModelType.LLM)
            if not llm_service:
                logger.warning("LLM服务不可用，使用规则匹配")
                return await self._fallback_tool_identification(message, context)
            
            # 获取可用工具列表
            available_tools = self.tool_registry.get_tools_for_llm()
            
            if not available_tools:
                return []
            
            # 构建工具识别提示词
            tools_description = self._build_tools_description()
            prompt = f"""分析用户请求，确定需要调用哪些工具来完成任务。

用户请求: {message}

可用工具:
{tools_description}

请以JSON格式返回需要调用的工具列表，格式如下：
[
    {{
        "tool_name": "工具名称",
        "parameters": {{
            "参数名": "参数值"
        }},
        "reason": "调用原因"
    }}
]

如果不需要调用任何工具，返回空数组 []。"""
            
            # 调用LLM
            messages = [
                {"role": "system", "content": "你是一个工具调用分析专家，能够准确识别用户需求并选择合适的工具。"},
                {"role": "user", "content": prompt}
            ]
            
            response = await llm_service.chat_completion(
                messages=messages,
                temperature=0.1,  # 低温度确保准确性
                max_tokens=1024
            )
            
            # 解析响应
            try:
                tool_calls = json.loads(response.strip())
                if isinstance(tool_calls, list):
                    return tool_calls[:self.max_tool_calls]  # 限制工具调用数量
            except json.JSONDecodeError:
                logger.warning("LLM返回的工具调用格式无效，使用降级方案")
                return await self._fallback_tool_identification(message, context)
            
            return []
            
        except Exception as e:
            logger.error(f"工具识别失败: {str(e)}")
            return await self._fallback_tool_identification(message, context)
    
    def _build_tools_description(self) -> str:
        """构建工具描述"""
        descriptions = []
        
        for tool in self.tool_registry.tools.values():
            params_desc = []
            for param_name, param_info in tool.parameters.items():
                required = "必需" if param_info.get('required', False) else "可选"
                params_desc.append(f"  - {param_name} ({param_info.get('type', 'string')}, {required}): {param_info.get('description', '')}")
            
            tool_desc = f"""
工具名: {tool.name}
描述: {tool.description}
类别: {tool.category}
参数:
{chr(10).join(params_desc) if params_desc else "  无参数"}
"""
            descriptions.append(tool_desc)
        
        return "\n".join(descriptions)
    
    async def _fallback_tool_identification(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """降级工具识别（基于规则）"""
        tool_calls = []
        message_lower = message.lower()
        
        # 简单的规则匹配
        if any(word in message_lower for word in ['商品', '产品']):
            if '查询' in message_lower or '搜索' in message_lower:
                tool_calls.append({
                    "tool_name": "search_products",
                    "parameters": {"query": message},
                    "reason": "用户请求搜索商品"
                })
        
        if any(word in message_lower for word in ['订单']):
            if '查询' in message_lower:
                tool_calls.append({
                    "tool_name": "get_order_info",
                    "parameters": {"query": message},
                    "reason": "用户请求查询订单"
                })
        
        return tool_calls
    
    async def _execute_tool_calls(
        self,
        tool_calls: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """执行工具调用"""
        results = []
        
        for tool_call in tool_calls:
            try:
                tool_name = tool_call.get('tool_name')
                parameters = tool_call.get('parameters', {})
                
                # 获取工具
                tool = self.tool_registry.get_tool(tool_name)
                if not tool:
                    results.append({
                        "tool_name": tool_name,
                        "success": False,
                        "error": f"工具 {tool_name} 不存在"
                    })
                    continue
                
                # 权限检查
                if tool.requires_auth and not self._check_tool_permission(tool_name, context):
                    results.append({
                        "tool_name": tool_name,
                        "success": False,
                        "error": "权限不足"
                    })
                    continue
                
                # 执行工具
                self.total_tool_calls += 1
                result = await tool.execute(**parameters)
                
                if result.get('success', False):
                    self.successful_calls += 1
                else:
                    self.failed_calls += 1
                
                results.append(result)
                
            except Exception as e:
                self.failed_calls += 1
                logger.error(f"工具调用执行失败: {str(e)}")
                results.append({
                    "tool_name": tool_call.get('tool_name', 'unknown'),
                    "success": False,
                    "error": str(e)
                })
        
        return results
    
    def _check_tool_permission(self, tool_name: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """检查工具权限"""
        # 简单的权限检查逻辑
        if not context:
            return False
        
        user_id = context.get('user_id')
        if not user_id:
            return False
        
        # 这里可以实现更复杂的权限逻辑
        return True
    
    async def _generate_tool_response(
        self,
        original_message: str,
        execution_results: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """基于工具执行结果生成回答"""
        try:
            # 统计执行结果
            successful_results = [r for r in execution_results if r.get('success', False)]
            failed_results = [r for r in execution_results if not r.get('success', False)]
            
            if not successful_results and not failed_results:
                return "没有执行任何工具调用。"
            
            # 构建结果摘要
            response_parts = []
            
            if successful_results:
                response_parts.append("✅ 成功执行的工具:")
                for result in successful_results:
                    tool_name = result.get('tool_name', '未知工具')
                    tool_result = result.get('result', '无结果')
                    response_parts.append(f"- {tool_name}: {tool_result}")
            
            if failed_results:
                response_parts.append("\n❌ 执行失败的工具:")
                for result in failed_results:
                    tool_name = result.get('tool_name', '未知工具')
                    error = result.get('error', '未知错误')
                    response_parts.append(f"- {tool_name}: {error}")
            
            # 使用LLM生成更自然的回答
            llm_service = model_manager.get_default_model(ModelType.LLM)
            if llm_service and successful_results:
                summary = "\n".join(response_parts)
                prompt = f"""用户请求: {original_message}

工具执行结果:
{summary}

请基于工具执行结果，用自然语言为用户生成一个友好、有用的回答。"""
                
                messages = [
                    {"role": "system", "content": "你是一个友好的助手，能够将工具执行结果转换为自然的回答。"},
                    {"role": "user", "content": prompt}
                ]
                
                try:
                    natural_response = await llm_service.chat_completion(
                        messages=messages,
                        temperature=0.7,
                        max_tokens=512
                    )
                    return natural_response
                except Exception as e:
                    logger.warning(f"生成自然回答失败: {str(e)}")
            
            # 降级：返回原始结果摘要
            return "\n".join(response_parts)
            
        except Exception as e:
            logger.error(f"生成工具回答失败: {str(e)}")
            return "工具执行完成，但生成回答时遇到问题。"
    
    # 工具注册方法
    async def _register_basic_tools(self):
        """注册基础工具"""
        
        async def get_current_time():
            """获取当前时间"""
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        self.tool_registry.register_tool(
            name="get_current_time",
            description="获取当前日期和时间",
            function=get_current_time,
            parameters={},
            category="basic"
        )
        
        async def calculate(expression: str):
            """简单计算器"""
            try:
                # 安全的数学表达式计算
                allowed_chars = set('0123456789+-*/.() ')
                if not all(c in allowed_chars for c in expression):
                    return "表达式包含不允许的字符"
                
                result = eval(expression)
                return f"{expression} = {result}"
            except Exception as e:
                return f"计算错误: {str(e)}"
        
        self.tool_registry.register_tool(
            name="calculate",
            description="执行简单的数学计算",
            function=calculate,
            parameters={
                "expression": {
                    "type": "string",
                    "description": "数学表达式，如 '2+3*4'",
                    "required": True
                }
            },
            category="basic"
        )
    
    async def _register_ecommerce_tools(self):
        """注册电商工具"""
        
        async def search_products(query: str, limit: int = 10):
            """搜索商品"""
            # 这里应该调用实际的商品搜索API
            return f"搜索商品 '{query}'，找到 {limit} 个相关结果"
        
        self.tool_registry.register_tool(
            name="search_products",
            description="搜索商品信息",
            function=search_products,
            parameters={
                "query": {
                    "type": "string",
                    "description": "搜索关键词",
                    "required": True
                },
                "limit": {
                    "type": "integer",
                    "description": "返回结果数量限制",
                    "required": False,
                    "default": 10
                }
            },
            category="ecommerce"
        )
        
        async def get_order_info(order_id: str):
            """获取订单信息"""
            # 这里应该调用实际的订单查询API
            return f"订单 {order_id} 的详细信息"
        
        self.tool_registry.register_tool(
            name="get_order_info",
            description="查询订单详细信息",
            function=get_order_info,
            parameters={
                "order_id": {
                    "type": "string",
                    "description": "订单ID",
                    "required": True
                }
            },
            category="ecommerce",
            requires_auth=True
        )
    
    async def _register_search_tools(self):
        """注册搜索工具"""
        
        async def web_search(query: str, num_results: int = 5):
            """网络搜索"""
            return f"网络搜索 '{query}'，返回 {num_results} 个结果"
        
        self.tool_registry.register_tool(
            name="web_search",
            description="执行网络搜索",
            function=web_search,
            parameters={
                "query": {
                    "type": "string",
                    "description": "搜索查询",
                    "required": True
                },
                "num_results": {
                    "type": "integer",
                    "description": "结果数量",
                    "required": False,
                    "default": 5
                }
            },
            category="search"
        )
    
    async def _register_file_tools(self):
        """注册文件工具"""
        
        async def analyze_file(file_path: str):
            """分析文件"""
            return f"分析文件: {file_path}"
        
        self.tool_registry.register_tool(
            name="analyze_file",
            description="分析上传的文件",
            function=analyze_file,
            parameters={
                "file_path": {
                    "type": "string",
                    "description": "文件路径",
                    "required": True
                }
            },
            category="file"
        )
    
    def get_tool_stats(self) -> Dict[str, Any]:
        """获取工具使用统计"""
        return {
            'agent_name': self.name,
            'total_tools': len(self.tool_registry.tools),
            'total_calls': self.total_tool_calls,
            'successful_calls': self.successful_calls,
            'failed_calls': self.failed_calls,
            'success_rate': self.successful_calls / max(self.total_tool_calls, 1),
            'tools_by_category': {
                category: len(tools) 
                for category, tools in self.tool_registry.categories.items()
            }
        }
