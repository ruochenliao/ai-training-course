"""
DeepSeek-Chat LLM服务 - 企业级RAG系统
严格按照技术栈要求：deepseek-chat API (模型热切换)
"""
import json
import time
from typing import List, Dict, Any, Optional, AsyncGenerator, Union

import httpx
from loguru import logger

from app.core import settings


class DeepSeekLLMService:
    """DeepSeek-Chat LLM服务"""
    
    def __init__(self):
        self.api_key = settings.LLM_API_KEY
        self.base_url = settings.LLM_BASE_URL + "/v1" if not settings.LLM_BASE_URL.endswith("/v1") else settings.LLM_BASE_URL
        self.model_name = settings.LLM_MODEL_NAME
        self.max_tokens = settings.LLM_MAX_TOKENS
        self.temperature = settings.LLM_TEMPERATURE
        self.timeout = 60
        self._client = None
        
        # 模型配置
        self.model_configs = {
            "deepseek-chat": {
                "max_tokens": 4096,
                "context_length": 32768,
                "supports_streaming": True,
                "supports_function_calling": True
            },
            "deepseek-coder": {
                "max_tokens": 4096,
                "context_length": 16384,
                "supports_streaming": True,
                "supports_function_calling": False
            }
        }
        
        # 请求统计
        self.request_count = 0
        self.total_tokens = 0
        self.total_latency = 0.0
        self.error_count = 0
    
    async def initialize(self):
        """初始化HTTP客户端"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                timeout=httpx.Timeout(self.timeout)
            )
            logger.info("DeepSeek LLM服务初始化完成")
    
    async def close(self):
        """关闭HTTP客户端"""
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.info("DeepSeek LLM服务已关闭")
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        temperature: float = None,
        max_tokens: int = None,
        stream: bool = False,
        functions: Optional[List[Dict[str, Any]]] = None,
        function_call: Optional[Union[str, Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """聊天补全"""
        try:
            await self.initialize()
            
            # 准备请求参数
            payload = {
                "model": model or self.model_name,
                "messages": messages,
                "temperature": temperature or self.temperature,
                "max_tokens": max_tokens or self.max_tokens,
                "stream": stream
            }
            
            # 添加函数调用支持
            if functions:
                payload["functions"] = functions
            if function_call:
                payload["function_call"] = function_call
            
            start_time = time.time()
            
            if stream:
                return await self._stream_completion(payload)
            else:
                return await self._non_stream_completion(payload)
                
        except Exception as e:
            self.error_count += 1
            logger.error(f"DeepSeek聊天补全失败: {e}")
            raise
    
    async def _non_stream_completion(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """非流式聊天补全"""
        try:
            start_time = time.time()
            
            response = await self._client.post("/chat/completions", json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            # 记录统计信息
            end_time = time.time()
            latency = (end_time - start_time) * 1000
            
            self.request_count += 1
            self.total_latency += latency
            
            if "usage" in result:
                self.total_tokens += result["usage"].get("total_tokens", 0)
            
            # 处理响应
            if "choices" in result and len(result["choices"]) > 0:
                choice = result["choices"][0]
                
                return {
                    "success": True,
                    "content": choice["message"]["content"],
                    "function_call": choice["message"].get("function_call"),
                    "finish_reason": choice.get("finish_reason"),
                    "usage": result.get("usage", {}),
                    "model": result.get("model"),
                    "latency_ms": latency
                }
            else:
                return {
                    "success": False,
                    "error": "无效的响应格式",
                    "latency_ms": latency
                }
                
        except httpx.HTTPStatusError as e:
            logger.error(f"DeepSeek API HTTP错误: {e.response.status_code} - {e.response.text}")
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}: {e.response.text}",
                "latency_ms": 0
            }
        except Exception as e:
            logger.error(f"DeepSeek API请求失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "latency_ms": 0
            }
    
    async def _stream_completion(self, payload: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """流式聊天补全"""
        try:
            start_time = time.time()
            
            async with self._client.stream("POST", "/chat/completions", json=payload) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]  # 移除 "data: " 前缀
                        
                        if data.strip() == "[DONE]":
                            break
                        
                        try:
                            chunk = json.loads(data)
                            
                            if "choices" in chunk and len(chunk["choices"]) > 0:
                                choice = chunk["choices"][0]
                                delta = choice.get("delta", {})
                                
                                yield {
                                    "success": True,
                                    "content": delta.get("content", ""),
                                    "function_call": delta.get("function_call"),
                                    "finish_reason": choice.get("finish_reason"),
                                    "model": chunk.get("model")
                                }
                                
                        except json.JSONDecodeError:
                            continue
            
            # 记录统计信息
            end_time = time.time()
            latency = (end_time - start_time) * 1000
            self.request_count += 1
            self.total_latency += latency
            
        except Exception as e:
            logger.error(f"DeepSeek流式请求失败: {e}")
            yield {
                "success": False,
                "error": str(e)
            }
    
    async def generate_response(
        self,
        prompt: str,
        context: Optional[str] = None,
        system_message: Optional[str] = None,
        temperature: float = None,
        max_tokens: int = None
    ) -> Dict[str, Any]:
        """生成响应的便捷方法"""
        try:
            # 构建消息列表
            messages = []
            
            # 添加系统消息
            if system_message:
                messages.append({
                    "role": "system",
                    "content": system_message
                })
            
            # 添加上下文
            if context:
                messages.append({
                    "role": "user",
                    "content": f"上下文信息：\n{context}\n\n问题：{prompt}"
                })
            else:
                messages.append({
                    "role": "user",
                    "content": prompt
                })
            
            # 调用聊天补全
            result = await self.chat_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return result
            
        except Exception as e:
            logger.error(f"生成响应失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def generate_with_retrieval_context(
        self,
        query: str,
        retrieved_chunks: List[Dict[str, Any]],
        system_prompt: str = None
    ) -> Dict[str, Any]:
        """基于检索结果生成响应"""
        try:
            # 构建上下文
            context_parts = []
            for i, chunk in enumerate(retrieved_chunks[:5]):  # 限制上下文长度
                context_parts.append(f"[文档{i+1}] {chunk.get('content', '')}")
            
            context = "\n\n".join(context_parts)
            
            # 默认系统提示
            if not system_prompt:
                system_prompt = """你是一个专业的AI助手，请基于提供的上下文信息回答用户问题。
要求：
1. 回答要准确、详细、有条理
2. 如果上下文中没有相关信息，请明确说明
3. 引用具体的文档内容时请标注来源
4. 保持客观中立的语调"""
            
            return await self.generate_response(
                prompt=query,
                context=context,
                system_message=system_prompt
            )
            
        except Exception as e:
            logger.error(f"基于检索生成响应失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def switch_model(self, model_name: str) -> bool:
        """切换模型"""
        try:
            if model_name in self.model_configs:
                self.model_name = model_name
                config = self.model_configs[model_name]
                self.max_tokens = config["max_tokens"]
                logger.info(f"已切换到模型: {model_name}")
                return True
            else:
                logger.warning(f"不支持的模型: {model_name}")
                return False
                
        except Exception as e:
            logger.error(f"切换模型失败: {e}")
            return False
    
    async def get_model_info(self) -> Dict[str, Any]:
        """获取当前模型信息"""
        config = self.model_configs.get(self.model_name, {})
        return {
            "current_model": self.model_name,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "context_length": config.get("context_length", 0),
            "supports_streaming": config.get("supports_streaming", False),
            "supports_function_calling": config.get("supports_function_calling", False),
            "available_models": list(self.model_configs.keys())
        }
    
    async def get_usage_stats(self) -> Dict[str, Any]:
        """获取使用统计"""
        avg_latency = self.total_latency / self.request_count if self.request_count > 0 else 0
        avg_tokens = self.total_tokens / self.request_count if self.request_count > 0 else 0
        error_rate = self.error_count / self.request_count if self.request_count > 0 else 0
        
        return {
            "total_requests": self.request_count,
            "total_tokens": self.total_tokens,
            "total_latency_ms": self.total_latency,
            "avg_latency_ms": avg_latency,
            "avg_tokens_per_request": avg_tokens,
            "error_count": self.error_count,
            "error_rate": error_rate,
            "current_model": self.model_name
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            # 测试简单的API调用
            test_messages = [
                {"role": "user", "content": "Hello"}
            ]
            
            start_time = time.time()
            result = await self.chat_completion(
                messages=test_messages,
                max_tokens=10
            )
            end_time = time.time()
            
            if result["success"]:
                return {
                    "status": "healthy",
                    "model": self.model_name,
                    "api_accessible": True,
                    "test_latency_ms": (end_time - start_time) * 1000,
                    "usage_stats": await self.get_usage_stats()
                }
            else:
                return {
                    "status": "unhealthy",
                    "model": self.model_name,
                    "api_accessible": False,
                    "error": result.get("error")
                }
                
        except Exception as e:
            return {
                "status": "error",
                "model": self.model_name,
                "api_accessible": False,
                "error": str(e)
            }


# 全局DeepSeek LLM服务实例
deepseek_llm_service = DeepSeekLLMService()


# 便捷函数
async def generate_answer(
    query: str,
    context: Optional[str] = None,
    system_prompt: Optional[str] = None
) -> Dict[str, Any]:
    """生成答案的便捷函数"""
    return await deepseek_llm_service.generate_response(
        prompt=query,
        context=context,
        system_message=system_prompt
    )


async def generate_rag_answer(
    query: str,
    retrieved_chunks: List[Dict[str, Any]],
    system_prompt: Optional[str] = None
) -> Dict[str, Any]:
    """基于RAG检索生成答案的便捷函数"""
    return await deepseek_llm_service.generate_with_retrieval_context(
        query, retrieved_chunks, system_prompt
    )


async def stream_answer(
    query: str,
    context: Optional[str] = None,
    system_prompt: Optional[str] = None
) -> AsyncGenerator[Dict[str, Any], None]:
    """流式生成答案的便捷函数"""
    messages = []
    
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    
    if context:
        messages.append({
            "role": "user",
            "content": f"上下文信息：\n{context}\n\n问题：{query}"
        })
    else:
        messages.append({"role": "user", "content": query})
    
    async for chunk in deepseek_llm_service.chat_completion(
        messages=messages,
        stream=True
    ):
        yield chunk
