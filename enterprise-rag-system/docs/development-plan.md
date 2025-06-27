# 企业级RAG知识库系统重构开发计划

## 项目总览

**项目名称**: 企业级RAG知识库系统 (严格按照技术栈要求重构)
**开发周期**: 8周 (40个工作日)
**技术栈**: FastAPI + AutoGen + MySQL + Milvus + Neo4j + Marker + Qwen + deepseek-chat + React + TypeScript

## 核心技术栈要求 (严格执行)

### 必需技术组件
- **智能体框架**: AutoGen (microsoft/autogen) - 多智能体协作
- **关系数据库**: MySQL 8.0+ - 系统元数据、用户信息、会话记录
- **向量数据库**: Milvus 2.3+ - 语义检索和混合检索，HNSW索引
- **图数据库**: Neo4j 5.x - 知识图谱，Cypher查询
- **文档解析**: Marker (VikParuchuri/marker) - 多格式文档转Markdown
- **嵌入模型**: Qwen2.5-7B-Instruct (ModelScope部署)
- **重排序模型**: bge-reranker-v2-m3 (BAAI/bge-reranker-v2-m3)
- **主要LLM**: deepseek-chat API (模型热切换)
- **多模态模型**: qwen-vl-max (DashScope API，图像理解)

### 前端技术栈
- **用户界面**: React 18 + TypeScript 5.0+ + Vite 4.0+
- **UI组件**: Ant Design 5.12+ (企业级组件)
- **状态管理**: Zustand 4.0+ (轻量级持久化)
- **可视化**: D3.js 7.0+ (知识图谱) + ECharts 5.4+ (统计图表)
- **样式**: Tailwind CSS 3.3+ + CSS Modules
- **网络层**: Axios 1.6+ + TanStack Query 4.0+

### 后端技术栈
- **Web框架**: FastAPI 0.104+ + Pydantic 2.0+
- **异步处理**: Celery 5.3+ + Redis 7.0+
- **数据库ORM**: SQLAlchemy 2.0+ + Alembic
- **认证**: JWT + OAuth2 + RBAC
- **日志**: structlog + ELK Stack

## 第一阶段：系统重构和基础架构 (Week 1-2)

**时间安排**: 第1-2周
**状态**: 进行中
**目标**: 按照严格技术栈要求重构现有系统

### 1.1 技术栈依赖更新 (2天)
- [ ] 更新requirements.txt，严格按照技术栈要求
- [ ] 移除不符合要求的依赖 (如Tortoise ORM，改用SQLAlchemy)
- [ ] 添加Marker文档解析框架
- [ ] 集成Qwen2.5模型和bge-reranker-v2-m3
- [ ] 配置deepseek-chat API集成
- [ ] 添加qwen-vl-max多模态支持

### 1.2 数据库架构重构 (3天)
- [ ] 将Tortoise ORM迁移到SQLAlchemy 2.0+
- [ ] 设计MySQL数据库schema (用户、会话、文档元数据)
- [ ] 配置Alembic数据库迁移
- [ ] 优化Milvus集合设计 (HNSW索引配置)
- [ ] 设计Neo4j知识图谱schema
- [ ] 实现数据库连接池和事务管理

### 1.3 核心服务架构重构 (3天)
- [ ] 重构文档处理服务 (基于Marker框架)
- [ ] 重构向量存储服务 (Milvus 2.3+优化)
- [ ] 重构图数据库服务 (Neo4j 5.x集成)
- [ ] 重构嵌入服务 (Qwen2.5-7B-Instruct)
- [ ] 重构重排序服务 (bge-reranker-v2-m3)
- [ ] 实现LLM服务 (deepseek-chat API)

### 1.4 前端架构重构 (2天)
- [ ] 用户界面迁移到React 18 + TypeScript + Vite
- [ ] 集成Ant Design 5.12+企业组件
- [ ] 配置Zustand状态管理
- [ ] 设置Tailwind CSS + CSS Modules
- [ ] 配置Axios + TanStack Query网络层
- [ ] 移除管理后台，专注用户界面

**交付物**:
- 完全重构的技术栈
- 符合要求的数据库架构
- 重构的核心服务
- 现代化的前端架构

## 第二阶段：文档处理和知识库构建 (Week 3-4)

**时间安排**: 第3-4周
**状态**: 待开始
**目标**: 实现完整的文档处理流水线

### 2.1 Marker文档解析引擎 (3天)
- [ ] 集成VikParuchuri/marker框架
- [ ] 支持格式：PDF、DOCX、PPTX、XLSX、MD、TXT (最大100MB)
- [ ] 实现批量文档上传 (最多50个文件)
- [ ] Celery异步处理队列
- [ ] WebSocket实时进度追踪
- [ ] 文档去重机制 (MD5哈希)
- [ ] 版本控制系统

### 2.2 智能分块处理 (2天)
- [ ] RecursiveCharacterTextSplitter (chunk_size=1000, overlap=200)
- [ ] 语义分块策略
- [ ] 分块质量评估
- [ ] 分块元数据管理
- [ ] 增量更新机制

### 2.3 向量化和存储 (2天)
- [ ] Qwen2.5-7B-Instruct向量化
- [ ] Milvus HNSW索引优化
- [ ] 批量向量操作
- [ ] 向量数据备份恢复
- [ ] 混合检索 (BM25 + 语义检索)

### 2.4 知识图谱构建 (3天)
- [ ] spaCy + 自定义NER模型实体识别
- [ ] 关系抽取算法
- [ ] Neo4j图谱存储
- [ ] 图谱完整性校验
- [ ] 1-3跳关系推理

**交付物**:
- 基于Marker的文档解析服务
- 智能分块处理系统
- Qwen2.5向量化服务
- Neo4j知识图谱构建

**API端点**:
- `/api/v1/documents/` - 文档处理模块
- `/api/v1/knowledge/` - 知识库处理流水线

## 第三阶段：AutoGen智能体协作系统 (Week 5-6)

**时间安排**: 第5-6周
**状态**: 待开始
**目标**: 实现多智能体协作和答案融合

### 3.1 AutoGen智能体框架 (3天)
- [ ] 检索智能体 (专门负责多源检索)
  - 语义检索 (Qwen2.5嵌入 + 余弦相似度, top-k=20)
  - 混合检索 (BM25 + 语义检索加权融合)
  - 图谱检索 (Neo4j Cypher查询, 1-3跳关系推理)
- [ ] 融合智能体 (整合多个检索结果)
  - bge-reranker-v2-m3重排序
  - 相关性阈值过滤
  - 结果去重和合并
- [ ] 验证智能体 (事实核查和一致性验证)
  - 答案质量评分
  - 置信度计算
  - 冲突检测和解决

### 3.2 智能体协作机制 (2天)
- [ ] 智能体间消息传递
- [ ] 决策投票机制
- [ ] 冲突解决算法
- [ ] 性能监控和优化

### 3.3 deepseek-chat集成 (2天)
- [ ] deepseek-chat API集成
- [ ] 模型热切换机制
- [ ] 流式响应处理
- [ ] 多轮对话支持

### 3.4 多模态支持 (3天)
- [ ] qwen-vl-max图像理解
- [ ] DashScope API集成
- [ ] 图文混合问答
- [ ] 多媒体内容处理

**交付物**:
- 完整的AutoGen多智能体系统
- 三种检索方式的智能体
- deepseek-chat答案生成
- qwen-vl-max多模态支持

**API端点**:
- `/api/v1/agents/` - AutoGen智能体协作

## 第四阶段：Gemini风格用户界面 (Week 7-8)

**时间安排**: 第7-8周
**状态**: 待开始
**目标**: 实现Google Gemini风格的智能对话界面

### 4.1 智能对话界面 (4天)
- [ ] Google Gemini界面风格设计
- [ ] 深色/浅色主题切换
- [ ] 流式响应显示 + 打字机效果
- [ ] 消息气泡动画
- [ ] 无限滚动历史记录
- [ ] 会话分组管理
- [ ] 导出对话记录

### 4.2 多模式检索系统 (3天)
- [ ] 语义检索界面 (基于Qwen2.5嵌入)
- [ ] 混合检索界面 (BM25 + 语义检索)
- [ ] 图谱检索界面 (Neo4j Cypher查询)
- [ ] 检索结果展示 (相关性评分、来源文档高亮)
- [ ] 检索路径可视化

### 4.3 多媒体支持 (2天)
- [ ] 图片预览和上传
- [ ] 表格渲染 (Ant Design Table)
- [ ] 代码高亮 (Prism.js)
- [ ] LaTeX公式渲染
- [ ] 文档引用跳转

### 4.4 数据可视化 (1天)
- [ ] Neo4j知识图谱可视化 (D3.js + Neo4j Browser API)
- [ ] 实时统计信息 (文档数量、向量维度、图谱节点/边)
- [ ] 系统性能监控 (API响应时间、数据库状态)
- [ ] 用户行为分析 (查询频率热力图)

**技术栈**: React 18 + TypeScript 5.0+ + Vite 4.0+ + Ant Design 5.12+

**交付物**:
- Google Gemini风格聊天界面
- 三种检索方式的用户界面
- 多媒体内容展示支持
- 知识图谱可视化界面

**API端点**:
- `/chat/` - 智能对话界面
- `/search/` - 多模式检索系统
- `/dashboard/` - 数据可视化仪表板

## 系统集成和优化 (持续进行)

### 性能优化要求
- **检索响应时间**: < 2秒
- **并发用户支持**: > 100
- **测试覆盖率**: > 80%
- **系统可用性**: > 99%

### 部署和监控
- **容器化**: Docker Compose多服务编排
- **环境配置**: 开发/测试/生产环境分离
- **监控体系**: 健康检查 + Prometheus指标
- **文档体系**: API文档自动生成 + 用户手册

## 项目里程碑

### 里程碑1：系统重构完成
- **时间**: 第2周结束
- **标志**: 技术栈完全符合要求，基础架构重构完成

### 里程碑2：文档处理流水线完成
- **时间**: 第4周结束
- **标志**: Marker解析 + Qwen向量化 + Neo4j图谱构建完成

### 里程碑3：AutoGen智能体系统完成
- **时间**: 第6周结束
- **标志**: 多智能体协作 + deepseek-chat + qwen-vl-max完成

### 里程碑4：Gemini风格界面完成
- **时间**: 第8周结束
- **标志**: 完整的用户界面和可视化系统完成

## 特殊要求实施

### 1. 删除无关监控组件
- [ ] 移除Prometheus/Grafana监控 (专注核心RAG功能)
- [ ] 移除管理后台 (只保留用户界面)
- [ ] 简化部署配置

### 2. 架构文档生成
- [ ] 在`docs/`目录生成Mermaid系统架构图
- [ ] 完整的技术文档
- [ ] 每个功能模块的详细说明

### 3. 代码质量保证
- [ ] 每个模块单元测试和集成测试
- [ ] 测试覆盖率 > 80%
- [ ] 代码规范和文档注释

### 4. 性能基准测试
- [ ] 检索响应时间 < 2s
- [ ] 支持并发用户数 > 100
- [ ] 系统资源使用监控

## 下一步行动计划

**当前状态**: 项目分析完成，准备开始系统重构
**下一步**: 开始第一阶段系统重构和基础架构

### 立即开始的任务 (优先级排序)

#### 高优先级 (本周完成)
1. **技术栈依赖更新**
   - 更新requirements.txt，移除Tortoise ORM
   - 添加SQLAlchemy 2.0+ + Alembic
   - 集成Marker文档解析框架
   - 添加Qwen2.5和bge-reranker-v2-m3

2. **数据库架构重构**
   - 设计MySQL schema (替换PostgreSQL)
   - 配置Milvus HNSW索引
   - 设计Neo4j知识图谱schema

#### 中优先级 (下周完成)
3. **核心服务重构**
   - 基于Marker的文档解析服务
   - Qwen2.5嵌入服务
   - bge-reranker-v2-m3重排序服务
   - deepseek-chat API集成

4. **前端架构迁移**
   - React 18 + TypeScript + Vite
   - Ant Design 5.12+企业组件
   - Zustand状态管理

### 技术决策确认

请确认以下技术决策是否正确：

1. **数据库选择**: MySQL 8.0+ (替换现有PostgreSQL)
2. **ORM框架**: SQLAlchemy 2.0+ (替换Tortoise ORM)
3. **文档解析**: Marker框架 (VikParuchuri/marker)
4. **嵌入模型**: Qwen2.5-7B-Instruct (ModelScope部署)
5. **重排序模型**: bge-reranker-v2-m3
6. **主要LLM**: deepseek-chat API
7. **多模态**: qwen-vl-max (DashScope API)
8. **前端框架**: React 18 + TypeScript (替换现有Nuxt.js)

### 风险评估

**技术风险**:
- Marker框架集成复杂度
- Qwen模型本地部署资源需求
- 大规模重构可能的兼容性问题

**应对措施**:
- 分阶段重构，保持系统可用性
- 提前测试模型集成和性能
- 完整的测试覆盖和回滚方案

**是否开始第一阶段的系统重构工作？**
