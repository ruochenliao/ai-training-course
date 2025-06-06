# 接口文档

## API模块

### 查看API列表
- 功能描述: 查看所有可用的API接口列表，支持分页和条件筛选。
- 入参:
  - `page`: `int` - 页码，默认为1
  - `page_size`: `int` - 每页数量，默认为10
  - `path`: `str` - API路径，用于搜索，可选
  - `summary`: `str` - API简介，用于搜索，可选
  - `tags`: `str` - API模块，用于搜索，可选
- 返回参数:
  - `data`: `list` - API对象列表
    - `id`: `int` - API ID
    - `path`: `str` - API路径
    - `method`: `str` - 请求方法
    - `summary`: `str` - API简介
    - `tags`: `str` - API模块
  - `total`: `int` - 总数量
  - `page`: `int` - 当前页码
  - `page_size`: `int` - 每页数量
- url地址: `/api/v1/api/list`
- 请求方式: `GET`

### 查看Api
- 功能描述: 根据API ID获取单个API的详细信息。
- 入参:
  - `id`: `int` - Api ID
- 返回参数:
  - `data`: `object` - API对象
    - `id`: `int` - API ID
    - `path`: `str` - API路径
    - `method`: `str` - 请求方法
    - `summary`: `str` - API简介
    - `tags`: `str` - API模块
- url地址: `/api/v1/api/get`
- 请求方式: `GET`

### 创建Api
- 功能描述: 创建一个新的API接口。
- 入参:
  - `api_in`: `ApiCreate` - API创建信息
    - `path`: `str` - API路径
    - `method`: `str` - 请求方法
    - `summary`: `str` - API简介
    - `tags`: `str` - API模块
- 返回参数:
  - `msg`: `str` - 操作结果信息
- url地址: `/api/v1/api/create`
- 请求方式: `POST`

### 更新Api
- 功能描述: 根据API ID更新现有的API接口信息。
- 入参:
  - `api_in`: `ApiUpdate` - API更新信息
    - `id`: `int` - API ID
    - `path`: `str` - API路径 (可选)
    - `method`: `str` - 请求方法 (可选)
    - `summary`: `str` - API简介 (可选)
    - `tags`: `str` - API模块 (可选)
- 返回参数:
  - `msg`: `str` - 操作结果信息
- url地址: `/api/v1/api/update`
- 请求方式: `POST`

### 删除Api
- 功能描述: 根据API ID删除一个API接口。
- 入参:
  - `api_id`: `int` - ApiID
- 返回参数:
  - `msg`: `str` - 操作结果信息
- url地址: `/api/v1/api/delete`
- 请求方式: `DELETE`

### 刷新API列表
- 功能描述: 刷新系统中的API列表，通常在新增或修改路由后调用。
- 入参: 无
- 返回参数:
  - `msg`: `str` - 操作结果信息
- url地址: `/api/v1/api/refresh`
- 请求方式: `POST`

## 操作日志模块

### 查看操作日志
- 功能描述: 查看系统操作日志，支持分页和多种条件筛选。
- 入参:
  - `page`: `int` - 页码，默认为1
  - `page_size`: `int` - 每页数量，默认为10
  - `username`: `str` - 操作人名称，可选
  - `module`: `str` - 功能模块，可选
  - `method`: `str` - 请求方法，可选
  - `summary`: `str` - 接口描述，可选
  - `status`: `int` - 状态码，可选
  - `start_time`: `datetime` - 开始时间，可选
  - `end_time`: `datetime` - 结束时间，可选
- 返回参数:
  - `data`: `list` - 日志对象列表
    - `id`: `int` - 日志ID
    - `username`: `str` - 操作人
    - `module`: `str` - 功能模块
    - `method`: `str` - 请求方法
    - `summary`: `str` - 接口描述
    - `path`: `str` - 请求路径
    - `params`: `dict` - 请求参数
    - `status_code`: `int` - 状态码
    - `response`: `dict` - 响应内容
    - `ip`: `str` - IP地址
    - `user_agent`: `str` - 用户代理
    - `created_at`: `datetime` - 创建时间
  - `total`: `int` - 总数量
  - `page`: `int` - 当前页码
  - `page_size`: `int` - 每页数量
- url地址: `/api/v1/auditlog/list`
- 请求方式: `GET`

## 基础模块

### 获取token
- 功能描述: 用户登录并获取访问令牌 (access_token)。
- 入参:
  - `credentials`: `CredentialsSchema` - 凭证信息
    - `username`: `str` - 用户名
    - `password`: `str` - 密码
- 返回参数:
  - `data`: `object` - JWT输出信息
    - `access_token`: `str` - 访问令牌
    - `username`: `str` - 用户名
- url地址: `/api/v1/base/access_token`
- 请求方式: `POST`

### 查看用户信息
- 功能描述: 获取当前登录用户的详细信息。
- 入参: 无 (通过请求头中的Authorization Bearer Token进行认证)
- 返回参数:
  - `data`: `object` - 用户信息对象 (不含密码)
    - `id`: `int` - 用户ID
    - `username`: `str` - 用户名
    - `email`: `str` - 邮箱
    - `is_active`: `bool` - 是否激活
    - `is_superuser`: `bool` - 是否超级用户
    - `avatar`: `str` - 用户头像URL
    - `last_login`: `datetime` - 上次登录时间
    - `created_at`: `datetime` - 创建时间
    - `updated_at`: `datetime` - 更新时间
    - `dept_id`: `int` - 部门ID (可选)
    - `roles`: `list` - 角色列表 (可选)
- url地址: `/api/v1/base/userinfo`
- 请求方式: `GET`

### 查看用户菜单
- 功能描述: 获取当前登录用户的菜单权限列表。
- 入参: 无 (通过请求头中的Authorization Bearer Token进行认证)
- 返回参数:
  - `data`: `list` - 菜单树形结构列表
    - `id`: `int` - 菜单ID
    - `name`: `str` - 菜单名称
    - `path`: `str` - 路由路径
    - `component`: `str` - 组件路径
    - `icon`: `str` - 图标
    - `order`: `int` - 排序
    - `is_visible`: `bool` - 是否可见
    - `parent_id`: `int` - 父菜单ID
    - `children`: `list` - 子菜单列表 (递归结构)
- url地址: `/api/v1/base/usermenu`
- 请求方式: `GET`

### 查看用户API
- 功能描述: 获取当前登录用户的API权限列表。
- 入参: 无 (通过请求头中的Authorization Bearer Token进行认证)
- 返回参数:
  - `data`: `list` - API路径列表 (格式: 'method/path')
- url地址: `/api/v1/base/userapi`
- 请求方式: `GET`

### 修改密码
- 功能描述: 当前登录用户修改自己的密码。
- 入参:
  - `req_in`: `UpdatePassword` - 更新密码请求体
    - `old_password`: `str` - 旧密码
    - `new_password`: `str` - 新密码
- 返回参数:
  - `msg`: `str` - 操作结果信息
- url地址: `/api/v1/base/update_password`
- 请求方式: `POST`

## 部门模块

### 查看部门列表
- 功能描述: 获取部门列表，支持按名称筛选，返回树形结构。
- 入参:
  - `name`: `str` - 部门名称，用于搜索，可选
- 返回参数:
  - `data`: `list` - 部门树形结构列表
    - `id`: `int` - 部门ID
    - `name`: `str` - 部门名称
    - `parent_id`: `int` - 父部门ID
    - `order`: `int` - 排序
    - `children`: `list` - 子部门列表 (递归结构)
- url地址: `/api/v1/dept/list`
- 请求方式: `GET`

### 查看部门
- 功能描述: 根据部门ID获取单个部门的详细信息。
- 入参:
  - `id`: `int` - 部门ID
- 返回参数:
  - `data`: `object` - 部门对象
    - `id`: `int` - 部门ID
    - `name`: `str` - 部门名称
    - `parent_id`: `int` - 父部门ID
    - `order`: `int` - 排序
    - `remark`: `str` - 备注
- url地址: `/api/v1/dept/get`
- 请求方式: `GET`

### 创建部门
- 功能描述: 创建一个新的部门。
- 入参:
  - `dept_in`: `DeptCreate` - 部门创建信息
    - `name`: `str` - 部门名称
    - `parent_id`: `int` - 父部门ID (0表示顶级部门)
    - `order`: `int` - 排序
    - `remark`: `str` - 备注 (可选)
- 返回参数:
  - `msg`: `str` - 操作结果信息
- url地址: `/api/v1/dept/create`
- 请求方式: `POST`

### 更新部门
- 功能描述: 根据部门ID更新现有的部门信息。
- 入参:
  - `dept_in`: `DeptUpdate` - 部门更新信息
    - `id`: `int` - 部门ID
    - `name`: `str` - 部门名称 (可选)
    - `parent_id`: `int` - 父部门ID (可选)
    - `order`: `int` - 排序 (可选)
    - `remark`: `str` - 备注 (可选)
- 返回参数:
  - `msg`: `str` - 操作结果信息
- url地址: `/api/v1/dept/update`
- 请求方式: `POST`

### 删除部门
- 功能描述: 根据部门ID删除一个部门。
- 入参:
  - `dept_id`: `int` - 部门ID
- 返回参数:
  - `msg`: `str` - 操作结果信息
- url地址: `/api/v1/dept/delete`
- 请求方式: `DELETE`

## 菜单模块

### 查看菜单列表
- 功能描述: 获取菜单列表，返回树形结构，支持分页 (实际未分页，返回全量树)。
- 入参:
  - `page`: `int` - 页码 (未使用)
  - `page_size`: `int` - 每页数量 (未使用)
- 返回参数:
  - `data`: `list` - 菜单树形结构列表
    - `id`: `int` - 菜单ID
    - `name`: `str` - 菜单名称
    - `path`: `str` - 路由路径
    - `component`: `str` - 组件路径
    - `icon`: `str` - 图标
    - `order`: `int` - 排序
    - `is_visible`: `bool` - 是否可见
    - `parent_id`: `int` - 父菜单ID
    - `children`: `list` - 子菜单列表 (递归结构)
  - `total`: `int` - 总数量 (顶层菜单数量)
  - `page`: `int` - 当前页码
  - `page_size`: `int` - 每页数量
- url地址: `/api/v1/menu/list`
- 请求方式: `GET`

### 查看菜单
- 功能描述: 根据菜单ID获取单个菜单的详细信息。
- 入参:
  - `menu_id`: `int` - 菜单id
- 返回参数:
  - `data`: `object` - 菜单对象
    - `id`: `int` - 菜单ID
    - `name`: `str` - 菜单名称
    - `path`: `str` - 路由路径
    - `component`: `str` - 组件路径
    - `icon`: `str` - 图标
    - `order`: `int` - 排序
    - `is_visible`: `bool` - 是否可见
    - `parent_id`: `int` - 父菜单ID
    - `perms`: `str` - 权限标识
- url地址: `/api/v1/menu/get`
- 请求方式: `GET`

### 创建菜单
- 功能描述: 创建一个新的菜单项。
- 入参:
  - `menu_in`: `MenuCreate` - 菜单创建信息
    - `name`: `str` - 菜单名称
    - `path`: `str` - 路由路径
    - `component`: `str` - 组件路径
    - `icon`: `str` - 图标 (可选)
    - `order`: `int` - 排序
    - `is_visible`: `bool` - 是否可见
    - `parent_id`: `int` - 父菜单ID (0表示顶级菜单)
    - `perms`: `str` - 权限标识 (可选)
- 返回参数:
  - `msg`: `str` - 操作结果信息
- url地址: `/api/v1/menu/create`
- 请求方式: `POST`

### 更新菜单
- 功能描述: 根据菜单ID更新现有的菜单信息。
- 入参:
  - `menu_in`: `MenuUpdate` - 菜单更新信息
    - `id`: `int` - 菜单ID
    - `name`: `str` - 菜单名称 (可选)
    - `path`: `str` - 路由路径 (可选)
    - `component`: `str` - 组件路径 (可选)
    - `icon`: `str` - 图标 (可选)
    - `order`: `int` - 排序 (可选)
    - `is_visible`: `bool` - 是否可见 (可选)
    - `parent_id`: `int` - 父菜单ID (可选)
    - `perms`: `str` - 权限标识 (可选)
- 返回参数:
  - `msg`: `str` - 操作结果信息
- url地址: `/api/v1/menu/update`
- 请求方式: `POST`

### 删除菜单
- 功能描述: 根据菜单ID删除一个菜单项。如果菜单下有子菜单，则不允许删除。
- 入参:
  - `id`: `int` - 菜单id
- 返回参数:
  - `msg`: `str` - 操作结果信息 (成功或失败原因)
- url地址: `/api/v1/menu/delete`
- 请求方式: `DELETE`

## 角色模块

### 查看角色列表
- 功能描述: 获取角色列表，支持分页和按角色名称筛选。
- 入参:
  - `page`: `int` - 页码，默认为1
  - `page_size`: `int` - 每页数量，默认为10
  - `role_name`: `str` - 角色名称，用于查询，可选
- 返回参数:
  - `data`: `list` - 角色对象列表
    - `id`: `int` - 角色ID
    - `name`: `str` - 角色名称
    - `remark`: `str` - 备注
    - `created_at`: `datetime` - 创建时间
    - `updated_at`: `datetime` - 更新时间
  - `total`: `int` - 总数量
  - `page`: `int` - 当前页码
  - `page_size`: `int` - 每页数量
- url地址: `/api/v1/role/list`
- 请求方式: `GET`

### 查看角色
- 功能描述: 根据角色ID获取单个角色的详细信息。
- 入参:
  - `role_id`: `int` - 角色ID
- 返回参数:
  - `data`: `object` - 角色对象
    - `id`: `int` - 角色ID
    - `name`: `str` - 角色名称
    - `remark`: `str` - 备注
    - `created_at`: `datetime` - 创建时间
    - `updated_at`: `datetime` - 更新时间
- url地址: `/api/v1/role/get`
- 请求方式: `GET`

### 创建角色
- 功能描述: 创建一个新的角色。如果角色名已存在，则不允许创建。
- 入参:
  - `role_in`: `RoleCreate` - 角色创建信息
    - `name`: `str` - 角色名称
    - `remark`: `str` - 备注 (可选)
- 返回参数:
  - `msg`: `str` - 操作结果信息
- url地址: `/api/v1/role/create`
- 请求方式: `POST`

### 更新角色
- 功能描述: 根据角色ID更新现有的角色信息。
- 入参:
  - `role_in`: `RoleUpdate` - 角色更新信息
    - `id`: `int` - 角色ID
    - `name`: `str` - 角色名称 (可选)
    - `remark`: `str` - 备注 (可选)
- 返回参数:
  - `msg`: `str` - 操作结果信息
- url地址: `/api/v1/role/update`
- 请求方式: `POST`

### 删除角色
- 功能描述: 根据角色ID删除一个角色。
- 入参:
  - `role_id`: `int` - 角色ID
- 返回参数:
  - `msg`: `str` - 操作结果信息
- url地址: `/api/v1/role/delete`
- 请求方式: `DELETE`

### 查看角色权限
- 功能描述: 根据角色ID查看该角色拥有的菜单和API权限。
- 入参:
  - `id`: `int` - 角色ID
- 返回参数:
  - `data`: `object` - 角色权限信息
    - `id`: `int` - 角色ID
    - `name`: `str` - 角色名称
    - `remark`: `str` - 备注
    - `menus`: `list` - 菜单对象列表
    - `apis`: `list` - API对象列表
- url地址: `/api/v1/role/authorized`
- 请求方式: `GET`

### 更新角色权限
- 功能描述: 更新指定角色的菜单和API权限。
- 入参:
  - `role_in`: `RoleUpdateMenusApis` - 角色权限更新信息
    - `id`: `int` - 角色ID
    - `menu_ids`: `list[int]` - 菜单ID列表
    - `api_infos`: `list[object]` - API信息列表 (包含 `method` 和 `path`)
- 返回参数:
  - `msg`: `str` - 操作结果信息
- url地址: `/api/v1/role/authorized`
- 请求方式: `POST`

## 用户模块

### 查看用户列表
- 功能描述: 获取用户列表，支持分页和按用户名、邮箱、部门ID筛选。
- 入参:
  - `page`: `int` - 页码，默认为1
  - `page_size`: `int` - 每页数量，默认为10
  - `username`: `str` - 用户名称，用于搜索，可选
  - `email`: `str` - 邮箱地址，可选
  - `dept_id`: `int` - 部门ID，可选
- 返回参数:
  - `data`: `list` - 用户对象列表 (不含密码)
    - `id`: `int` - 用户ID
    - `username`: `str` - 用户名
    - `email`: `str` - 邮箱
    - `is_active`: `bool` - 是否激活
    - `is_superuser`: `bool` - 是否超级用户
    - `avatar`: `str` - 用户头像URL (固定值)
    - `last_login`: `datetime` - 上次登录时间
    - `created_at`: `datetime` - 创建时间
    - `updated_at`: `datetime` - 更新时间
    - `dept`: `object` - 部门信息 (如果存在)
    - `roles`: `list` - 角色列表
  - `total`: `int` - 总数量
  - `page`: `int` - 当前页码
  - `page_size`: `int` - 每页数量
- url地址: `/api/v1/user/list`
- 请求方式: `GET`

### 查看用户
- 功能描述: 根据用户ID获取单个用户的详细信息 (不含密码)。
- 入参:
  - `user_id`: `int` - 用户ID
- 返回参数:
  - `data`: `object` - 用户对象 (不含密码)
    - `id`: `int` - 用户ID
    - `username`: `str` - 用户名
    - `email`: `str` - 邮箱
    - `is_active`: `bool` - 是否激活
    - `is_superuser`: `bool` - 是否超级用户
    - `avatar`: `str` - 用户头像URL (固定值)
    - `last_login`: `datetime` - 上次登录时间
    - `created_at`: `datetime` - 创建时间
    - `updated_at`: `datetime` - 更新时间
    - `dept_id`: `int` - 部门ID (可选)
    - `roles`: `list` - 角色列表 (可选)
- url地址: `/api/v1/user/get`
- 请求方式: `GET`

### 创建用户
- 功能描述: 创建一个新用户。如果邮箱已存在，则不允许创建。
- 入参:
  - `user_in`: `UserCreate` - 用户创建信息
    - `username`: `str` - 用户名
    - `email`: `str` - 邮箱
    - `password`: `str` - 密码
    - `dept_id`: `int` - 部门ID (可选)
    - `role_ids`: `list[int]` - 角色ID列表
- 返回参数:
  - `msg`: `str` - 操作结果信息
- url地址: `/api/v1/user/create`
- 请求方式: `POST`

### 更新用户
- 功能描述: 根据用户ID更新现有的用户信息。
- 入参:
  - `user_in`: `UserUpdate` - 用户更新信息
    - `id`: `int` - 用户ID
    - `username`: `str` - 用户名 (可选)
    - `email`: `str` - 邮箱 (可选)
    - `dept_id`: `int` - 部门ID (可选)
    - `role_ids`: `list[int]` - 角色ID列表 (可选)
    - `is_active`: `bool` - 是否激活 (可选)
- 返回参数:
  - `msg`: `str` - 操作结果信息
- url地址: `/api/v1/user/update`
- 请求方式: `POST`

### 删除用户
- 功能描述: 根据用户ID删除一个用户。
- 入参:
  - `user_id`: `int` - 用户ID
- 返回参数:
  - `msg`: `str` - 操作结果信息
- url地址: `/api/v1/user/delete`
- 请求方式: `DELETE`

### 重置密码
- 功能描述: 管理员根据用户ID重置用户的密码为默认密码 '123456'。
- 入参:
  - `user_id`: `int` - 用户ID (通过请求体 `embed=True` 传递)
- 返回参数:
  - `msg`: `str` - 操作结果信息
- url地址: `/api/v1/user/reset_password`
- 请求方式: `POST`