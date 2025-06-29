# 聊天接口模块 API 文档

## 📋 模块概述

聊天接口模块提供智能问答功能，支持实时聊天和流式聊天，集成知识库检索和多智能体协作。

**基础路径**: `/api/v1/chat`

## 🤖 功能特性

- **智能问答**: 基于知识库的智能回答
- **流式响应**: 支持实时流式输出
- **多模态**: 支持文本、图片等多种输入
- **上下文记忆**: 维护对话上下文
- **知识检索**: 自动检索相关知识
- **多智能体**: 可选择使用多智能体协作

## 📚 接口列表

### 1. 发送消息

**接口名称**: 发送消息  
**功能描述**: 发送消息并获取AI回复  
**接口地址**: `/api/v1/chat/`  
**请求方式**: POST  
**认证**: 需要Bearer Token

#### 请求参数
```json
{
  "message": "什么是人工智能？",
  "conversation_id": 1,
  "knowledge_base_ids": [1, 2],
  "use_agents": true,
  "temperature": 0.7,
  "max_tokens": 2000,
  "metadata": {
    "source": "web",
    "user_agent": "Mozilla/5.0..."
  }
}
```

| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|-------|------|-----|------|--------|
| message | string | 是 | 用户消息内容 | 什么是人工智能？ |
| conversation_id | int | 否 | 对话ID（不提供则创建新对话） | 1 |
| knowledge_base_ids | array | 否 | 知识库ID列表 | [1, 2] |
| use_agents | bool | 否 | 是否使用多智能体（默认true） | true |
| temperature | float | 否 | 生成温度（0-1，默认0.7） | 0.7 |
| max_tokens | int | 否 | 最大生成长度（默认2000） | 2000 |
| metadata | object | 否 | 附加元数据 | 见元数据对象 |

#### 响应参数
```json
{
  "conversation_id": 1,
  "message_id": 123,
  "response": "人工智能（Artificial Intelligence，AI）是指由机器展现出的智能...",
  "sources": [
    {
      "document_id": 1,
      "document_name": "AI基础知识.pdf",
      "chunk_id": 45,
      "content": "人工智能是计算机科学的一个分支...",
      "score": 0.95,
      "page": 3
    }
  ],
  "confidence": 0.92,
  "processing_time": 2.5,
  "token_usage": {
    "prompt_tokens": 150,
    "completion_tokens": 200,
    "total_tokens": 350
  },
  "metadata": {
    "search_type": "hybrid",
    "agent_used": true,
    "knowledge_bases_searched": [1, 2]
  }
}
```

| 参数名 | 类型 | 说明 | 示例值 |
|-------|------|------|--------|
| conversation_id | int | 对话ID | 1 |
| message_id | int | 消息ID | 123 |
| response | string | AI回复内容 | 人工智能是指... |
| sources | array | 知识来源列表 | 见来源对象 |
| confidence | float | 回答置信度 | 0.92 |
| processing_time | float | 处理时间（秒） | 2.5 |
| token_usage | object | Token使用统计 | 见Token对象 |
| metadata | object | 响应元数据 | 见元数据对象 |

#### 来源对象字段说明
| 参数名 | 类型 | 说明 | 示例值 |
|-------|------|------|--------|
| document_id | int | 文档ID | 1 |
| document_name | string | 文档名称 | AI基础知识.pdf |
| chunk_id | int | 文档块ID | 45 |
| content | string | 相关内容片段 | 人工智能是计算机... |
| score | float | 相关性评分 | 0.95 |
| page | int | 页码 | 3 |

---

### 2. 流式聊天

**接口名称**: 流式聊天  
**功能描述**: 发送消息并获取流式AI回复  
**接口地址**: `/api/v1/chat/stream`  
**请求方式**: POST  
**认证**: 需要Bearer Token  
**响应类型**: text/event-stream

#### 请求参数
与"发送消息"接口相同。

#### 响应格式
```
data: {"type": "start", "conversation_id": 1, "message_id": 123}

data: {"type": "content", "content": "人工智能"}

data: {"type": "content", "content": "（Artificial Intelligence，AI）"}

data: {"type": "sources", "sources": [...]}

data: {"type": "end", "metadata": {...}}
```

#### 流式事件类型
| 事件类型 | 说明 | 数据内容 |
|---------|------|----------|
| start | 开始响应 | conversation_id, message_id |
| content | 内容片段 | content |
| sources | 知识来源 | sources数组 |
| metadata | 元数据信息 | 处理统计信息 |
| error | 错误信息 | error描述 |
| end | 响应结束 | 完整的元数据 |

---

### 3. 多轮对话

**接口名称**: 多轮对话  
**功能描述**: 在现有对话中继续聊天  
**接口地址**: `/api/v1/chat/continue`  
**请求方式**: POST  
**认证**: 需要Bearer Token

#### 请求参数
```json
{
  "conversation_id": 1,
  "message": "请详细解释一下机器学习",
  "context_length": 5
}
```

| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|-------|------|-----|------|--------|
| conversation_id | int | 是 | 对话ID | 1 |
| message | string | 是 | 用户消息 | 请详细解释一下机器学习 |
| context_length | int | 否 | 上下文长度（默认5） | 5 |

#### 响应参数
与"发送消息"接口相同。

---

### 4. 获取对话历史

**接口名称**: 获取对话历史  
**功能描述**: 获取指定对话的消息历史  
**接口地址**: `/api/v1/chat/history/{conversation_id}`  
**请求方式**: GET  
**认证**: 需要Bearer Token

#### 请求参数
| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|-------|------|-----|------|--------|
| conversation_id | int | 是 | 对话ID（路径参数） | 1 |
| page | int | 否 | 页码（默认1） | 1 |
| size | int | 否 | 每页数量（默认20） | 20 |

#### 响应参数
```json
{
  "conversation_id": 1,
  "messages": [
    {
      "id": 123,
      "role": "user",
      "content": "什么是人工智能？",
      "created_at": "2024-01-01T12:00:00Z",
      "metadata": {}
    },
    {
      "id": 124,
      "role": "assistant",
      "content": "人工智能是指由机器展现出的智能...",
      "created_at": "2024-01-01T12:00:05Z",
      "sources": [...],
      "metadata": {}
    }
  ],
  "total": 10,
  "page": 1,
  "size": 20
}
```

---

### 5. 清除对话

**接口名称**: 清除对话  
**功能描述**: 清除指定对话的所有消息  
**接口地址**: `/api/v1/chat/clear/{conversation_id}`  
**请求方式**: DELETE  
**认证**: 需要Bearer Token

#### 请求参数
| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|-------|------|-----|------|--------|
| conversation_id | int | 是 | 对话ID（路径参数） | 1 |

#### 响应参数
```json
{
  "message": "对话已清除",
  "conversation_id": 1,
  "cleared_messages": 10
}
```

---

### 6. 评价回答

**接口名称**: 评价回答  
**功能描述**: 对AI回答进行评价反馈  
**接口地址**: `/api/v1/chat/feedback`  
**请求方式**: POST  
**认证**: 需要Bearer Token

#### 请求参数
```json
{
  "message_id": 124,
  "rating": 5,
  "feedback": "回答很准确和详细",
  "tags": ["准确", "详细", "有用"]
}
```

| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|-------|------|-----|------|--------|
| message_id | int | 是 | 消息ID | 124 |
| rating | int | 是 | 评分（1-5） | 5 |
| feedback | string | 否 | 文字反馈 | 回答很准确和详细 |
| tags | array | 否 | 标签列表 | ["准确", "详细"] |

#### 响应参数
```json
{
  "message": "反馈已记录",
  "feedback_id": 456
}
```

## 🔧 使用示例

### 基础聊天流程
```bash
# 1. 发送消息（创建新对话）
curl -X POST "http://localhost:8000/api/v1/chat/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "什么是人工智能？",
    "knowledge_base_ids": [1, 2],
    "use_agents": true
  }'

# 2. 继续对话
curl -X POST "http://localhost:8000/api/v1/chat/continue" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": 1,
    "message": "请详细解释机器学习"
  }'

# 3. 获取对话历史
curl -X GET "http://localhost:8000/api/v1/chat/history/1" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# 4. 评价回答
curl -X POST "http://localhost:8000/api/v1/chat/feedback" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message_id": 124,
    "rating": 5,
    "feedback": "回答很准确"
  }'
```

### 流式聊天示例
```javascript
// JavaScript 流式聊天示例
const response = await fetch('/api/v1/chat/stream', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_ACCESS_TOKEN',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    message: '什么是人工智能？',
    knowledge_base_ids: [1, 2]
  })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  
  const chunk = decoder.decode(value);
  const lines = chunk.split('\n');
  
  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const data = JSON.parse(line.slice(6));
      
      switch (data.type) {
        case 'start':
          console.log('开始响应:', data);
          break;
        case 'content':
          console.log('内容片段:', data.content);
          break;
        case 'sources':
          console.log('知识来源:', data.sources);
          break;
        case 'end':
          console.log('响应结束:', data);
          break;
      }
    }
  }
}
```

## 🚨 注意事项

1. **Token限制**: 单次对话最大Token数有限制
2. **并发限制**: 用户同时进行的对话数量有限制
3. **上下文长度**: 对话上下文会影响响应质量和速度
4. **知识库权限**: 只能检索有权限的知识库
5. **流式连接**: 流式聊天需要保持连接稳定
6. **错误重试**: 网络错误时建议重试
7. **反馈机制**: 用户反馈有助于改进AI回答质量
