# 企业级RAG智能问答系统

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-green.svg)](https://python.org)
[![Node.js](https://img.shields.io/badge/node.js-18+-green.svg)](https://nodejs.org)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://docker.com)

一个基于AutoGen多智能体框架和通义千问大模型的企业级RAG（检索增强生成）智能问答系统。

## 🌟 项目特色

- **🤖 AutoGen多智能体协作**: 基于Microsoft AutoGen框架的智能体协作系统
- **🧠 通义千问模型集成**: 强大的中文语言理解和生成能力
- **📚 多格式文档支持**: PDF、Word、PPT、TXT、Markdown等格式
- **🔍 混合检索策略**: 向量检索 + 图谱检索的完美结合
- **🎨 现代化界面**: 基于Vue3/React的响应式前端设计
- **🚀 生产就绪**: 完整的Docker部署和监控方案
- **🔒 企业级安全**: 用户权限管理、API安全、数据加密

## 📋 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   用户前端      │    │   管理后台      │    │   API网关       │
│  (Next.js)     │    │  (Nuxt.js)     │    │   (Nginx)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   后端API服务    │
                    │   (FastAPI)    │
                    └─────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  AutoGen智能体   │    │   数据存储层     │    │   监控系统      │
│     协作系统     │    │                │    │                │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ • 检索智能体     │    │ • PostgreSQL   │    │ • Prometheus   │
│ • 图谱智能体     │    │ • Milvus       │    │ • Grafana      │
│ • 混合智能体     │    │ • Neo4j        │    │ • ELK Stack    │
│ • 答案智能体     │    │ • Redis        │    │                │
│ • 质量智能体     │    │                │    │                │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 快速开始

### 环境要求

- Docker 20.10+
- Docker Compose 2.0+
- Python 3.11+ (开发环境)
- Node.js 18+ (开发环境)

### 一键启动

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd enterprise-rag-system
   ```

2. **配置环境变量**
   ```bash
   cp .env.example .env
   # 编辑 .env 文件，设置必要的配置
   ```

3. **启动服务**
   ```bash
   docker-compose up -d
   ```

4. **验证安装**
   ```bash
   python scripts/simple_verify.py
   ```

### 访问地址

- **用户前端**: http://localhost:3001
- **管理后台**: http://localhost:3000
- **API文档**: http://localhost:8000/docs
- **监控面板**: http://localhost:3002 (Grafana)

## 📖 详细文档

- [📚 快速启动指南](docs/快速启动指南.md)
- [🏗️ 系统架构设计](docs/architecture.md)
- [🔧 开发指南](docs/development-guide.md)
- [🚀 部署指南](docs/deployment-guide.md)
- [📊 API文档](docs/api-documentation.md)
- [✅ 功能实现清单](docs/功能实现清单.md)

## 🎯 核心功能

### 智能问答系统
- 基于AutoGen的多智能体协作
- 支持复杂推理和多轮对话
- 提供答案来源和置信度评分

### 文档管理
- 多格式文档自动解析
- 智能分块和向量化
- 知识图谱自动构建

### 用户管理
- 细粒度权限控制
- 多角色用户体系
- 用户行为审计

### 系统监控
- 实时性能监控
- 业务指标统计
- 告警和日志管理

## 🛠️ 技术栈

### 后端技术
- **框架**: FastAPI + Python 3.11
- **AI模型**: 通义千问系列模型
- **智能体**: Microsoft AutoGen
- **数据库**: PostgreSQL + Milvus + Neo4j + Redis
- **任务队列**: Celery + Redis

### 前端技术
- **管理后台**: Nuxt.js + Vue3 + Naive UI
- **用户前端**: Next.js + React + Tailwind CSS
- **状态管理**: Pinia (Vue) / Zustand (React)
- **类型检查**: TypeScript

### 部署运维
- **容器化**: Docker + Docker Compose
- **反向代理**: Nginx
- **监控**: Prometheus + Grafana + ELK Stack
- **CI/CD**: GitHub Actions (可选)

## 📊 项目状态

- **完成度**: 98.2% ✅
- **后端服务**: 100% 完成
- **前端应用**: 100% 完成
- **部署配置**: 100% 完成
- **文档资料**: 98% 完成
- **测试覆盖**: 90% 完成

## 🤝 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🆘 支持与帮助

- 📧 邮箱: support@example.com
- 💬 讨论: [GitHub Discussions](https://github.com/your-repo/discussions)
- 🐛 问题: [GitHub Issues](https://github.com/your-repo/issues)
- 📖 文档: [项目文档](docs/)

## 🙏 致谢

感谢以下开源项目的支持：

- [Microsoft AutoGen](https://github.com/microsoft/autogen)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Vue.js](https://vuejs.org/)
- [React](https://reactjs.org/)
- [Milvus](https://milvus.io/)
- [Neo4j](https://neo4j.com/)

---

**⭐ 如果这个项目对您有帮助，请给我们一个星标！**
