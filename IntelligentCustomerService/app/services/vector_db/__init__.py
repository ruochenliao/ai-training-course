"""
基于ChromaDB的向量数据库管理系统
提供完整的文档操作、集合管理和元数据处理功能

核心组件：
- ChromaVectorDBManager: ChromaDB向量数据库管理器
- DocumentOperationService: 文档操作服务
- CollectionNamingStrategy: 集合命名策略管理
- MetadataManager: 元数据管理器

支持功能：
- 本地和远程ChromaDB连接
- BAAI/bge-small-zh-v1.5中文嵌入模型
- 智能文档分块和向量化
- 高效的相似度搜索和元数据过滤
- 批量文档操作和集合管理
- 完整的错误处理和日志记录
"""

# 导入核心管理器类
from .chroma_manager import (
    ChromaVectorDBManager,
    ChromaConfig,
    ConnectionType,
    CollectionType,
    DocumentMetadata,
    SearchResult,
    CollectionNamingStrategy,
    MetadataManager
)

# 导入文档操作服务
from .document_service import (
    DocumentOperationService,
    DocumentInfo,
    SearchQuery
)

# 导出所有公共接口
__all__ = [
    # 核心管理器
    'ChromaVectorDBManager',
    'ChromaConfig',
    'ConnectionType',
    'CollectionType',
    'DocumentMetadata',
    'SearchResult',
    'CollectionNamingStrategy',
    'MetadataManager',
    
    # 文档操作服务
    'DocumentOperationService',
    'DocumentInfo',
    'SearchQuery'
]

# 版本信息
__version__ = "1.0.0"
__author__ = "Intelligent Customer Service Team"
__description__ = "基于ChromaDB的向量数据库管理系统"

# 便捷函数
def create_default_config(
    connection_type: ConnectionType = ConnectionType.LOCAL,
    persist_directory: str = None,
    embedding_model: str = "BAAI/bge-small-zh-v1.5"
) -> ChromaConfig:
    """
    创建默认配置
    
    Args:
        connection_type: 连接类型
        persist_directory: 持久化目录
        embedding_model: 嵌入模型名称
        
    Returns:
        ChromaDB配置对象
    """
    config = ChromaConfig(
        connection_type=connection_type,
        embedding_model_name=embedding_model
    )
    
    if persist_directory:
        config.persist_directory = persist_directory
    
    return config


def create_remote_config(
    host: str,
    port: int,
    ssl: bool = False,
    headers: dict = None,
    embedding_model: str = "BAAI/bge-small-zh-v1.5"
) -> ChromaConfig:
    """
    创建远程连接配置
    
    Args:
        host: 服务器地址
        port: 端口号
        ssl: 是否使用SSL
        headers: 请求头
        embedding_model: 嵌入模型名称
        
    Returns:
        ChromaDB配置对象
    """
    return ChromaConfig(
        connection_type=ConnectionType.REMOTE,
        host=host,
        port=port,
        ssl=ssl,
        headers=headers or {},
        embedding_model_name=embedding_model
    )


async def create_document_service(config: ChromaConfig = None) -> DocumentOperationService:
    """
    创建并初始化文档操作服务
    
    Args:
        config: ChromaDB配置
        
    Returns:
        已初始化的文档操作服务
    """
    service = DocumentOperationService(config)
    await service.initialize()
    return service


# 示例用法
"""
# 基本用法示例

# 1. 创建本地服务
from app.services.vector_db import create_document_service, create_default_config

config = create_default_config()
service = await create_document_service(config)

# 2. 添加文档
from app.services.vector_db import DocumentInfo, CollectionType

document = DocumentInfo(
    file_id="doc_001",
    file_name="example.txt",
    file_type="text",
    file_size=1024,
    content="这是一个示例文档内容...",
    knowledge_base_id="kb_001",
    knowledge_type="general",
    is_public=False,
    owner_id="user_001"
)

success, chunk_ids = await service.add_document(document, CollectionType.PRIVATE)

# 3. 搜索文档
from app.services.vector_db import SearchQuery

query = SearchQuery(
    query_text="示例文档",
    knowledge_type="general",
    n_results=5
)

results = await service.search_documents(query, user_id="user_001")

# 4. 删除文档
success = await service.delete_document(
    "doc_001", "general", CollectionType.PRIVATE, "user_001"
)

# 5. 批量操作
documents = [document1, document2, document3]
batch_result = await service.batch_add_documents(documents)

# 6. 健康检查
health = await service.health_check()

# 7. 关闭服务
await service.close()
"""

# 配置示例
"""
# 配置示例

# 本地配置
local_config = ChromaConfig(
    connection_type=ConnectionType.LOCAL,
    persist_directory="/path/to/chroma/data",
    embedding_model_name="BAAI/bge-small-zh-v1.5",
    embedding_dimension=512,
    batch_size=100,
    max_workers=4
)

# 远程配置
remote_config = ChromaConfig(
    connection_type=ConnectionType.REMOTE,
    host="localhost",
    port=8000,
    ssl=False,
    headers={"Authorization": "Bearer token"},
    embedding_model_name="BAAI/bge-small-zh-v1.5",
    embedding_dimension=512
)
"""

# 集合命名示例
"""
# 集合命名示例

from app.services.vector_db import CollectionNamingStrategy, CollectionType

# 公共集合: general_public_memory
public_name = CollectionNamingStrategy.get_collection_name(
    "general", CollectionType.PUBLIC
)

# 私有集合: general_user001
private_name = CollectionNamingStrategy.get_collection_name(
    "general", CollectionType.PRIVATE, "user001"
)

# 验证集合名称
is_valid = CollectionNamingStrategy.validate_collection_name(public_name)
"""

# 元数据管理示例
"""
# 元数据管理示例

from app.services.vector_db import MetadataManager

# 创建块级元数据
metadata = MetadataManager.create_chunk_metadata(
    file_id="doc_001",
    knowledge_base_id="kb_001",
    file_type="text",
    file_name="example.txt",
    file_size=1024,
    file_hash="abc123",
    chunk_content="文档内容块",
    chunk_index=0,
    total_chunks=5,
    is_public=False,
    owner_id="user_001",
    knowledge_type="general"
)

# 构建搜索过滤条件
filters = MetadataManager.build_search_filter(
    knowledge_base_id="kb_001",
    file_type="text",
    is_public=False
)
"""
