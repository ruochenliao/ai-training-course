"""
内容创作智能体

专门用于创作各类文案、文章、营销内容等。
"""

import logging
from typing import Dict, Any, List, Optional
import json
from datetime import datetime
from enum import Enum

from .base import BaseAgent, AgentMessage, AgentConfig
from .llm_interface import llm_manager

logger = logging.getLogger(__name__)


class ContentType(Enum):
    """内容类型"""
    ARTICLE = "article"  # 文章
    BLOG_POST = "blog_post"  # 博客文章
    MARKETING_COPY = "marketing_copy"  # 营销文案
    SOCIAL_MEDIA = "social_media"  # 社交媒体
    EMAIL = "email"  # 邮件
    PRODUCT_DESCRIPTION = "product_description"  # 产品描述
    PRESS_RELEASE = "press_release"  # 新闻稿
    TECHNICAL_DOC = "technical_doc"  # 技术文档
    CREATIVE_WRITING = "creative_writing"  # 创意写作


class ContentStyle(Enum):
    """内容风格"""
    PROFESSIONAL = "professional"  # 专业
    CASUAL = "casual"  # 随意
    FORMAL = "formal"  # 正式
    FRIENDLY = "friendly"  # 友好
    PERSUASIVE = "persuasive"  # 说服性
    INFORMATIVE = "informative"  # 信息性
    CREATIVE = "creative"  # 创意性
    TECHNICAL = "technical"  # 技术性


class ContentTone(Enum):
    """内容语调"""
    ENTHUSIASTIC = "enthusiastic"  # 热情
    CONFIDENT = "confident"  # 自信
    EMPATHETIC = "empathetic"  # 同理心
    AUTHORITATIVE = "authoritative"  # 权威
    CONVERSATIONAL = "conversational"  # 对话式
    INSPIRING = "inspiring"  # 鼓舞人心
    URGENT = "urgent"  # 紧急
    CALM = "calm"  # 平静


class ContentRequest:
    """内容创作请求"""
    
    def __init__(self, content_type: ContentType, topic: str, 
                 target_audience: str = "", style: ContentStyle = ContentStyle.PROFESSIONAL,
                 tone: ContentTone = ContentTone.CONVERSATIONAL, word_count: int = 500,
                 keywords: List[str] = None, requirements: str = ""):
        self.content_type = content_type
        self.topic = topic
        self.target_audience = target_audience
        self.style = style
        self.tone = tone
        self.word_count = word_count
        self.keywords = keywords or []
        self.requirements = requirements
        self.created_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "content_type": self.content_type.value,
            "topic": self.topic,
            "target_audience": self.target_audience,
            "style": self.style.value,
            "tone": self.tone.value,
            "word_count": self.word_count,
            "keywords": self.keywords,
            "requirements": self.requirements,
            "created_at": self.created_at.isoformat()
        }


class CreatedContent:
    """创作的内容"""
    
    def __init__(self, title: str, content: str, content_request: ContentRequest,
                 metadata: Dict[str, Any] = None):
        self.id = f"content_{datetime.now().timestamp()}"
        self.title = title
        self.content = content
        self.content_request = content_request
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        self.word_count = len(content.split())
        self.character_count = len(content)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "content_request": self.content_request.to_dict(),
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "word_count": self.word_count,
            "character_count": self.character_count
        }


class ContentCreationAgent(BaseAgent):
    """内容创作智能体"""
    
    def __init__(self, config: AgentConfig = None):
        if config is None:
            config = AgentConfig(
                name="ContentCreationAgent",
                description="专业的内容创作智能体，擅长各类文案和文章创作",
                model="gpt-4o",
                temperature=0.8,
                system_prompt=self._get_system_prompt()
            )
        
        super().__init__(config)
        
        # 内容库
        self.content_library: Dict[str, CreatedContent] = {}
        
        # 模板库
        self.templates: Dict[ContentType, Dict[str, str]] = {}
        
        # 创作统计
        self.stats = {
            "total_content": 0,
            "content_by_type": {},
            "average_word_count": 0,
            "popular_topics": {}
        }
        
        # 初始化模板
        self._initialize_templates()
    
    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是一个专业的内容创作专家，擅长创作各种类型的高质量内容。

核心能力：
1. 文章写作：博客文章、新闻稿、技术文档
2. 营销文案：产品描述、广告文案、邮件营销
3. 社交媒体：微博、朋友圈、短视频脚本
4. 创意写作：故事、诗歌、创意内容
5. 商务写作：报告、提案、演讲稿

创作原则：
1. 目标导向：明确内容目的和目标受众
2. 价值提供：确保内容对读者有价值
3. 结构清晰：逻辑分明，层次清楚
4. 语言精准：用词准确，表达清晰
5. 风格一致：保持统一的写作风格

创作流程：
1. 理解需求：分析内容类型、目标、受众
2. 构思大纲：规划内容结构和要点
3. 撰写内容：按照要求创作内容
4. 优化完善：检查语言、逻辑、格式
5. 质量保证：确保内容质量和效果

特色服务：
- 多种风格适配
- SEO优化建议
- 情感色彩调节
- 品牌调性匹配
- 多平台适配

始终记住：好的内容不仅要有价值，还要能够触动读者，产生共鸣。"""
    
    def _initialize_templates(self):
        """初始化内容模板"""
        self.templates = {
            ContentType.ARTICLE: {
                "structure": "标题 -> 引言 -> 主体(3-5个要点) -> 结论 -> 行动号召",
                "intro_template": "在当今{背景}的环境下，{主题}变得越来越重要...",
                "conclusion_template": "总的来说，{总结要点}。{行动建议}"
            },
            ContentType.MARKETING_COPY: {
                "structure": "吸引注意 -> 激发兴趣 -> 建立渴望 -> 促成行动(AIDA)",
                "hook_template": "你是否曾经{痛点描述}？",
                "cta_template": "立即{行动}，{好处描述}！"
            },
            ContentType.SOCIAL_MEDIA: {
                "structure": "钩子 -> 价值内容 -> 互动引导",
                "hook_template": "🔥{引人注目的开头}",
                "engagement_template": "你觉得呢？在评论区告诉我们！"
            },
            ContentType.EMAIL: {
                "structure": "主题行 -> 个性化开头 -> 价值内容 -> 明确CTA",
                "subject_template": "{个性化}，{价值承诺}",
                "opening_template": "Hi {姓名}，希望你{状态描述}..."
            }
        }
    
    async def process_message(self, message: AgentMessage) -> AgentMessage:
        """处理内容创作请求"""
        try:
            # 解析创作请求
            request_data = self._parse_content_request(message.content, message.metadata)
            content_request = self._create_content_request(request_data)
            
            # 创作内容
            created_content = await self._create_content(content_request)
            
            # 存储内容
            self.content_library[created_content.id] = created_content
            
            # 更新统计
            self._update_stats(created_content)
            
            # 构建响应
            response_content = json.dumps({
                "title": created_content.title,
                "content": created_content.content,
                "word_count": created_content.word_count,
                "metadata": created_content.metadata
            }, ensure_ascii=False, indent=2)
            
            response = AgentMessage(
                id=f"content_response_{message.id}",
                sender=self.name,
                receiver=message.sender,
                content=response_content,
                message_type="content_creation_response",
                metadata={
                    "original_message_id": message.id,
                    "content_id": created_content.id,
                    "content_request": content_request.to_dict()
                }
            )
            
            return response
            
        except Exception as e:
            logger.error(f"内容创作处理失败: {e}")
            error_response = AgentMessage(
                id=f"content_error_{message.id}",
                sender=self.name,
                receiver=message.sender,
                content=f"内容创作失败: {str(e)}",
                message_type="error"
            )
            return error_response
    
    def _parse_content_request(self, content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """解析内容创作请求"""
        # 从消息内容和元数据中提取创作参数
        request_data = {
            "topic": content,
            "content_type": metadata.get("content_type", "article"),
            "target_audience": metadata.get("target_audience", ""),
            "style": metadata.get("style", "professional"),
            "tone": metadata.get("tone", "conversational"),
            "word_count": metadata.get("word_count", 500),
            "keywords": metadata.get("keywords", []),
            "requirements": metadata.get("requirements", "")
        }
        return request_data
    
    def _create_content_request(self, request_data: Dict[str, Any]) -> ContentRequest:
        """创建内容请求对象"""
        return ContentRequest(
            content_type=ContentType(request_data["content_type"]),
            topic=request_data["topic"],
            target_audience=request_data["target_audience"],
            style=ContentStyle(request_data["style"]),
            tone=ContentTone(request_data["tone"]),
            word_count=request_data["word_count"],
            keywords=request_data["keywords"],
            requirements=request_data["requirements"]
        )
    
    async def _create_content(self, request: ContentRequest) -> CreatedContent:
        """创作内容"""
        try:
            # 生成大纲
            outline = await self._generate_outline(request)
            
            # 生成标题
            title = await self._generate_title(request)
            
            # 生成内容
            content = await self._generate_content_body(request, outline, title)
            
            # 优化内容
            optimized_content = await self._optimize_content(content, request)
            
            # 创建内容对象
            created_content = CreatedContent(
                title=title,
                content=optimized_content,
                content_request=request,
                metadata={
                    "outline": outline,
                    "seo_keywords": request.keywords,
                    "readability_score": self._calculate_readability(optimized_content)
                }
            )
            
            return created_content
            
        except Exception as e:
            logger.error(f"内容创作失败: {e}")
            raise
    
    async def _generate_outline(self, request: ContentRequest) -> List[str]:
        """生成内容大纲"""
        try:
            template = self.templates.get(request.content_type, {}).get("structure", "")
            
            prompt = f"""
为以下内容创作请求生成详细大纲：

内容类型：{request.content_type.value}
主题：{request.topic}
目标受众：{request.target_audience}
字数要求：{request.word_count}字
关键词：{', '.join(request.keywords)}
特殊要求：{request.requirements}

模板结构：{template}

请生成JSON格式的大纲：
["大纲要点1", "大纲要点2", "大纲要点3", ...]

要求：
1. 逻辑清晰，层次分明
2. 符合内容类型特点
3. 考虑目标受众需求
4. 包含关键词
5. 适合指定字数
"""
            
            response = await llm_manager.generate(
                prompt=prompt,
                model=self.model,
                temperature=0.6,
                max_tokens=800
            )
            
            try:
                outline = json.loads(response.content)
                return outline if isinstance(outline, list) else []
            except json.JSONDecodeError:
                # 简单解析
                lines = response.content.strip().split('\n')
                return [line.strip('- ').strip() for line in lines if line.strip()]
                
        except Exception as e:
            logger.error(f"大纲生成失败: {e}")
            return ["引言", "主要内容", "结论"]
    
    async def _generate_title(self, request: ContentRequest) -> str:
        """生成标题"""
        try:
            prompt = f"""
为以下内容创作一个吸引人的标题：

内容类型：{request.content_type.value}
主题：{request.topic}
目标受众：{request.target_audience}
风格：{request.style.value}
语调：{request.tone.value}
关键词：{', '.join(request.keywords)}

要求：
1. 吸引目标受众注意
2. 准确反映内容主题
3. 符合指定风格和语调
4. 包含关键词（如果合适）
5. 长度适中（10-60字符）

标题：
"""
            
            response = await llm_manager.generate(
                prompt=prompt,
                model=self.model,
                temperature=0.8,
                max_tokens=100
            )
            
            return response.content.strip().strip('"').strip("'")
            
        except Exception as e:
            logger.error(f"标题生成失败: {e}")
            return request.topic
    
    async def _generate_content_body(self, request: ContentRequest, 
                                   outline: List[str], title: str) -> str:
        """生成内容主体"""
        try:
            outline_text = '\n'.join([f"{i+1}. {point}" for i, point in enumerate(outline)])
            
            prompt = f"""
根据以下要求创作内容：

标题：{title}
内容类型：{request.content_type.value}
主题：{request.topic}
目标受众：{request.target_audience}
风格：{request.style.value}
语调：{request.tone.value}
字数要求：约{request.word_count}字
关键词：{', '.join(request.keywords)}
特殊要求：{request.requirements}

大纲：
{outline_text}

创作要求：
1. 严格按照大纲结构
2. 保持一致的风格和语调
3. 自然融入关键词
4. 内容有价值、有深度
5. 语言流畅、逻辑清晰
6. 符合目标受众需求
7. 达到指定字数要求

内容：
"""
            
            response = await llm_manager.generate(
                prompt=prompt,
                model=self.model,
                temperature=self.temperature,
                max_tokens=request.word_count * 3  # 给足够的token空间
            )
            
            return response.content.strip()
            
        except Exception as e:
            logger.error(f"内容主体生成失败: {e}")
            raise
    
    async def _optimize_content(self, content: str, request: ContentRequest) -> str:
        """优化内容"""
        try:
            prompt = f"""
请优化以下内容，使其更加完善：

原内容：
{content}

优化要求：
1. 检查语法和拼写
2. 改善句子流畅度
3. 增强逻辑连贯性
4. 优化关键词密度
5. 提升可读性
6. 保持原有风格和语调

目标受众：{request.target_audience}
风格：{request.style.value}
语调：{request.tone.value}

优化后的内容：
"""
            
            response = await llm_manager.generate(
                prompt=prompt,
                model=self.model,
                temperature=0.5,
                max_tokens=len(content.split()) * 2
            )
            
            return response.content.strip()
            
        except Exception as e:
            logger.error(f"内容优化失败: {e}")
            return content
    
    def _calculate_readability(self, content: str) -> float:
        """计算可读性分数（简化版）"""
        try:
            # 简单的可读性评估
            sentences = content.count('。') + content.count('！') + content.count('？')
            words = len(content.split())
            
            if sentences == 0:
                return 0.5
            
            avg_sentence_length = words / sentences
            
            # 基于平均句长评估可读性（简化算法）
            if avg_sentence_length <= 15:
                return 0.9
            elif avg_sentence_length <= 25:
                return 0.7
            elif avg_sentence_length <= 35:
                return 0.5
            else:
                return 0.3
                
        except Exception:
            return 0.5
    
    def _update_stats(self, content: CreatedContent):
        """更新统计信息"""
        self.stats["total_content"] += 1
        
        content_type = content.content_request.content_type.value
        if content_type not in self.stats["content_by_type"]:
            self.stats["content_by_type"][content_type] = 0
        self.stats["content_by_type"][content_type] += 1
        
        # 更新平均字数
        total = self.stats["total_content"]
        current_avg = self.stats["average_word_count"]
        self.stats["average_word_count"] = (current_avg * (total - 1) + content.word_count) / total
        
        # 更新热门话题
        topic = content.content_request.topic[:20]  # 截取前20字符作为话题
        if topic not in self.stats["popular_topics"]:
            self.stats["popular_topics"][topic] = 0
        self.stats["popular_topics"][topic] += 1
    
    async def generate_response(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """生成响应"""
        response = await llm_manager.generate(
            prompt=prompt,
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        return response.content
    
    def get_content(self, content_id: str) -> Optional[CreatedContent]:
        """获取内容"""
        return self.content_library.get(content_id)
    
    def list_content(self, content_type: ContentType = None) -> List[CreatedContent]:
        """列出内容"""
        contents = list(self.content_library.values())
        if content_type:
            contents = [c for c in contents if c.content_request.content_type == content_type]
        return contents
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.stats
