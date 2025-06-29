"""
大语言模型服务
"""

import asyncio
import json
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, AsyncGenerator, Union

import httpx
from loguru import logger

from app.core import AIServiceException
from app.core import settings


@dataclass
class ChatMessage:
    """聊天消息"""
    role: str  # system, user, assistant
    content: str
    name: Optional[str] = None
    function_call: Optional[Dict] = None


@dataclass
class ChatCompletionRequest:
    """聊天完成请求"""
    messages: List[ChatMessage]
    model: str = "deepseek-chat"
    temperature: float = 0.1
    max_tokens: int = 4096
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stream: bool = False
    stop: Optional[List[str]] = None
    functions: Optional[List[Dict]] = None
    function_call: Optional[Union[str, Dict]] = None


@dataclass
class ChatCompletionResponse:
    """聊天完成响应"""
    id: str
    object: str
    created: int
    model: str
    choices: List[Dict]
    usage: Dict[str, int]


class LLMService:
    """大语言模型服务类"""
    
    def __init__(self):
        self.api_base = settings.LLM_BASE_URL
        self.api_key = settings.LLM_API_KEY
        self.model_name = settings.LLM_MODEL_NAME
        self.max_tokens = settings.LLM_MAX_TOKENS
        self.temperature = settings.LLM_TEMPERATURE
        
        # HTTP客户端配置
        self.timeout = httpx.Timeout(60.0, connect=10.0)
        self.limits = httpx.Limits(max_keepalive_connections=20, max_connections=100)
    
    async def chat_completion(
        self, 
        messages: List[Dict[str, str]],
        model: str = None,
        temperature: float = None,
        max_tokens: int = None,
        stream: bool = False,
        **kwargs
    ) -> Union[ChatCompletionResponse, AsyncGenerator[Dict, None]]:
        """聊天完成"""
        try:
            # 构建请求
            request_data = {
                "model": model or self.model_name,
                "messages": messages,
                "temperature": temperature or self.temperature,
                "max_tokens": max_tokens or self.max_tokens,
                "stream": stream,
                **kwargs
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            if stream:
                return self._stream_chat_completion(request_data, headers)
            else:
                return await self._sync_chat_completion(request_data, headers)
                
        except Exception as e:
            logger.error(f"LLM聊天完成失败: {e}")
            raise AIServiceException(f"LLM聊天完成失败: {e}")
    
    async def _sync_chat_completion(
        self, 
        request_data: Dict, 
        headers: Dict
    ) -> ChatCompletionResponse:
        """同步聊天完成"""
        async with httpx.AsyncClient(timeout=self.timeout, limits=self.limits) as client:
            response = await client.post(
                f"{self.api_base}/chat/completions",
                json=request_data,
                headers=headers
            )
            
            if response.status_code != 200:
                error_msg = f"LLM API错误: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise AIServiceException(error_msg)
            
            result = response.json()
            
            return ChatCompletionResponse(
                id=result["id"],
                object=result["object"],
                created=result["created"],
                model=result["model"],
                choices=result["choices"],
                usage=result["usage"]
            )
    
    async def _stream_chat_completion(
        self, 
        request_data: Dict, 
        headers: Dict
    ) -> AsyncGenerator[Dict, None]:
        """流式聊天完成"""
        async with httpx.AsyncClient(timeout=self.timeout, limits=self.limits) as client:
            async with client.stream(
                "POST",
                f"{self.api_base}/chat/completions",
                json=request_data,
                headers=headers
            ) as response:
                
                if response.status_code != 200:
                    error_msg = f"LLM API错误: {response.status_code}"
                    logger.error(error_msg)
                    raise AIServiceException(error_msg)
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]  # 移除 "data: " 前缀
                        
                        if data == "[DONE]":
                            break
                        
                        try:
                            chunk = json.loads(data)
                            yield chunk
                        except json.JSONDecodeError:
                            continue
    
    async def generate_text(
        self, 
        prompt: str,
        system_prompt: str = None,
        temperature: float = None,
        max_tokens: int = None
    ) -> str:
        """生成文本"""
        try:
            messages = []
            
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            messages.append({"role": "user", "content": prompt})
            
            response = await self.chat_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0]["message"]["content"]
            
        except Exception as e:
            logger.error(f"文本生成失败: {e}")
            raise AIServiceException(f"文本生成失败: {e}")
    
    async def generate_text_stream(
        self, 
        prompt: str,
        system_prompt: str = None,
        temperature: float = None,
        max_tokens: int = None
    ) -> AsyncGenerator[str, None]:
        """流式生成文本"""
        try:
            messages = []
            
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            messages.append({"role": "user", "content": prompt})
            
            async for chunk in await self.chat_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            ):
                if "choices" in chunk and len(chunk["choices"]) > 0:
                    delta = chunk["choices"][0].get("delta", {})
                    if "content" in delta:
                        yield delta["content"]
                        
        except Exception as e:
            logger.error(f"流式文本生成失败: {e}")
            raise AIServiceException(f"流式文本生成失败: {e}")
    
    async def summarize_text(
        self, 
        text: str, 
        max_length: int = 200,
        language: str = "zh"
    ) -> str:
        """文本摘要"""
        try:
            if language == "zh":
                system_prompt = f"你是一个专业的文本摘要助手。请为以下文本生成一个简洁准确的摘要，长度控制在{max_length}字以内。"
                prompt = f"请为以下文本生成摘要：\n\n{text}"
            else:
                system_prompt = f"You are a professional text summarization assistant. Please generate a concise and accurate summary of the following text, keeping it within {max_length} words."
                prompt = f"Please summarize the following text:\n\n{text}"
            
            summary = await self.generate_text(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.1,
                max_tokens=max_length * 2  # 给一些余量
            )
            
            return summary.strip()
            
        except Exception as e:
            logger.error(f"文本摘要失败: {e}")
            raise AIServiceException(f"文本摘要失败: {e}")
    
    async def extract_keywords(
        self, 
        text: str, 
        num_keywords: int = 10,
        language: str = "zh"
    ) -> List[str]:
        """提取关键词"""
        try:
            if language == "zh":
                system_prompt = "你是一个专业的关键词提取助手。请从给定文本中提取最重要的关键词。"
                prompt = f"请从以下文本中提取{num_keywords}个最重要的关键词，用逗号分隔：\n\n{text}"
            else:
                system_prompt = "You are a professional keyword extraction assistant. Please extract the most important keywords from the given text."
                prompt = f"Please extract {num_keywords} most important keywords from the following text, separated by commas:\n\n{text}"
            
            response = await self.generate_text(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.1,
                max_tokens=200
            )
            
            # 解析关键词
            keywords = [kw.strip() for kw in response.split(',')]
            return keywords[:num_keywords]
            
        except Exception as e:
            logger.error(f"关键词提取失败: {e}")
            raise AIServiceException(f"关键词提取失败: {e}")
    
    async def classify_text(
        self, 
        text: str, 
        categories: List[str],
        language: str = "zh"
    ) -> Dict[str, float]:
        """文本分类"""
        try:
            categories_str = "、".join(categories) if language == "zh" else ", ".join(categories)
            
            if language == "zh":
                system_prompt = "你是一个专业的文本分类助手。请根据给定的类别对文本进行分类。"
                prompt = f"请将以下文本分类到这些类别中：{categories_str}\n\n文本：{text}\n\n请返回每个类别的置信度分数（0-1之间），格式为JSON。"
            else:
                system_prompt = "You are a professional text classification assistant. Please classify the text according to the given categories."
                prompt = f"Please classify the following text into these categories: {categories_str}\n\nText: {text}\n\nPlease return confidence scores (0-1) for each category in JSON format."
            
            response = await self.generate_text(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.1,
                max_tokens=500
            )
            
            # 尝试解析JSON响应
            try:
                scores = json.loads(response)
                return scores
            except json.JSONDecodeError:
                # 如果解析失败，返回均匀分布
                return {cat: 1.0/len(categories) for cat in categories}
                
        except Exception as e:
            logger.error(f"文本分类失败: {e}")
            raise AIServiceException(f"文本分类失败: {e}")
    
    async def answer_question(
        self, 
        question: str, 
        context: str = None,
        language: str = "zh"
    ) -> str:
        """问答"""
        try:
            if language == "zh":
                if context:
                    system_prompt = "你是一个专业的问答助手。请根据提供的上下文信息准确回答用户的问题。如果上下文中没有相关信息，请明确说明。"
                    prompt = f"上下文信息：\n{context}\n\n问题：{question}\n\n请基于上下文信息回答问题："
                else:
                    system_prompt = "你是一个专业的问答助手。请准确、详细地回答用户的问题。"
                    prompt = question
            else:
                if context:
                    system_prompt = "You are a professional Q&A assistant. Please answer the user's question accurately based on the provided context. If there is no relevant information in the context, please state it clearly."
                    prompt = f"Context: {context}\n\nQuestion: {question}\n\nPlease answer the question based on the context:"
                else:
                    system_prompt = "You are a professional Q&A assistant. Please answer the user's question accurately and in detail."
                    prompt = question
            
            answer = await self.generate_text(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.1
            )
            
            return answer.strip()
            
        except Exception as e:
            logger.error(f"问答失败: {e}")
            raise AIServiceException(f"问答失败: {e}")
    
    async def analyze_query_intent(self, query: str) -> Dict[str, Any]:
        """
        分析用户查询意图

        Args:
            query: 用户查询

        Returns:
            分析结果
        """
        system_prompt = """你是一个查询分析专家。请分析用户的查询意图，提取关键信息。

请按照以下JSON格式返回分析结果：
{
    "intent": "查询意图类型(question_answering|information_retrieval|comparison|explanation|other)",
    "entities": ["实体1", "实体2"],
    "keywords": ["关键词1", "关键词2"],
    "query_type": "simple|complex|multi_step",
    "search_strategy": "vector|graph|hybrid",
    "domain": "查询领域",
    "complexity": "low|medium|high"
}"""

        try:
            response = await self.generate_text(
                prompt=f"请分析这个查询：{query}",
                system_prompt=system_prompt,
                temperature=0.1,
                max_tokens=500
            )

            # 尝试解析JSON
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                # 如果解析失败，返回默认结果
                return {
                    "intent": "question_answering",
                    "entities": [],
                    "keywords": query.split(),
                    "query_type": "simple",
                    "search_strategy": "hybrid",
                    "domain": "general",
                    "complexity": "medium"
                }
        except Exception as e:
            logger.error(f"查询意图分析失败: {e}")
            raise AIServiceException(f"查询意图分析失败: {e}")

    async def generate_rag_answer(
        self,
        query: str,
        context: str,
        sources: List[Dict[str, Any]] = None,
        conversation_history: List[Dict[str, str]] = None
    ) -> str:
        """
        基于检索结果生成RAG答案

        Args:
            query: 用户查询
            context: 检索到的上下文
            sources: 来源信息
            conversation_history: 对话历史

        Returns:
            生成的答案
        """
        system_prompt = """你是一个专业的知识问答助手。请基于提供的上下文信息，准确回答用户的问题。

要求：
1. 答案要准确、完整、有条理
2. 如果上下文中没有相关信息，请明确说明
3. 引用具体的来源信息
4. 使用清晰的中文表达
5. 保持客观中立的态度
6. 如果有多个观点，请都提及并说明来源"""

        # 构建用户提示
        user_prompt = f"问题：{query}\n\n"

        if context:
            user_prompt += f"上下文信息：\n{context}\n\n"

        if sources:
            user_prompt += "来源信息：\n"
            for i, source in enumerate(sources, 1):
                user_prompt += f"{i}. {source.get('title', '未知来源')}\n"
            user_prompt += "\n"

        if conversation_history:
            user_prompt += "对话历史：\n"
            for msg in conversation_history[-3:]:  # 只保留最近3轮对话
                user_prompt += f"{msg['role']}: {msg['content']}\n"
            user_prompt += "\n"

        user_prompt += "请基于上述信息回答问题："

        try:
            answer = await self.generate_text(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.3,
                max_tokens=1500
            )
            return answer.strip()
        except Exception as e:
            logger.error(f"RAG答案生成失败: {e}")
            raise AIServiceException(f"RAG答案生成失败: {e}")

    async def generate_rag_answer_stream(
        self,
        query: str,
        context: str,
        sources: List[Dict[str, Any]] = None,
        conversation_history: List[Dict[str, str]] = None
    ) -> AsyncGenerator[str, None]:
        """
        流式生成RAG答案
        """
        system_prompt = """你是一个专业的知识问答助手。请基于提供的上下文信息，准确回答用户的问题。

要求：
1. 答案要准确、完整、有条理
2. 如果上下文中没有相关信息，请明确说明
3. 引用具体的来源信息
4. 使用清晰的中文表达
5. 保持客观中立的态度"""

        # 构建用户提示
        user_prompt = f"问题：{query}\n\n"

        if context:
            user_prompt += f"上下文信息：\n{context}\n\n"

        if sources:
            user_prompt += "来源信息：\n"
            for i, source in enumerate(sources, 1):
                user_prompt += f"{i}. {source.get('title', '未知来源')}\n"
            user_prompt += "\n"

        user_prompt += "请基于上述信息回答问题："

        try:
            async for chunk in self.generate_text_stream(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.3,
                max_tokens=1500
            ):
                yield chunk
        except Exception as e:
            logger.error(f"流式RAG答案生成失败: {e}")
            raise AIServiceException(f"流式RAG答案生成失败: {e}")

    async def check_model_health(self) -> Dict[str, Any]:
        """检查模型健康状态"""
        try:
            test_messages = [
                {"role": "user", "content": "Hello, how are you?"}
            ]

            start_time = asyncio.get_event_loop().time()
            response = await self.chat_completion(
                messages=test_messages,
                max_tokens=50
            )
            end_time = asyncio.get_event_loop().time()

            return {
                "status": "healthy",
                "model": response.model,
                "response_time": end_time - start_time,
                "usage": response.usage
            }

        except Exception as e:
            logger.error(f"模型健康检查失败: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }


# 全局LLM服务实例
llm_service = LLMService()
