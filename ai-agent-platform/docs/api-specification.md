# API接口规范文档

## 1. 接口设计原则

### 1.1 RESTful设计规范
- 使用HTTP动词表示操作：GET(查询)、POST(创建)、PUT(更新)、DELETE(删除)
- 使用名词表示资源，避免动词
- 使用复数形式表示资源集合
- 使用嵌套路径表示资源关系

### 1.2 统一响应格式
```json
{
  "code": 200,
  "message": "Success",
  "data": {},
  "timestamp": "2025-08-02T10:30:00Z",
  "request_id": "req_123456789"
}
```

### 1.3 错误码规范
- 2xx: 成功
- 4xx: 客户端错误
- 5xx: 服务器错误

## 2. 认证授权接口

### 2.1 用户登录
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "password123"
}
```

**响应**:
```json
{
  "code": 200,
  "message": "Login successful",
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer",
    "expires_in": 3600,
    "user": {
      "id": 1,
      "username": "user@example.com",
      "full_name": "John Doe",
      "roles": ["user"]
    }
  }
}
```

### 2.2 刷新Token
```http
POST /api/v1/auth/refresh
Authorization: Bearer <refresh_token>
```

### 2.3 用户注册
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "username": "newuser@example.com",
  "password": "password123",
  "full_name": "New User",
  "email": "newuser@example.com"
}
```

### 2.4 用户登出
```http
POST /api/v1/auth/logout
Authorization: Bearer <access_token>
```

## 3. 用户管理接口

### 3.1 获取用户信息
```http
GET /api/v1/users/me
Authorization: Bearer <access_token>
```

### 3.2 更新用户信息
```http
PUT /api/v1/users/me
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "full_name": "Updated Name",
  "avatar_url": "https://example.com/avatar.jpg"
}
```

### 3.3 修改密码
```http
POST /api/v1/users/change-password
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "old_password": "oldpass123",
  "new_password": "newpass123"
}
```

### 3.4 用户列表 (管理员)
```http
GET /api/v1/users?page=1&size=20&search=john
Authorization: Bearer <admin_token>
```

## 4. 智能体对话接口

### 4.1 创建会话
```http
POST /api/v1/conversations
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "agent_type": "customer_service",
  "title": "客服咨询",
  "context": {}
}
```

### 4.2 发送消息
```http
POST /api/v1/conversations/{conversation_id}/messages
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "content": "你好，我想咨询一下产品信息",
  "attachments": [
    {
      "type": "image",
      "url": "https://example.com/image.jpg"
    }
  ]
}
```

### 4.3 WebSocket流式对话
```javascript
// WebSocket连接
const ws = new WebSocket('ws://localhost:8000/api/v1/conversations/{conversation_id}/stream');

// 发送消息
ws.send(JSON.stringify({
  "type": "message",
  "content": "你好",
  "token": "bearer_token"
}));

// 接收流式响应
ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  if (data.type === 'chunk') {
    // 处理流式内容块
    console.log(data.content);
  } else if (data.type === 'done') {
    // 响应完成
    console.log('Response completed');
  }
};
```

### 4.4 获取会话历史
```http
GET /api/v1/conversations/{conversation_id}/messages?page=1&size=50
Authorization: Bearer <access_token>
```

### 4.5 获取会话列表
```http
GET /api/v1/conversations?agent_type=customer_service&page=1&size=20
Authorization: Bearer <access_token>
```

## 5. 知识库管理接口

### 5.1 创建知识库
```http
POST /api/v1/knowledge-bases
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "产品知识库",
  "description": "包含所有产品相关信息",
  "type": "private",
  "settings": {
    "chunk_size": 1000,
    "chunk_overlap": 200,
    "embedding_model": "text-embedding-ada-002"
  }
}
```

### 5.2 上传文件
```http
POST /api/v1/knowledge-bases/{kb_id}/files
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

files: [File1, File2, ...]
```

### 5.3 获取文件列表
```http
GET /api/v1/knowledge-bases/{kb_id}/files?status=completed&page=1&size=20
Authorization: Bearer <access_token>
```

### 5.4 删除文件
```http
DELETE /api/v1/knowledge-bases/{kb_id}/files/{file_id}
Authorization: Bearer <access_token>
```

### 5.5 知识库搜索
```http
POST /api/v1/knowledge-bases/{kb_id}/search
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "query": "产品价格信息",
  "top_k": 5,
  "score_threshold": 0.7
}
```

**响应**:
```json
{
  "code": 200,
  "data": {
    "results": [
      {
        "chunk_id": 123,
        "content": "产品A的价格为999元...",
        "score": 0.95,
        "metadata": {
          "file_name": "产品手册.pdf",
          "page": 5,
          "source": "section_2.1"
        }
      }
    ],
    "total": 5
  }
}
```

## 6. Text2SQL接口

### 6.1 自然语言转SQL
```http
POST /api/v1/agents/text2sql/query
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "question": "查询上个月销售额最高的前10个产品",
  "database_schema": "sales_db",
  "context": {}
}
```

**响应**:
```json
{
  "code": 200,
  "data": {
    "sql": "SELECT product_name, SUM(sales_amount) as total_sales FROM sales WHERE created_at >= '2025-07-01' AND created_at < '2025-08-01' GROUP BY product_name ORDER BY total_sales DESC LIMIT 10;",
    "explanation": "这个查询会统计上个月每个产品的销售总额，并按销售额降序排列，返回前10名。",
    "confidence": 0.92
  }
}
```

### 6.2 执行SQL查询
```http
POST /api/v1/agents/text2sql/execute
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "sql": "SELECT * FROM products LIMIT 10;",
  "database": "main"
}
```

### 6.3 生成图表
```http
POST /api/v1/agents/text2sql/visualize
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "data": [...],
  "chart_type": "bar",
  "x_axis": "product_name",
  "y_axis": "sales_amount"
}
```

## 7. 文案创作接口

### 7.1 创作文案
```http
POST /api/v1/agents/content-creation/generate
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "template": "social_media_post",
  "topic": "新产品发布",
  "target_audience": "年轻用户",
  "style": "活泼有趣",
  "keywords": ["创新", "科技", "便捷"],
  "length": "short",
  "requirements": "包含call-to-action"
}
```

### 7.2 优化文案
```http
POST /api/v1/agents/content-creation/optimize
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "original_content": "原始文案内容...",
  "optimization_type": "improve_engagement",
  "feedback": "需要更有吸引力"
}
```

## 8. 管理后台接口

### 8.1 系统统计
```http
GET /api/v1/admin/statistics
Authorization: Bearer <admin_token>
```

**响应**:
```json
{
  "code": 200,
  "data": {
    "users": {
      "total": 1250,
      "active_today": 89,
      "new_this_week": 23
    },
    "conversations": {
      "total": 5680,
      "today": 156
    },
    "knowledge_bases": {
      "total": 45,
      "total_files": 1234,
      "total_size_mb": 2048
    },
    "api_calls": {
      "today": 2345,
      "this_week": 15678
    }
  }
}
```

### 8.2 系统健康检查
```http
GET /api/v1/admin/health
Authorization: Bearer <admin_token>
```

### 8.3 用户管理
```http
GET /api/v1/admin/users?page=1&size=20&role=user&status=active
PUT /api/v1/admin/users/{user_id}/status
DELETE /api/v1/admin/users/{user_id}
```

## 9. 文件上传接口

### 9.1 单文件上传
```http
POST /api/v1/files/upload
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

file: <file_data>
purpose: "knowledge_base"
knowledge_base_id: 123
```

### 9.2 获取上传进度
```http
GET /api/v1/files/{file_id}/status
Authorization: Bearer <access_token>
```

### 9.3 批量上传状态
```http
GET /api/v1/files/batch-status?file_ids=1,2,3,4,5
Authorization: Bearer <access_token>
```

## 10. WebSocket事件规范

### 10.1 连接认证
```javascript
// 连接时发送认证信息
{
  "type": "auth",
  "token": "bearer_token"
}
```

### 10.2 消息类型
```javascript
// 用户消息
{
  "type": "user_message",
  "conversation_id": 123,
  "content": "用户输入的内容"
}

// AI响应块
{
  "type": "ai_chunk",
  "conversation_id": 123,
  "content": "AI回复的部分内容",
  "chunk_id": 1
}

// 响应完成
{
  "type": "ai_complete",
  "conversation_id": 123,
  "message_id": 456
}

// 工具调用状态
{
  "type": "tool_calling",
  "conversation_id": 123,
  "tool_name": "search_knowledge_base",
  "status": "running"
}

// 错误消息
{
  "type": "error",
  "code": 4001,
  "message": "Authentication failed"
}
```

## 11. 错误码定义

### 11.1 认证相关 (401x)
- 4010: Token无效
- 4011: Token过期
- 4012: 权限不足
- 4013: 账户被禁用

### 11.2 业务相关 (400x)
- 4001: 参数错误
- 4002: 资源不存在
- 4003: 资源已存在
- 4004: 操作不允许

### 11.3 系统相关 (500x)
- 5001: 数据库错误
- 5002: 外部服务错误
- 5003: 文件处理错误
- 5004: AI服务错误

## 12. 限流规则

### 12.1 API限流
- 普通用户: 60次/分钟
- VIP用户: 300次/分钟
- 管理员: 1000次/分钟

### 12.2 特殊接口限流
- 文件上传: 10次/分钟
- AI对话: 30次/分钟
- 知识库搜索: 100次/分钟
