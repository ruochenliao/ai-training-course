# 多智能体协作模块 API 文档

## 📋 模块概述

多智能体协作模块基于AutoGen框架，提供多个AI智能体协同工作的能力，用于处理复杂的知识查询和任务分解。

**基础路径**: `/api/v1/autogen`

## 🤖 智能体类型

- **协调者智能体**: 负责任务分解和结果整合
- **检索智能体**: 专门负责知识库搜索和信息检索
- **分析智能体**: 负责数据分析和逻辑推理
- **总结智能体**: 负责信息总结和答案生成
- **验证智能体**: 负责答案质量验证和事实核查

## 📚 接口列表

### 1. 多智能体聊天

**接口名称**: 多智能体聊天  
**功能描述**: 使用多个智能体协作处理用户查询  
**接口地址**: `/api/v1/autogen/chat`  
**请求方式**: POST  
**认证**: 需要Bearer Token

#### 请求参数
```json
{
  "query": "请分析人工智能在医疗领域的应用现状和发展趋势",
  "knowledge_base_ids": [1, 2, 3],
  "conversation_id": 1,
  "temperature": 0.7,
  "max_tokens": 2000,
  "agent_config": {
    "use_retrieval_agent": true,
    "use_analysis_agent": true,
    "use_summary_agent": true,
    "use_verification_agent": false,
    "max_rounds": 5,
    "collaboration_mode": "sequential"
  },
  "context": {
    "domain": "healthcare",
    "language": "zh",
    "detail_level": "comprehensive"
  }
}
```

| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|-------|------|-----|------|--------|
| query | string | 是 | 用户查询 | 请分析人工智能在医疗... |
| knowledge_base_ids | array | 否 | 知识库ID列表 | [1, 2, 3] |
| conversation_id | int | 否 | 对话ID | 1 |
| temperature | float | 否 | 生成温度（默认0.7） | 0.7 |
| max_tokens | int | 否 | 最大Token数（默认2000） | 2000 |
| agent_config | object | 否 | 智能体配置 | 见配置对象 |
| context | object | 否 | 上下文信息 | 见上下文对象 |

#### 智能体配置说明
| 参数名 | 类型 | 说明 | 示例值 |
|-------|------|------|--------|
| use_retrieval_agent | bool | 是否使用检索智能体 | true |
| use_analysis_agent | bool | 是否使用分析智能体 | true |
| use_summary_agent | bool | 是否使用总结智能体 | true |
| use_verification_agent | bool | 是否使用验证智能体 | false |
| max_rounds | int | 最大协作轮数 | 5 |
| collaboration_mode | string | 协作模式 | sequential/parallel |

#### 协作模式说明
- `sequential`: 顺序协作，智能体按顺序工作
- `parallel`: 并行协作，智能体同时工作
- `hybrid`: 混合模式，根据任务自动选择

#### 响应参数
```json
{
  "query": "请分析人工智能在医疗领域的应用现状和发展趋势",
  "answer": "基于多智能体协作分析，人工智能在医疗领域的应用现状如下：\n\n1. 医学影像诊断...",
  "sources": [
    {
      "document_id": 1,
      "document_name": "AI医疗应用报告.pdf",
      "chunk_id": 23,
      "content": "人工智能在医学影像诊断中的应用...",
      "score": 0.95,
      "retrieved_by": "retrieval_agent"
    }
  ],
  "confidence": 0.92,
  "processing_time": 8.5,
  "conversation_id": 1,
  "agent_results": {
    "coordinator": {
      "task_decomposition": [
        "检索医疗AI相关文献",
        "分析应用现状",
        "预测发展趋势",
        "整合分析结果"
      ],
      "execution_plan": "sequential_processing"
    },
    "retrieval_agent": {
      "documents_found": 15,
      "search_queries": [
        "人工智能医疗应用",
        "AI医学影像诊断",
        "医疗AI发展趋势"
      ],
      "processing_time": 2.1
    },
    "analysis_agent": {
      "analysis_points": [
        "技术成熟度分析",
        "市场应用情况",
        "挑战和机遇"
      ],
      "processing_time": 3.2
    },
    "summary_agent": {
      "summary_structure": [
        "现状概述",
        "主要应用领域",
        "发展趋势预测",
        "结论建议"
      ],
      "processing_time": 2.8
    }
  },
  "metadata": {
    "total_agents_used": 4,
    "collaboration_rounds": 3,
    "collaboration_mode": "sequential",
    "knowledge_bases_searched": [1, 2, 3],
    "total_documents_analyzed": 15
  }
}
```

| 参数名 | 类型 | 说明 | 示例值 |
|-------|------|------|--------|
| query | string | 原始查询 | 请分析人工智能... |
| answer | string | 协作生成的答案 | 基于多智能体协作分析... |
| sources | array | 知识来源列表 | 见来源对象 |
| confidence | float | 答案置信度 | 0.92 |
| processing_time | float | 总处理时间（秒） | 8.5 |
| conversation_id | int | 对话ID | 1 |
| agent_results | object | 各智能体结果 | 见智能体结果 |
| metadata | object | 协作元数据 | 见元数据对象 |

---

### 2. 获取智能体状态

**接口名称**: 获取智能体状态  
**功能描述**: 获取当前智能体的工作状态  
**接口地址**: `/api/v1/autogen/agents/status`  
**请求方式**: GET  
**认证**: 需要Bearer Token

#### 请求参数
无

#### 响应参数
```json
{
  "agents": [
    {
      "agent_id": "coordinator_001",
      "agent_type": "coordinator",
      "status": "idle",
      "current_task": null,
      "load": 0.0,
      "last_active": "2024-01-01T12:00:00Z",
      "total_tasks_completed": 156,
      "average_processing_time": 1.2
    },
    {
      "agent_id": "retrieval_001",
      "agent_type": "retrieval",
      "status": "busy",
      "current_task": "searching_knowledge_base_1",
      "load": 0.8,
      "last_active": "2024-01-01T12:05:00Z",
      "total_tasks_completed": 234,
      "average_processing_time": 2.1
    }
  ],
  "total_agents": 5,
  "active_agents": 2,
  "system_load": 0.4
}
```

#### 智能体状态说明
- `idle`: 空闲
- `busy`: 忙碌
- `error`: 错误
- `maintenance`: 维护中

---

### 3. 配置智能体

**接口名称**: 配置智能体  
**功能描述**: 配置智能体的工作参数  
**接口地址**: `/api/v1/autogen/agents/config`  
**请求方式**: POST  
**认证**: 需要Bearer Token（管理员）

#### 请求参数
```json
{
  "agent_type": "retrieval",
  "config": {
    "max_concurrent_tasks": 3,
    "timeout_seconds": 30,
    "search_parameters": {
      "default_top_k": 20,
      "score_threshold": 0.7
    },
    "model_parameters": {
      "temperature": 0.5,
      "max_tokens": 1000
    }
  }
}
```

| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|-------|------|-----|------|--------|
| agent_type | string | 是 | 智能体类型 | retrieval |
| config | object | 是 | 配置参数 | 见配置对象 |

#### 响应参数
```json
{
  "message": "智能体配置更新成功",
  "agent_type": "retrieval",
  "updated_config": {
    "max_concurrent_tasks": 3,
    "timeout_seconds": 30,
    "search_parameters": {
      "default_top_k": 20,
      "score_threshold": 0.7
    }
  },
  "restart_required": false
}
```

---

### 4. 智能体协作历史

**接口名称**: 获取智能体协作历史  
**功能描述**: 获取智能体协作的历史记录  
**接口地址**: `/api/v1/autogen/collaboration/history`  
**请求方式**: GET  
**认证**: 需要Bearer Token

#### 请求参数
| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|-------|------|-----|------|--------|
| conversation_id | int | 否 | 对话ID过滤 | 1 |
| start_time | string | 否 | 开始时间 | 2024-01-01T00:00:00Z |
| end_time | string | 否 | 结束时间 | 2024-01-01T23:59:59Z |
| page | int | 否 | 页码 | 1 |
| size | int | 否 | 每页数量 | 20 |

#### 响应参数
```json
{
  "collaborations": [
    {
      "collaboration_id": "collab_123",
      "conversation_id": 1,
      "query": "分析AI在医疗领域的应用",
      "start_time": "2024-01-01T12:00:00Z",
      "end_time": "2024-01-01T12:08:30Z",
      "total_time": 8.5,
      "agents_involved": ["coordinator", "retrieval", "analysis", "summary"],
      "collaboration_mode": "sequential",
      "rounds": 3,
      "success": true,
      "confidence": 0.92,
      "user_feedback": {
        "rating": 5,
        "comment": "回答很全面"
      }
    }
  ],
  "total": 50,
  "page": 1,
  "size": 20,
  "pages": 3
}
```

---

### 5. 重启智能体

**接口名称**: 重启智能体  
**功能描述**: 重启指定类型的智能体  
**接口地址**: `/api/v1/autogen/agents/restart`  
**请求方式**: POST  
**认证**: 需要Bearer Token（管理员）

#### 请求参数
```json
{
  "agent_types": ["retrieval", "analysis"],
  "force": false,
  "wait_for_completion": true
}
```

| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|-------|------|-----|------|--------|
| agent_types | array | 是 | 智能体类型列表 | ["retrieval"] |
| force | bool | 否 | 是否强制重启 | false |
| wait_for_completion | bool | 否 | 是否等待完成 | true |

#### 响应参数
```json
{
  "message": "智能体重启完成",
  "restarted_agents": ["retrieval_001", "analysis_001"],
  "restart_time": 5.2,
  "status": "success"
}
```

## 🔧 使用示例

### 基础多智能体协作
```bash
# 1. 多智能体聊天
curl -X POST "http://localhost:8000/api/v1/autogen/chat" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "分析人工智能在教育领域的应用前景",
    "knowledge_base_ids": [1, 2],
    "agent_config": {
      "use_retrieval_agent": true,
      "use_analysis_agent": true,
      "use_summary_agent": true,
      "max_rounds": 3,
      "collaboration_mode": "sequential"
    }
  }'

# 2. 获取智能体状态
curl -X GET "http://localhost:8000/api/v1/autogen/agents/status" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# 3. 获取协作历史
curl -X GET "http://localhost:8000/api/v1/autogen/collaboration/history?page=1&size=10" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 智能体管理
```bash
# 配置智能体
curl -X POST "http://localhost:8000/api/v1/autogen/agents/config" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_type": "retrieval",
    "config": {
      "max_concurrent_tasks": 5,
      "timeout_seconds": 60
    }
  }'

# 重启智能体
curl -X POST "http://localhost:8000/api/v1/autogen/agents/restart" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_types": ["retrieval"],
    "force": false
  }'
```

## 🚨 注意事项

1. **处理时间**: 多智能体协作比单一AI响应时间更长
2. **资源消耗**: 多智能体会消耗更多计算资源
3. **协作模式**: 选择合适的协作模式影响效果和效率
4. **智能体配置**: 不同任务需要不同的智能体组合
5. **错误处理**: 单个智能体失败不会影响整体协作
6. **负载均衡**: 系统会自动进行智能体负载均衡
7. **质量保证**: 多智能体协作通常能提供更高质量的答案
