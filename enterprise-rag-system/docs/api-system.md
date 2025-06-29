# 系统管理模块 API 文档

## 📋 模块概述

系统管理模块提供系统信息查询、健康检查、监控数据、配置管理等功能，用于系统运维和状态监控。

**基础路径**: `/api/v1/system` 和 `/api/v1/admin`

## 🔐 权限说明

- **系统信息**: 所有用户可访问
- **健康检查**: 所有用户可访问
- **管理功能**: 需要管理员权限
- **监控数据**: 需要相应权限

## 📚 接口列表

### 1. 获取系统信息

**接口名称**: 获取系统信息  
**功能描述**: 获取系统基本信息和版本  
**接口地址**: `/api/v1/system/info`  
**请求方式**: GET  
**认证**: 无需认证

#### 请求参数
无

#### 响应参数
```json
{
  "name": "企业级Agent+RAG知识库系统",
  "version": "1.0.0",
  "description": "基于多智能体协作的企业级知识库系统",
  "build_time": "2024-01-01T12:00:00Z",
  "git_commit": "abc123def456",
  "environment": "production",
  "api_version": "v1",
  "supported_features": [
    "knowledge_base",
    "document_processing",
    "vector_search",
    "graph_search",
    "multi_agent",
    "rbac"
  ]
}
```

| 参数名 | 类型 | 说明 | 示例值 |
|-------|------|------|--------|
| name | string | 系统名称 | 企业级Agent+RAG知识库系统 |
| version | string | 系统版本 | 1.0.0 |
| description | string | 系统描述 | 基于多智能体协作... |
| build_time | string | 构建时间 | 2024-01-01T12:00:00Z |
| git_commit | string | Git提交哈希 | abc123def456 |
| environment | string | 运行环境 | production |
| api_version | string | API版本 | v1 |
| supported_features | array | 支持的功能 | 见功能列表 |

---

### 2. 健康检查

**接口名称**: 健康检查  
**功能描述**: 检查系统各组件的健康状态  
**接口地址**: `/api/v1/system/health` 或 `/health`  
**请求方式**: GET  
**认证**: 无需认证

#### 请求参数
无

#### 响应参数
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "uptime": 86400,
  "version": "1.0.0",
  "checks": {
    "database": {
      "status": "healthy",
      "response_time": 5,
      "details": {
        "connection_pool": "8/20",
        "active_connections": 8
      }
    },
    "redis": {
      "status": "healthy",
      "response_time": 2,
      "details": {
        "memory_usage": "45%",
        "connected_clients": 12
      }
    },
    "milvus": {
      "status": "healthy",
      "response_time": 15,
      "details": {
        "collections": 5,
        "total_vectors": 150000
      }
    },
    "neo4j": {
      "status": "healthy",
      "response_time": 8,
      "details": {
        "nodes": 25000,
        "relationships": 45000
      }
    },
    "llm_service": {
      "status": "healthy",
      "response_time": 200,
      "details": {
        "model": "deepseek-chat",
        "api_quota": "80%"
      }
    }
  }
}
```

| 参数名 | 类型 | 说明 | 示例值 |
|-------|------|------|--------|
| status | string | 整体状态 | healthy/unhealthy |
| timestamp | string | 检查时间 | 2024-01-01T12:00:00Z |
| uptime | int | 运行时间（秒） | 86400 |
| version | string | 系统版本 | 1.0.0 |
| checks | object | 各组件检查结果 | 见检查对象 |

#### 组件状态说明
- `healthy`: 健康
- `unhealthy`: 不健康
- `degraded`: 性能下降
- `unknown`: 状态未知

---

### 3. 系统统计

**接口名称**: 系统统计  
**功能描述**: 获取系统使用统计信息  
**接口地址**: `/api/v1/admin/stats`  
**请求方式**: GET  
**认证**: 需要Bearer Token（管理员）

#### 请求参数
| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|-------|------|-----|------|--------|
| period | string | 否 | 统计周期（day/week/month） | day |

#### 响应参数
```json
{
  "period": "day",
  "timestamp": "2024-01-01T12:00:00Z",
  "users": {
    "total": 1000,
    "active_today": 150,
    "new_today": 5,
    "online_now": 25
  },
  "knowledge_bases": {
    "total": 50,
    "public": 20,
    "private": 30,
    "created_today": 2
  },
  "documents": {
    "total": 5000,
    "processed_today": 25,
    "total_size_gb": 120.5,
    "processing_queue": 3
  },
  "conversations": {
    "total": 15000,
    "today": 200,
    "active_sessions": 15
  },
  "api_requests": {
    "total_today": 10000,
    "successful": 9800,
    "failed": 200,
    "avg_response_time": 250
  },
  "system_resources": {
    "cpu_usage": 45.2,
    "memory_usage": 68.5,
    "disk_usage": 35.8,
    "network_io": {
      "in_mbps": 12.5,
      "out_mbps": 8.3
    }
  }
}
```

---

### 4. 系统配置

**接口名称**: 获取系统配置  
**功能描述**: 获取系统配置信息  
**接口地址**: `/api/v1/admin/config`  
**请求方式**: GET  
**认证**: 需要Bearer Token（管理员）

#### 请求参数
无

#### 响应参数
```json
{
  "system": {
    "debug": false,
    "log_level": "INFO",
    "max_upload_size": 104857600,
    "session_timeout": 3600
  },
  "database": {
    "pool_size": 20,
    "max_overflow": 10,
    "pool_timeout": 30
  },
  "ai_services": {
    "llm_model": "deepseek-chat",
    "embedding_model": "text-embedding-ada-002",
    "max_tokens": 4000,
    "temperature": 0.7
  },
  "search": {
    "default_top_k": 10,
    "score_threshold": 0.5,
    "enable_rerank": true
  },
  "security": {
    "jwt_expire_minutes": 60,
    "password_min_length": 8,
    "max_login_attempts": 5
  }
}
```

---

### 5. 更新系统配置

**接口名称**: 更新系统配置  
**功能描述**: 更新系统配置参数  
**接口地址**: `/api/v1/admin/config`  
**请求方式**: PUT  
**认证**: 需要Bearer Token（超级管理员）

#### 请求参数
```json
{
  "system": {
    "log_level": "DEBUG",
    "max_upload_size": 209715200
  },
  "ai_services": {
    "temperature": 0.8,
    "max_tokens": 5000
  }
}
```

#### 响应参数
```json
{
  "message": "配置更新成功",
  "updated_configs": [
    "system.log_level",
    "system.max_upload_size",
    "ai_services.temperature",
    "ai_services.max_tokens"
  ],
  "restart_required": false
}
```

---

### 6. 系统日志

**接口名称**: 获取系统日志  
**功能描述**: 获取系统运行日志  
**接口地址**: `/api/v1/admin/logs`  
**请求方式**: GET  
**认证**: 需要Bearer Token（管理员）

#### 请求参数
| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|-------|------|-----|------|--------|
| level | string | 否 | 日志级别过滤 | ERROR |
| start_time | string | 否 | 开始时间 | 2024-01-01T00:00:00Z |
| end_time | string | 否 | 结束时间 | 2024-01-01T23:59:59Z |
| page | int | 否 | 页码 | 1 |
| size | int | 否 | 每页数量 | 100 |

#### 响应参数
```json
{
  "logs": [
    {
      "timestamp": "2024-01-01T12:00:00Z",
      "level": "INFO",
      "logger": "app.api.chat",
      "message": "用户发起聊天请求",
      "user_id": 123,
      "request_id": "req_456789",
      "extra": {
        "conversation_id": 1,
        "processing_time": 2.5
      }
    }
  ],
  "total": 1000,
  "page": 1,
  "size": 100,
  "pages": 10
}
```

---

### 7. 清理缓存

**接口名称**: 清理系统缓存  
**功能描述**: 清理指定类型的系统缓存  
**接口地址**: `/api/v1/admin/cache/clear`  
**请求方式**: POST  
**认证**: 需要Bearer Token（管理员）

#### 请求参数
```json
{
  "cache_types": ["redis", "memory", "search"],
  "force": false
}
```

| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|-------|------|-----|------|--------|
| cache_types | array | 是 | 缓存类型列表 | ["redis", "memory"] |
| force | bool | 否 | 是否强制清理 | false |

#### 缓存类型说明
- `redis`: Redis缓存
- `memory`: 内存缓存
- `search`: 搜索缓存
- `session`: 会话缓存

#### 响应参数
```json
{
  "message": "缓存清理完成",
  "cleared_caches": ["redis", "memory", "search"],
  "cleared_keys": 1500,
  "freed_memory_mb": 256
}
```

---

### 8. 系统维护

**接口名称**: 系统维护模式  
**功能描述**: 启用或禁用系统维护模式  
**接口地址**: `/api/v1/admin/maintenance`  
**请求方式**: POST  
**认证**: 需要Bearer Token（超级管理员）

#### 请求参数
```json
{
  "enabled": true,
  "message": "系统正在进行维护升级，预计30分钟后恢复",
  "allowed_ips": ["192.168.1.100", "10.0.0.50"]
}
```

| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|-------|------|-----|------|--------|
| enabled | bool | 是 | 是否启用维护模式 | true |
| message | string | 否 | 维护提示信息 | 系统正在维护... |
| allowed_ips | array | 否 | 允许访问的IP列表 | ["192.168.1.100"] |

#### 响应参数
```json
{
  "message": "维护模式已启用",
  "maintenance_enabled": true,
  "start_time": "2024-01-01T12:00:00Z",
  "allowed_ips": ["192.168.1.100", "10.0.0.50"]
}
```

## 🔧 使用示例

### 基础系统管理
```bash
# 1. 获取系统信息
curl -X GET "http://localhost:8000/api/v1/system/info"

# 2. 健康检查
curl -X GET "http://localhost:8000/health"

# 3. 获取系统统计（需要管理员权限）
curl -X GET "http://localhost:8000/api/v1/admin/stats?period=day" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"

# 4. 获取系统配置
curl -X GET "http://localhost:8000/api/v1/admin/config" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"

# 5. 更新配置
curl -X PUT "http://localhost:8000/api/v1/admin/config" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "system": {
      "log_level": "DEBUG"
    }
  }'

# 6. 清理缓存
curl -X POST "http://localhost:8000/api/v1/admin/cache/clear" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "cache_types": ["redis", "memory"]
  }'

# 7. 启用维护模式
curl -X POST "http://localhost:8000/api/v1/admin/maintenance" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": true,
    "message": "系统维护中，请稍后访问"
  }'
```

### 监控和日志查询
```bash
# 查询错误日志
curl -X GET "http://localhost:8000/api/v1/admin/logs?level=ERROR&page=1&size=50" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"

# 查询指定时间范围的日志
curl -X GET "http://localhost:8000/api/v1/admin/logs?start_time=2024-01-01T00:00:00Z&end_time=2024-01-01T23:59:59Z" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"
```

## 🚨 注意事项

1. **权限控制**: 管理功能需要相应的管理员权限
2. **维护模式**: 启用维护模式会影响普通用户访问
3. **配置更新**: 某些配置更新可能需要重启服务
4. **缓存清理**: 清理缓存可能暂时影响系统性能
5. **日志查询**: 大量日志查询可能影响系统性能
6. **健康检查**: 可用于负载均衡器的健康检查
7. **统计数据**: 统计数据可能有一定延迟
