# 用户管理模块 API 文档

## 📋 模块概述

用户管理模块提供用户信息的增删改查、用户状态管理、用户统计等功能，支持普通用户自我管理和管理员用户管理。

**基础路径**: `/api/v1/users`

## 🔐 权限说明

- **普通用户**: 只能访问和修改自己的信息 (`/me` 相关接口)
- **超级用户**: 可以管理所有用户信息和状态

## 📚 接口列表

### 1. 获取当前用户信息

**接口名称**: 获取当前用户信息  
**功能描述**: 获取当前登录用户的详细信息  
**接口地址**: `/api/v1/users/me`  
**请求方式**: GET  
**认证**: 需要Bearer Token

#### 请求参数
无

#### 响应参数
```json
{
  "id": 1,
  "username": "testuser",
  "email": "test@example.com",
  "full_name": "测试用户",
  "avatar_url": null,
  "bio": "这是我的个人简介",
  "phone": "13800138000",
  "is_email_verified": true,
  "is_phone_verified": false,
  "is_superuser": false,
  "is_staff": false,
  "status": "active",
  "language": "zh",
  "timezone": "Asia/Shanghai",
  "theme": "light",
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z",
  "last_login_at": "2024-01-01T12:30:00Z",
  "login_count": 5
}
```

| 参数名 | 类型 | 说明 | 示例值 |
|-------|------|------|--------|
| id | int | 用户ID | 1 |
| username | string | 用户名 | testuser |
| email | string | 邮箱地址 | test@example.com |
| full_name | string | 真实姓名 | 测试用户 |
| avatar_url | string | 头像URL | null |
| bio | string | 个人简介 | 这是我的个人简介 |
| phone | string | 手机号码 | 13800138000 |
| is_email_verified | bool | 邮箱是否验证 | true |
| is_phone_verified | bool | 手机是否验证 | false |
| is_superuser | bool | 是否超级用户 | false |
| is_staff | bool | 是否员工 | false |
| status | string | 用户状态 | active |
| language | string | 语言设置 | zh |
| timezone | string | 时区设置 | Asia/Shanghai |
| theme | string | 主题设置 | light |
| created_at | string | 创建时间 | 2024-01-01T12:00:00Z |
| updated_at | string | 更新时间 | 2024-01-01T12:00:00Z |
| last_login_at | string | 最后登录时间 | 2024-01-01T12:30:00Z |
| login_count | int | 登录次数 | 5 |

---

### 2. 更新当前用户信息

**接口名称**: 更新当前用户信息  
**功能描述**: 更新当前登录用户的个人信息  
**接口地址**: `/api/v1/users/me`  
**请求方式**: PUT  
**认证**: 需要Bearer Token

#### 请求参数
```json
{
  "full_name": "新的姓名",
  "bio": "更新的个人简介",
  "phone": "13900139000",
  "language": "en",
  "timezone": "UTC",
  "theme": "dark"
}
```

| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|-------|------|-----|------|--------|
| full_name | string | 否 | 真实姓名 | 新的姓名 |
| bio | string | 否 | 个人简介 | 更新的个人简介 |
| phone | string | 否 | 手机号码 | 13900139000 |
| language | string | 否 | 语言设置 | en |
| timezone | string | 否 | 时区设置 | UTC |
| theme | string | 否 | 主题设置 | dark |

#### 响应参数
返回更新后的用户信息，格式同"获取当前用户信息"。

---

### 3. 获取用户列表

**接口名称**: 获取用户列表  
**功能描述**: 获取系统中所有用户的列表（仅超级用户）  
**接口地址**: `/api/v1/users/`  
**请求方式**: GET  
**认证**: 需要Bearer Token（超级用户）

#### 请求参数
| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|-------|------|-----|------|--------|
| page | int | 否 | 页码（默认1） | 1 |
| size | int | 否 | 每页数量（默认20，最大100） | 20 |
| search | string | 否 | 搜索关键词（用户名、邮箱、姓名） | test |
| status | string | 否 | 用户状态过滤 | active |

#### 响应参数
```json
{
  "users": [
    {
      "id": 1,
      "username": "testuser",
      "email": "test@example.com",
      "full_name": "测试用户",
      "status": "active",
      "is_superuser": false,
      "created_at": "2024-01-01T12:00:00Z"
    }
  ],
  "total": 100,
  "page": 1,
  "size": 20,
  "pages": 5
}
```

| 参数名 | 类型 | 说明 | 示例值 |
|-------|------|------|--------|
| users | array | 用户列表 | 见用户对象 |
| total | int | 总用户数 | 100 |
| page | int | 当前页码 | 1 |
| size | int | 每页数量 | 20 |
| pages | int | 总页数 | 5 |

---

### 4. 获取用户详情

**接口名称**: 获取用户详情  
**功能描述**: 获取指定用户的详细信息（仅超级用户）  
**接口地址**: `/api/v1/users/{user_id}`  
**请求方式**: GET  
**认证**: 需要Bearer Token（超级用户）

#### 请求参数
| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|-------|------|-----|------|--------|
| user_id | int | 是 | 用户ID（路径参数） | 1 |

#### 响应参数
返回用户详细信息，格式同"获取当前用户信息"。

#### 错误码
- `404`: 用户不存在
- `403`: 权限不足

---

### 5. 更新用户信息

**接口名称**: 更新用户信息  
**功能描述**: 更新指定用户的信息（仅超级用户）  
**接口地址**: `/api/v1/users/{user_id}`  
**请求方式**: PUT  
**认证**: 需要Bearer Token（超级用户）

#### 请求参数
| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|-------|------|-----|------|--------|
| user_id | int | 是 | 用户ID（路径参数） | 1 |

请求体格式同"更新当前用户信息"。

#### 响应参数
返回更新后的用户信息。

---

### 6. 删除用户

**接口名称**: 删除用户  
**功能描述**: 软删除指定用户（仅超级用户）  
**接口地址**: `/api/v1/users/{user_id}`  
**请求方式**: DELETE  
**认证**: 需要Bearer Token（超级用户）

#### 请求参数
| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|-------|------|-----|------|--------|
| user_id | int | 是 | 用户ID（路径参数） | 1 |

#### 响应参数
```json
{
  "message": "用户已删除"
}
```

---

### 7. 激活用户

**接口名称**: 激活用户  
**功能描述**: 激活指定用户账户（仅超级用户）  
**接口地址**: `/api/v1/users/{user_id}/activate`  
**请求方式**: POST  
**认证**: 需要Bearer Token（超级用户）

#### 请求参数
| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|-------|------|-----|------|--------|
| user_id | int | 是 | 用户ID（路径参数） | 1 |

#### 响应参数
```json
{
  "message": "用户已激活"
}
```

---

### 8. 停用用户

**接口名称**: 停用用户  
**功能描述**: 停用指定用户账户（仅超级用户）  
**接口地址**: `/api/v1/users/{user_id}/deactivate`  
**请求方式**: POST  
**认证**: 需要Bearer Token（超级用户）

#### 请求参数
| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|-------|------|-----|------|--------|
| user_id | int | 是 | 用户ID（路径参数） | 1 |

#### 响应参数
```json
{
  "message": "用户已停用"
}
```

---

### 9. 锁定用户

**接口名称**: 锁定用户  
**功能描述**: 临时锁定指定用户账户（仅超级用户）  
**接口地址**: `/api/v1/users/{user_id}/lock`  
**请求方式**: POST  
**认证**: 需要Bearer Token（超级用户）

#### 请求参数
| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|-------|------|-----|------|--------|
| user_id | int | 是 | 用户ID（路径参数） | 1 |
| duration_minutes | int | 否 | 锁定时长（分钟，默认30） | 60 |

#### 响应参数
```json
{
  "message": "用户已锁定 60 分钟"
}
```

---

### 10. 解锁用户

**接口名称**: 解锁用户  
**功能描述**: 解锁指定用户账户（仅超级用户）  
**接口地址**: `/api/v1/users/{user_id}/unlock`  
**请求方式**: POST  
**认证**: 需要Bearer Token（超级用户）

#### 请求参数
| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|-------|------|-----|------|--------|
| user_id | int | 是 | 用户ID（路径参数） | 1 |

#### 响应参数
```json
{
  "message": "用户已解锁"
}
```

---

### 11. 获取用户统计

**接口名称**: 获取用户统计  
**功能描述**: 获取用户相关的统计信息（仅超级用户）  
**接口地址**: `/api/v1/users/stats/overview`  
**请求方式**: GET  
**认证**: 需要Bearer Token（超级用户）

#### 请求参数
无

#### 响应参数
```json
{
  "total_users": 1000,
  "active_users": 950,
  "new_users_today": 5,
  "new_users_this_week": 25,
  "new_users_this_month": 100,
  "login_count_today": 200,
  "login_count_this_week": 1200,
  "login_count_this_month": 5000
}
```

| 参数名 | 类型 | 说明 | 示例值 |
|-------|------|------|--------|
| total_users | int | 总用户数 | 1000 |
| active_users | int | 活跃用户数 | 950 |
| new_users_today | int | 今日新增用户 | 5 |
| new_users_this_week | int | 本周新增用户 | 25 |
| new_users_this_month | int | 本月新增用户 | 100 |
| login_count_today | int | 今日登录次数 | 200 |
| login_count_this_week | int | 本周登录次数 | 1200 |
| login_count_this_month | int | 本月登录次数 | 5000 |

## 🔧 使用示例

### 用户自我管理
```bash
# 获取当前用户信息
curl -X GET "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# 更新当前用户信息
curl -X PUT "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "新的姓名",
    "bio": "更新的个人简介",
    "theme": "dark"
  }'
```

### 管理员用户管理
```bash
# 获取用户列表
curl -X GET "http://localhost:8000/api/v1/users/?page=1&size=20&search=test" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"

# 激活用户
curl -X POST "http://localhost:8000/api/v1/users/1/activate" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"

# 锁定用户60分钟
curl -X POST "http://localhost:8000/api/v1/users/1/lock?duration_minutes=60" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"

# 获取用户统计
curl -X GET "http://localhost:8000/api/v1/users/stats/overview" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"
```

## 🚨 注意事项

1. **权限控制**: 普通用户只能管理自己的信息，管理员可以管理所有用户
2. **软删除**: 删除用户采用软删除方式，数据不会真正删除
3. **状态管理**: 用户状态包括 active（活跃）、inactive（停用）、locked（锁定）
4. **搜索功能**: 支持按用户名、邮箱、姓名进行模糊搜索
5. **分页查询**: 用户列表支持分页，建议合理设置每页数量
