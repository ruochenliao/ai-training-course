# 企业级Agent+RAG知识库系统

## 项目概述

基于多智能体协作的下一代企业级知识库系统，融合向量检索、图谱检索和混合检索技术，为用户提供精准、全面、可溯源的智能问答体验。

## 核心特性

- 🤖 **多智能体协作**: 基于AutoGen的智能体编排和协调
- 🔍 **多模态检索**: 向量检索 + 图谱检索 + 混合检索
- 📊 **智能融合**: 多路径检索结果的智能分析和融合
- 🎨 **现代化界面**: 参考Gemini的用户体验设计
- 🔒 **企业级安全**: 完整的权限管理和数据安全保障

## 技术栈

### 后端
- **语言**: Python 3.10+
- **框架**: FastAPI
- **ORM**: Tortoise ORM
- **智能体**: AutoGen
- **任务队列**: Celery + Redis
- **缓存**: Redis

### 前端
- **用户端**: Next.js 14 + React 18 + TypeScript
- **管理端**: Vue 3 + Nuxt.js 3 + TypeScript
- **UI组件**: Ant Design + Naive UI
- **样式**: Tailwind CSS + UnoCSS

### AI模型
- **LLM**: DeepSeek-Chat
- **VLM**: Qwen-VL-Max
- **嵌入**: 通义千问3-8B
- **重排**: 通义千问3-Reranker-8B

### 数据库
- **关系型**: MySQL 8.0
- **向量型**: Milvus 2.4+
- **图数据库**: Neo4j 5.x
- **文件存储**: MinIO
- **缓存**: Redis

## 项目结构

```
enterprise-rag-system/
├── backend/                    # 后端服务
│   ├── app/                   # 应用主体
│   │   ├── api/              # API路由
│   │   ├── core/             # 核心配置
│   │   ├── models/           # 数据模型
│   │   ├── services/         # 业务服务
│   │   ├── agents/           # 智能体模块
│   │   ├── utils/            # 工具函数
│   │   └── main.py           # 应用入口
│   ├── tests/                # 测试代码
│   ├── migrations/           # 数据库迁移
│   ├── requirements.txt      # Python依赖
│   └── Dockerfile           # Docker配置
├── frontend/                  # 前端应用
│   ├── user-app/             # 用户端应用(Next.js)
│   └── admin-app/            # 管理端应用(Vue3)
├── docs/                     # 项目文档
├── scripts/                  # 部署脚本
├── docker-compose.yml        # 开发环境配置
├── k8s/                      # Kubernetes配置
└── README.md                 # 项目说明
```

## 🚀 快速开始

### 环境要求

- Docker 20.10+
- Docker Compose 2.0+
- 8GB+ 内存
- 50GB+ 磁盘空间

### 一键启动

#### Windows用户
```bash
# 克隆项目
git clone https://github.com/your-org/enterprise-rag-system.git
cd enterprise-rag-system

# 启动开发环境
scripts\start-dev.bat
```

#### Linux/macOS用户
```bash
# 克隆项目
git clone https://github.com/your-org/enterprise-rag-system.git
cd enterprise-rag-system

# 启动开发环境
chmod +x scripts/start-dev.sh
./scripts/start-dev.sh
```

### 配置API密钥

编辑 `backend/.env` 文件，填入实际的API密钥：

```env
# AI模型配置
LLM_API_KEY=your_deepseek_api_key_here
VLM_API_KEY=your_qwen_api_key_here
EMBEDDING_API_KEY=your_embedding_api_key_here
RERANKER_API_KEY=your_reranker_api_key_here
```

### 访问系统

启动完成后，可以通过以下地址访问：

- 🌐 **用户端**: http://localhost:3000
- 🔧 **管理端**: http://localhost:3001
- 📊 **监控面板**: http://localhost:3002
- 🔍 **API文档**: http://localhost:8000/docs
- 📈 **Prometheus**: http://localhost:9090
- 📁 **MinIO**: http://localhost:9001 (minioadmin/minioadmin)
- 🕸️ **Neo4j**: http://localhost:7474 (neo4j/password)

### 默认账户

- **管理员账户**: admin / admin123

### 本地开发

#### 后端开发
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 前端开发
```bash
# 用户端
cd frontend/user-app
npm install
npm run dev

# 管理端
cd frontend/admin-app
npm install
npm run dev
```

## 开发指南

### 代码规范
- Python: 遵循PEP 8，使用Black格式化
- TypeScript: 使用ESLint + Prettier
- 提交信息: 遵循Conventional Commits规范

### 测试
```bash
# 后端测试
cd backend
pytest

# 前端测试
cd frontend/user-app
npm test

cd frontend/admin-app
npm test
```

### 部署

#### 开发环境
```bash
docker-compose up -d
```

#### 生产环境
```bash
# 构建镜像
docker build -t enterprise-rag-backend ./backend
docker build -t enterprise-rag-frontend ./frontend

# 部署到Kubernetes
kubectl apply -f k8s/
```

## API文档

详细的API文档可以在以下地址查看：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 联系方式

- 项目维护者: [维护者邮箱]
- 问题反馈: [GitHub Issues]
- 技术讨论: [讨论群组]

## 更新日志

查看 [CHANGELOG.md](CHANGELOG.md) 了解版本更新详情。
