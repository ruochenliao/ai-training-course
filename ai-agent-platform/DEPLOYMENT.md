# AI智能体平台部署指南

## 系统要求

- Python 3.8+
- Node.js 16+
- SQLite (开发环境) / PostgreSQL (生产环境)

## 快速启动

### 1. 后端服务

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置必要的环境变量

# 启动服务
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. 前端服务

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

## 访问地址

- 前端应用: http://localhost:3000
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs

## 环境配置

### 后端环境变量 (.env)

```env
# 数据库配置
DATABASE_URL=sqlite:///./ai_agent_platform.db

# JWT配置
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Redis配置
REDIS_URL=redis://localhost:6379/0

# 文件上传配置
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=52428800

# OpenAI配置
OPENAI_API_KEY=your-openai-api-key-here

# 环境配置
ENVIRONMENT=development
DEBUG=true
```

## 功能特性

### ✅ 已实现功能

1. **用户认证系统**
   - 用户注册/登录
   - JWT令牌认证
   - 权限管理

2. **智能体管理**
   - 智能体创建/编辑/删除
   - 智能体配置管理
   - 智能体类型支持

3. **对话系统**
   - 多轮对话支持
   - 对话历史管理
   - 实时消息传输

4. **知识库管理**
   - 文档上传/管理
   - 文档解析和分块
   - 向量化存储

5. **文件管理**
   - 文件上传/下载
   - 文件类型验证
   - 存储管理

### 🚧 开发中功能

1. **高级AI功能**
   - 多模态支持
   - 工具调用
   - 代码执行

2. **企业级功能**
   - 多租户支持
   - 审计日志
   - 性能监控

## 技术栈

### 后端
- FastAPI - Web框架
- SQLAlchemy - ORM
- Pydantic - 数据验证
- JWT - 身份认证
- SQLite/PostgreSQL - 数据库

### 前端
- Vue.js 3 - 前端框架
- TypeScript - 类型安全
- Vite - 构建工具
- Element Plus - UI组件库
- Axios - HTTP客户端

## 开发指南

### 代码结构

```
ai-agent-platform/
├── backend/                 # 后端代码
│   ├── app/
│   │   ├── api/            # API路由
│   │   ├── core/           # 核心配置
│   │   ├── models/         # 数据模型
│   │   ├── schemas/        # Pydantic模式
│   │   ├── services/       # 业务逻辑
│   │   └── utils/          # 工具函数
│   ├── requirements.txt    # Python依赖
│   └── .env               # 环境配置
├── frontend/               # 前端代码
│   ├── src/
│   │   ├── components/     # Vue组件
│   │   ├── views/          # 页面视图
│   │   ├── router/         # 路由配置
│   │   ├── store/          # 状态管理
│   │   └── utils/          # 工具函数
│   ├── package.json        # Node.js依赖
│   └── vite.config.ts     # Vite配置
└── README.md              # 项目说明
```

### 测试

运行系统测试：

```bash
python test_system.py
```

## 生产部署

### Docker部署

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d
```

### 手动部署

1. 配置生产环境变量
2. 使用PostgreSQL数据库
3. 配置反向代理(Nginx)
4. 启用HTTPS
5. 配置日志和监控

## 故障排除

### 常见问题

1. **依赖安装失败**
   - 检查Python/Node.js版本
   - 使用国内镜像源

2. **数据库连接失败**
   - 检查数据库配置
   - 确认数据库服务运行

3. **API调用失败**
   - 检查CORS配置
   - 验证API密钥

## 支持

如有问题，请查看：
- API文档: http://localhost:8000/docs
- 项目仓库: [GitHub链接]
- 问题反馈: [Issues链接]
