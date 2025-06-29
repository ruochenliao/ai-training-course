# RBAC权限管理模块 API 文档

## 📋 模块概述

RBAC（基于角色的访问控制）权限管理模块提供完整的权限管理体系，包括部门、角色、权限的管理和用户权限分配。

**基础路径**: `/api/v1/rbac`

## 🔐 权限模型

- **部门（Department）**: 组织结构单位
- **角色（Role）**: 权限的集合
- **权限（Permission）**: 具体的操作权限
- **用户角色（UserRole）**: 用户与角色的关联
- **用户权限（UserPermission）**: 用户的直接权限

## 📚 接口列表

### 1. 部门管理

#### 1.1 获取部门列表

**接口名称**: 获取部门列表  
**功能描述**: 获取组织架构中的部门列表  
**接口地址**: `/api/v1/rbac/departments`  
**请求方式**: GET  
**认证**: 需要Bearer Token

##### 请求参数
| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|-------|------|-----|------|--------|
| page | int | 否 | 页码（默认1） | 1 |
| size | int | 否 | 每页数量（默认20） | 20 |
| search | string | 否 | 搜索关键词 | 技术部 |

##### 响应参数
```json
{
  "departments": [
    {
      "id": 1,
      "name": "技术部",
      "description": "负责技术研发工作",
      "parent_id": null,
      "level": 1,
      "sort_order": 1,
      "status": "active",
      "created_at": "2024-01-01T12:00:00Z",
      "children": [
        {
          "id": 2,
          "name": "前端组",
          "parent_id": 1,
          "level": 2
        }
      ]
    }
  ],
  "total": 10,
  "page": 1,
  "size": 20
}
```

#### 1.2 创建部门

**接口名称**: 创建部门  
**功能描述**: 创建新的部门  
**接口地址**: `/api/v1/rbac/departments`  
**请求方式**: POST  
**认证**: 需要Bearer Token（管理员）

##### 请求参数
```json
{
  "name": "产品部",
  "description": "负责产品设计和规划",
  "parent_id": null,
  "sort_order": 2
}
```

##### 响应参数
```json
{
  "id": 3,
  "name": "产品部",
  "description": "负责产品设计和规划",
  "parent_id": null,
  "level": 1,
  "sort_order": 2,
  "status": "active",
  "created_at": "2024-01-01T12:00:00Z"
}
```

---

### 2. 角色管理

#### 2.1 获取角色列表

**接口名称**: 获取角色列表  
**功能描述**: 获取系统中的角色列表  
**接口地址**: `/api/v1/rbac/roles`  
**请求方式**: GET  
**认证**: 需要Bearer Token

##### 请求参数
| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|-------|------|-----|------|--------|
| page | int | 否 | 页码 | 1 |
| size | int | 否 | 每页数量 | 20 |
| status | string | 否 | 状态过滤 | active |

##### 响应参数
```json
{
  "roles": [
    {
      "id": 1,
      "name": "系统管理员",
      "code": "admin",
      "description": "系统超级管理员，拥有所有权限",
      "status": "active",
      "is_system": true,
      "created_at": "2024-01-01T12:00:00Z",
      "permissions_count": 50
    }
  ],
  "total": 5,
  "page": 1,
  "size": 20
}
```

#### 2.2 创建角色

**接口名称**: 创建角色  
**功能描述**: 创建新的角色  
**接口地址**: `/api/v1/rbac/roles`  
**请求方式**: POST  
**认证**: 需要Bearer Token（管理员）

##### 请求参数
```json
{
  "name": "知识库管理员",
  "code": "kb_admin",
  "description": "负责知识库的管理和维护",
  "permission_ids": [1, 2, 3, 10, 11, 12]
}
```

##### 响应参数
```json
{
  "id": 6,
  "name": "知识库管理员",
  "code": "kb_admin",
  "description": "负责知识库的管理和维护",
  "status": "active",
  "is_system": false,
  "created_at": "2024-01-01T12:00:00Z",
  "permissions": [
    {
      "id": 1,
      "name": "knowledge_base:read",
      "description": "读取知识库"
    }
  ]
}
```

---

### 3. 权限管理

#### 3.1 获取权限列表

**接口名称**: 获取权限列表  
**功能描述**: 获取系统中的权限列表  
**接口地址**: `/api/v1/rbac/permissions`  
**请求方式**: GET  
**认证**: 需要Bearer Token

##### 请求参数
| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|-------|------|-----|------|--------|
| page | int | 否 | 页码 | 1 |
| size | int | 否 | 每页数量 | 50 |
| module | string | 否 | 模块过滤 | knowledge_base |

##### 响应参数
```json
{
  "permissions": [
    {
      "id": 1,
      "name": "knowledge_base:read",
      "description": "读取知识库",
      "module": "knowledge_base",
      "resource": "knowledge_base",
      "action": "read",
      "status": "active",
      "is_system": true,
      "created_at": "2024-01-01T12:00:00Z"
    }
  ],
  "total": 50,
  "page": 1,
  "size": 50,
  "modules": ["auth", "user", "knowledge_base", "document", "chat"]
}
```

#### 3.2 创建权限

**接口名称**: 创建权限  
**功能描述**: 创建新的权限  
**接口地址**: `/api/v1/rbac/permissions`  
**请求方式**: POST  
**认证**: 需要Bearer Token（超级管理员）

##### 请求参数
```json
{
  "name": "document:export",
  "description": "导出文档",
  "module": "document",
  "resource": "document",
  "action": "export"
}
```

##### 响应参数
```json
{
  "id": 51,
  "name": "document:export",
  "description": "导出文档",
  "module": "document",
  "resource": "document",
  "action": "export",
  "status": "active",
  "is_system": false,
  "created_at": "2024-01-01T12:00:00Z"
}
```

---

### 4. 用户权限分配

#### 4.1 分配用户角色

**接口名称**: 分配用户角色  
**功能描述**: 为用户分配角色  
**接口地址**: `/api/v1/rbac/users/{user_id}/roles`  
**请求方式**: POST  
**认证**: 需要Bearer Token（管理员）

##### 请求参数
```json
{
  "role_ids": [2, 3],
  "expires_at": "2024-12-31T23:59:59Z",
  "department_id": 1
}
```

| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|-------|------|-----|------|--------|
| role_ids | array | 是 | 角色ID列表 | [2, 3] |
| expires_at | string | 否 | 过期时间 | 2024-12-31T23:59:59Z |
| department_id | int | 否 | 部门ID | 1 |

##### 响应参数
```json
{
  "message": "用户角色分配成功",
  "user_id": 123,
  "assigned_roles": [
    {
      "role_id": 2,
      "role_name": "知识库管理员",
      "expires_at": "2024-12-31T23:59:59Z"
    }
  ]
}
```

#### 4.2 获取用户权限

**接口名称**: 获取用户权限  
**功能描述**: 获取用户的所有权限（角色权限+直接权限）  
**接口地址**: `/api/v1/rbac/users/{user_id}/permissions`  
**请求方式**: GET  
**认证**: 需要Bearer Token

##### 请求参数
| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|-------|------|-----|------|--------|
| user_id | int | 是 | 用户ID（路径参数） | 123 |

##### 响应参数
```json
{
  "user_id": 123,
  "permissions": [
    {
      "permission_id": 1,
      "permission_name": "knowledge_base:read",
      "permission_description": "读取知识库",
      "source": "role",
      "source_name": "知识库管理员",
      "expires_at": "2024-12-31T23:59:59Z"
    }
  ],
  "roles": [
    {
      "role_id": 2,
      "role_name": "知识库管理员",
      "expires_at": "2024-12-31T23:59:59Z"
    }
  ],
  "total_permissions": 15
}
```

---

### 5. 权限检查

#### 5.1 检查用户权限

**接口名称**: 检查用户权限  
**功能描述**: 检查用户是否具有指定权限  
**接口地址**: `/api/v1/rbac/check-permissions`  
**请求方式**: POST  
**认证**: 需要Bearer Token

##### 请求参数
```json
{
  "user_id": 123,
  "permission_codes": [
    "knowledge_base:read",
    "knowledge_base:write",
    "document:upload"
  ]
}
```

##### 响应参数
```json
{
  "user_id": 123,
  "permissions": {
    "knowledge_base:read": true,
    "knowledge_base:write": true,
    "document:upload": false
  }
}
```

#### 5.2 获取权限菜单

**接口名称**: 获取权限菜单  
**功能描述**: 根据用户权限获取可访问的菜单  
**接口地址**: `/api/v1/rbac/menus`  
**请求方式**: GET  
**认证**: 需要Bearer Token

##### 请求参数
无

##### 响应参数
```json
{
  "menus": [
    {
      "id": 1,
      "name": "知识库管理",
      "path": "/knowledge-bases",
      "icon": "database",
      "sort_order": 1,
      "children": [
        {
          "id": 2,
          "name": "知识库列表",
          "path": "/knowledge-bases/list",
          "permission": "knowledge_base:read"
        }
      ]
    }
  ]
}
```

## 🔧 使用示例

### 完整权限管理流程
```bash
# 1. 创建部门
curl -X POST "http://localhost:8000/api/v1/rbac/departments" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "技术部",
    "description": "负责技术研发"
  }'

# 2. 创建角色
curl -X POST "http://localhost:8000/api/v1/rbac/roles" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "知识库管理员",
    "code": "kb_admin",
    "description": "管理知识库",
    "permission_ids": [1, 2, 3]
  }'

# 3. 分配用户角色
curl -X POST "http://localhost:8000/api/v1/rbac/users/123/roles" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "role_ids": [2],
    "department_id": 1
  }'

# 4. 检查用户权限
curl -X POST "http://localhost:8000/api/v1/rbac/check-permissions" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 123,
    "permission_codes": ["knowledge_base:read", "knowledge_base:write"]
  }'

# 5. 获取用户菜单
curl -X GET "http://localhost:8000/api/v1/rbac/menus" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 权限查询
```bash
# 获取权限列表
curl -X GET "http://localhost:8000/api/v1/rbac/permissions?module=knowledge_base" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# 获取用户权限详情
curl -X GET "http://localhost:8000/api/v1/rbac/users/123/permissions" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# 获取角色列表
curl -X GET "http://localhost:8000/api/v1/rbac/roles?status=active" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 🚨 注意事项

1. **权限继承**: 用户权限 = 角色权限 + 直接权限
2. **权限过期**: 角色分配可以设置过期时间
3. **部门权限**: 用户在不同部门可能有不同权限
4. **系统权限**: 系统内置权限不能删除或修改
5. **权限缓存**: 权限检查结果会被缓存以提高性能
6. **权限审计**: 所有权限操作都会记录审计日志
7. **权限验证**: 每个API请求都会进行权限验证
