# 对话管理模块 API 文档

## 📋 模块概述

对话管理模块提供对话的创建、查询、管理和消息历史记录功能，支持多轮对话和上下文维护。

**基础路径**: `/api/v1/conversations`

## 💬 功能特性

- **对话创建**: 创建新的对话会话
- **消息管理**: 管理对话中的消息记录
- **上下文维护**: 保持对话的上下文连续性
- **对话分类**: 支持对话的分类和标签
- **历史查询**: 查询历史对话记录
- **对话统计**: 提供对话相关的统计信息

## 📚 接口列表

### 1. 获取对话列表

**接口名称**: 获取对话列表  
**功能描述**: 获取当前用户的对话列表  
**接口地址**: `/api/v1/conversations/`  
**请求方式**: GET  
**认证**: 需要Bearer Token

#### 请求参数
| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|-------|------|-----|------|--------|
| page | int | 否 | 页码（默认1） | 1 |
| size | int | 否 | 每页数量（默认20，最大100） | 20 |

#### 响应参数
```json
{
  "conversations": [
    {
      "id": 1,
      "title": "关于人工智能的讨论",
      "created_at": "2024-01-01T12:00:00Z",
      "updated_at": "2024-01-01T12:30:00Z",
      "message_count": 8
    },
    {
      "id": 2,
      "title": "机器学习算法咨询",
      "created_at": "2024-01-01T10:00:00Z",
      "updated_at": "2024-01-01T10:15:00Z",
      "message_count": 4
    }
  ],
  "total": 25,
  "page": 1,
  "size": 20
}
```

| 参数名 | 类型 | 说明 | 示例值 |
|-------|------|------|--------|
| conversations | array | 对话列表 | 见对话对象 |
| total | int | 总对话数 | 25 |
| page | int | 当前页码 | 1 |
| size | int | 每页数量 | 20 |

#### 对话对象字段说明
| 参数名 | 类型 | 说明 | 示例值 |
|-------|------|------|--------|
| id | int | 对话ID | 1 |
| title | string | 对话标题 | 关于人工智能的讨论 |
| created_at | string | 创建时间 | 2024-01-01T12:00:00Z |
| updated_at | string | 更新时间 | 2024-01-01T12:30:00Z |
| message_count | int | 消息数量 | 8 |

---

### 2. 创建对话

**接口名称**: 创建对话  
**功能描述**: 创建新的对话会话  
**接口地址**: `/api/v1/conversations/`  
**请求方式**: POST  
**认证**: 需要Bearer Token

#### 请求参数
```json
{
  "title": "新的对话"
}
```

| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|-------|------|-----|------|--------|
| title | string | 否 | 对话标题（默认"新对话"） | 新的对话 |

#### 响应参数
```json
{
  "id": 3,
  "title": "新的对话",
  "created_at": "2024-01-01T13:00:00Z",
  "updated_at": "2024-01-01T13:00:00Z",
  "message_count": 0
}
```

---

### 3. 获取对话详情

**接口名称**: 获取对话详情  
**功能描述**: 获取指定对话的详细信息和消息历史  
**接口地址**: `/api/v1/conversations/{conversation_id}`  
**请求方式**: GET  
**认证**: 需要Bearer Token

#### 请求参数
| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|-------|------|-----|------|--------|
| conversation_id | int | 是 | 对话ID（路径参数） | 1 |

#### 响应参数
```json
{
  "id": 1,
  "title": "关于人工智能的讨论",
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:30:00Z",
  "messages": [
    {
      "id": 1,
      "role": "user",
      "content": "什么是人工智能？",
      "created_at": "2024-01-01T12:00:00Z",
      "metadata": {}
    },
    {
      "id": 2,
      "role": "assistant",
      "content": "人工智能（Artificial Intelligence，AI）是指由机器展现出的智能...",
      "created_at": "2024-01-01T12:00:05Z",
      "metadata": {
        "sources": [
          {
            "document_id": 1,
            "document_name": "AI基础知识.pdf",
            "score": 0.95
          }
        ],
        "processing_time": 2.3,
        "confidence": 0.92
      }
    }
  ]
}
```

| 参数名 | 类型 | 说明 | 示例值 |
|-------|------|------|--------|
| id | int | 对话ID | 1 |
| title | string | 对话标题 | 关于人工智能的讨论 |
| created_at | string | 创建时间 | 2024-01-01T12:00:00Z |
| updated_at | string | 更新时间 | 2024-01-01T12:30:00Z |
| messages | array | 消息列表 | 见消息对象 |

#### 消息对象字段说明
| 参数名 | 类型 | 说明 | 示例值 |
|-------|------|------|--------|
| id | int | 消息ID | 1 |
| role | string | 角色（user/assistant/system） | user |
| content | string | 消息内容 | 什么是人工智能？ |
| created_at | string | 创建时间 | 2024-01-01T12:00:00Z |
| metadata | object | 消息元数据 | 见元数据对象 |

---

### 4. 更新对话标题

**接口名称**: 更新对话标题  
**功能描述**: 更新指定对话的标题  
**接口地址**: `/api/v1/conversations/{conversation_id}`  
**请求方式**: PUT  
**认证**: 需要Bearer Token

#### 请求参数
| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|-------|------|-----|------|--------|
| conversation_id | int | 是 | 对话ID（路径参数） | 1 |

```json
{
  "title": "更新后的对话标题"
}
```

| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|-------|------|-----|------|--------|
| title | string | 是 | 新的对话标题 | 更新后的对话标题 |

#### 响应参数
```json
{
  "id": 1,
  "title": "更新后的对话标题",
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T13:00:00Z",
  "message_count": 8
}
```

#### 错误码
- `404`: 对话不存在
- `403`: 无权修改此对话

---

### 5. 删除对话

**接口名称**: 删除对话  
**功能描述**: 删除指定的对话及其所有消息  
**接口地址**: `/api/v1/conversations/{conversation_id}`  
**请求方式**: DELETE  
**认证**: 需要Bearer Token

#### 请求参数
| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|-------|------|-----|------|--------|
| conversation_id | int | 是 | 对话ID（路径参数） | 1 |

#### 响应参数
```json
{
  "message": "对话已删除",
  "conversation_id": 1,
  "deleted_messages": 8
}
```

#### 错误码
- `404`: 对话不存在
- `403`: 无权删除此对话

---

### 6. 获取对话消息

**接口名称**: 获取对话消息  
**功能描述**: 分页获取指定对话的消息列表  
**接口地址**: `/api/v1/conversations/{conversation_id}/messages`  
**请求方式**: GET  
**认证**: 需要Bearer Token

#### 请求参数
| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|-------|------|-----|------|--------|
| conversation_id | int | 是 | 对话ID（路径参数） | 1 |
| page | int | 否 | 页码（默认1） | 1 |
| size | int | 否 | 每页数量（默认50） | 50 |
| role | string | 否 | 角色过滤 | user |

#### 响应参数
```json
{
  "conversation_id": 1,
  "messages": [
    {
      "id": 1,
      "role": "user",
      "content": "什么是人工智能？",
      "created_at": "2024-01-01T12:00:00Z",
      "metadata": {}
    }
  ],
  "total": 8,
  "page": 1,
  "size": 50
}
```

---

### 7. 搜索对话

**接口名称**: 搜索对话  
**功能描述**: 根据关键词搜索对话  
**接口地址**: `/api/v1/conversations/search`  
**请求方式**: GET  
**认证**: 需要Bearer Token

#### 请求参数
| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|-------|------|-----|------|--------|
| q | string | 是 | 搜索关键词 | 人工智能 |
| page | int | 否 | 页码 | 1 |
| size | int | 否 | 每页数量 | 20 |

#### 响应参数
```json
{
  "query": "人工智能",
  "conversations": [
    {
      "id": 1,
      "title": "关于人工智能的讨论",
      "created_at": "2024-01-01T12:00:00Z",
      "updated_at": "2024-01-01T12:30:00Z",
      "message_count": 8,
      "highlights": [
        "关于<em>人工智能</em>的讨论",
        "什么是<em>人工智能</em>？"
      ]
    }
  ],
  "total": 3,
  "page": 1,
  "size": 20
}
```

---

### 8. 对话统计

**接口名称**: 获取对话统计  
**功能描述**: 获取用户的对话统计信息  
**接口地址**: `/api/v1/conversations/stats`  
**请求方式**: GET  
**认证**: 需要Bearer Token

#### 请求参数
| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|-------|------|-----|------|--------|
| period | string | 否 | 统计周期（day/week/month） | week |

#### 响应参数
```json
{
  "period": "week",
  "total_conversations": 25,
  "total_messages": 150,
  "conversations_this_period": 5,
  "messages_this_period": 30,
  "average_messages_per_conversation": 6.0,
  "most_active_day": "2024-01-01",
  "conversation_topics": [
    {
      "topic": "人工智能",
      "count": 8
    },
    {
      "topic": "机器学习",
      "count": 6
    }
  ]
}
```

## 🔧 使用示例

### 基础对话管理
```bash
# 1. 获取对话列表
curl -X GET "http://localhost:8000/api/v1/conversations/?page=1&size=20" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# 2. 创建新对话
curl -X POST "http://localhost:8000/api/v1/conversations/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "关于深度学习的讨论"
  }'

# 3. 获取对话详情
curl -X GET "http://localhost:8000/api/v1/conversations/1" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# 4. 更新对话标题
curl -X PUT "http://localhost:8000/api/v1/conversations/1" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "深度学习技术探讨"
  }'

# 5. 删除对话
curl -X DELETE "http://localhost:8000/api/v1/conversations/1" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 对话搜索和统计
```bash
# 搜索对话
curl -X GET "http://localhost:8000/api/v1/conversations/search?q=人工智能&page=1&size=10" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# 获取对话统计
curl -X GET "http://localhost:8000/api/v1/conversations/stats?period=week" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# 获取对话消息
curl -X GET "http://localhost:8000/api/v1/conversations/1/messages?page=1&size=50" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 🚨 注意事项

1. **权限控制**: 用户只能访问自己的对话
2. **消息顺序**: 消息按时间顺序排列
3. **对话标题**: 系统会根据首条消息自动生成标题
4. **删除操作**: 删除对话会同时删除所有相关消息
5. **搜索功能**: 支持对话标题和消息内容的全文搜索
6. **分页限制**: 消息列表建议使用分页避免数据量过大
7. **上下文维护**: 系统自动维护对话的上下文关系
