# 知识库管理模块 API 文档

## 📋 模块概述

知识库管理模块提供知识库的创建、查询、更新、删除等功能，支持权限控制和可见性管理。

**基础路径**: `/api/v1/knowledge-bases`

## 🔐 权限说明

- **knowledge_base:read**: 读取知识库权限
- **knowledge_base:write**: 创建知识库权限
- **knowledge_base:delete**: 删除知识库权限
- **knowledge_base:manage**: 管理知识库权限

## 📚 接口列表

### 1. 获取知识库列表

**接口名称**: 获取知识库列表
**功能描述**: 获取用户有权访问的知识库列表
**接口地址**: `/api/v1/knowledge-bases/`
**请求方式**: GET
**认证**: 需要Bearer Token + knowledge_base:read权限

#### 请求参数
| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|-------|------|-----|------|--------|
| page | int | 否 | 页码（默认1） | 1 |
| size | int | 否 | 每页数量（默认20，最大100） | 20 |
| search | string | 否 | 搜索关键词（知识库名称） | 技术文档 |
| knowledge_type | string | 否 | 知识库类型过滤 | general |

#### 响应参数
```json
{
  "items": [
    {
      "id": 1,
      "name": "技术文档知识库",
      "description": "存储技术相关文档",
      "knowledge_type": "general",
      "visibility": "private",
      "owner_id": 1,
      "created_at": "2024-01-01T12:00:00Z",
      "updated_at": "2024-01-01T12:00:00Z"
    }
  ],
  "total": 10,
  "page": 1,
  "size": 20,
  "pages": 1
}
```

| 参数名 | 类型 | 说明 | 示例值 |
|-------|------|------|--------|
| items | array | 知识库列表 | 见知识库对象 |
| total | int | 总数量 | 10 |
| page | int | 当前页码 | 1 |
| size | int | 每页数量 | 20 |
| pages | int | 总页数 | 1 |

#### 知识库对象字段说明
| 参数名 | 类型 | 说明 | 示例值 |
|-------|------|------|--------|
| id | int | 知识库ID | 1 |
| name | string | 知识库名称 | 技术文档知识库 |
| description | string | 知识库描述 | 存储技术相关文档 |
| knowledge_type | string | 知识库类型 | general |
| visibility | string | 可见性（public/private） | private |
| owner_id | int | 所有者ID | 1 |
| created_at | string | 创建时间 | 2024-01-01T12:00:00Z |
| updated_at | string | 更新时间 | 2024-01-01T12:00:00Z |

---

### 2. 创建知识库

**接口名称**: 创建知识库  
**功能描述**: 创建新的知识库  
**接口地址**: `/api/v1/knowledge-bases/`  
**请求方式**: POST  
**认证**: 需要Bearer Token + knowledge_base:write权限

#### 请求参数
```json
{
  "name": "新知识库",
  "description": "这是一个新的知识库",
  "is_public": false
}
```

| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|-------|------|-----|------|--------|
| name | string | 是 | 知识库名称（1-100字符） | 新知识库 |
| description | string | 否 | 知识库描述 | 这是一个新的知识库 |
| is_public | bool | 否 | 是否公开（默认false） | false |

#### 响应参数
```json
{
  "id": 2,
  "name": "新知识库",
  "description": "这是一个新的知识库",
  "knowledge_type": "general",
  "visibility": "private",
  "owner_id": 1,
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

#### 错误码
- `400`: 知识库名称不能为空 / 知识库名称已存在
- `403`: 权限不足

---

### 3. 获取知识库详情

**接口名称**: 获取知识库详情  
**功能描述**: 获取指定知识库的详细信息  
**接口地址**: `/api/v1/knowledge-bases/{kb_id}`  
**请求方式**: GET  
**认证**: 需要Bearer Token + knowledge_base:read权限

#### 请求参数
| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|-------|------|-----|------|--------|
| kb_id | int | 是 | 知识库ID（路径参数） | 1 |

#### 响应参数
```json
{
  "id": 1,
  "name": "技术文档知识库",
  "description": "存储技术相关文档",
  "knowledge_type": "general",
  "visibility": "private",
  "owner_id": 1,
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

#### 错误码
- `404`: 知识库不存在
- `403`: 权限不足

---

### 4. 更新知识库

**接口名称**: 更新知识库  
**功能描述**: 更新指定知识库的信息  
**接口地址**: `/api/v1/knowledge-bases/{kb_id}`  
**请求方式**: PUT  
**认证**: 需要Bearer Token（所有者或超级用户）

#### 请求参数
| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|-------|------|-----|------|--------|
| kb_id | int | 是 | 知识库ID（路径参数） | 1 |
| name | string | 否 | 知识库名称 | 更新的名称 |
| description | string | 否 | 知识库描述 | 更新的描述 |
| visibility | string | 否 | 可见性（public/private） | public |

#### 响应参数
```json
{
  "id": 1,
  "name": "更新的名称",
  "description": "更新的描述",
  "knowledge_type": "general",
  "visibility": "public",
  "owner_id": 1,
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T13:00:00Z"
}
```

#### 错误码
- `404`: 知识库不存在
- `403`: 无权修改此知识库

---

### 5. 删除知识库

**接口名称**: 删除知识库  
**功能描述**: 软删除指定的知识库  
**接口地址**: `/api/v1/knowledge-bases/{kb_id}`  
**请求方式**: DELETE  
**认证**: 需要Bearer Token（所有者或超级用户）

#### 请求参数
| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|-------|------|-----|------|--------|
| kb_id | int | 是 | 知识库ID（路径参数） | 1 |

#### 响应参数
```json
{
  "message": "知识库已删除"
}
```

#### 错误码
- `404`: 知识库不存在
- `403`: 无权删除此知识库

## 🔧 使用示例

### 完整知识库管理流程
```bash
# 1. 获取知识库列表
curl -X GET "http://localhost:8000/api/v1/knowledge-bases/?page=1&size=20" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# 2. 创建知识库
curl -X POST "http://localhost:8000/api/v1/knowledge-bases/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "我的知识库",
    "description": "这是我的第一个知识库",
    "is_public": false
  }'

# 3. 获取知识库详情
curl -X GET "http://localhost:8000/api/v1/knowledge-bases/1" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# 4. 更新知识库
curl -X PUT "http://localhost:8000/api/v1/knowledge-bases/1" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "更新的知识库名称",
    "description": "更新的描述",
    "visibility": "public"
  }'

# 5. 删除知识库
curl -X DELETE "http://localhost:8000/api/v1/knowledge-bases/1" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 搜索和过滤
```bash
# 按名称搜索知识库
curl -X GET "http://localhost:8000/api/v1/knowledge-bases/?search=技术文档" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# 按类型过滤知识库
curl -X GET "http://localhost:8000/api/v1/knowledge-bases/?knowledge_type=general" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# 组合查询
curl -X GET "http://localhost:8000/api/v1/knowledge-bases/?page=1&size=10&search=文档&knowledge_type=general" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 🔒 权限控制

### 可见性规则
1. **私有知识库（private）**: 只有所有者和超级用户可以访问
2. **公开知识库（public）**: 所有有读取权限的用户都可以访问

### 操作权限
1. **创建**: 需要 `knowledge_base:write` 权限
2. **读取**: 需要 `knowledge_base:read` 权限 + 可见性检查
3. **更新**: 需要是所有者或超级用户
4. **删除**: 需要是所有者或超级用户

### 审计日志
系统会记录所有知识库访问操作的审计日志，包括：
- 用户ID和用户名
- 操作类型（read/write/delete）
- 资源ID
- 操作时间
- 操作结果

## 🚨 注意事项

1. **名称唯一性**: 同一用户下的知识库名称必须唯一
2. **软删除**: 删除操作采用软删除，数据不会立即物理删除
3. **权限检查**: 所有操作都会进行严格的权限检查
4. **分页限制**: 列表查询最大每页100条记录
5. **搜索功能**: 支持按知识库名称进行模糊搜索
6. **类型管理**: 知识库类型目前支持 general 类型，后续可扩展
