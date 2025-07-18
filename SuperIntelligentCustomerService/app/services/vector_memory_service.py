import os
import tempfile
import shutil
from typing import List, Dict, Optional, Union, Any

from autogen_core.memory import MemoryContent, MemoryMimeType
from autogen_ext.memory.chromadb import ChromaDBVectorMemory, PersistentChromaDBVectorMemoryConfig, \
    HttpChromaDBVectorMemoryConfig
from fastapi import UploadFile

from app.schemas.customer import ChatMessage
from app.settings.config import settings
from .memory_service import MemoryService, KnowledgeType


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
        
        # 根据配置选择使用本地或HTTP连接
        if hasattr(settings, 'CHROMA_DB_HOST') and hasattr(settings, 'CHROMA_DB_PORT'):
            self.memory = self._get_memory_http()
        else:
            self.memory = self._get_memory()
            
        self.logger.info(f"初始化向量记忆服务，集合名称: {collection_name}，知识库类型: {self.knowledge_type}")

        # 支持的文件类型
        self.supported_file_types = [".pdf", ".docx", ".txt"]

    def _get_memory(self) -> ChromaDBVectorMemory:
        """获取或创建本地向量记忆实例"""
        config = PersistentChromaDBVectorMemoryConfig(
            collection_name=self.collection_name,
            persistence_path=self.vector_dir,
            k=5,  # 返回最相关的5条记录
            score_threshold=0.4  # 最小相似度阈值
        )
        return ChromaDBVectorMemory(config=config)

    def _get_memory_http(self) -> ChromaDBVectorMemory:
        """获取或创建HTTP向量记忆实例"""
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
            try:
                from pypdf import PdfReader
                text = ""
                with open(file_path, 'rb') as f:
                    pdf = PdfReader(f)
                    for page in pdf.pages:
                        text += page.extract_text() + "\n\n"
                return text
            except ImportError:
                raise ImportError("需要安装pypdf库来处理PDF文件: pip install pypdf")

        elif file_ext == '.docx':
            try:
                import docx2txt
                return docx2txt.process(file_path)
            except ImportError:
                raise ImportError("需要安装docx2txt库来处理DOCX文件: pip install docx2txt")

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
        collection_name = f"{knowledge_type or KnowledgeType.CUSTOMER_SERVICE}_{user_id}"
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
        super().__init__(f"{knowledge_type or KnowledgeType.CUSTOMER_SERVICE}_public_memory", base_dir, knowledge_type)
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
