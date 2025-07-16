"""
聊天会话管理类
管理单用户对话状态，集成多记忆服务
与chat_service_api.py完全集成，不兼容旧代码
"""
import asyncio
import logging
import traceback
from datetime import datetime, timedelta
from io import BytesIO
from typing import List, Optional, Any, AsyncGenerator

import PIL.Image

# 直接导入 AutoGen 组件，不使用 try-except
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage, MultiModalMessage
from autogen_core import Image
from autogen_ext.models.openai import OpenAIChatCompletionClient

# 从 custom_context 导入 AUTOGEN_AVAILABLE 状态
from ..core.custom_context import AUTOGEN_AVAILABLE

# TaskResult 可能不存在，创建一个简单的替代类
class TaskResult:
    def __init__(self, messages=None, stop_reason=None):
        self.messages = messages or []
        self.stop_reason = stop_reason

from ..schemas.chat_service import (
    ChatServiceMessage, ChatServiceConfig
)
from ..core.custom_context import create_safe_assistant_with_memory
from .memory.autogen_memory import AutoGenMemoryAdapter

logger = logging.getLogger(__name__)


class ChatSession:
    """
    聊天会话管理类
    管理单用户对话状态，集成记忆服务
    与SmartChatSystem完全集成，支持多模态处理
    """

    def __init__(
        self,
        user_id: int,
        session_id: str,
        text_model_client: Optional[Any] = None,
        vision_model_client: Optional[Any] = None,
        config: Optional[ChatServiceConfig] = None
    ):
        """
        初始化聊天会话

        Args:
            user_id: 用户ID（整数类型）
            session_id: 会话ID
            text_model_client: 文本模型客户端
            vision_model_client: 视觉模型客户端
            config: 会话配置
        """
        self.user_id = user_id
        self.session_id = session_id
        self.text_model_client = text_model_client
        self.vision_model_client = vision_model_client
        self.config = config or ChatServiceConfig()

        # 模型名称（从客户端中提取，如果可用）
        self.text_model_name = getattr(text_model_client, 'model', None) if text_model_client else None
        self.vision_model_name = getattr(vision_model_client, 'model', None) if vision_model_client else None

        # 会话状态
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.message_count = 0
        self.is_active = True

        # 消息历史
        self.messages: List[ChatServiceMessage] = []

        # AutoGen智能体
        self.text_agent: Optional[AssistantAgent] = None
        self.vision_agent: Optional[AssistantAgent] = None

        # 记忆适配器
        self.memory_adapter: Optional[AutoGenMemoryAdapter] = None

        # 延迟初始化标志
        self._agents_initialized = False
        self._memory_initialized = False

        logger.info(f"创建聊天会话: {session_id} (用户: {user_id})")

    async def _ensure_memory_initialized(self):
        """确保记忆服务已初始化"""
        if not self._memory_initialized:
            await self._init_memory_adapter()
            self._memory_initialized = True

    async def _init_memory_adapter(self):
        """初始化记忆适配器"""
        try:
            # 获取数据库路径
            try:
                from app.settings.config import settings
                db_path = settings.TORTOISE_ORM["connections"]["sqlite"]["credentials"]["file_path"]
            except (AttributeError, KeyError, ImportError):
                db_path = "db.sqlite3"

            # 创建记忆适配器
            self.memory_adapter = AutoGenMemoryAdapter(str(self.user_id), db_path)
            logger.info(f"会话 {self.session_id} 记忆适配器初始化完成")
        except Exception as e:
            logger.error(f"初始化记忆适配器失败: {e}")
            self.memory_adapter = None
    
    async def _ensure_agents_initialized(self):
        """确保智能体已初始化"""
        if not self._agents_initialized:
            await self._init_agents()
            self._agents_initialized = True

    async def _init_agents(self):
        """初始化智能体"""
        if not AUTOGEN_AVAILABLE:
            logger.warning("AutoGen不可用，无法创建智能体")
            return

        try:
            # 确保记忆已初始化
            await self._ensure_memory_initialized()

            # 准备记忆适配器
            memory_adapters = []
            if self.memory_adapter:
                memory_adapters = [self.memory_adapter]

            # 创建文本智能体
            if self.text_model_client:
                logger.info(f"会话 {self.session_id} 开始创建文本智能体")
                self.text_agent = create_safe_assistant_with_memory(
                    name="text_agent",
                    model_client=self.text_model_client,
                    memory_adapters=memory_adapters,
                    system_message=self._get_text_system_prompt()
                )
                if self.text_agent:
                    logger.info(f"会话 {self.session_id} 文本智能体创建成功")
                else:
                    logger.error(f"会话 {self.session_id} 文本智能体创建失败")

            # 创建视觉智能体
            if self.vision_model_client:
                logger.info(f"会话 {self.session_id} 开始创建视觉智能体")
                self.vision_agent = create_safe_assistant_with_memory(
                    name="vision_agent",
                    model_client=self.vision_model_client,
                    memory_adapters=memory_adapters,
                    system_message=self._get_vision_system_prompt()
                )
                if self.vision_agent:
                    logger.info(f"会话 {self.session_id} 视觉智能体创建成功")
                else:
                    logger.error(f"会话 {self.session_id} 视觉智能体创建失败")

        except Exception as e:
            logger.error(f"初始化智能体失败: {e}")
            self.text_agent = None
            self.vision_agent = None

    def _get_text_system_prompt(self) -> str:
        """获取文本智能体系统提示"""
        return """你是专门处理文本对话的智能客服助手。你的职责是：

1. 回答用户的文本问题
2. 提供专业、友好、准确的服务
3. 理解用户意图并给出有用的建议
4. 保持对话的连贯性和上下文理解
5. 利用历史对话记忆和用户偏好提供个性化服务

## 📚 知识库使用策略（重要）

### 🎯 优先级原则：
1. **知识库优先**：优先使用记忆中的知识库内容回答问题
2. **智能匹配**：当知识库有相关信息时，即使相关度不是很高也要使用
3. **综合回答**：可以结合多个相关的知识库条目提供完整答案
4. **明确标注**：回答时要明确说明信息来源

### 📋 知识库内容识别：
- 记忆中标记为"public"来源的内容是公共知识库
- 记忆中标记为"private"来源的内容是用户个人知识库
- 这些内容是权威的信息来源

### 🔍 使用策略：
1. **有明确匹配时**：
   - 格式："根据知识库信息：[直接引用知识库内容]"
   - 严格基于知识库内容回答

2. **有相关内容时**：
   - 格式："根据知识库相关信息：[整合相关内容]"
   - 可以整合多个相关条目提供完整答案

3. **知识库内容不足时**：
   - 格式："知识库中有部分相关信息：[已有内容]。如需更详细信息，建议查阅官方文档。"
   - 先提供已有信息，再说明限制

4. **完全无相关内容时**：
   - 格式："知识库中暂无相关信息。建议查阅官方文档或联系相关部门获取准确信息。"

### ⚠️ 特别注意：
- 对于具体事实性问题（如书籍作者、产品信息等），必须优先使用知识库信息
- 当知识库有相关内容时，不要轻易说"暂无相关信息"
- 可以适当整合和总结知识库内容，但不要添加知识库中没有的信息
- 相关度较低但内容相关的信息也可以使用，但要说明"部分相关信息"

## 重要格式要求：
**必须严格使用标准 Markdown 格式**输出所有回复，确保内容能够正确渲染：

### 1. 代码块格式（严格要求）：
```语言名称
代码内容
```

**代码块规范**：
- 必须使用三个反引号开始和结束
- 必须指定正确的语言名称（如：python, javascript, html, css, sql等）
- 代码内容必须完整、格式化良好
- 每行代码独立成行，保持正确的缩进
- 包含适当的注释说明

### 2. 文本格式规范：
- **标题**：使用 # ## ### 层级标题
- **列表**：使用 - 或 1. 2. 3. 格式
- **强调**：**粗体** *斜体*
- **行内代码**：`代码片段`
- **引用**：> 引用内容
- **表格**：使用标准Markdown表格格式

### 3. 内容完整性要求：
- 提供完整的代码示例，确保可以直接运行
- 包含必要的导入语句和依赖
- 添加清晰的注释和说明
- 确保所有代码块都有正确的语言标识

请用中文回复，语气要专业且友好。确保所有内容都能在前端正确渲染显示。

**记住：知识库优先，但要智能灵活地使用相关信息！**"""

    def _get_vision_system_prompt(self) -> str:
        """获取视觉智能体系统提示"""
        return """你是专门处理多模态内容的智能客服助手。你的职责是：

1. 分析和理解图片、视频等多媒体内容
2. 结合视觉信息和文本描述回答用户问题
3. 提供基于视觉内容的专业建议
4. 识别图片中的物品、场景、文字等信息
5. 利用历史对话记忆和用户偏好提供个性化服务

## 知识库使用指南（重要）：

**你必须优先使用记忆中的知识库内容来回答用户问题**

### 多模态知识库处理：
- 记忆中的知识库内容可能包含图片、文档等多媒体信息
- 结合视觉分析和知识库内容提供综合回答
- 当用户上传的图片与知识库内容相关时，优先引用知识库信息

### 使用策略：
1. **视觉分析 + 知识库**：先分析图片内容，然后检查记忆中的相关知识库信息
2. **优先知识库**：如果知识库中有相关信息，必须基于知识库内容回答
3. **标注信息来源**：明确区分视觉分析结果和知识库信息
4. **综合回答**：将视觉分析和知识库内容结合，提供完整回答

## 重要格式要求：
**必须严格使用标准 Markdown 格式**输出所有回复，确保内容能够正确渲染：

### 1. 代码块格式（严格要求）：
```语言名称
代码内容
```

**代码块规范**：
- 必须使用三个反引号开始和结束
- 必须指定正确的语言名称（如：python, javascript, html, css等）
- 代码内容必须完整、格式化良好
- 每行代码独立成行，保持正确的缩进
- 包含适当的注释说明

### 2. 图像分析格式：
- **图像描述**：详细描述图像内容
- **识别结果**：列出识别到的物品、文字、场景
- **分析建议**：基于视觉内容提供专业建议

### 3. 文本格式规范：
- **标题**：使用 # ## ### 层级标题
- **列表**：使用 - 或 1. 2. 3. 格式
- **强调**：**粗体** *斜体*
- **行内代码**：`代码片段`
- **引用**：> 引用内容

请用中文回复，详细描述你看到的内容，并提供相关的帮助。确保所有内容都能在前端正确渲染显示。"""
    
    async def send_message(
        self,
        content: str,
        files: Optional[List[Any]] = None
    ) -> AsyncGenerator[str, None]:
        """
        发送消息并获取流式响应

        Args:
            content: 消息内容
            files: 上传的文件列表（UploadFile对象）

        Yields:
            str: 响应内容片段
        """
        try:
            # 更新活动时间
            self.last_activity = datetime.now()

            # 检测是否为多模态内容
            is_multimodal = self._detect_multimodal_content(content, files)

            # 确保智能体已初始化
            await self._ensure_agents_initialized()

            # 选择合适的智能体
            if is_multimodal and self.vision_agent:
                selected_agent = self.vision_agent
                agent_type = "多模态智能体"
            elif self.text_agent:
                selected_agent = self.text_agent
                agent_type = "文本智能体"
            else:
                # 强制重新初始化智能体
                logger.error("❌ 智能体不可用，尝试强制重新初始化")

                # 强制重新初始化
                self._agents_initialized = False
                await self._ensure_agents_initialized()

                # 重新选择智能体
                if is_multimodal and self.vision_agent:
                    selected_agent = self.vision_agent
                    agent_type = "视觉智能体"
                elif self.text_agent:
                    selected_agent = self.text_agent
                    agent_type = "文本智能体"
                else:
                    # 如果仍然失败，抛出异常而不是返回回退响应
                    error_msg = f"智能体初始化失败: AutoGen={AUTOGEN_AVAILABLE}, 文本客户端={self.text_model_client is not None}, 视觉客户端={self.vision_model_client is not None}"
                    logger.error(error_msg)
                    raise Exception(error_msg)

            logger.info(f"会话 {self.session_id} 选择了{agent_type}来处理消息")
            logger.info(f"🤖 智能体类型: {type(selected_agent)}")

            # 创建消息对象
            if is_multimodal and files:
                user_message = await self._create_multimodal_message(content, files)
                logger.info(f"📷 创建多模态消息: {len(files)} 个文件")
            else:
                user_message = content
                logger.info(f"📝 创建文本消息: {content[:50]}...")

            # 流式处理响应
            full_response = ""
            content_buffer = ""
            last_yield_time = 0
            min_yield_interval = 0.05
            chunk_count = 0
            total_chars = 0

            logger.info(f"🚀 开始调用智能体流式处理...")
            logger.info(f"📝 用户消息: {user_message}")
            logger.info(f"🤖 智能体类型: {type(selected_agent)}")

            try:
                logger.info(f"🔄 开始智能体流式调用...")
                message_count = 0
                async for message in selected_agent.run_stream(task=user_message):
                    message_count += 1
                    logger.info(f"📨 收到消息 #{message_count}: {type(message)}")
                    message_type = getattr(message, 'type', None)

                    # 处理流式token块
                    if message_type == 'ModelClientStreamingChunkEvent':
                        if hasattr(message, 'content') and message.content:
                            content_chunk = str(message.content)
                            if content_chunk:
                                content_buffer += content_chunk
                                full_response += content_chunk
                                chunk_count += 1
                                total_chars += len(content_chunk)

                                current_time = asyncio.get_event_loop().time()
                                if current_time - last_yield_time >= min_yield_interval or len(content_buffer) > 100:
                                    yield content_buffer
                                    content_buffer = ""
                                    last_yield_time = current_time
                                    await asyncio.sleep(0.01)

                    # 处理文本消息
                    elif message_type == 'TextMessage':
                        if (hasattr(message, 'source') and message.source == 'assistant' and
                            hasattr(message, 'content') and message.content):
                            content_chunk = str(message.content).strip()

                            if content_chunk and content_chunk != str(user_message).strip():
                                if not full_response:
                                    full_response = content_chunk
                                    yield content_chunk
                                    chunk_count += 1
                                    total_chars += len(content_chunk)
                                    await asyncio.sleep(0.01)
                                elif len(content_chunk) > len(full_response):
                                    remaining = content_chunk[len(full_response):]
                                    if remaining.strip():
                                        full_response = content_chunk
                                        yield remaining
                                        chunk_count += 1
                                        total_chars += len(remaining)
                                        await asyncio.sleep(0.01)

                    # 处理TaskResult
                    elif hasattr(message, 'messages'):
                        if not full_response:
                            for msg in message.messages:
                                if (hasattr(msg, 'source') and msg.source == 'assistant' and
                                    hasattr(msg, 'content') and msg.content):
                                    content_chunk = str(msg.content).strip()
                                    if content_chunk and content_chunk != str(user_message).strip():
                                        full_response = content_chunk
                                        yield content_chunk
                                        chunk_count += 1
                                        total_chars += len(content_chunk)
                                        await asyncio.sleep(0.01)
                                        break

                # 输出剩余缓冲内容
                if content_buffer:
                    yield content_buffer

                # 更新消息计数
                self.message_count += 1

                logger.info(f"会话 {self.session_id} 消息处理完成，响应长度: {len(full_response)}")
                logger.info(f"📊 处理统计: 块数={chunk_count}, 字符数={total_chars}")

            except Exception as inner_e:
                logger.error(f"❌ 智能体调用失败: {inner_e}")
                logger.error(f"详细错误: {traceback.format_exc()}")
                yield f"抱歉，AI处理时出现错误: {str(inner_e)}"

        except Exception as e:
            logger.error(f"❌ 发送消息失败: {e}")
            logger.error(f"详细错误: {traceback.format_exc()}")
            yield f"抱歉，处理您的消息时出现错误: {str(e)}"

    def _detect_multimodal_content(self, message: str, files: Optional[List[Any]] = None) -> bool:
        """检测是否包含多模态内容"""
        # 检查是否有文件上传
        if files and len(files) > 0:
            return True

        # 检查文本中是否提到图片、视频等
        multimodal_keywords = [
            '图片', '照片', '图像', '截图', '视频', '录像',
            'image', 'photo', 'picture', 'video', 'screenshot'
        ]

        message_lower = message.lower()
        return any(keyword in message_lower for keyword in multimodal_keywords)

    async def _create_multimodal_message(self, text: str, files: List[Any]) -> MultiModalMessage:
        """创建多模态消息"""
        content = [text]  # 文本内容

        for file in files:
            try:
                # 读取文件内容
                file_content = await file.read()

                # 检查文件类型
                if file.content_type and file.content_type.startswith('image/'):
                    # 处理图片文件
                    pil_image = PIL.Image.open(BytesIO(file_content))
                    img = Image(pil_image)
                    content.append(img)
                    logger.info(f"会话 {self.session_id} 添加图片到多模态消息: {file.filename}")
                else:
                    logger.warning(f"不支持的文件类型: {file.content_type}")

            except Exception as e:
                logger.error(f"处理文件 {file.filename} 失败: {e}")

        return MultiModalMessage(content=content, source="user")
    
    async def get_memory_stats(self) -> dict:
        """获取记忆统计信息"""
        try:
            if not self.memory_adapter:
                return {
                    "memory_enabled": False,
                    "message": "记忆功能未启用"
                }

            # 获取记忆健康信息
            health_info = await self.memory_adapter.health_check()

            return {
                "memory_enabled": True,
                "user_id": self.user_id,
                "session_id": self.session_id,
                "health_info": health_info
            }

        except Exception as e:
            logger.error(f"获取记忆统计失败: {e}")
            return {
                "memory_enabled": False,
                "error": str(e)
            }

    async def query_memory(self, query: str, limit: int = 5) -> List[dict]:
        """查询相关记忆"""
        try:
            if not self.memory_adapter:
                return []

            # 查询相关记忆
            memories = await self.memory_adapter.query(query, limit)

            # 转换为可序列化的格式
            memory_data = []
            for memory in memories:
                memory_info = {
                    "content": memory.content,
                    "metadata": memory.metadata,
                    "relevance_score": memory.metadata.get("relevance_score", 0)
                }
                memory_data.append(memory_info)

            return memory_data

        except Exception as e:
            logger.error(f"查询记忆失败: {e}")
            return []

    async def clear_memory(self, memory_type: str = "private") -> bool:
        """清空记忆数据"""
        try:
            if not self.memory_adapter:
                return False

            if memory_type == "all":
                await self.memory_adapter.clear()
            elif memory_type == "private":
                await self.memory_adapter.private_memory.clear()
            elif memory_type == "chat":
                await self.memory_adapter.chat_memory.clear()
            else:
                return False

            logger.info(f"会话 {self.session_id} 清空 {memory_type} 记忆成功")
            return True

        except Exception as e:
            logger.error(f"清空记忆失败: {e}")
            return False
    
    def get_session_info(self) -> dict:
        """获取会话信息"""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "message_count": self.message_count,
            "status": "active" if self.is_active else "inactive",
            "agents_initialized": self._agents_initialized,
            "memory_initialized": self._memory_initialized,
            "text_agent_available": self.text_agent is not None,
            "vision_agent_available": self.vision_agent is not None
        }

    async def close(self):
        """关闭会话"""
        try:
            self.is_active = False

            # 清理智能体
            self.text_agent = None
            self.vision_agent = None

            # 清理记忆适配器
            if self.memory_adapter:
                # 记忆适配器通常不需要显式关闭，但可以清理引用
                self.memory_adapter = None

            logger.info(f"会话 {self.session_id} 已关闭")

        except Exception as e:
            logger.error(f"关闭会话失败: {e}")

    def is_expired(self, timeout_minutes: int = 30) -> bool:
        """检查会话是否过期"""
        timeout = timedelta(minutes=timeout_minutes)
        return datetime.now() - self.last_activity > timeout

    def update_activity(self):
        """更新活动时间"""
        self.last_activity = datetime.now()

    def get_agent_status(self) -> dict:
        """获取智能体状态"""
        return {
            "text_agent": {
                "available": self.text_agent is not None,
                "model_client": self.text_model_client is not None
            },
            "vision_agent": {
                "available": self.vision_agent is not None,
                "model_client": self.vision_model_client is not None
            },
            "memory_adapter": {
                "available": self.memory_adapter is not None,
                "initialized": self._memory_initialized
            }
        }
