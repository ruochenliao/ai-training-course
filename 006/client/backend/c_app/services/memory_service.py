import asyncio
import os
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Optional, AsyncGenerator, Union, BinaryIO, Any, Type, TypeVar, Generic, Protocol, runtime_checkable
import json
import logging
from datetime import datetime
import uuid
from abc import ABC, abstractmethod

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.base import TaskResult
from autogen_agentchat.messages import ModelClientStreamingChunkEvent
from autogen_core import CancellationToken
from autogen_core.memory import ListMemory, MemoryContent, MemoryMimeType
from autogen_core.memory._list_memory import ListMemoryConfig
from autogen_ext.memory.chromadb import ChromaDBVectorMemory, PersistentChromaDBVectorMemoryConfig, \
    HttpChromaDBVectorMemoryConfig
from fastapi import UploadFile
from typing_extensions import Self

from c_app.schemas.customer import ChatMessage
from c_app.core.config import settings

class KnowledgeType:
    """知识库类型常量"""
    CUSTOMER_SERVICE = "customer_service"  # 智能客服知识库
    TEXT_SQL = "text_sql"  # TextSQL知识库
    RAG = "rag"  # RAG知识库
    CONTENT_CREATION = "content_creation"  # 文案创作知识库

class PersistentListMemoryConfig(ListMemoryConfig):
    """Configuration for PersistentListMemory component."""

    storage_dir: str = str(Path.home() / ".autogen_memory")
    """Directory to store memory files"""
    auto_save: bool = True
    """Whether to automatically save memory after each modification"""


class PersistentListMemory(ListMemory):
    """ListMemory implementation with disk persistence support."""

    component_type = "memory"
    component_provider_override = "c_app.services.memory_service.PersistentListMemory"
    component_config_schema = PersistentListMemoryConfig

    def __init__(
            self,
            name: str | None = None,
            memory_contents: List[MemoryContent] | None = None,
            storage_dir: str | None = None,
            auto_save: bool = False
    ) -> None:
        super().__init__(name, memory_contents)
        self.storage_dir = storage_dir or str(Path.home() / ".autogen_memory")
        self.auto_save = auto_save
        self._file_path = Path(self.storage_dir) / f"{self.name}.json"

        # 确保存储目录存在
        os.makedirs(self.storage_dir, exist_ok=True)

        # 如果存在保存的数据，则加载它
        self._load_from_disk()

    def _load_from_disk(self) -> None:
        """从磁盘加载记忆内容"""
        if self._file_path.exists():
            try:
                with open(self._file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    config = ListMemoryConfig.model_validate(data)
                    self._contents = config.memory_contents
            except Exception as e:
                print(f"Failed to load memory from {self._file_path}: {e}")

    async def save_to_disk(self) -> None:
        """将记忆内容保存到磁盘"""
        try:
            config = self._to_config()
            with open(self._file_path, 'w', encoding='utf-8') as f:
                json.dump(config.model_dump(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Failed to save memory to {self._file_path}: {e}")

    @property
    def content(self) -> List[MemoryContent]:
        """获取当前内存内容"""
        return self._contents

    @content.setter
    def content(self, value: List[MemoryContent]) -> None:
        """设置内存内容并自动保存"""
        self._contents = value
        if self.auto_save:
            asyncio.create_task(self.save_to_disk())

    async def add(self, content, cancellation_token: CancellationToken | None = None) -> None:
        """添加新内容并自动保存"""
        await super().add(content, cancellation_token)
        if self.auto_save:
            await self.save_to_disk()

    async def clear(self) -> None:
        """清除所有内容并自动保存"""
        await super().clear()
        if self.auto_save:
            await self.save_to_disk()

    async def close(self) -> None:
        """关闭前保存数据"""
        await self.save_to_disk()
        await super().close()

    @classmethod
    def _from_config(cls, config: PersistentListMemoryConfig) -> Self:
        return cls(
            name=config.name,
            memory_contents=config.memory_contents,
            storage_dir=config.storage_dir,
            auto_save=config.auto_save
        )

    def _to_config(self) -> PersistentListMemoryConfig:
        return PersistentListMemoryConfig(
            name=self.name,
            memory_contents=self._contents,
            storage_dir=self.storage_dir,
            auto_save=self.auto_save
        )


class MemoryService(ABC):
    """抽象基类，定义所有记忆服务的通用接口和功能"""

    def __init__(self, base_dir: Optional[str] = None):
        """初始化记忆服务

        Args:
            base_dir: 基础存储目录，如果为None则使用默认目录
        """
        self.logger = logging.getLogger(self.__class__.__name__)

        # 确定基础目录
        if base_dir is None:
            # 获取项目根目录
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            self.base_dir = os.path.join(project_root, "data", "memories")
        else:
            self.base_dir = base_dir

        # 确保存储目录存在
        os.makedirs(self.base_dir, exist_ok=True)
        self.logger.info(f"初始化记忆服务，存储目录: {self.base_dir}")

    @abstractmethod
    async def add(self, content: Any, metadata: Optional[Dict[str, Any]] = None) -> None:
        """添加内容到记忆服务

        Args:
            content: 要添加的内容
            metadata: 内容相关的元数据
        """
        pass

    @abstractmethod
    async def query(self, query: str, **kwargs) -> List[Dict]:
        """查询记忆服务

        Args:
            query: 查询字符串
            **kwargs: 额外的查询参数

        Returns:
            查询结果列表
        """
        pass

    @abstractmethod
    async def clear(self) -> None:
        """清除所有记忆内容"""
        pass

    @abstractmethod
    async def close(self) -> None:
        """关闭记忆服务，释放资源"""
        pass

    def _get_timestamp(self) -> str:
        """获取当前时间戳字符串"""
        return datetime.now().isoformat()

    def _create_base_metadata(self, custom_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """创建基础元数据

        Args:
            custom_metadata: 自定义元数据

        Returns:
            合并后的元数据字典
        """
        base_metadata = {
            "timestamp": self._get_timestamp(),
            "service": self.__class__.__name__
        }

        if custom_metadata:
            base_metadata.update(custom_metadata)

        return base_metadata


class ChatMemoryService(MemoryService):
    """聊天历史记忆服务，使用PersistentListMemory存储聊天历史"""

    def __init__(self, user_id: str, base_dir: Optional[str] = None):
        """初始化聊天历史记忆服务

        Args:
            user_id: 用户ID
            base_dir: 基础存储目录，如果为None则使用默认目录
        """
        super().__init__(base_dir)
        self.user_id = user_id
        self.memory = PersistentListMemory(
            name=f"chat_memory_{user_id}",
            storage_dir=self.base_dir,
            auto_save=True
        )
        self.logger.info(f"初始化聊天历史记忆服务，用户ID: {user_id}")

    async def add(self, content: Union[ChatMessage, str], metadata: Optional[Dict[str, Any]] = None) -> None:
        """添加聊天消息或文本到记忆服务

        Args:
            content: 聊天消息对象或文本字符串
            metadata: 额外的元数据
        """
        base_metadata = self._create_base_metadata(metadata)

        if isinstance(content, ChatMessage):
            # 如果是ChatMessage对象
            message_content = f"{content.role}: {content.content}"
            base_metadata["role"] = content.role
            base_metadata["type"] = "message"
        else:
            # 如果是字符串
            message_content = content
            base_metadata["type"] = "text"

        # 添加到记忆
        await self.memory.add(
            MemoryContent(
                content=message_content,
                mime_type=MemoryMimeType.TEXT,
                metadata=base_metadata
            )
        )

    async def query(self, query: str, **kwargs) -> List[Dict]:
        """查询聊天历史

        Args:
            query: 查询字符串，在聊天历史中查找匹配的内容
            **kwargs: 额外的查询参数

        Returns:
            匹配的聊天历史列表
        """
        # 由于PersistentListMemory不支持语义查询，这里简单实现一个基于关键词的查询
        results = []
        for item in self.memory.content:
            if query.lower() in item.content.lower():
                results.append({
                    "content": item.content,
                    "metadata": item.metadata,
                    "source": "chat_history"
                })

        # 应用可选的限制
        limit = kwargs.get("limit", None)
        if limit is not None:
            results = results[:limit]

        return results

    async def get_all_messages(self) -> List[Dict]:
        """获取所有聊天消息

        Returns:
            所有聊天消息的列表
        """
        return [
            {
                "content": item.content,
                "metadata": item.metadata,
                "timestamp": item.metadata.get("timestamp", "")
            }
            for item in self.memory.content
        ]

    async def clear(self) -> None:
        """清除所有聊天历史"""
        await self.memory.clear()
        self.logger.info(f"已清除用户 {self.user_id} 的聊天历史")

    async def close(self) -> None:
        """关闭聊天历史记忆服务"""
        await self.memory.close()
        self.logger.info(f"已关闭用户 {self.user_id} 的聊天历史记忆服务")


class VectorMemoryService(MemoryService):
    """基于向量数据库的记忆服务基类"""

    def __init__(self, collection_name: str, base_dir: Optional[str] = None, knowledge_type: Optional[str] = None):
        """初始化向量记忆服务

        Args:
            collection_name: 集合名称
            base_dir: 基础存储目录，如果为None则使用默认目录
            knowledge_type: 知识库类型，如果为None则使用默认类型
        """
        super().__init__(base_dir)

        # 确保向量数据库目录存在
        self.vector_dir = os.path.join(self.base_dir, "vector_db")
        os.makedirs(self.vector_dir, exist_ok=True)

        self.collection_name = collection_name
        self.knowledge_type = knowledge_type or KnowledgeType.CUSTOMER_SERVICE
        # self.memory = self._get_memory()
        self.memory = self._get_memory_http()
        self.logger.info(f"初始化向量记忆服务，集合名称: {collection_name}，知识库类型: {self.knowledge_type}")

        # 支持的文件类型
        self.supported_file_types = [".pdf", ".docx", ".txt"]


    def _get_memory(self) -> ChromaDBVectorMemory:
        """获取或创建向量记忆实例"""
        config = PersistentChromaDBVectorMemoryConfig(
            collection_name=self.collection_name,
            persistence_path=self.vector_dir,
            k=5,  # 返回最相关的5条记录
            score_threshold=0.4  # 最小相似度阈值
        )
        return ChromaDBVectorMemory(config=config)

    def _get_memory_http(self) -> ChromaDBVectorMemory:
        """获取或创建向量记忆实例"""

        config = HttpChromaDBVectorMemoryConfig(
            host=settings.CHROMA_DB_HOST,
            port=settings.CHROMA_DB_PORT,
            collection_name=self.collection_name,
            k=5,  # 返回最相关的5条记录
            score_threshold=0.4  # 最小相似度阈值
        )
        return ChromaDBVectorMemory(config=config)

    async def add(self, content: Union[str, ChatMessage], metadata: Optional[Dict[str, Any]] = None) -> None:
        """添加内容到向量记忆

        Args:
            content: 文本内容或ChatMessage对象
            metadata: 额外的元数据
        """
        base_metadata = self._create_base_metadata(metadata)

        if isinstance(content, ChatMessage):
            # 如果是ChatMessage对象
            text_content = f"{content.role}: {content.content}"
            base_metadata["role"] = content.role
            base_metadata["type"] = "message"
        else:
            # 如果是字符串
            text_content = content
            base_metadata["type"] = "text"

        await self.memory.add(
            MemoryContent(
                content=text_content,
                mime_type=MemoryMimeType.TEXT,
                metadata=base_metadata
            )
        )

    async def query(self, query: str, **kwargs) -> List[Dict]:
        """查询向量记忆

        Args:
            query: 查询字符串
            **kwargs: 额外的查询参数

        Returns:
            查询结果列表
        """
        results = []

        # 执行向量查询
        query_results = await self.memory.query(query)

        for result in query_results.results:
            result_dict = {
                "content": result.content,
                "metadata": result.metadata,
                "source": self.collection_name
            }
            results.append(result_dict)

        return results

    async def clear(self) -> None:
        """清除所有向量记忆内容"""
        await self.memory.clear()
        self.logger.info(f"已清除集合 {self.collection_name} 的所有内容")

    async def close(self) -> None:
        """关闭向量记忆服务"""
        await self.memory.close()
        self.logger.info(f"已关闭集合 {self.collection_name} 的向量记忆服务")


    async def add_file(self, file: UploadFile) -> Dict[str, Any]:
        """从上传的文件中提取文本并添加到记忆体

        Args:
            file: 上传的文件

        Returns:
            文件处理结果信息
        """
        # 检查文件类型
        filename = file.filename or ""
        file_ext = os.path.splitext(filename)[1].lower()

        if file_ext not in self.supported_file_types:
            raise ValueError(f"不支持的文件类型: {file_ext}，仅支持 {', '.join(self.supported_file_types)}")

        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            # 保存上传的文件内容
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name

        try:
            # 提取文本内容
            content = self._extract_text_from_file(tmp_path, file_ext)

            # 准备元数据
            metadata = {
                "filename": filename,
                "file_type": file_ext,
                "type": "file"
            }

            # 添加到记忆体
            await self.add(content, metadata)

            return {
                "filename": filename,
                "size": len(content),
                "content_preview": content[:200] + "..." if len(content) > 200 else content,
                "added_to": self.collection_name
            }
        finally:
            # 删除临时文件
            os.unlink(tmp_path)

    def _extract_text_from_file(self, file_path: str, file_ext: str) -> str:
        """从文件中提取文本

        Args:
            file_path: 文件路径
            file_ext: 文件扩展名

        Returns:
            提取的文本内容
        """
        if file_ext == '.pdf':
            from pypdf import PdfReader
            text = ""
            with open(file_path, 'rb') as f:
                pdf = PdfReader(f)
                for page in pdf.pages:
                    text += page.extract_text() + "\n\n"
            return text

        elif file_ext == '.docx':
            import docx2txt
            return docx2txt.process(file_path)

        elif file_ext == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()

        else:
            raise ValueError(f"不支持的文件类型: {file_ext}")


class PrivateMemoryService(VectorMemoryService):
    """用户私有记忆服务，存储用户特定的私有数据"""

    def __init__(self, user_id: str, base_dir: Optional[str] = None, knowledge_type: Optional[str] = None):
        """初始化用户私有记忆服务

        Args:
            user_id: 用户ID
            base_dir: 基础存储目录，如果为None则使用默认目录
            knowledge_type: 知识库类型，如果为None则使用默认类型
        """
        collection_name = f"{knowledge_type}_{user_id}"
        super().__init__(collection_name, base_dir, knowledge_type)
        self.user_id = user_id
        self.logger.info(f"初始化用户私有记忆服务，用户ID: {user_id}，知识库类型: {self.knowledge_type}")

    async def add(self, content: Union[str, ChatMessage], metadata: Optional[Dict[str, Any]] = None) -> None:
        """添加内容到用户私有记忆

        Args:
            content: 文本内容或ChatMessage对象
            metadata: 额外的元数据
        """
        # 确保元数据中包含用户ID
        if metadata is None:
            metadata = {}
        metadata["user_id"] = self.user_id
        metadata["private"] = True

        await super().add(content, metadata)


class PublicMemoryService(VectorMemoryService):
    """公共记忆服务，存储所有用户共享的公共数据"""

    def __init__(self, base_dir: Optional[str] = None, knowledge_type: Optional[str] = None):
        """初始化公共记忆服务

        Args:
            base_dir: 基础存储目录，如果为None则使用默认目录
            knowledge_type: 知识库类型，如果为None则使用默认类型
        """
        super().__init__(f"{knowledge_type}_public_memory", base_dir, knowledge_type)
        self.logger.info(f"初始化公共记忆服务，知识库类型: {self.knowledge_type}")

    async def add(self, content: Union[str, ChatMessage], metadata: Optional[Dict[str, Any]] = None) -> None:
        """添加内容到公共记忆

        Args:
            content: 文本内容或ChatMessage对象
            metadata: 额外的元数据
        """
        # 确保元数据中标记为公共
        if metadata is None:
            metadata = {}
        metadata["public"] = True

        await super().add(content, metadata)

class MemoryServiceFactory:
    """记忆服务工厂类，用于创建和管理不同类型的记忆服务"""

    def __init__(self, base_dir: Optional[str] = None):
        """初始化记忆服务工厂

        Args:
            base_dir: 基础存储目录，如果为None则使用默认目录
        """
        self.base_dir = base_dir
        self.logger = logging.getLogger(self.__class__.__name__)
        self._chat_services: Dict[str, ChatMemoryService] = {}
        self._private_services: Dict[str, Dict[str, PrivateMemoryService]] = {}
        self._public_services: Dict[str, PublicMemoryService] = {}

    def get_chat_memory_service(self, user_id: str) -> ChatMemoryService:
        """获取指定用户的聊天历史记忆服务

        Args:
            user_id: 用户ID

        Returns:
            聊天历史记忆服务实例
        """
        if user_id not in self._chat_services:
            self._chat_services[user_id] = ChatMemoryService(user_id, self.base_dir)
        return self._chat_services[user_id]

    def get_private_memory_service(self, user_id: str, knowledge_type: str = KnowledgeType.CUSTOMER_SERVICE) -> PrivateMemoryService:
        """获取指定用户的私有记忆服务

        Args:
            user_id: 用户ID
            knowledge_type: 知识库类型

        Returns:
            私有记忆服务实例
        """
        # 初始化用户的私有服务字典
        if user_id not in self._private_services:
            self._private_services[user_id] = {}

        # 获取或创建指定类型的私有服务
        if knowledge_type not in self._private_services[user_id]:
            self._private_services[user_id][knowledge_type] = PrivateMemoryService(
                user_id,
                self.base_dir,
                knowledge_type
            )

        return self._private_services[user_id][knowledge_type]

    def get_public_memory_service(self, knowledge_type: str = KnowledgeType.CUSTOMER_SERVICE) -> PublicMemoryService:
        """获取公共记忆服务

        Args:
            knowledge_type: 知识库类型

        Returns:
            公共记忆服务实例
        """
        if knowledge_type not in self._public_services:
            self._public_services[knowledge_type] = PublicMemoryService(
                self.base_dir,
                knowledge_type
            )

        return self._public_services[knowledge_type]

    async def close_all(self) -> None:
        """关闭所有记忆服务"""
        # 关闭聊天历史记忆服务
        for service in self._chat_services.values():
            await service.close()

        # 关闭私有记忆服务
        for user_services in self._private_services.values():
            for service in user_services.values():
                await service.close()

        # 关闭公共记忆服务
        for service in self._public_services.values():
            await service.close()

        self.logger.info("已关闭所有记忆服务")