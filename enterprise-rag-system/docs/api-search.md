# 搜索接口模块 API 文档

## 📋 模块概述

搜索接口模块提供多种搜索方式，包括向量搜索、图谱搜索和混合搜索，支持语义理解和精确匹配。

**基础路径**: `/api/v1/search`

## 🔍 搜索类型

- **向量搜索**: 基于语义相似度的搜索
- **图谱搜索**: 基于知识图谱的关系搜索
- **混合搜索**: 结合多种搜索方式的综合搜索
- **全文搜索**: 基于关键词的传统搜索

## 📚 接口列表

### 1. 混合搜索

**接口名称**: 混合搜索  
**功能描述**: 使用多种搜索算法进行综合搜索  
**接口地址**: `/api/v1/search/`  
**请求方式**: POST  
**认证**: 需要Bearer Token

#### 请求参数
```json
{
  "query": "人工智能的发展历史",
  "knowledge_base_ids": [1, 2],
  "top_k": 10,
  "score_threshold": 0.7,
  "search_type": "hybrid",
  "filters": {
    "document_type": "pdf",
    "date_range": {
      "start": "2020-01-01",
      "end": "2024-01-01"
    }
  },
  "rerank": true
}
```

| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|-------|------|-----|------|--------|
| query | string | 是 | 搜索查询 | 人工智能的发展历史 |
| knowledge_base_ids | array | 否 | 知识库ID列表 | [1, 2] |
| top_k | int | 否 | 返回结果数量（默认10） | 10 |
| score_threshold | float | 否 | 相似度阈值（默认0.5） | 0.7 |
| search_type | string | 否 | 搜索类型（默认hybrid） | hybrid |
| filters | object | 否 | 过滤条件 | 见过滤对象 |
| rerank | bool | 否 | 是否重排序（默认true） | true |

#### 搜索类型说明
- `vector`: 向量搜索
- `graph`: 图谱搜索
- `hybrid`: 混合搜索
- `fulltext`: 全文搜索

#### 响应参数
```json
{
  "query": "人工智能的发展历史",
  "results": [
    {
      "id": "doc_1_chunk_45",
      "document_id": 1,
      "document_name": "AI发展史.pdf",
      "chunk_id": 45,
      "content": "人工智能的发展可以追溯到1950年代...",
      "score": 0.95,
      "metadata": {
        "page": 3,
        "chapter": "第一章",
        "document_type": "pdf",
        "created_at": "2023-01-01T00:00:00Z"
      },
      "highlights": [
        "人工智能的<em>发展</em>可以追溯到1950年代",
        "图灵测试标志着AI<em>历史</em>的重要节点"
      ]
    }
  ],
  "total": 25,
  "search_type": "hybrid",
  "processing_time": 0.8,
  "metadata": {
    "vector_results": 15,
    "graph_results": 8,
    "fulltext_results": 12,
    "reranked": true,
    "knowledge_bases_searched": [1, 2]
  }
}
```

| 参数名 | 类型 | 说明 | 示例值 |
|-------|------|------|--------|
| query | string | 原始查询 | 人工智能的发展历史 |
| results | array | 搜索结果列表 | 见结果对象 |
| total | int | 总结果数 | 25 |
| search_type | string | 实际搜索类型 | hybrid |
| processing_time | float | 处理时间（秒） | 0.8 |
| metadata | object | 搜索元数据 | 见元数据对象 |

#### 搜索结果对象字段说明
| 参数名 | 类型 | 说明 | 示例值 |
|-------|------|------|--------|
| id | string | 结果唯一标识 | doc_1_chunk_45 |
| document_id | int | 文档ID | 1 |
| document_name | string | 文档名称 | AI发展史.pdf |
| chunk_id | int | 文档块ID | 45 |
| content | string | 内容片段 | 人工智能的发展... |
| score | float | 相关性评分 | 0.95 |
| metadata | object | 结果元数据 | 见元数据对象 |
| highlights | array | 高亮片段 | 见高亮数组 |

---

### 2. 向量搜索

**接口名称**: 向量搜索  
**功能描述**: 基于语义向量的相似度搜索  
**接口地址**: `/api/v1/search/vector`  
**请求方式**: POST  
**认证**: 需要Bearer Token

#### 请求参数
```json
{
  "query": "机器学习算法",
  "knowledge_base_ids": [1],
  "top_k": 20,
  "score_threshold": 0.6,
  "embedding_model": "text-embedding-ada-002"
}
```

| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|-------|------|-----|------|--------|
| query | string | 是 | 搜索查询 | 机器学习算法 |
| knowledge_base_ids | array | 否 | 知识库ID列表 | [1] |
| top_k | int | 否 | 返回结果数量 | 20 |
| score_threshold | float | 否 | 相似度阈值 | 0.6 |
| embedding_model | string | 否 | 嵌入模型 | text-embedding-ada-002 |

#### 响应参数
```json
{
  "query": "机器学习算法",
  "results": [
    {
      "document_id": 1,
      "chunk_id": 23,
      "content": "监督学习是机器学习的一个重要分支...",
      "vector_score": 0.92,
      "cosine_similarity": 0.89,
      "metadata": {
        "document_name": "ML基础.pdf",
        "page": 15
      }
    }
  ],
  "total": 15,
  "search_type": "vector",
  "processing_time": 0.3,
  "embedding_time": 0.1
}
```

---

### 3. 图谱搜索

**接口名称**: 图谱搜索  
**功能描述**: 基于知识图谱的关系搜索  
**接口地址**: `/api/v1/search/graph`  
**请求方式**: POST  
**认证**: 需要Bearer Token

#### 请求参数
```json
{
  "query": "深度学习与神经网络的关系",
  "knowledge_base_ids": [1, 2],
  "top_k": 15,
  "max_depth": 3,
  "relation_types": ["相关", "包含", "应用于"]
}
```

| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|-------|------|-----|------|--------|
| query | string | 是 | 搜索查询 | 深度学习与神经网络的关系 |
| knowledge_base_ids | array | 否 | 知识库ID列表 | [1, 2] |
| top_k | int | 否 | 返回结果数量 | 15 |
| max_depth | int | 否 | 最大搜索深度 | 3 |
| relation_types | array | 否 | 关系类型过滤 | ["相关", "包含"] |

#### 响应参数
```json
{
  "query": "深度学习与神经网络的关系",
  "results": [
    {
      "entity_id": "entity_123",
      "entity_name": "深度学习",
      "entity_type": "概念",
      "relations": [
        {
          "relation_type": "基于",
          "target_entity": "神经网络",
          "confidence": 0.95
        }
      ],
      "content": "深度学习是基于人工神经网络的机器学习方法...",
      "graph_score": 0.88
    }
  ],
  "total": 8,
  "search_type": "graph",
  "processing_time": 1.2,
  "graph_traversal_time": 0.9
}
```

---

### 4. 全文搜索

**接口名称**: 全文搜索  
**功能描述**: 基于关键词的传统全文搜索  
**接口地址**: `/api/v1/search/fulltext`  
**请求方式**: POST  
**认证**: 需要Bearer Token

#### 请求参数
```json
{
  "query": "人工智能 AND 机器学习",
  "knowledge_base_ids": [1, 2],
  "top_k": 30,
  "highlight": true,
  "fuzzy": true,
  "operator": "AND"
}
```

| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|-------|------|-----|------|--------|
| query | string | 是 | 搜索查询 | 人工智能 AND 机器学习 |
| knowledge_base_ids | array | 否 | 知识库ID列表 | [1, 2] |
| top_k | int | 否 | 返回结果数量 | 30 |
| highlight | bool | 否 | 是否高亮（默认true） | true |
| fuzzy | bool | 否 | 是否模糊匹配 | true |
| operator | string | 否 | 逻辑操作符（AND/OR） | AND |

#### 响应参数
```json
{
  "query": "人工智能 AND 机器学习",
  "results": [
    {
      "document_id": 1,
      "chunk_id": 67,
      "content": "人工智能和机器学习是现代科技的重要组成部分...",
      "fulltext_score": 0.85,
      "term_frequency": 3,
      "highlights": [
        "<em>人工智能</em>和<em>机器学习</em>是现代科技"
      ]
    }
  ],
  "total": 22,
  "search_type": "fulltext",
  "processing_time": 0.2
}
```

---

### 5. 搜索建议

**接口名称**: 搜索建议  
**功能描述**: 根据输入提供搜索建议  
**接口地址**: `/api/v1/search/suggestions`  
**请求方式**: GET  
**认证**: 需要Bearer Token

#### 请求参数
| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|-------|------|-----|------|--------|
| q | string | 是 | 查询前缀 | 人工智 |
| limit | int | 否 | 建议数量（默认10） | 10 |
| knowledge_base_ids | array | 否 | 知识库ID列表 | [1, 2] |

#### 响应参数
```json
{
  "query": "人工智",
  "suggestions": [
    {
      "text": "人工智能",
      "frequency": 156,
      "type": "entity"
    },
    {
      "text": "人工智能算法",
      "frequency": 89,
      "type": "concept"
    },
    {
      "text": "人工智能应用",
      "frequency": 67,
      "type": "topic"
    }
  ],
  "total": 3
}
```

## 🔧 使用示例

### 基础搜索流程
```bash
# 1. 混合搜索
curl -X POST "http://localhost:8000/api/v1/search/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "人工智能的发展历史",
    "knowledge_base_ids": [1, 2],
    "top_k": 10,
    "search_type": "hybrid"
  }'

# 2. 向量搜索
curl -X POST "http://localhost:8000/api/v1/search/vector" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "机器学习算法",
    "top_k": 20,
    "score_threshold": 0.7
  }'

# 3. 图谱搜索
curl -X POST "http://localhost:8000/api/v1/search/graph" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "深度学习与神经网络的关系",
    "max_depth": 3
  }'

# 4. 全文搜索
curl -X POST "http://localhost:8000/api/v1/search/fulltext" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "人工智能 AND 机器学习",
    "highlight": true,
    "fuzzy": true
  }'

# 5. 搜索建议
curl -X GET "http://localhost:8000/api/v1/search/suggestions?q=人工智&limit=10" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 高级搜索示例
```bash
# 带过滤条件的搜索
curl -X POST "http://localhost:8000/api/v1/search/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "深度学习",
    "knowledge_base_ids": [1, 2],
    "top_k": 15,
    "filters": {
      "document_type": "pdf",
      "date_range": {
        "start": "2020-01-01",
        "end": "2024-01-01"
      },
      "tags": ["技术", "算法"]
    },
    "rerank": true
  }'
```

## 🚨 注意事项

1. **搜索性能**: 不同搜索类型的性能差异较大
2. **结果排序**: 混合搜索会自动进行结果重排序
3. **权限控制**: 只能搜索有权限的知识库
4. **查询优化**: 建议使用具体的查询词获得更好结果
5. **缓存机制**: 相同查询会使用缓存提高响应速度
6. **并发限制**: 同时进行的搜索请求数量有限制
7. **结果过滤**: 可以通过多种条件过滤搜索结果
