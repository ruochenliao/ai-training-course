# 企业级RAG知识库系统API接口规范文档

## 📋 API设计概述

本文档定义了企业级RAG知识库系统的完整API接口规范，包括RESTful API设计标准、认证授权机制、接口详细定义和测试用例。

## 🏗️ RESTful API设计规范

### 基础规范
- **API版本**: `/api/v1/`
- **请求格式**: JSON
- **响应格式**: JSON
- **字符编码**: UTF-8
- **时间格式**: ISO 8601 (YYYY-MM-DDTHH:mm:ssZ)

### HTTP方法规范
| 方法 | 用途 | 幂等性 | 安全性 |
|------|------|--------|--------|
| GET | 查询资源 | ✅ | ✅ |
| POST | 创建资源 | ❌ | ❌ |
| PUT | 更新资源(完整) | ✅ | ❌ |
| PATCH | 更新资源(部分) | ❌ | ❌ |
| DELETE | 删除资源 | ✅ | ❌ |

### 状态码规范
| 状态码 | 含义 | 使用场景 |
|--------|------|----------|
| 200 | 成功 | 请求成功处理 |
| 201 | 已创建 | 资源创建成功 |
| 204 | 无内容 | 删除成功 |
| 400 | 请求错误 | 参数验证失败 |
| 401 | 未认证 | 需要登录 |
| 403 | 禁止访问 | 权限不足 |
| 404 | 未找到 | 资源不存在 |
| 409 | 冲突 | 资源冲突 |
| 422 | 实体错误 | 业务逻辑错误 |
| 500 | 服务器错误 | 内部错误 |

### 统一响应格式
```json
{
  "success": true,
  "code": 200,
  "message": "操作成功",
  "data": {},
  "timestamp": "2024-01-01T12:00:00Z",
  "request_id": "req_123456789"
}
```

### 错误响应格式
```json
{
  "success": false,
  "code": 400,
  "message": "参数验证失败",
  "error": {
    "type": "ValidationError",
    "details": [
      {
        "field": "email",
        "message": "邮箱格式不正确"
      }
    ]
  },
  "timestamp": "2024-01-01T12:00:00Z",
  "request_id": "req_123456789"
}
```

## 🔐 认证授权机制

### JWT Token认证
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Token结构
```json
{
  "header": {
    "alg": "HS256",
    "typ": "JWT"
  },
  "payload": {
    "user_id": 123,
    "username": "user@example.com",
    "roles": ["user"],
    "permissions": ["knowledge_base:read"],
    "exp": 1640995200,
    "iat": 1640908800
  }
}
```

### 权限控制
- **角色**: admin, user, guest
- **权限**: resource:action (如 knowledge_base:read)
- **范围**: 全局、知识库级别、文档级别

## 📚 接口详细定义

### 1. 认证授权接口

#### 1.1 用户登录
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "password123"
}
```

**响应示例**:
```json
{
  "success": true,
  "code": 200,
  "message": "登录成功",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 86400,
    "user": {
      "id": 123,
      "username": "user@example.com",
      "full_name": "张三",
      "roles": ["user"]
    }
  }
}
```

#### 1.2 用户注册
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "username": "newuser@example.com",
  "password": "password123",
  "full_name": "新用户",
  "phone": "13800138000"
}
```

#### 1.3 刷新Token
```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### 2. 用户管理接口

#### 2.1 获取用户信息
```http
GET /api/v1/users/profile
Authorization: Bearer {access_token}
```

#### 2.2 更新用户信息
```http
PUT /api/v1/users/profile
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "full_name": "张三",
  "phone": "13800138000",
  "avatar": "https://example.com/avatar.jpg"
}
```

#### 2.3 用户列表(管理员)
```http
GET /api/v1/users/?page=1&size=20&search=张三
Authorization: Bearer {admin_token}
```

### 3. 知识库管理接口

#### 3.1 创建知识库
```http
POST /api/v1/knowledge-bases/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "name": "技术文档库",
  "description": "存储技术相关文档",
  "is_public": false,
  "settings": {
    "chunk_size": 1000,
    "chunk_overlap": 200,
    "embedding_model": "qwen3-8b"
  }
}
```

#### 3.2 知识库列表
```http
GET /api/v1/knowledge-bases/?page=1&size=20&search=技术
Authorization: Bearer {access_token}
```

**响应示例**:
```json
{
  "success": true,
  "code": 200,
  "data": {
    "items": [
      {
        "id": 1,
        "name": "技术文档库",
        "description": "存储技术相关文档",
        "is_public": false,
        "document_count": 25,
        "created_at": "2024-01-01T12:00:00Z",
        "updated_at": "2024-01-01T12:00:00Z",
        "owner": {
          "id": 123,
          "username": "user@example.com",
          "full_name": "张三"
        }
      }
    ],
    "total": 1,
    "page": 1,
    "size": 20,
    "pages": 1
  }
}
```

#### 3.3 更新知识库
```http
PUT /api/v1/knowledge-bases/{id}
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "name": "更新后的技术文档库",
  "description": "更新后的描述"
}
```

#### 3.4 删除知识库
```http
DELETE /api/v1/knowledge-bases/{id}
Authorization: Bearer {access_token}
```

### 4. 文档管理接口

#### 4.1 上传文档
```http
POST /api/v1/documents/upload
Authorization: Bearer {access_token}
Content-Type: multipart/form-data

file: [binary data]
knowledge_base_id: 1
extract_images: true
extract_tables: true
```

**响应示例**:
```json
{
  "success": true,
  "code": 201,
  "message": "文档上传成功",
  "data": {
    "document_id": 456,
    "filename": "技术文档.pdf",
    "file_size": 1024000,
    "status": "processing",
    "processing_id": "proc_123456789"
  }
}
```

#### 4.2 文档列表
```http
GET /api/v1/documents/?knowledge_base_id=1&page=1&size=20
Authorization: Bearer {access_token}
```

#### 4.3 文档详情
```http
GET /api/v1/documents/{id}
Authorization: Bearer {access_token}
```

#### 4.4 删除文档
```http
DELETE /api/v1/documents/{id}
Authorization: Bearer {access_token}
```

#### 4.5 批量上传文档
```http
POST /api/v1/documents/batch-upload
Authorization: Bearer {access_token}
Content-Type: multipart/form-data

files: [multiple binary data]
knowledge_base_id: 1
```

### 5. 对话管理接口

#### 5.1 创建对话
```http
POST /api/v1/conversations/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "title": "技术问题咨询",
  "knowledge_base_ids": [1, 2]
}
```

#### 5.2 发送消息
```http
POST /api/v1/conversations/{id}/messages
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "content": "什么是RAG技术？",
  "message_type": "text",
  "attachments": []
}
```

#### 5.3 AutoGen智能体对话
```http
POST /api/v1/autogen/chat
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "query": "什么是RAG技术？",
  "knowledge_base_ids": [1, 2],
  "conversation_id": 789,
  "use_multimodal": false
}
```

**响应示例**:
```json
{
  "success": true,
  "code": 200,
  "data": {
    "query": "什么是RAG技术？",
    "answer": "RAG（Retrieval-Augmented Generation）是一种结合检索和生成的技术...",
    "sources": [
      {
        "document_id": 456,
        "chunk_id": "chunk_123",
        "content": "RAG技术的相关内容...",
        "score": 0.95
      }
    ],
    "confidence": 0.92,
    "processing_time": 2.5,
    "agent_results": {
      "retrieval_agent": "检索到5个相关文档片段",
      "analysis_agent": "分析了技术定义和应用场景",
      "answer_agent": "生成了详细的技术解释",
      "quality_agent": "答案质量评分: 0.92"
    }
  }
}
```

### 6. 搜索接口

#### 6.1 基础搜索
```http
POST /api/v1/search/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "query": "RAG技术",
  "knowledge_base_ids": [1, 2],
  "search_type": "hybrid",
  "top_k": 10,
  "score_threshold": 0.7
}
```

#### 6.2 高级搜索
```http
POST /api/v1/advanced-search/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "query": "RAG技术",
  "filters": {
    "document_type": ["pdf", "docx"],
    "date_range": {
      "start": "2024-01-01",
      "end": "2024-12-31"
    },
    "tags": ["AI", "技术"]
  },
  "sort": {
    "field": "relevance",
    "order": "desc"
  }
}
```

### 7. 知识图谱接口

#### 7.1 图谱查询
```http
POST /api/v1/graph/query
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "entity": "RAG技术",
  "relation_types": ["相关", "包含"],
  "max_depth": 2,
  "limit": 50
}
```

#### 7.2 图谱统计
```http
GET /api/v1/graph/stats?knowledge_base_id=1
Authorization: Bearer {access_token}
```

### 8. 系统管理接口

#### 8.1 系统健康检查
```http
GET /api/v1/system/health
```

**响应示例**:
```json
{
  "success": true,
  "code": 200,
  "data": {
    "status": "healthy",
    "services": {
      "database": "healthy",
      "milvus": "healthy",
      "neo4j": "healthy",
      "redis": "healthy"
    },
    "version": "1.0.0",
    "uptime": 86400
  }
}
```

#### 8.2 系统统计
```http
GET /api/v1/system/stats
Authorization: Bearer {admin_token}
```

## 🧪 接口测试用例

### 认证测试用例
```javascript
// 测试用例1: 正常登录
{
  "name": "正常登录测试",
  "request": {
    "method": "POST",
    "url": "/api/v1/auth/login",
    "body": {
      "username": "test@example.com",
      "password": "password123"
    }
  },
  "expected": {
    "status": 200,
    "body": {
      "success": true,
      "data.access_token": "string",
      "data.user.id": "number"
    }
  }
}

// 测试用例2: 密码错误
{
  "name": "密码错误测试",
  "request": {
    "method": "POST",
    "url": "/api/v1/auth/login",
    "body": {
      "username": "test@example.com",
      "password": "wrongpassword"
    }
  },
  "expected": {
    "status": 401,
    "body": {
      "success": false,
      "message": "用户名或密码错误"
    }
  }
}
```

### 知识库测试用例
```javascript
// 测试用例3: 创建知识库
{
  "name": "创建知识库测试",
  "request": {
    "method": "POST",
    "url": "/api/v1/knowledge-bases/",
    "headers": {
      "Authorization": "Bearer {valid_token}"
    },
    "body": {
      "name": "测试知识库",
      "description": "用于测试的知识库"
    }
  },
  "expected": {
    "status": 201,
    "body": {
      "success": true,
      "data.id": "number",
      "data.name": "测试知识库"
    }
  }
}
```

### 文档上传测试用例
```javascript
// 测试用例4: 文档上传
{
  "name": "文档上传测试",
  "request": {
    "method": "POST",
    "url": "/api/v1/documents/upload",
    "headers": {
      "Authorization": "Bearer {valid_token}",
      "Content-Type": "multipart/form-data"
    },
    "body": {
      "file": "test.pdf",
      "knowledge_base_id": 1
    }
  },
  "expected": {
    "status": 201,
    "body": {
      "success": true,
      "data.document_id": "number",
      "data.status": "processing"
    }
  }
}
```

## 📊 性能指标

### API性能要求
- **响应时间**: 95%的请求 < 2秒
- **吞吐量**: > 1000 QPS
- **并发用户**: > 500人同时在线
- **可用性**: 99.9%年度可用性

### 监控指标
- 请求响应时间分布
- 错误率统计
- API调用频次
- 数据库连接池状态
- 缓存命中率

这个API规范文档提供了完整的接口定义和测试标准，为前后端开发和联调提供了详细的技术指导。
