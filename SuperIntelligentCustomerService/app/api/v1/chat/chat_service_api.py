"""
聊天服务API端点
基于AutoGen框架的智能体聊天服务接口
支持文本和多模态内容的智能识别和处理
集成记忆功能，提供上下文感知的智能对话
标准化实现，参考roles.py模式
"""
import asyncio
import logging
from io import BytesIO
from typing import AsyncGenerator

import PIL.Image
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import MultiModalMessage
from autogen_core import Image
from autogen_core.models import ModelInfo, ModelFamily
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.models.openai._model_info import _MODEL_INFO, _MODEL_TOKEN_LIMITS
from fastapi import APIRouter, Request, Query, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from ....controllers.chat import chat_controller
from ....controllers.memory.autogen_memory import AutoGenMemoryAdapter
from ....controllers.memory.factory import MemoryServiceFactory
from ....controllers.model import model_controller
from ....core.dependency import DependAuth
from ....core.custom_context import create_safe_assistant_with_memory
from ....models.admin import User
from ....schemas import Success, Fail, SuccessExtra
from ....schemas.chat_service import *
from ....utils.encryption import decrypt_api_key, is_api_key_encrypted
from ....utils.serializer import safe_serialize

logger = logging.getLogger(__name__)

router = APIRouter()

# 默认模型信息配置
DEFAULT_TEXT_MODEL_INFO = ModelInfo(
    vision=False,  # 不支持视觉功能
    function_calling=True,  # 支持函数调用
    json_output=True,  # 支持JSON输出
    structured_output=True,  # 支持结构化输出
    family=ModelFamily.UNKNOWN,  # 模型系列为未知
)

DEFAULT_VISION_MODEL_INFO = ModelInfo(
    vision=True,  # 支持视觉功能
    function_calling=True,  # 支持函数调用
    json_output=True,  # 支持JSON输出
    structured_output=True,  # 支持结构化输出
    family=ModelFamily.UNKNOWN,  # 模型系列为未知
)

# 默认令牌限制
DEFAULT_TOKEN_LIMIT = 128000


class SmartChatSystem:
    """智能聊天系统 - 根据内容类型自动选择合适的处理方式，集成记忆功能"""

    def __init__(self):
        self.text_agent = None
        self.vision_agent = None
        self.initialized = False
        self.current_text_model = None
        self.current_vision_model = None

        # 记忆功能 - 使用BGE模型
        self.memory_factory = None
        self.memory_adapters = {}  # 用户ID -> AutoGenMemoryAdapter
        self.memory_enabled = True  # 启用记忆功能

    def _update_model_info(self, model_name: str, vision_support: bool):
        """更新模型信息到全局缓存"""
        model_info = DEFAULT_VISION_MODEL_INFO if vision_support else DEFAULT_TEXT_MODEL_INFO
        if model_name not in _MODEL_INFO:
            _MODEL_INFO[model_name] = model_info
        if model_name not in _MODEL_TOKEN_LIMITS:
            _MODEL_TOKEN_LIMITS[model_name] = DEFAULT_TOKEN_LIMIT
        return model_info

    def _create_model_client(self, model_name: str, api_host: str, api_key: str, model_info):
        """创建模型客户端"""
        return OpenAIChatCompletionClient(
            model=model_name,
            base_url=api_host,
            api_key=api_key,
            model_info=model_info,
        )

    def _get_default_config(self, vision_support: bool):
        """获取默认模型配置"""
        return {
            "model_name": "gpt-3.5-turbo",
            "api_host": "https://api.openai.com/v1",
            "api_key": "sk-default-key"
        }

    async def _get_model_config(self, model_name: str = None, vision_support: bool = False):
        """获取模型配置"""
        if not model_name:
            # 根据是否需要视觉支持选择默认模型
            model_type = "multimodal" if vision_support else "chat"
            default_model = await model_controller.model.filter(
                is_active=True,
                model_type=model_type
            ).first()

            if not default_model:
                logger.warning("数据库中没有找到可用模型，使用默认配置")
                return self._get_default_config(vision_support)

            # 验证API密钥必须是加密的
            if not is_api_key_encrypted(default_model.api_key):
                raise Exception(f"模型 {default_model.model_name} 的API密钥未加密")

            return {
                "model_name": default_model.model_name,
                "api_host": default_model.api_host,
                "api_key": decrypt_api_key(default_model.api_key)
            }
        else:
            # 根据模型名称获取配置
            try:
                model_config = await model_controller.get_model_by_name(model_name)
                if not model_config:
                    raise Exception(f"模型 {model_name} 不存在或未启用")

                # 验证API密钥必须是加密的
                if not is_api_key_encrypted(model_config.api_key):
                    raise Exception(f"模型 {model_name} 的API密钥未加密")

                return {
                    "model_name": model_name,
                    "api_host": model_config.api_host,
                    "api_key": decrypt_api_key(model_config.api_key)
                }
            except Exception:
                logger.warning(f"获取模型 {model_name} 配置失败，使用默认配置")
                default_config = self._get_default_config(vision_support)
                default_config["model_name"] = model_name  # 保持用户指定的模型名
                return default_config

    async def get_model_client(self, model_name: str = None, vision_support: bool = False):
        """动态获取模型客户端"""
        try:
            # 获取模型配置
            config = await self._get_model_config(model_name, vision_support)

            # 更新模型信息并创建客户端
            model_info = self._update_model_info(config["model_name"], vision_support)
            return self._create_model_client(
                config["model_name"],
                config["api_host"],
                config["api_key"],
                model_info
            )
        except Exception as e:
            logger.error(f"创建模型客户端失败: {e}")
            # 使用默认配置创建客户端
            default_config = self._get_default_config(vision_support)
            model_info = self._update_model_info(default_config["model_name"], vision_support)
            return self._create_model_client(
                default_config["model_name"],
                default_config["api_host"],
                default_config["api_key"],
                model_info
            )

    async def initialize_memory_system(self):
        """初始化记忆系统"""
        try:
            if self.memory_factory is None:
                # 获取数据库路径
                try:
                    from ....settings.config import settings
                    db_path = settings.TORTOISE_ORM["connections"]["sqlite"]["credentials"]["file_path"]
                except (AttributeError, KeyError):
                    db_path = "db.sqlite3"

                self.memory_factory = MemoryServiceFactory(db_path)
                logger.info("记忆系统初始化成功")
        except Exception as e:
            logger.warning(f"记忆系统初始化失败，将禁用记忆功能: {e}")
            self.memory_enabled = False

    async def get_memory_adapter(self, user_id: int, session_id: str = None) -> Optional[AutoGenMemoryAdapter]:
        """获取用户的记忆适配器"""
        if not self.memory_enabled:
            return None

        try:
            # 确保记忆系统已初始化
            await self.initialize_memory_system()

            user_key = str(user_id)
            if user_key not in self.memory_adapters:
                # 创建新的记忆适配器
                db_path = None
                try:
                    from ....settings.config import settings
                    db_path = settings.TORTOISE_ORM["connections"]["sqlite"]["credentials"]["file_path"]
                except (AttributeError, KeyError):
                    db_path = "db.sqlite3"

                self.memory_adapters[user_key] = AutoGenMemoryAdapter(user_key, db_path)
                logger.info(f"为用户 {user_id} 创建记忆适配器")

            return self.memory_adapters[user_key]
        except Exception as e:
            logger.error(f"获取记忆适配器失败: {e}")
            return None

    async def initialize_agents(self, text_model_name: str = None, vision_model_name: str = None, user_id: int = None, session_id: str = None):
        """初始化智能体系统，集成记忆功能"""
        try:
            # 初始化记忆系统
            await self.initialize_memory_system()

            # 获取模型客户端
            text_model_client = await self.get_model_client(model_name=text_model_name, vision_support=False)
            vision_model_client = await self.get_model_client(model_name=vision_model_name, vision_support=True)

            # 记忆功能已启用，使用BGE嵌入模型
            memory_adapters = []
            if user_id and self.memory_enabled:
                try:
                    memory_adapter = await self.get_memory_adapter(user_id, session_id)
                    if memory_adapter:
                        memory_adapters = [memory_adapter]
                        logger.info(f"为智能体配置记忆适配器 (用户: {user_id}, 会话: {session_id})")
                except Exception as memory_error:
                    logger.warning(f"记忆适配器初始化失败，将禁用记忆功能: {memory_error}")
                    memory_adapters = []

            # 创建文本智能体（使用修复后的上下文）
            self.text_agent = create_safe_assistant_with_memory(
                name="text_agent",
                model_client=text_model_client,
                memory_adapters=memory_adapters,
                system_message="""你是专门处理文本对话的智能客服助手。你的职责是：

1. 回答用户的文本问题
2. 提供专业、友好、准确的服务
3. 理解用户意图并给出有用的建议
4. 保持对话的连贯性和上下文理解
5. 利用历史对话记忆和用户偏好提供个性化服务

## 知识库使用指南（重要）：

**你必须优先使用记忆中的知识库内容来回答用户问题**

### 知识库内容识别：
- 记忆中标记为"公共知识库"的内容是上传的文档知识
- 记忆中标记为"个人相关信息"的内容是用户的个人知识库
- 这些内容是最权威和准确的信息来源

### 使用策略：
1. **优先检查记忆**：首先检查记忆中是否有与用户问题相关的知识库内容
2. **严格基于知识库**：如果找到相关内容，必须严格基于这些内容回答，不要添加额外信息
3. **明确标注来源**：在回答中明确说明信息来源于知识库
4. **保持准确性**：不要修改或解释知识库内容，直接使用原始信息
5. **结构化呈现**：将知识库内容整理成清晰易懂的格式

### 回答模式：
- **有知识库内容**：基于知识库内容回答，格式："根据知识库信息：[具体内容]"
- **无相关知识库**：基于常识回答，但要说明："基于一般知识，[回答内容]，建议查阅相关文档获取准确信息"

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

请用中文回复，语气要专业且友好。确保所有内容都能在前端正确渲染显示。"""
            )

            # 创建多模态智能体（使用修复后的上下文）
            self.vision_agent = create_safe_assistant_with_memory(
                name="vision_agent",
                model_client=vision_model_client,
                memory_adapters=memory_adapters,
                system_message="""你是专门处理多模态内容的智能客服助手。你的职责是：

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
            )

            # 记录当前使用的模型
            self.current_text_model = text_model_name
            self.current_vision_model = vision_model_name
            self.initialized = True
            logger.info(f"智能聊天系统初始化成功 - 文本模型: {text_model_name}, 视觉模型: {vision_model_name}, 记忆: {'启用' if memory_adapters else '禁用'}")

        except Exception as e:
            logger.error(f"初始化智能体系统失败: {e}")
            raise



    async def process_message(self, message: str, files: List[UploadFile] = None, model_name: str = None, user_id: int = None, session_id: str = None) -> AsyncGenerator[str, None]:
        """处理消息并生成流式响应，集成AutoGen记忆功能"""
        try:
            # 检测是否为多模态内容
            is_multimodal = self.detect_multimodal_content(message, files)

            # 确定需要使用的模型
            target_model = model_name if model_name else None

            # 检查是否需要重新初始化智能体（模型切换或用户切换）
            need_reinit = False
            if not self.initialized:
                need_reinit = True
            elif is_multimodal and self.current_vision_model != target_model:
                need_reinit = True
                logger.info(f"检测到视觉模型切换: {self.current_vision_model} -> {target_model}")
            elif not is_multimodal and self.current_text_model != target_model:
                need_reinit = True
                logger.info(f"检测到文本模型切换: {self.current_text_model} -> {target_model}")

            # 重新初始化智能体（如果需要），传递用户信息以集成记忆
            if need_reinit:
                if is_multimodal:
                    await self.initialize_agents(vision_model_name=target_model, user_id=user_id, session_id=session_id)
                else:
                    await self.initialize_agents(text_model_name=target_model, user_id=user_id, session_id=session_id)

            # 根据内容类型选择智能体
            if is_multimodal:
                selected_agent = self.vision_agent
                agent_type = "多模态智能体"
                current_model = self.current_vision_model or "默认视觉模型"
            else:
                selected_agent = self.text_agent
                agent_type = "文本智能体"
                current_model = self.current_text_model or "默认文本模型"

            logger.info(f"选择了{agent_type}({current_model})来处理用户消息: {message[:50]}...")

            # 注意：不再手动添加记忆，AutoGen框架会自动处理
            # 记忆的添加和检索将通过Memory协议自动完成

            # 创建消息对象
            if is_multimodal and files:
                # 创建多模态消息
                user_message = await self.create_multimodal_message(message, files)
            else:
                # 创建文本消息
                user_message = message

            # 使用选定的智能体生成流式响应
            try:
                logger.info("开始流式处理...")

                # 优化的流式响应处理逻辑
                full_response = ""
                content_buffer = ""
                last_yield_time = 0
                min_yield_interval = 0.05  # 最小输出间隔50ms，减少渲染频率

                async for message in selected_agent.run_stream(task=user_message):
                    try:
                        # 检查消息类型
                        message_type = getattr(message, 'type', None)

                        # 处理流式token块 (ModelClientStreamingChunkEvent)
                        if message_type == 'ModelClientStreamingChunkEvent':
                            if hasattr(message, 'content') and message.content:
                                content = str(message.content)
                                if content:
                                    content_buffer += content
                                    full_response += content

                                    # 控制输出频率，避免过于频繁的渲染
                                    current_time = asyncio.get_event_loop().time()
                                    if current_time - last_yield_time >= min_yield_interval or len(content_buffer) > 100:
                                        logger.debug(f"流式块输出: {content_buffer[:50]}... (缓冲长度: {len(content_buffer)})")
                                        yield content_buffer
                                        content_buffer = ""
                                        last_yield_time = current_time
                                        await asyncio.sleep(0.01)

                        # 处理文本消息 (TextMessage)
                        elif message_type == 'TextMessage':
                            if (hasattr(message, 'source') and message.source == 'assistant' and
                                hasattr(message, 'content') and message.content):
                                content = str(message.content).strip()

                                # 确保不重复输出用户输入
                                if content and content != str(user_message).strip():
                                    # 如果没有流式内容，直接输出完整内容
                                    if not full_response:
                                        full_response = content
                                        logger.debug(f"完整文本消息: {content[:100]}... (总长度: {len(content)})")
                                        yield content
                                        await asyncio.sleep(0.01)
                                    # 如果有流式内容但内容更完整，输出差异部分
                                    elif len(content) > len(full_response):
                                        remaining = content[len(full_response):]
                                        if remaining.strip():
                                            full_response = content
                                            logger.debug(f"补充内容: {remaining[:50]}... (补充长度: {len(remaining)})")
                                            yield remaining
                                            await asyncio.sleep(0.01)

                        # 处理TaskResult（最终结果）
                        elif hasattr(message, 'messages'):
                            logger.debug("收到TaskResult")
                            # 如果没有收到任何流式内容，从TaskResult中提取
                            if not full_response:
                                for msg in message.messages:
                                    if (hasattr(msg, 'source') and msg.source == 'assistant' and
                                        hasattr(msg, 'content') and msg.content):
                                        content = str(msg.content).strip()
                                        if content and content != str(user_message).strip():
                                            full_response = content
                                            logger.debug(f"TaskResult内容: {content[:100]}... (总长度: {len(content)})")
                                            yield content
                                            await asyncio.sleep(0.01)
                                            break

                        # 处理其他类型的消息
                        else:
                            logger.debug(f"收到其他类型消息: {message_type}")

                    except Exception as chunk_error:
                        logger.warning(f"处理消息时出错: {chunk_error}")
                        continue

                # 输出剩余的缓冲内容
                if content_buffer:
                    logger.debug(f"输出剩余缓冲内容: {content_buffer[:50]}... (长度: {len(content_buffer)})")
                    yield content_buffer

                logger.info(f"流式处理完成，总长度: {len(full_response)}")

                # 检查代码完整性
                if "```" in full_response:
                    code_blocks = full_response.count("```")
                    if code_blocks % 2 != 0:
                        logger.warning("检测到不完整的代码块，代码块标记数量为奇数")
                    else:
                        logger.info(f"代码块完整性检查通过，共 {code_blocks // 2} 个代码块")

                # 检查是否包含函数定义
                if "def " in full_response:
                    logger.info("响应包含函数定义")
                    # 检查是否有完整的函数结构
                    if full_response.count("def ") > 0:
                        logger.info(f"检测到 {full_response.count('def ')} 个函数定义")
                        # 检查第一个函数定义的位置
                        first_def_pos = full_response.find("def ")
                        logger.info(f"第一个函数定义位置: {first_def_pos}")
                        if first_def_pos > 0:
                            logger.info(f"函数定义前的内容: {repr(full_response[:first_def_pos])}")

                # 注意：不再手动添加AI回复到记忆
                # AutoGen框架会自动通过Memory协议处理记忆的添加和管理

            except Exception as e:
                logger.error(f"智能体响应生成失败: {e}")
                yield f"抱歉，生成回复时出现错误：{str(e)}"

        except Exception as e:
            logger.error(f"智能体处理消息失败: {e}")
            yield f"抱歉，处理您的请求时出现了错误：{str(e)}"

    async def create_multimodal_message(self, text: str, files: List[UploadFile]) -> MultiModalMessage:
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
                    logger.info(f"添加图片到多模态消息: {file.filename}")
                else:
                    logger.warning(f"不支持的文件类型: {file.content_type}")

            except Exception as e:
                logger.error(f"处理文件 {file.filename} 失败: {e}")

        return MultiModalMessage(content=content, source="user")

    def detect_multimodal_content(self, message: str, files: List[UploadFile] = None) -> bool:
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


# 全局智能聊天系统实例
smart_chat_system = SmartChatSystem()


@router.post("/send", summary="发送聊天消息（支持多模态）")
async def send_chat_message(
    request: Request,
    current_user: User = DependAuth
):
    """
    发送聊天消息并获取AI回复（统一接口）
    支持三种输入方式：
    1. JSON格式：纯文本消息
    2. Form格式：支持文件上传（多模态消息）
    3. Form格式：纯文本消息（兼容性）
    智能识别内容类型并选择合适的处理方式
    只支持流式响应
    """
    try:
        content_type = request.headers.get("content-type", "")
        logger.info(f"收到请求，Content-Type: {content_type}")

        # 解析请求数据
        message_data = await _parse_request_data(request, content_type)
        if not message_data:
            return Fail(msg="请求数据解析失败")

        # 验证消息内容
        if not message_data.get("message") or not message_data["message"].strip():
            return Fail(msg="消息内容不能为空")

        # 返回流式响应
        return StreamingResponse(
            _generate_stream_response(
                message=message_data["message"],
                session_id=message_data.get("session_id"),
                files=message_data.get("files", []),
                model_name=message_data.get("model_name"),
                user_id=current_user.id
            ),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
                "X-Accel-Buffering": "no"  # 禁用Nginx缓冲，确保流式响应实时传输
            }
        )

    except Exception as e:
        logger.error(f"发送聊天消息失败: {e}")
        return Fail(msg=f"发送消息失败: {str(e)}")


async def _parse_request_data(request: Request, content_type: str) -> Optional[dict]:
    """解析请求数据的辅助函数"""
    try:
        if "application/json" in content_type:
            # JSON格式输入（纯文本）
            json_data = await request.json()
            logger.info(f"解析JSON数据: {json_data}")

            # 验证数据格式
            if "messages" in json_data and json_data["messages"]:
                # 获取用户消息
                user_message = None
                for msg in reversed(json_data["messages"]):
                    if msg.get("role") == "user":
                        user_message = msg
                        break

                if user_message and user_message.get("content"):
                    return {
                        "message": user_message["content"].strip(),
                        "session_id": json_data.get("session_id"),
                        "model_name": json_data.get("model_name"),
                        "files": []
                    }
            elif "message" in json_data:
                # 简单消息格式
                return {
                    "message": json_data["message"].strip(),
                    "session_id": json_data.get("session_id"),
                    "model_name": json_data.get("model_name"),
                    "files": []
                }

        elif "multipart/form-data" in content_type or "application/x-www-form-urlencoded" in content_type:
            # Form格式输入（支持多模态）
            form_data = await request.form()
            message = form_data.get("message")

            if message and message.strip():
                # 处理上传的文件
                uploaded_files = []
                files = form_data.getlist("files")
                for file in files:
                    if hasattr(file, 'filename') and file.filename:
                        # 验证文件类型
                        if file.content_type and not file.content_type.startswith('image/'):
                            logger.warning(f"不支持的文件类型: {file.content_type}")
                            continue
                        uploaded_files.append(file)

                # 处理 session_id 类型转换
                session_id = form_data.get("session_id")
                if session_id:
                    try:
                        session_id = int(session_id)
                    except (ValueError, TypeError):
                        logger.warning(f"无效的session_id格式: {session_id}")
                        session_id = None

                return {
                    "message": message.strip(),
                    "session_id": session_id,
                    "model_name": form_data.get("model_name"),
                    "files": uploaded_files
                }

        return None
    except Exception as e:
        logger.error(f"解析请求数据失败: {e}")
        return None


async def _generate_stream_response(
        message: str,
        session_id: Optional[str],
        files: List[UploadFile],
        model_name: Optional[str],
        user_id: int
) -> AsyncGenerator[str, None]:
    """生成优化的流式响应，包含完整的元数据和状态信息"""
    import json
    import time
    from datetime import datetime

    message_id = f"msg_{int(time.time() * 1000)}"
    start_time = datetime.now()

    def create_stream_event(event_type: str, data: any = None, **kwargs) -> str:
        """创建标准化的流式事件"""
        event = {
            "id": message_id,
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "user_id": user_id,
            "model_name": model_name or "smart-chat-system",
            **kwargs
        }
        if data is not None:
            event["data"] = data
        return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    try:
        # 发送开始事件
        yield create_stream_event("start", {"message": "开始处理您的请求..."})

        # 保存用户消息到数据库
        if session_id:
            try:
                from ....controllers.chat import chat_controller
                from ....schemas.chat import ChatMessageCreate

                # 安全地转换session_id为整数
                try:
                    if isinstance(session_id, int):
                        session_id_int = session_id
                    elif isinstance(session_id, str) and session_id.isdigit():
                        session_id_int = int(session_id)
                    else:
                        session_id_int = 1
                except (ValueError, AttributeError):
                    session_id_int = 1

                user_message_create = ChatMessageCreate(
                    session_id=session_id_int,
                    user_id=user_id,
                    role="user",
                    content=message,
                    model_name="smart-agent",
                    total_tokens=0,
                    deduct_cost=0
                )
                await chat_controller.create_message(user_message_create)
                yield create_stream_event("user_message_saved", {"status": "success"})
            except Exception as save_error:
                logger.warning(f"保存用户消息失败: {save_error}")
                yield create_stream_event("user_message_saved", {"status": "failed", "error": str(save_error)})

        # 发送处理状态
        yield create_stream_event("processing", {"message": "AI正在思考中..."})

        # 使用智能聊天系统处理消息（集成记忆功能）
        full_response = ""
        chunk_count = 0

        async for content in smart_chat_system.process_message(message, files, model_name, user_id, session_id):
            if content.strip():
                full_response += content
                chunk_count += 1

                # 发送内容块事件
                yield create_stream_event(
                    "content",
                    content,
                    chunk_index=chunk_count,
                    total_length=len(full_response),
                    is_markdown=True
                )

        # 发送完成事件
        processing_time = (datetime.now() - start_time).total_seconds()
        yield create_stream_event(
            "complete",
            {
                "full_content": full_response,
                "total_chunks": chunk_count,
                "processing_time": processing_time,
                "word_count": len(full_response.split()),
                "char_count": len(full_response)
            }
        )

        # 保存AI回复到数据库
        if session_id and full_response:
            try:
                # 安全地转换session_id为整数
                try:
                    if isinstance(session_id, int):
                        session_id_int = session_id
                    elif isinstance(session_id, str) and session_id.isdigit():
                        session_id_int = int(session_id)
                    else:
                        session_id_int = 1
                except (ValueError, AttributeError):
                    session_id_int = 1

                ai_message_create = ChatMessageCreate(
                    session_id=session_id_int,
                    user_id=user_id,
                    role="assistant",
                    content=full_response.strip(),
                    model_name="smart-chat-system",
                    total_tokens=len(full_response.split()),
                    deduct_cost=0.001
                )
                await chat_controller.create_message(ai_message_create)
                yield create_stream_event("ai_message_saved", {"status": "success"})
            except Exception as save_error:
                logger.warning(f"保存AI回复失败: {save_error}")
                yield create_stream_event("ai_message_saved", {"status": "failed", "error": str(save_error)})

        # 发送结束标记
        yield create_stream_event("done", {"message": "处理完成"})

    except Exception as e:
        logger.error(f"流式响应生成失败: {e}")
        # 发送错误事件
        yield create_stream_event(
            "error",
            {
                "message": f"抱歉，处理您的请求时出现了错误：{str(e)}",
                "error_type": type(e).__name__,
                "recoverable": True
            }
        )
        yield create_stream_event("done", {"message": "处理结束（出现错误）"})


@router.get("/session/get", summary="获取会话信息")
async def get_session_info(
        session_id: int = Query(..., description="会话ID"),
        current_user: User = DependAuth
):
    """获取指定会话的信息"""
    try:
        from ....controllers.session import session_controller

        session = await session_controller.get_user_session(session_id, current_user.id)
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在或无权限访问")

        session_dict = await session.to_dict()
        return Success(data=session_dict)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取会话信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取会话信息失败: {str(e)}")


@router.get("/session/list", summary="获取用户会话列表")
async def list_user_sessions(
        page: int = Query(1, description="页码"),
        page_size: int = Query(20, description="每页数量"),
        current_user: User = DependAuth
):
    """获取当前用户的会话列表"""
    try:
        from ....controllers.session import session_controller

        total, sessions = await session_controller.get_user_sessions(
            user_id=current_user.id,
            page=page,
            page_size=page_size
        )

        # 转换为标准格式
        session_list = []
        for session in sessions:
            session_dict = await session.to_dict()
            session_list.append({
                "id": str(session_dict["id"]),
                "title": session_dict.get("session_title", "新对话"),
                "updated_at": session_dict.get("updated_at")
            })

        return SuccessExtra(data=session_list, total=total, page=page, page_size=page_size)

    except Exception as e:
        logger.error(f"获取会话列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取会话列表失败: {str(e)}")


@router.delete("/session/delete", summary="删除会话")
async def delete_session(
        session_id: int = Query(..., description="会话ID"),
        current_user: User = DependAuth
):
    """删除指定的会话"""
    try:
        from ....controllers.session import session_controller

        deleted_count = await session_controller.delete_user_sessions(
            [session_id],
            current_user.id
        )

        if deleted_count > 0:
            return Success(msg="会话删除成功")
        else:
            raise HTTPException(status_code=404, detail="会话不存在或无权限删除")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除会话失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除会话失败: {str(e)}")


@router.post("/session/create", summary="创建新会话")
async def create_session(
        session_in: SessionCreate,
        current_user: User = DependAuth
):
    """创建新的聊天会话"""
    try:
        from ....controllers.session import session_controller
        from ....schemas.session import SessionCreate as SessionCreateSchema

        session_data = SessionCreateSchema(
            session_title=session_in.session_title,
            user_id=current_user.id,
            session_content=""
        )

        new_session = await session_controller.create_user_session(session_data)
        session_dict = await new_session.to_dict()

        return Success(data={
            "session_id": str(session_dict["id"]),
            "session_title": session_dict["session_title"],
            "user_id": session_dict["user_id"],
            "created_at": session_dict["created_at"]
        }, msg="会话创建成功")

    except Exception as e:
        logger.error(f"创建会话失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建会话失败: {str(e)}")


@router.get("/stats", summary="获取服务统计")
async def get_service_stats(
        current_user: User = DependAuth
):
    """获取多智能体聊天服务统计信息（管理员功能）"""
    try:
        # 检查是否为管理员
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="权限不足")

        from ....controllers.session import session_controller

        # 获取会话统计
        total_sessions, _ = await session_controller.get_user_sessions(
            user_id=None,  # 获取所有用户的会话
            page=1,
            page_size=1
        )

        # 获取消息统计
        total_messages = await chat_controller.get_total_message_count()

        stats_data = ServiceStats(
            total_sessions=total_sessions,
            total_messages=total_messages,
            agent_system="smart-chat-system",
            agents=["text_agent", "vision_agent"],
            features=["流式响应", "多模态识别", "智能选择"]
        )

        return Success(data=stats_data.model_dump())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取服务统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取服务统计失败: {str(e)}")


@router.post("/session/validate", summary="智能会话验证")
async def validate_or_create_session(
        validate_request: SessionValidateRequest,
        current_user: User = DependAuth
):
    """智能验证会话是否存在，如果不存在则自动创建新会话"""
    try:
        from ....controllers.session import session_controller
        from ....schemas.session import SessionCreate

        user_id = current_user.id
        session_id = validate_request.session_id

        # 如果没有提供session_id或session_id无效，创建新会话
        if not session_id or session_id.strip() in ["", "not_login", "undefined", "null"]:
            session_data = SessionCreate(
                session_title="新对话",
                user_id=user_id,
                session_content=""
            )
            new_session = await session_controller.create_user_session(session_data)
            session_dict = await new_session.to_dict()
            return Success(data={
                "session_id": session_dict["id"],
                "session_title": session_dict["session_title"],
                "created": True
            })

        # 验证现有会话
        try:
            session_id_int = int(session_id.strip())
            if session_id_int <= 0:
                raise ValueError("会话ID必须为正整数")
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="会话ID格式错误")

        # 检查会话是否存在且属于当前用户
        session = await session_controller.get_user_session(session_id_int, user_id)
        if session:
            session_dict = await session.to_dict()
            return Success(data={
                "session_id": session_dict["id"],
                "session_title": session_dict["session_title"],
                "created": False
            })
        else:
            raise HTTPException(status_code=404, detail="会话不存在或无权访问")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"验证会话失败: {e}")
        raise HTTPException(status_code=500, detail=f"验证会话失败: {str(e)}")


@router.get("/models/list", summary="获取可用模型列表")
async def get_available_models(
        page: int = Query(1, description="页码"),
        page_size: int = Query(50, description="每页数量"),
        model_type: str = Query("chat", description="模型类型")
):
    """获取可用的聊天模型列表"""
    try:
        total, models = await model_controller.get_active_models(
            model_type=model_type,
            page=page,
            page_size=page_size
        )

        model_list = []
        for model in models:
            model_dict = await model.to_dict()
            model_info = ChatModelInfo(
                id=model_dict["model_name"],
                name=model_dict["model_show"],
                description=model_dict["model_describe"],
                price=safe_serialize(model_dict["model_price"]),
                model_type=model_dict["model_type"]
            )
            model_list.append(model_info.model_dump())

        return SuccessExtra(data=model_list, total=total, page=page, page_size=page_size)

    except Exception as e:
        logger.error(f"获取模型列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取模型列表失败: {str(e)}")


@router.get("/memory/stats", summary="获取记忆统计信息")
async def get_memory_stats(
        current_user: User = DependAuth
):
    """获取当前用户的记忆统计信息"""
    try:
        memory_adapter = await smart_chat_system.get_memory_adapter(current_user.id)
        if not memory_adapter:
            return Success(data={
                "memory_enabled": False,
                "message": "记忆功能未启用"
            })

        # 获取记忆统计
        health_info = await memory_adapter.health_check()

        return Success(data={
            "memory_enabled": True,
            "user_id": current_user.id,
            "health_info": health_info
        })

    except Exception as e:
        logger.error(f"获取记忆统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取记忆统计失败: {str(e)}")


@router.post("/memory/query", summary="查询相关记忆")
async def query_memory(
        query: str = Query(..., description="查询内容"),
        limit: int = Query(5, description="返回数量限制"),
        current_user: User = DependAuth
):
    """查询用户的相关记忆"""
    try:
        memory_adapter = await smart_chat_system.get_memory_adapter(current_user.id)
        if not memory_adapter:
            return Success(data=[], msg="记忆功能未启用")

        # 查询相关记忆
        memories = await memory_adapter.query(query, limit)

        # 转换为可序列化的格式
        memory_data = []
        for memory in memories:
            memory_info = {
                "content": memory.content,
                "metadata": memory.metadata,
                "relevance_score": memory.metadata.get("relevance_score", 0)
            }
            memory_data.append(memory_info)

        return Success(data=memory_data, msg=f"找到 {len(memory_data)} 条相关记忆")

    except Exception as e:
        logger.error(f"查询记忆失败: {e}")
        raise HTTPException(status_code=500, detail=f"查询记忆失败: {str(e)}")


@router.delete("/memory/clear", summary="清空用户记忆")
async def clear_user_memory(
        memory_type: str = Query("private", description="记忆类型: private, chat, all"),
        current_user: User = DependAuth
):
    """清空用户的记忆数据"""
    try:
        # 检查是否为管理员或用户本人
        if not current_user.is_superuser:
            # 普通用户只能清空自己的私有记忆
            if memory_type not in ["private"]:
                raise HTTPException(status_code=403, detail="权限不足，只能清空私有记忆")

        memory_adapter = await smart_chat_system.get_memory_adapter(current_user.id)
        if not memory_adapter:
            return Success(msg="记忆功能未启用")

        if memory_type == "all":
            # 清空所有记忆（仅管理员）
            await memory_adapter.clear()
            return Success(msg="已清空所有记忆")
        elif memory_type == "private":
            # 清空私有记忆
            await memory_adapter.private_memory.clear()
            return Success(msg="已清空私有记忆")
        elif memory_type == "chat":
            # 清空聊天记忆
            await memory_adapter.chat_memory.clear()
            return Success(msg="已清空聊天记忆")
        else:
            raise HTTPException(status_code=400, detail="无效的记忆类型")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"清空记忆失败: {e}")
        raise HTTPException(status_code=500, detail=f"清空记忆失败: {str(e)}")


@router.get("/health", summary="健康检查")
async def health_check():
    """智能聊天服务健康检查"""
    try:
        # 检查智能聊天系统状态
        agent_status = {
            "text_agent": smart_chat_system.text_agent is not None,
            "vision_agent": smart_chat_system.vision_agent is not None,
            "initialized": smart_chat_system.initialized,
            "memory_enabled": smart_chat_system.memory_enabled
        }

        all_agents_ready = smart_chat_system.initialized and all([
            smart_chat_system.text_agent is not None,
            smart_chat_system.vision_agent is not None
        ])

        features = ["流式响应", "多模态识别", "智能选择", "图片分析"]
        if smart_chat_system.memory_enabled:
            features.extend(["对话记忆", "用户偏好", "知识库检索"])

        health_status = HealthStatus(
            status="healthy" if all_agents_ready else "initializing",
            agent_system="Smart Chat System with Memory",
            agents_status=agent_status,
            features=features,
            service_uptime="正常运行"
        )

        return Success(data=health_status.model_dump())

    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise HTTPException(status_code=500, detail=f"服务异常: {str(e)}")
