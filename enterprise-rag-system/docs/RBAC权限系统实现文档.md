# RBAC权限系统实现文档

## 📋 概述

本文档详细介绍了企业RAG系统中RBAC（基于角色的访问控制）权限系统的完整实现，包括数据库设计、后端API、前端组件和集成方案。

## 🏗️ 系统架构

### 核心组件

1. **数据模型层**：基于tortoise-orm的RBAC数据模型
2. **API服务层**：FastAPI实现的权限管理接口
3. **前端组件层**：React + Ant Design的权限控制组件
4. **权限中间件**：统一的权限检查和路由保护

### 技术栈

- **后端**：FastAPI + tortoise-orm + MySQL
- **前端**：React 18 + TypeScript + Ant Design
- **认证**：JWT Token
- **数据库**：MySQL 8.0

## 📊 数据库设计

### 核心表结构

#### 1. 用户表 (users)
```sql
- id: 主键
- username: 用户名
- email: 邮箱
- password_hash: 密码哈希
- is_superuser: 是否超级用户
- department_id: 所属部门ID
- status: 用户状态
- created_at/updated_at: 时间戳
```

#### 2. 角色表 (roles)
```sql
- id: 主键
- name: 角色名称
- code: 角色代码
- description: 角色描述
- role_type: 角色类型(system/custom)
- data_scope: 数据权限范围
- parent_id: 父角色ID
- level: 角色层级
- status: 角色状态
```

#### 3. 权限表 (permissions)
```sql
- id: 主键
- name: 权限名称
- code: 权限代码
- group: 权限分组
- resource: 资源
- action: 操作
- permission_type: 权限类型(menu/api/button)
- menu_path: 菜单路径
- menu_icon: 菜单图标
- parent_id: 父权限ID
```

#### 4. 部门表 (departments)
```sql
- id: 主键
- name: 部门名称
- code: 部门代码
- parent_id: 父部门ID
- level: 部门层级
- manager_id: 部门负责人ID
```

#### 5. 关联表
- **user_roles**: 用户角色关联
- **role_permissions**: 角色权限关联
- **user_permissions**: 用户直接权限关联
- **role_departments**: 角色部门关联

## 🔧 后端实现

### 1. 数据模型

#### 核心模型文件
- `app/models/rbac.py`: RBAC核心模型
- `app/models/user.py`: 用户模型扩展

#### 关键特性
- 支持角色继承和层级结构
- 支持权限的直接分配和拒绝
- 支持数据权限范围控制
- 支持权限过期时间

### 2. API接口

#### 权限管理API (`/api/v1/rbac/`)
```python
# 部门管理
GET    /departments          # 获取部门列表
POST   /departments          # 创建部门
PUT    /departments/{id}     # 更新部门
DELETE /departments/{id}     # 删除部门

# 角色管理
GET    /roles               # 获取角色列表
POST   /roles               # 创建角色
PUT    /roles/{id}          # 更新角色
DELETE /roles/{id}          # 删除角色

# 权限管理
GET    /permissions         # 获取权限列表
POST   /permissions         # 创建权限
PUT    /permissions/{id}    # 更新权限
DELETE /permissions/{id}    # 删除权限

# 用户角色分配
POST   /user-roles          # 分配用户角色
GET    /users/{id}/roles    # 获取用户角色

# 权限检查
POST   /check-permissions   # 批量检查权限
GET    /menu-tree          # 获取菜单树
```

### 3. 权限检查装饰器

```python
from app.core import PermissionChecker, RoleChecker


# 权限检查
@router.get("/users")
async def get_users(
        current_user: User = Depends(PermissionChecker("user:view"))
):
    pass


# 角色检查
@router.get("/admin")
async def admin_panel(
        current_user: User = Depends(RoleChecker("admin"))
):
    pass
```

### 4. 数据权限控制

```python
# 获取用户数据权限范围
async def get_user_data_scope(user: User) -> List[Department]:
    return await user.get_data_scope_departments()

# 根据数据权限过滤查询
async def filter_by_data_scope(user: User, query):
    accessible_depts = await user.get_data_scope_departments()
    dept_ids = [dept.id for dept in accessible_depts]
    return query.filter(department_id__in=dept_ids)
```

## 🎨 前端实现

### 1. 权限上下文

#### PermissionContext
```typescript
// 权限上下文提供者
<PermissionProvider>
  <App />
</PermissionProvider>

// 使用权限Hook
const { hasPermission, hasRole } = usePermissions();
const canEdit = hasPermission('user:edit');
const isAdmin = hasRole('admin');
```

### 2. 权限控制组件

#### PermissionGuard
```typescript
// 页面级权限控制
<PermissionGuard permission="user:manage">
  <UserManagementPage />
</PermissionGuard>

// 组件级权限控制
<PermissionGuard permission={["user:view", "user:edit"]} requireAll={false}>
  <UserEditForm />
</PermissionGuard>
```

#### PermissionButton
```typescript
// 按钮权限控制
<PermissionButton permission="user:delete" onClick={handleDelete}>
  删除用户
</PermissionButton>
```

### 3. 管理界面

#### 角色管理 (`RoleManagement.tsx`)
- 角色列表展示
- 角色创建/编辑
- 权限分配
- 角色删除

#### 权限管理 (`PermissionManagement.tsx`)
- 权限列表展示
- 权限创建/编辑
- 权限分组管理
- 菜单权限配置

#### 用户角色分配 (`UserRoleAssignment.tsx`)
- 用户列表展示
- 角色分配界面
- 数据权限配置
- 过期时间设置

## 🚀 部署和初始化

### 1. 数据库初始化

```bash
# 运行数据库初始化脚本
cd backend
python init_rbac_db.py
```

### 2. 基础数据创建

系统会自动创建以下基础数据：

#### 默认角色
- **超级管理员** (super_admin): 拥有所有权限
- **系统管理员** (admin): 拥有系统管理权限
- **部门管理员** (dept_admin): 拥有部门数据权限
- **普通用户** (user): 拥有基础功能权限
- **访客** (guest): 只有查看权限

#### 权限分组
- 系统管理 (system)
- 用户管理 (user)
- 角色管理 (role)
- 权限管理 (permission)
- 部门管理 (department)
- 知识库管理 (knowledge)
- 文档管理 (document)
- 聊天功能 (chat)
- 搜索功能 (search)
- 监控管理 (monitor)

### 3. 测试验证

```bash
# 运行RBAC系统测试
python test_rbac.py

# 查看测试报告
cat rbac_test_report.json
```

## 🔒 安全特性

### 1. 权限继承
- 支持角色层级结构
- 子角色自动继承父角色权限
- 支持权限覆盖和拒绝

### 2. 数据权限
- 全部数据权限
- 本部门数据权限
- 本部门及子部门数据权限
- 自定义数据权限

### 3. 权限缓存
- 用户权限缓存
- 角色权限缓存
- 菜单权限缓存

### 4. 审计日志
- 权限变更记录
- 用户操作日志
- 登录审计

## 📝 使用示例

### 1. 后端权限检查

```python
from app.core import PermissionChecker


@router.post("/knowledge-bases")
async def create_knowledge_base(
        data: CreateKnowledgeBaseRequest,
        current_user: User = Depends(PermissionChecker("knowledge:create"))
):
    # 创建知识库逻辑
    pass
```

### 2. 前端权限控制

```typescript
import { PermissionGuard } from '@/components/common/PermissionGuard';

function KnowledgeBasePage() {
  return (
    <div>
      <PermissionGuard permission="knowledge:view">
        <KnowledgeBaseList />
      </PermissionGuard>
      
      <PermissionGuard permission="knowledge:create">
        <CreateKnowledgeBaseButton />
      </PermissionGuard>
    </div>
  );
}
```

### 3. 菜单权限控制

```typescript
import { usePermissions } from '@/contexts/PermissionContext';

function Navigation() {
  const { hasPermission } = usePermissions();
  
  return (
    <Menu>
      {hasPermission('user:manage') && (
        <Menu.Item key="users">用户管理</Menu.Item>
      )}
      {hasPermission('knowledge:manage') && (
        <Menu.Item key="knowledge">知识库管理</Menu.Item>
      )}
    </Menu>
  );
}
```

## 🔧 配置说明

### 1. 环境变量

```bash
# 数据库配置
DATABASE_URL=mysql+aiomysql://user:password@host:port/database

# JWT配置
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS配置
BACKEND_CORS_ORIGINS=["http://localhost:3000"]
```

### 2. 权限配置

权限代码格式：`{resource}:{action}`
- 资源：user, role, permission, knowledge, document, chat等
- 操作：view, create, update, delete, manage等

### 3. 数据权限配置

- `all`: 全部数据权限
- `dept`: 本部门数据权限
- `dept_and_child`: 本部门及子部门数据权限
- `custom`: 自定义数据权限

## 📚 扩展指南

### 1. 添加新权限

1. 在数据库中添加权限记录
2. 为相关角色分配权限
3. 在API中添加权限检查
4. 在前端添加权限控制

### 2. 自定义权限检查

```python
async def custom_permission_check(user: User, resource_id: int) -> bool:
    # 自定义权限检查逻辑
    if user.is_superuser:
        return True
    
    # 检查资源所有权
    resource = await Resource.get(id=resource_id)
    if resource.owner_id == user.id:
        return True
    
    # 检查部门权限
    user_depts = await user.get_data_scope_departments()
    if resource.department_id in [dept.id for dept in user_depts]:
        return True
    
    return False
```

### 3. 集成第三方认证

系统支持集成LDAP、OAuth2等第三方认证系统，只需实现相应的认证适配器即可。

## 🐛 故障排除

### 常见问题

1. **权限检查失败**
   - 检查用户是否有对应角色
   - 检查角色是否有对应权限
   - 检查权限代码是否正确

2. **菜单不显示**
   - 检查菜单权限配置
   - 检查前端权限上下文
   - 检查API返回数据

3. **数据权限异常**
   - 检查用户部门配置
   - 检查角色数据权限范围
   - 检查部门层级结构

## 📞 技术支持

如有问题，请参考：
1. 系统日志文件
2. 测试报告文件
3. API文档
4. 前端控制台错误信息

---

**注意**：本RBAC系统已完全集成到企业RAG系统中，支持知识库、文档、聊天等所有业务模块的权限控制。
