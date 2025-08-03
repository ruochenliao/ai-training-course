"""
总结智能体

负责对文本、对话、文档等内容进行总结和摘要。
"""

import json
import logging
from typing import Dict, Any, List, Optional
from enum import Enum
from .base import BaseAgent, AgentMessage, AgentConfig
from .llm_interface import llm_manager, TokenCounter

logger = logging.getLogger(__name__)


class SummaryType(Enum):
    """总结类型"""
    BRIEF = "brief"  # 简要总结
    DETAILED = "detailed"  # 详细总结
    BULLET_POINTS = "bullet_points"  # 要点总结
    EXECUTIVE = "executive"  # 执行摘要
    TECHNICAL = "technical"  # 技术总结


class SummaryRequest:
    """总结请求"""
    
    def __init__(self, content: str, summary_type: SummaryType = SummaryType.BRIEF,
                 max_length: int = 200, language: str = "zh", 
                 focus_areas: List[str] = None):
        self.content = content
        self.summary_type = summary_type
        self.max_length = max_length
        self.language = language
        self.focus_areas = focus_areas or []


class SummaryResult:
    """总结结果"""
    
    def __init__(self, summary: str, key_points: List[str] = None,
                 word_count: int = 0, compression_ratio: float = 0.0,
                 metadata: Dict[str, Any] = None):
        self.summary = summary
        self.key_points = key_points or []
        self.word_count = word_count
        self.compression_ratio = compression_ratio
        self.metadata = metadata or {}


class SummarizingAgent(BaseAgent):
    """总结智能体"""
    
    def __init__(self, config: AgentConfig = None):
        if config is None:
            config = AgentConfig(
                name="SummarizingAgent",
                description="负责对文本、对话、文档等内容进行总结和摘要",
                model="gpt-4o",
                temperature=0.3,
                system_prompt=self._get_system_prompt()
            )
        super().__init__(config)
    
    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是一个专业的内容总结助手，能够对各种类型的文本进行高质量的总结和摘要。

总结类型说明：
- brief: 简要总结，突出核心要点
- detailed: 详细总结，保留重要细节
- bullet_points: 要点总结，以列表形式呈现
- executive: 执行摘要，面向决策者
- technical: 技术总结，保留技术细节

总结原则：
1. 准确性：确保总结内容准确反映原文
2. 完整性：涵盖所有重要信息
3. 简洁性：用最少的文字表达最多的信息
4. 可读性：结构清晰，易于理解
5. 针对性：根据总结类型调整风格和重点

请根据用户要求返回以下JSON格式的总结：
{
    "summary": "总结内容",
    "key_points": ["要点1", "要点2", "要点3"],
    "word_count": 150,
    "compression_ratio": 0.15,
    "metadata": {
        "original_length": 1000,
        "summary_type": "brief",
        "language": "zh"
    }
}"""
    
    async def process_message(self, message: AgentMessage) -> AgentMessage:
        """处理总结请求"""
        try:
            # 解析总结请求
            request_data = self._parse_summary_request(message.content, message.metadata)
            
            # 执行总结
            result = await self._summarize_content(request_data)
            
            # 构建响应
            response_content = json.dumps({
                "summary": result.summary,
                "key_points": result.key_points,
                "word_count": result.word_count,
                "compression_ratio": result.compression_ratio,
                "metadata": result.metadata
            }, ensure_ascii=False, indent=2)
            
            response = AgentMessage(
                id=f"summary_response_{message.id}",
                sender=self.name,
                receiver=message.sender,
                content=response_content,
                message_type="summary_result",
                metadata={
                    "original_message_id": message.id,
                    "summary_type": request_data.summary_type.value
                }
            )
            
            return response
            
        except Exception as e:
            logger.error(f"总结处理失败: {e}")
            error_response = AgentMessage(
                id=f"summary_error_{message.id}",
                sender=self.name,
                receiver=message.sender,
                content=f"总结生成失败: {str(e)}",
                message_type="error"
            )
            return error_response
    
    def _parse_summary_request(self, content: str, metadata: Dict[str, Any]) -> SummaryRequest:
        """解析总结请求"""
        # 从metadata中获取参数，如果没有则使用默认值
        summary_type_str = metadata.get("summary_type", "brief")
        try:
            summary_type = SummaryType(summary_type_str)
        except ValueError:
            summary_type = SummaryType.BRIEF
        
        max_length = metadata.get("max_length", 200)
        language = metadata.get("language", "zh")
        focus_areas = metadata.get("focus_areas", [])
        
        return SummaryRequest(
            content=content,
            summary_type=summary_type,
            max_length=max_length,
            language=language,
            focus_areas=focus_areas
        )
    
    async def _summarize_content(self, request: SummaryRequest) -> SummaryResult:
        """执行内容总结"""
        # 计算原文长度
        original_length = len(request.content)
        original_tokens = TokenCounter.count_tokens(request.content)
        
        # 如果内容太长，先进行分块总结
        if original_tokens > 3000:
            return await self._hierarchical_summarize(request)
        else:
            return await self._direct_summarize(request)
    
    async def _direct_summarize(self, request: SummaryRequest) -> SummaryResult:
        """直接总结"""
        # 构建总结提示
        prompt = self._build_summary_prompt(request)
        
        # 调用LLM生成总结
        response = await llm_manager.generate(
            prompt=prompt,
            model=self.model,
            temperature=self.temperature,
            max_tokens=min(request.max_length * 2, 1000)
        )
        
        try:
            # 解析JSON响应
            result_data = json.loads(response.content)
            
            # 计算压缩比
            original_length = len(request.content)
            summary_length = len(result_data["summary"])
            compression_ratio = summary_length / original_length if original_length > 0 else 0
            
            return SummaryResult(
                summary=result_data["summary"],
                key_points=result_data.get("key_points", []),
                word_count=result_data.get("word_count", summary_length),
                compression_ratio=compression_ratio,
                metadata={
                    "original_length": original_length,
                    "summary_type": request.summary_type.value,
                    "language": request.language,
                    "method": "direct"
                }
            )
            
        except json.JSONDecodeError:
            # 如果JSON解析失败，直接使用响应内容
            summary = response.content
            return SummaryResult(
                summary=summary,
                key_points=[],
                word_count=len(summary),
                compression_ratio=len(summary) / len(request.content),
                metadata={
                    "original_length": len(request.content),
                    "summary_type": request.summary_type.value,
                    "language": request.language,
                    "method": "direct_fallback"
                }
            )
    
    async def _hierarchical_summarize(self, request: SummaryRequest) -> SummaryResult:
        """分层总结（用于长文本）"""
        # 将长文本分块
        chunks = self._split_content(request.content, max_tokens=2000)
        
        # 对每个块进行总结
        chunk_summaries = []
        for i, chunk in enumerate(chunks):
            chunk_request = SummaryRequest(
                content=chunk,
                summary_type=SummaryType.BRIEF,
                max_length=request.max_length // len(chunks),
                language=request.language
            )
            
            chunk_result = await self._direct_summarize(chunk_request)
            chunk_summaries.append(chunk_result.summary)
        
        # 合并块总结
        combined_summary = "\n\n".join(chunk_summaries)
        
        # 对合并的总结再次总结
        final_request = SummaryRequest(
            content=combined_summary,
            summary_type=request.summary_type,
            max_length=request.max_length,
            language=request.language,
            focus_areas=request.focus_areas
        )
        
        final_result = await self._direct_summarize(final_request)
        
        # 更新元数据
        final_result.metadata.update({
            "method": "hierarchical",
            "chunks_count": len(chunks),
            "original_length": len(request.content)
        })
        
        return final_result
    
    def _split_content(self, content: str, max_tokens: int = 2000) -> List[str]:
        """分割内容为块"""
        # 按段落分割
        paragraphs = content.split('\n\n')
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            # 检查添加这个段落后是否超过限制
            test_chunk = current_chunk + "\n\n" + paragraph if current_chunk else paragraph
            if TokenCounter.count_tokens(test_chunk) <= max_tokens:
                current_chunk = test_chunk
            else:
                # 如果当前块不为空，保存它
                if current_chunk:
                    chunks.append(current_chunk)
                
                # 如果单个段落就超过限制，需要进一步分割
                if TokenCounter.count_tokens(paragraph) > max_tokens:
                    # 按句子分割
                    sentences = paragraph.split('。')
                    temp_chunk = ""
                    for sentence in sentences:
                        test_sentence = temp_chunk + "。" + sentence if temp_chunk else sentence
                        if TokenCounter.count_tokens(test_sentence) <= max_tokens:
                            temp_chunk = test_sentence
                        else:
                            if temp_chunk:
                                chunks.append(temp_chunk)
                            temp_chunk = sentence
                    if temp_chunk:
                        current_chunk = temp_chunk
                else:
                    current_chunk = paragraph
        
        # 添加最后一个块
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def _build_summary_prompt(self, request: SummaryRequest) -> str:
        """构建总结提示"""
        focus_text = ""
        if request.focus_areas:
            focus_text = f"\n重点关注领域：{', '.join(request.focus_areas)}"
        
        type_instructions = {
            SummaryType.BRIEF: "生成简洁的总结，突出核心要点",
            SummaryType.DETAILED: "生成详细的总结，保留重要细节和背景信息",
            SummaryType.BULLET_POINTS: "以要点列表的形式总结，每个要点简洁明了",
            SummaryType.EXECUTIVE: "生成执行摘要，面向决策者，突出关键信息和建议",
            SummaryType.TECHNICAL: "生成技术总结，保留技术细节和专业术语"
        }
        
        instruction = type_instructions.get(request.summary_type, "生成总结")
        
        return f"""
请对以下内容进行总结：

{request.content}

总结要求：
- 类型：{request.summary_type.value}
- 指导：{instruction}
- 最大长度：约{request.max_length}字
- 语言：{request.language}{focus_text}

请返回JSON格式的结果。
"""
    
    async def generate_response(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """生成响应"""
        response = await llm_manager.generate(
            prompt=prompt,
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        return response.content
    
    async def summarize_conversation(self, messages: List[AgentMessage], 
                                   summary_type: SummaryType = SummaryType.BRIEF) -> SummaryResult:
        """总结对话"""
        # 构建对话文本
        conversation_text = ""
        for msg in messages:
            conversation_text += f"{msg.sender}: {msg.content}\n\n"
        
        request = SummaryRequest(
            content=conversation_text,
            summary_type=summary_type,
            max_length=300,
            language="zh"
        )
        
        return await self._summarize_content(request)
    
    async def extract_key_points(self, content: str, max_points: int = 5) -> List[str]:
        """提取关键要点"""
        prompt = f"""
请从以下内容中提取{max_points}个最重要的关键要点：

{content}

要求：
1. 每个要点简洁明了
2. 按重要性排序
3. 返回JSON数组格式：["要点1", "要点2", ...]
"""
        
        response = await llm_manager.generate(
            prompt=prompt,
            model=self.model,
            temperature=0.3,
            max_tokens=500
        )
        
        try:
            key_points = json.loads(response.content)
            return key_points if isinstance(key_points, list) else []
        except json.JSONDecodeError:
            return []
