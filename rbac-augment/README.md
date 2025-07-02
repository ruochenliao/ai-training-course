# RBAC权限管理系统

基于 FastAPI + Vue 3 + TypeScript + Element Plus 的企业级RBAC（基于角色的访问控制）权限管理系统。

## 🚀 项目特性

- **现代化技术栈**：FastAPI + Vue 3 + TypeScript + Element Plus
- **完整的RBAC模型**：用户、角色、权限、菜单四层权限控制
- **JWT双Token认证**：Access Token + Refresh Token 安全认证
- **动态路由**：基于用户权限动态生成前端路由和菜单
- **细粒度权限控制**：页面级 + 按钮级权限控制
- **企业级代码规范**：完整的类型定义、错误处理、API文档
- **响应式设计**：支持桌面端、平板端、移动端

## 📋 技术栈

### 后端
- **FastAPI** - 高性能异步Web框架
- **Tortoise ORM** - 异步ORM框架
- **SQLite/PostgreSQL** - 数据库
- **JWT** - 身份认证
- **Pydantic** - 数据验证
- **Uvicorn** - ASGI服务器

### 前端
- **Vue 3** - 渐进式JavaScript框架
- **TypeScript** - 类型安全的JavaScript
- **Element Plus** - Vue 3组件库
- **Vue Router** - 路由管理
- **Pinia** - 状态管理
- **Axios** - HTTP客户端
- **Vite** - 构建工具

## 🏗️ 项目结构

```
rbac-augment/
├── backend/                 # FastAPI后端
│   ├── app/
│   │   ├── api/            # API路由
│   │   ├── core/           # 核心配置
│   │   ├── crud/           # 数据库操作
│   │   ├── models/         # 数据模型
│   │   ├── schemas/        # Pydantic模式
│   │   ├── middleware/     # 中间件
│   │   └── utils/          # 工具函数
│   ├── requirements.txt
│   ├── main.py
│   └── init_db.py
├── frontend/               # Vue 3前端
│   ├── src/
│   │   ├── api/           # API接口
│   │   ├── components/    # 公共组件
│   │   ├── views/         # 页面组件
│   │   ├── router/        # 路由配置
│   │   ├── stores/        # Pinia状态管理
│   │   ├── utils/         # 工具函数
│   │   └── types/         # TypeScript类型定义
│   ├── package.json
│   └── vite.config.ts
└── README.md
```

## 🚀 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- pnpm (推荐) 或 npm

### 一键启动（Windows）

双击运行 `start.bat` 脚本，自动完成环境检查、依赖安装和服务启动。

### 手动启动

#### 后端启动

1. 进入后端目录
```bash
cd backend
```

2. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 复制环境变量文件
```bash
cp .env.example .env
```

5. 初始化数据库
```bash
python init_db.py
```

6. 启动服务
```bash
python main.py
```

后端服务将在 http://localhost:8000 启动

#### 前端启动

1. 进入前端目录
```bash
cd frontend
```

2. 安装依赖
```bash
pnpm install
# 或
npm install
```

3. 启动开发服务器
```bash
pnpm dev
# 或
npm run dev
```

前端服务将在 http://localhost:5173 启动

## 👤 演示账户

| 角色 | 用户名 | 密码 | 权限说明 |
|------|--------|------|----------|
| 超级管理员 | admin | admin123 | 拥有所有权限 |
| 系统管理员 | manager | manager123 | 拥有用户和角色管理权限 |
| 普通用户 | user | user123 | 只有基础查看权限 |

## 📚 API文档

启动后端服务后，访问以下地址查看API文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🔧 配置说明

### 后端配置

主要配置文件：`backend/.env`

```env
# 应用配置
APP_NAME=RBAC管理系统
APP_VERSION=1.0.0
DEBUG=True

# 数据库配置
DATABASE_URL=sqlite:///./rbac.db

# JWT配置
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS配置
ALLOWED_ORIGINS=["http://localhost:5173"]
```

### 前端配置

主要配置文件：`frontend/.env.development`

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_TITLE=RBAC管理系统
```

## 🎯 核心功能

### 1. 用户管理
- ✅ 用户CRUD操作（列表、详情、新增、编辑、删除）
- ✅ 批量删除用户
- ✅ 用户状态切换（激活/禁用）
- ✅ 密码重置功能
- ✅ 角色分配管理
- ✅ 用户搜索和筛选
- ✅ 分页显示

### 2. 角色管理
- ✅ 角色CRUD操作
- ✅ 批量删除角色
- ✅ 权限分配管理
- ✅ 菜单分配管理
- ✅ 角色状态管理
- ✅ 用户统计显示

### 3. 权限管理
- ✅ 权限CRUD操作
- ✅ 权限树形结构展示
- ✅ 权限分组管理
- ✅ 多视图模式（树形/表格/分组）
- ✅ 权限层级关系

### 4. 菜单管理
- ✅ 菜单CRUD操作
- ✅ 树形结构管理
- ✅ 动态路由生成
- ✅ 菜单排序功能
- ✅ 菜单展开/折叠
- ✅ 外链菜单支持

### 5. 认证授权
- ✅ JWT双Token认证（Access + Refresh）
- ✅ 自动Token刷新
- ✅ 权限验证中间件
- ✅ 动态路由守卫
- ✅ 按钮级权限控制
- ✅ 权限指令（v-permission）

### 6. 系统功能
- ✅ 仪表板数据统计
- ✅ 用户个人资料管理
- ✅ 密码修改功能
- ✅ 主题切换（明/暗）
- ✅ 全屏模式
- ✅ 面包屑导航
- ✅ 响应式设计

## 🔒 安全特性

- **密码加密**：使用bcrypt加密存储
- **JWT安全**：双Token机制，自动刷新
- **权限验证**：前后端双重权限验证
- **SQL注入防护**：ORM层面防护
- **CORS配置**：跨域请求控制

## 📱 响应式设计

- **桌面端**：≥1200px，完整功能展示
- **平板端**：768px-1199px，适配触摸操作
- **移动端**：<768px，简化界面布局

## 🛠️ 开发指南

### 添加新的权限

1. 在 `init_db.py` 中添加权限定义
2. 在前端添加权限验证
3. 在后端API中添加权限装饰器

### 添加新的菜单

1. 在 `init_db.py` 中添加菜单定义
2. 创建对应的Vue组件
3. 配置路由和权限

### 自定义权限验证

```python
# 后端权限装饰器
@require_permissions(["user:read", "user:write"])
async def some_api():
    pass
```

```vue
<!-- 前端权限指令 -->
<el-button v-permission="['user:create']">新增用户</el-button>
```

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📸 项目截图

### 登录页面
- 现代化登录界面设计
- 支持记住登录状态
- 演示账户信息展示

### 仪表板
- 数据统计卡片展示
- 快捷操作入口
- 最近活动记录
- 响应式布局设计

### 用户管理
- 用户列表展示
- 高级搜索筛选
- 批量操作支持
- 用户详情查看

### 角色管理
- 角色权限配置
- 用户统计信息
- 状态管理功能

### 权限管理
- 多视图展示模式
- 权限树形结构
- 分组管理功能

### 菜单管理
- 树形表格展示
- 拖拽排序支持
- 菜单配置管理

## 🚀 部署指南

### 开发环境部署

1. **克隆项目**
```bash
git clone <repository-url>
cd rbac-augment
```

2. **使用一键启动脚本**
```bash
# Windows
start.bat

# Linux/Mac
chmod +x start.sh
./start.sh
```

### 生产环境部署

#### 后端部署

1. **安装依赖**
```bash
cd backend
pip install -r requirements.txt
```

2. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件，配置生产环境参数
```

3. **初始化数据库**
```bash
python init_db.py
```

4. **启动服务**
```bash
# 使用 Gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000

# 或使用 Uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

#### 前端部署

1. **构建项目**
```bash
cd frontend
npm install
npm run build
```

2. **部署到Web服务器**
```bash
# 将 dist 目录部署到 Nginx、Apache 等Web服务器
cp -r dist/* /var/www/html/
```

3. **Nginx配置示例**
```nginx
server {
    listen 80;
    server_name your-domain.com;
    root /var/www/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Docker部署

1. **构建镜像**
```bash
# 后端
cd backend
docker build -t rbac-backend .

# 前端
cd frontend
docker build -t rbac-frontend .
```

2. **使用Docker Compose**
```bash
docker-compose up -d
```

## 🔧 开发指南

### 添加新功能

1. **后端API开发**
   - 在 `app/api/v1/` 下创建新的路由文件
   - 在 `app/crud/` 下添加数据操作逻辑
   - 在 `app/schemas/` 下定义数据模型
   - 更新 `app/utils/deps.py` 添加权限验证

2. **前端页面开发**
   - 在 `src/views/` 下创建页面组件
   - 在 `src/api/` 下添加API接口
   - 在 `src/types/` 下定义TypeScript类型
   - 更新路由配置和权限验证

### 代码规范

- **后端**：遵循PEP 8规范，使用类型注解
- **前端**：使用ESLint + Prettier，遵循Vue 3规范
- **提交**：使用Conventional Commits规范

### 测试

```bash
# 后端测试
cd backend
pytest

# 前端测试
cd frontend
npm run test
```

## 📞 联系方式

如有问题，请提交 Issue 或联系开发团队。

## 🙏 致谢

感谢以下开源项目的支持：
- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的Python Web框架
- [Vue 3](https://vuejs.org/) - 渐进式JavaScript框架
- [Element Plus](https://element-plus.org/) - Vue 3组件库
- [Tortoise ORM](https://tortoise-orm.readthedocs.io/) - 异步ORM框架
