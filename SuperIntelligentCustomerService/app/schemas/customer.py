from typing import List, Optional, Dict, Union, Literal

import requests
from pydantic import BaseModel


class ImageContent(BaseModel):
    """图片内容模型"""
    url: str  # 图片URL
    file_name: Optional[str] = None  # 原始文件名


class AGImage(BaseModel):
    """模拟AutoGen的Image类"""
    data: bytes  # 图片数据
    type: str = "image"  # 类型

    @classmethod
    def from_url(cls, url: str) -> 'AGImage':
        """从图片URL创建图片对象"""
        try:
            response = requests.get(url)
            response.raise_for_status()
            image_data = response.content
            return cls(data=image_data)
        except Exception as e:
            raise ValueError(f"无法从 URL 加载图片: {e}")


class MultiModalMessage(BaseModel):
    """模拟AutoGen的MultiModalMessage类"""
    content: List[Union[str, AGImage]]  # 多模态内容列表
    source: str  # 消息来源
    type: str = "MultiModalMessage"  # 消息类型
    task: Optional[str] = None  # 任务类型

    def to_text(self) -> str:
        """将多模态消息转换为文本表示"""
        result = ""

        # 添加任务类型
        if self.task:
            result += f"[任务类型: {self.task}]\n"

        # 处理内容列表
        for i, item in enumerate(self.content):
            if isinstance(item, str):
                result += f"{item}\n"
            elif item.type == "image":
                result += f"[图片 {i+1}]\n"

        return result


class MultiModalContent(BaseModel):
    """多模态内容模型，参考AutoGen的MultiModalMessage"""
    text: Optional[str] = None  # 文本内容
    image: Optional[ImageContent] = None  # 图片内容


class MessageContent(BaseModel):
    """消息内容模型"""
    type: Literal["text", "multi-modal"] = "text"  # 消息类型：文本或多模态
    text: Optional[str] = None  # 文本内容
    content: Optional[List[MultiModalContent]] = None  # 多模态内容列表
    task: Optional[str] = None  # 任务类型，参考AutoGen多模态消息格式


class ChatMessage(BaseModel):
    """单条聊天消息模型"""
    role: str  # 'user' 或 'assistant'
    content: Union[str, MessageContent]  # 消息内容，可以是字符串或MessageContent对象

    def get_content_text(self) -> str:
        """获取消息的文本内容"""
        # 先处理复杂类型，再处理简单类型，避免简单类型判断先执行
        if isinstance(self.content, MessageContent):
            if self.content.type == "text":
                return self.content.text or ""
            elif self.content.type == "multi-modal":
                # 构建多模态消息的文本表示
                result = ""

                # 如果有任务类型，添加到消息中
                if self.content.task:
                    result += f"[任务类型: {self.content.task}]\n"

                # 添加主文本内容
                if self.content.text:
                    result += f"{self.content.text}\n\n"

                # 处理多模态内容列表
                if self.content.content:
                    for i, item in enumerate(self.content.content):
                        # 处理图片内容
                        if item.image:
                            image_desc = f"[图片 {i+1}: {item.image.file_name if item.image.file_name else '未命名图片'}]"
                            if item.image.url:
                                image_desc += f" {item.image.url}"
                            result += image_desc + "\n"

                        # 处理文本内容
                        if item.text:
                            result += f"[文本 {i+1}]: {item.text}\n"

                return result
        # 如果是字符串类型
        elif isinstance(self.content, str):
            return self.content

        # 其他情况
        return ""


class ChatRequest(BaseModel):
    """聊天请求模型"""
    messages: List[ChatMessage]  # 当前请求的消息，只用于当前请求，不会存储
    model: Optional[str] = None
    system_prompt: Optional[str] = None
    user_id: Optional[str] = "default"  # 用户ID，用于维护用户的记忆体
    session_id: Optional[str] = None  # 会话ID，如果提供则使用指定会话，否则创建新会话


class ChatResponse(BaseModel):
    """聊天响应模型"""
    content: str
    role: str = "assistant"


class MemoryAddRequest(BaseModel):
    """添加记忆请求模型"""
    user_id: str
    task: str
    insight: str


class MemoryRetrieveRequest(BaseModel):
    """检索记忆请求模型"""
    user_id: str
    task: str


class SessionRequest(BaseModel):
    """会话请求模型"""
    user_id: str
    session_id: Optional[str] = None


class SessionResponse(BaseModel):
    """会话响应模型"""
    session_id: str
    user_id: str
    created_at: str
    last_active: str
    messages: List[Dict[str, Union[str, dict]]]
