"""
测试配置文件
"""

import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient
from tortoise import Tortoise
from tortoise.contrib.test import finalizer, initializer

from app.main import app
from app.core.config import settings
from app.models import User, Role, KnowledgeBase, Document
from app.services.auth import create_access_token


# 测试数据库配置
TEST_DB_URL = "sqlite://:memory:"

# 配置测试数据库
TORTOISE_TEST_CONFIG = {
    "connections": {
        "default": TEST_DB_URL
    },
    "apps": {
        "models": {
            "models": ["app.models", "aerich.models"],
            "default_connection": "default",
        },
    },
}


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def init_db():
    """初始化测试数据库"""
    await initializer(
        TORTOISE_TEST_CONFIG,
        app_label="models",
        db_url=TEST_DB_URL
    )
    yield
    await finalizer()


@pytest_asyncio.fixture
async def client(init_db) -> AsyncGenerator[AsyncClient, None]:
    """创建测试客户端"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def test_user() -> User:
    """创建测试用户"""
    user = await User.create(
        username="testuser",
        email="test@example.com",
        password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6hsxq5/Qe2",
        full_name="Test User",
        is_active=True
    )
    return user


@pytest_asyncio.fixture
async def admin_user() -> User:
    """创建管理员用户"""
    user = await User.create(
        username="admin",
        email="admin@example.com",
        password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6hsxq5/Qe2",
        full_name="Admin User",
        is_superuser=True,
        is_active=True
    )
    return user


@pytest_asyncio.fixture
async def test_role() -> Role:
    """创建测试角色"""
    role = await Role.create(
        name="test_role",
        display_name="测试角色",
        description="用于测试的角色"
    )
    return role


@pytest_asyncio.fixture
async def test_knowledge_base(test_user: User) -> KnowledgeBase:
    """创建测试知识库"""
    kb = await KnowledgeBase.create(
        name="测试知识库",
        description="这是一个测试知识库",
        owner_id=test_user.id,
        is_public=True
    )
    return kb


@pytest_asyncio.fixture
async def test_document(test_knowledge_base: KnowledgeBase, test_user: User) -> Document:
    """创建测试文档"""
    doc = await Document.create(
        knowledge_base_id=test_knowledge_base.id,
        filename="test_document.txt",
        original_filename="test_document.txt",
        file_path="/tmp/test_document.txt",
        file_size=1024,
        file_type="txt",
        mime_type="text/plain",
        content="这是一个测试文档的内容。",
        uploaded_by=test_user.id,
        status="processed"
    )
    return doc


@pytest_asyncio.fixture
async def auth_headers(test_user: User) -> dict:
    """创建认证头"""
    token = create_access_token(data={"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def admin_auth_headers(admin_user: User) -> dict:
    """创建管理员认证头"""
    token = create_access_token(data={"sub": str(admin_user.id)})
    return {"Authorization": f"Bearer {token}"}


class TestDataFactory:
    """测试数据工厂"""
    
    @staticmethod
    async def create_user(
        username: str = "testuser",
        email: str = "test@example.com",
        **kwargs
    ) -> User:
        """创建用户"""
        defaults = {
            "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6hsxq5/Qe2",
            "full_name": "Test User",
            "is_active": True
        }
        defaults.update(kwargs)
        
        return await User.create(
            username=username,
            email=email,
            **defaults
        )
    
    @staticmethod
    async def create_knowledge_base(
        owner: User,
        name: str = "测试知识库",
        **kwargs
    ) -> KnowledgeBase:
        """创建知识库"""
        defaults = {
            "description": "这是一个测试知识库",
            "is_public": True
        }
        defaults.update(kwargs)
        
        return await KnowledgeBase.create(
            name=name,
            owner_id=owner.id,
            **defaults
        )
    
    @staticmethod
    async def create_document(
        knowledge_base: KnowledgeBase,
        uploader: User,
        filename: str = "test_document.txt",
        **kwargs
    ) -> Document:
        """创建文档"""
        defaults = {
            "original_filename": filename,
            "file_path": f"/tmp/{filename}",
            "file_size": 1024,
            "file_type": "txt",
            "mime_type": "text/plain",
            "content": "这是一个测试文档的内容。",
            "status": "processed"
        }
        defaults.update(kwargs)
        
        return await Document.create(
            knowledge_base_id=knowledge_base.id,
            filename=filename,
            uploaded_by=uploader.id,
            **defaults
        )


@pytest.fixture
def test_factory():
    """测试数据工厂实例"""
    return TestDataFactory


# 测试标记
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.e2e = pytest.mark.e2e
pytest.mark.slow = pytest.mark.slow


# 测试辅助函数
def assert_response_success(response, expected_status: int = 200):
    """断言响应成功"""
    assert response.status_code == expected_status
    assert response.json().get("success", True) is True


def assert_response_error(response, expected_status: int = 400):
    """断言响应错误"""
    assert response.status_code == expected_status
    data = response.json()
    assert "error" in data or "detail" in data


def assert_pagination_response(response, expected_status: int = 200):
    """断言分页响应"""
    assert_response_success(response, expected_status)
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "size" in data
    assert isinstance(data["items"], list)
    assert isinstance(data["total"], int)
    assert isinstance(data["page"], int)
    assert isinstance(data["size"], int)


# 模拟数据
MOCK_EMBEDDING = [0.1] * 1536  # 模拟1536维向量

MOCK_LLM_RESPONSE = {
    "choices": [
        {
            "message": {
                "content": "这是一个模拟的LLM响应。",
                "role": "assistant"
            },
            "finish_reason": "stop"
        }
    ],
    "usage": {
        "prompt_tokens": 10,
        "completion_tokens": 20,
        "total_tokens": 30
    }
}

MOCK_SEARCH_RESULTS = [
    {
        "id": "1",
        "content": "这是第一个搜索结果。",
        "score": 0.95,
        "metadata": {
            "document_id": 1,
            "chunk_index": 0
        }
    },
    {
        "id": "2", 
        "content": "这是第二个搜索结果。",
        "score": 0.87,
        "metadata": {
            "document_id": 1,
            "chunk_index": 1
        }
    }
]


# 测试配置
class TestConfig:
    """测试配置类"""
    
    # API测试配置
    API_TIMEOUT = 30
    MAX_RETRIES = 3
    
    # 文件测试配置
    TEST_FILE_SIZE = 1024
    TEST_UPLOAD_DIR = "/tmp/test_uploads"
    
    # 模拟服务配置
    MOCK_LLM_ENABLED = True
    MOCK_EMBEDDING_ENABLED = True
    MOCK_VECTOR_DB_ENABLED = True
    
    # 性能测试配置
    PERFORMANCE_TEST_ITERATIONS = 100
    PERFORMANCE_TEST_TIMEOUT = 60


@pytest.fixture
def test_config():
    """测试配置实例"""
    return TestConfig
