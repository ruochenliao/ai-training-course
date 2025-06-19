# 知识库功能说明文档

## 📚 概述

本项目基于现有的 `model_downloader.py` 文件实现了完整的个人知识库和公共知识库功能，使用 ChromaDB 向量数据库作为存储后端，集成了 Qwen3-0.6B 嵌入模型和 Qwen3-Reranker-0.6B 重排模型，提供高质量的语义搜索和检索能力。

## 🏗️ 架构设计

### 核心组件

1. **模型管理层**
   - `ModelDownloader`: 从 ModelScope 下载和管理模型
   - `ModelManager`: 单例模式管理嵌入和重排模型
   - 支持本地缓存和自动回退机制

2. **知识库服务层**
   - `PrivateMemoryService`: 个人知识库服务
   - `PublicMemoryService`: 公共知识库服务
   - `MemoryServiceFactory`: 服务工厂，管理服务实例

3. **API接口层**
   - `/api/v1/knowledge/*`: 知识库管理接口
   - `/api/v1/models/*`: 模型管理接口
   - 支持 RESTful API 和异步处理

4. **工具层**
   - `KnowledgeInitializer`: 知识库初始化工具
   - `manage_knowledge.py`: 命令行管理工具

### 技术特性

- ✅ **向量数据库**: 使用 ChromaDB 存储和检索
- ✅ **语义搜索**: 基于 Qwen3-0.6B 嵌入模型
- ✅ **结果重排**: 使用 Qwen3-Reranker-0.6B 优化排序
- ✅ **模型本地化**: 所有模型存储在项目目录
- ✅ **ModelScope 集成**: 从魔塔社区下载模型
- ✅ **异步处理**: 支持高并发访问
- ✅ **自动回退**: 模型加载失败时的降级方案

## 🚀 快速开始

### 1. 系统初始化

```bash
# 使用命令行工具初始化
python scripts/manage_knowledge.py init

# 或者使用 API
curl -X POST "http://localhost:8000/api/v1/models/download" \
  -H "Content-Type: application/json" \
  -d '{"model_type": "all", "force_download": false}'
```

### 2. 检查系统状态

```bash
# 命令行检查
python scripts/manage_knowledge.py status

# API 检查
curl -X GET "http://localhost:8000/api/v1/models/status"
```

### 3. 添加知识

```bash
# 添加公共知识
python scripts/manage_knowledge.py add "人工智能是计算机科学的一个分支" \
  --public --category "AI" --title "AI简介" --tags "人工智能,技术"

# 添加个人知识
python scripts/manage_knowledge.py add "我喜欢使用Python编程" \
  --user-id "user123" --category "个人偏好"
```

### 4. 搜索知识

```bash
# 搜索公共知识库
python scripts/manage_knowledge.py search "人工智能" --search-public

# 搜索个人知识库
python scripts/manage_knowledge.py search "编程" --user-id "user123" --search-private
```

## 📖 API 接口文档

### 知识库管理接口

#### 添加公共知识
```http
POST /api/v1/knowledge/public/add
Content-Type: application/json

{
  "content": "知识内容",
  "category": "分类",
  "title": "标题",
  "tags": ["标签1", "标签2"],
  "priority": 3,
  "metadata": {}
}
```

#### 添加个人知识
```http
POST /api/v1/knowledge/private/add
Content-Type: application/json

{
  "user_id": "用户ID",
  "content": "知识内容",
  "category": "分类",
  "title": "标题",
  "tags": ["标签1", "标签2"]
}
```

#### 搜索知识库
```http
POST /api/v1/knowledge/search
Content-Type: application/json

{
  "query": "搜索查询",
  "user_id": "用户ID",
  "search_public": true,
  "search_private": true,
  "limit": 10
}
```

#### 获取公共知识分类
```http
GET /api/v1/knowledge/public/categories
```

#### 按分类获取公共知识
```http
GET /api/v1/knowledge/public/category/{category}?limit=10
```

#### 更新公共知识
```http
PUT /api/v1/knowledge/public/{knowledge_id}
Content-Type: application/json

{
  "content": "更新的内容",
  "title": "更新的标题",
  "tags": ["新标签"],
  "priority": 4
}
```

#### 删除公共知识
```http
DELETE /api/v1/knowledge/public/{knowledge_id}
```

### 模型管理接口

#### 获取模型状态
```http
GET /api/v1/models/status
```

#### 下载模型
```http
POST /api/v1/models/download
Content-Type: application/json

{
  "model_type": "embedding",  // "embedding", "reranker", "all"
  "force_download": false
}
```

#### 验证模型
```http
POST /api/v1/models/validate
```

#### 清理模型缓存
```http
DELETE /api/v1/models/cache?model_type=embedding
```

## 🔧 配置说明

### 环境变量配置

```bash
# 模型缓存目录
MODEL_CACHE_DIR=/path/to/models

# 嵌入模型配置
EMBEDDING_MODEL_NAME=Qwen3-0.6B
USE_LOCAL_EMBEDDING=true

# 重排模型配置
RERANKER_MODEL_NAME=Qwen3-Reranker-0.6B
USE_RERANKER=true
USE_LOCAL_RERANKER=true

# ChromaDB配置
CHROMA_PERSIST_DIRECTORY=/path/to/chromadb
```

### 模型配置

项目使用以下模型：

- **嵌入模型**: `Qwen/Qwen3-0.6B` (ModelScope)
- **重排模型**: `Qwen/Qwen3-Reranker-0.6B` (ModelScope)
- **存储位置**: `{项目根目录}/models/`

## 📊 性能优化

### 向量检索优化

1. **两阶段检索**: 先用向量检索获取候选结果，再用重排模型精确排序
2. **批量处理**: 支持批量嵌入和重排操作
3. **缓存机制**: 模型和向量结果的多级缓存
4. **异步处理**: 非阻塞的模型加载和检索

### 存储优化

1. **向量压缩**: ChromaDB 自动优化向量存储
2. **分片存储**: 按用户和分类分离存储
3. **增量更新**: 支持增量添加和更新
4. **定期清理**: 自动清理无效数据

## 🛠️ 开发指南

### 扩展知识库服务

```python
from app.services.memory.factory import MemoryServiceFactory

# 获取服务实例
memory_factory = MemoryServiceFactory()
public_memory = memory_factory.get_public_memory_service()
private_memory = memory_factory.get_private_memory_service("user_id")

# 添加知识
knowledge_id = await public_memory.add_memory(
    content="知识内容",
    metadata={"category": "技术", "tags": ["AI", "ML"]}
)

# 搜索知识
results = await public_memory.retrieve_memories("查询内容", limit=5)
```

### 自定义模型加载

```python
from app.config.vector_db_config import model_manager

# 获取模型实例
embedding_model = model_manager.get_embedding_model()
reranker_model = model_manager.get_reranker_model()

# 使用模型
embeddings = embedding_model.encode(["文本1", "文本2"])
scores = reranker_model.predict([("查询", "文档1"), ("查询", "文档2")])
```

## 🔍 故障排除

### 常见问题

1. **模型下载失败**
   - 检查网络连接
   - 确认 ModelScope 访问权限
   - 查看磁盘空间是否充足

2. **向量检索无结果**
   - 确认知识库已初始化
   - 检查嵌入模型是否正常加载
   - 验证查询文本格式

3. **性能问题**
   - 检查模型是否使用 GPU 加速
   - 调整批处理大小
   - 优化查询限制参数

### 日志调试

```python
import logging
logging.getLogger("app.services.memory").setLevel(logging.DEBUG)
logging.getLogger("app.utils.model_downloader").setLevel(logging.DEBUG)
```

## 📈 监控和维护

### 系统监控

- 模型加载状态监控
- 知识库大小和性能监控
- API 响应时间监控
- 错误率和异常监控

### 定期维护

- 清理过期缓存
- 优化向量索引
- 备份知识库数据
- 更新模型版本

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request 来改进知识库功能！

### 开发环境设置

```bash
# 安装依赖
pip install -r requirements.txt

# 运行测试
python -m pytest tests/

# 代码格式化
black app/ scripts/
```

## 📄 许可证

本项目遵循 MIT 许可证。
