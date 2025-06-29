# 企业级RAG知识库系统 API 总览

## 📋 系统概述

企业级Agent+RAG知识库系统是基于多智能体协作的企业级知识库系统，提供完整的知识管理、智能问答、文档处理和权限管理功能。

## 🏗️ API架构设计

### 基础信息
- **API版本**: v1
- **基础路径**: `/api/v1`
- **请求格式**: JSON
- **响应格式**: JSON
- **字符编码**: UTF-8
- **时间格式**: ISO 8601 (YYYY-MM-DDTHH:mm:ssZ)

### 认证方式
- **认证类型**: JWT Bearer Token
- **Token获取**: POST `/api/v1/auth/login`
- **Token刷新**: POST `/api/v1/auth/refresh`
- **权限控制**: 基于RBAC权限模型

### 统一响应格式
```json
{
  "success": true,
  "code": 200,
  "message": "操作成功",
  "data": {},
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## 📚 API模块概览

### 1. 认证模块 (`/auth`)
- 用户注册、登录、登出
- JWT令牌管理
- 密码重置

### 2. 用户管理 (`/users`)
- 用户信息CRUD
- 用户权限管理
- 用户状态控制

### 3. 知识库管理 (`/knowledge-bases`)
- 知识库创建、查询、更新、删除
- 知识库权限控制
- 知识库统计信息

### 4. 文档管理 (`/documents`)
- 文档上传、处理
- 文档查询、下载
- 文档元数据管理

### 5. 对话管理 (`/conversations`)
- 对话创建、查询
- 消息历史管理
- 对话上下文维护

### 6. 聊天接口 (`/chat`)
- 实时聊天
- 流式聊天
- 多模态对话

### 7. 搜索接口 (`/search`)
- 向量搜索
- 图谱搜索
- 混合搜索

### 8. 多智能体协作 (`/autogen`)
- AutoGen多智能体聊天
- 智能体协作配置
- 任务分发与执行

### 9. 权限管理 (`/rbac`)
- 角色权限管理
- 部门管理
- 权限检查

### 10. 系统管理 (`/system`, `/admin`)
- 系统信息查询
- 健康检查
- 系统配置

### 11. 监控管理 (`/monitoring`, `/dashboard`)
- 系统监控
- 性能指标
- 监控仪表板

### 12. 高级功能
- 高级搜索 (`/advanced-search`)
- 知识图谱 (`/graph`)
- 缓存管理 (`/cache`)
- 文件上传 (`/upload`)

## 🔗 快速导航

| 模块 | 文档链接 | 主要功能 |
|------|----------|----------|
| 认证模块 | [api-auth.md](./api-auth.md) | 用户认证、授权 |
| 用户管理 | [api-users.md](./api-users.md) | 用户CRUD、权限 |
| 知识库管理 | [api-knowledge-bases.md](./api-knowledge-bases.md) | 知识库管理 |
| 文档管理 | [api-documents.md](./api-documents.md) | 文档处理、存储 |
| 对话管理 | [api-conversations.md](./api-conversations.md) | 对话历史管理 |
| 聊天接口 | [api-chat.md](./api-chat.md) | 智能问答 |
| 搜索接口 | [api-search.md](./api-search.md) | 多种搜索方式 |
| 多智能体 | [api-autogen.md](./api-autogen.md) | 智能体协作 |
| 权限管理 | [api-rbac.md](./api-rbac.md) | RBAC权限系统 |
| 系统管理 | [api-system.md](./api-system.md) | 系统信息、监控 |

## 🚀 快速开始

### 1. 获取访问令牌
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "password"
  }'
```

### 2. 使用令牌访问API
```bash
curl -X GET "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 3. 创建知识库
```bash
curl -X POST "http://localhost:8000/api/v1/knowledge-bases" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "我的知识库",
    "description": "测试知识库",
    "is_public": false
  }'
```

## 📖 文档说明

每个API模块的详细文档包含：
- 接口列表和基本信息
- 请求参数详细说明
- 响应格式和字段说明
- 错误码和处理方式
- 完整的请求示例
- 业务流程图（如适用）

## 🔧 开发工具

- **API文档**: http://localhost:8000/docs (Swagger UI)
- **ReDoc文档**: http://localhost:8000/redoc
- **健康检查**: http://localhost:8000/health
- **API信息**: http://localhost:8000/api/v1/

## 📞 技术支持

如有问题，请参考：
1. 各模块的详细API文档
2. 系统架构设计文档
3. RBAC权限系统文档
4. 智能RAG需求文档
