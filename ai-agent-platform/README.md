# 智能体应用综合平台

## 🚀 项目简介

智能体应用综合平台是一个集成了前沿AI技术的"一站式"智能体解决方案平台，旨在成为企业数字化转型的核心引擎。平台提供四个核心智能体服务：

- **🤖 智能客服智能体**: SSE实时对话、工具调用、会话管理
- **📊 Text2SQL数据分析智能体**: 自然语言转SQL、数据可视化  
- **📚 企业知识库问答智能体**: RAG检索问答、来源引用
- **✍️ 文案创作智能体**: 结构化创作、模板选择、多格式输出

## 🏗️ 技术架构

### 核心技术栈

**前端**:
- Vue.js 3 + TypeScript + Vite
- Element-Plus / Ant Design Vue
- Pinia (状态管理)
- EventSource (SSE客户端)

**后端**:
- Python 3.11+ + FastAPI
- SQLAlchemy 2.0 + Alembic
- Celery + Redis (异步任务)
- JWT认证 + RBAC权限

**AI与智能体**:
- Autogen (智能体框架)
- OpenAI GPT-4o / Google Gemini / DeepSeek
- Langchain (LLM工具链)
- sentence-transformers (嵌入模型)

**数据存储**:
- MySQL 8.x (关系型数据库)
- Milvus 2.3+ (向量数据库)
- Minio (对象存储)
- Redis 7.x (缓存和消息队列)

### 四层架构模型

```
┌─────────────────────────────────────────┐
│           表现层 (Vue.js 3)              │
└─────────────────────────────────────────┘
                    │
┌─────────────────────────────────────────┐
│        服务与API层 (FastAPI)             │
└─────────────────────────────────────────┘
                    │
┌─────────────────────────────────────────┐
│      智能体与AI核心层 (Autogen)           │
└─────────────────────────────────────────┘
                    │
┌─────────────────────────────────────────┐
│   数据持久化层 (MySQL+Milvus+Minio)      │
└─────────────────────────────────────────┘
```

## 📋 项目状态

### 当前进度
- ✅ **架构设计完成** (100%)
- ✅ **数据库设计完成** (100%)  
- ✅ **API接口设计完成** (100%)
- 🔄 **基础设施搭建** (进行中)
- 📋 **用户认证系统** (待开始)
- 📋 **智能体核心框架** (待开始)

### 预计时间线
- **第1-2周**: 架构设计与规划 ✅
- **第3-4周**: 基础设施搭建 🔄
- **第5-6周**: 用户认证授权系统
- **第7-9周**: 智能体核心框架
- **第10-12周**: RAG知识库系统
- **第13-16周**: 智能体功能开发

## 🛠️ 快速开始

### 环境要求
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Git

### 本地开发环境搭建

1. **克隆项目**
```bash
git clone <repository-url>
cd ai-agent-platform
```

2. **数据库和Redis配置**

**外部服务配置**
- MySQL: `192.168.244.128:3306` (用户名: root, 密码: 123456)
- Redis: `192.168.244.128:6379` (密码: 123456)

配置文件 `.env` 已经预配置好了连接信息：
```bash
# 数据库配置 (本地服务)
DATABASE_URL=mysql+pymysql://root:123456@192.168.244.128:3306/ai_platform

# Redis配置 (本地服务)
REDIS_URL=redis://:123456@192.168.244.128:6379/0

# Celery配置
CELERY_BROKER_URL=redis://:123456@192.168.244.128:6379/1
CELERY_RESULT_BACKEND=redis://:123456@192.168.244.128:6379/2
```

**自动初始化功能**
- 服务启动时会自动创建数据库（如果不存在）
- 自动创建所有数据表
- 自动初始化基础数据（角色、智能体模板、示例数据等）

3. **快速启动**

**使用启动脚本 (推荐)**
```bash
# 安装Python依赖
cd backend
pip install -r requirements.txt
cd ..

# 启动后端服务 (会自动初始化数据库)
python start.py backend

# 或者使用PowerShell (Windows)
.\start.ps1 backend
```

**手动启动**
```bash
# 后端服务
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 前端服务 (新终端)
cd frontend
npm install
npm run dev
```

4. **访问应用**
- 前端应用: http://localhost:3000
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

**默认管理员账号**
- 邮箱: admin@example.com
- 用户名: admin
- 密码: admin123456

## 📁 项目结构

```
ai-agent-platform/
├── frontend/           # Vue.js前端应用
├── backend/            # FastAPI后端应用
├── docs/              # 项目文档
│   ├── architecture-design.md
│   ├── database-design.md
│   └── api-specification.md
├── docker/            # Docker配置文件
├── scripts/           # 部署和工具脚本
└── README.md         # 项目说明
```

## 🔧 开发指南

### 代码规范
- **Python**: 遵循PEP 8，使用Black格式化
- **TypeScript**: 使用ESLint + Prettier
- **Git提交**: 遵循Conventional Commits规范

### API设计规范
- RESTful API设计
- 统一JSON响应格式
- JWT Token认证
- 完整的错误处理

### 测试策略
- 单元测试覆盖率 > 80%
- 集成测试自动化
- API接口测试
- 前端组件测试

## 🚀 部署指南

### Docker部署
```bash
# 构建镜像
docker-compose build

# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps
```

### 生产环境配置
- 使用环境变量管理配置
- 配置HTTPS和域名
- 设置数据库备份策略
- 配置监控和日志收集

## 📖 文档

- [架构设计文档](docs/architecture-design.md)
- [数据库设计文档](docs/database-design.md)
- [API接口规范](docs/api-specification.md)
- [SSE实时通信使用指南](SSE_USAGE.md)
- [详细任务清单](task.md)
- [开发待办事项](todolist.md)

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 开发流程
1. 从`develop`分支创建功能分支
2. 完成开发并通过测试
3. 提交PR到`develop`分支
4. 代码审查通过后合并
5. 定期从`develop`合并到`main`分支

## 📞 联系方式

- **项目负责人**: [待定]
- **技术负责人**: [待定]
- **问题反馈**: [GitHub Issues]

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🎯 路线图

### 近期目标 (1-2个月)
- [ ] 完成基础架构搭建
- [ ] 实现用户认证授权系统
- [ ] 开发智能体核心框架
- [ ] 实现RAG知识库系统

### 中期目标 (3-4个月)  
- [ ] 完成四个核心智能体开发
- [ ] 实现后台管理系统
- [ ] 完成系统测试和优化
- [ ] 生产环境部署

### 长期目标 (6个月+)
- [ ] 性能优化和扩展
- [ ] 更多智能体类型支持
- [ ] 多租户架构支持
- [ ] 移动端应用开发

---

## ⭐ Star History

如果这个项目对你有帮助，请给我们一个 Star ⭐

---

*最后更新: 2025-08-09 (SSE替换完成)*
