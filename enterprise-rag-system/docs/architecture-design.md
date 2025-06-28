# 企业级RAG知识库系统架构设计文档

## 📋 系统概述

本系统是基于AutoGen多智能体协作的企业级RAG知识库系统，采用现代化微服务架构，集成Marker文档解析、Qwen3-8B嵌入模型、DeepSeek-chat LLM，提供完整的知识库管理和智能问答功能。

### 核心特性
- **多智能体协作**: 基于Microsoft AutoGen框架的智能体系统
- **混合检索**: 语义检索 + 关键词检索 + 知识图谱检索
- **高质量文档解析**: 基于Marker框架的多格式文档处理
- **仿Gemini界面**: 现代化的用户交互体验
- **企业级安全**: 完整的认证授权和权限控制

## 🏗️ 整体技术架构图

```mermaid
graph TB
    subgraph "前端层 - React 18 + TypeScript"
        A[用户聊天界面<br/>Gemini风格设计]
        B[管理后台<br/>系统管理]
        C[知识图谱可视化<br/>D3.js实现]
        D[文档管理界面<br/>批量上传处理]
    end
    
    subgraph "API网关层 - FastAPI 0.104+"
        E[认证授权<br/>JWT + RBAC]
        F[API路由<br/>/api/v1/*]
        G[WebSocket<br/>实时通信]
        H[中间件<br/>限流/日志/CORS]
    end
    
    subgraph "业务服务层"
        I[用户管理服务<br/>User Management]
        J[知识库管理服务<br/>Knowledge Base]
        K[文档处理服务<br/>Document Processing]
        L[对话管理服务<br/>Conversation]
    end
    
    subgraph "AI智能体层 - AutoGen Framework"
        M[检索智能体<br/>Retrieval Agent]
        N[分析智能体<br/>Analysis Agent]
        O[回答智能体<br/>Answer Agent]
        P[质量控制智能体<br/>Quality Agent]
    end
    
    subgraph "AI模型层"
        Q[Marker文档解析<br/>PDF/DOCX/PPTX]
        R[Qwen3-8B嵌入<br/>向量化模型]
        S[Qwen3-Reranker-8B<br/>重排序模型]
        T[DeepSeek-Chat<br/>大语言模型]
        U[Qwen-VL-Max<br/>多模态模型]
    end
    
    subgraph "数据存储层"
        V[MySQL 8.0+<br/>关系数据]
        W[Milvus 2.3+<br/>向量数据库]
        X[Neo4j 5.x<br/>知识图谱]
        Y[Redis 7.0+<br/>缓存队列]
        Z[MinIO<br/>文件存储]
    end
    
    A --> E
    B --> F
    C --> G
    D --> H
    E --> I
    F --> J
    G --> K
    H --> L
    I --> M
    J --> N
    K --> O
    L --> P
    M --> Q
    N --> R
    O --> S
    P --> T
    Q --> U
    R --> V
    S --> W
    T --> X
    U --> Y
    V --> Z
```

## 🔄 数据流架构图

```mermaid
sequenceDiagram
    participant U as 用户
    participant FE as 前端应用
    participant API as FastAPI网关
    participant AG as AutoGen智能体
    participant DOC as 文档处理
    participant VEC as 向量检索
    participant GRAPH as 图谱检索
    participant LLM as 大语言模型
    participant DB as 数据库集群
    
    Note over U,DB: 文档上传处理流程
    U->>FE: 上传文档
    FE->>API: POST /api/v1/documents/upload
    API->>DOC: Marker解析文档
    DOC->>VEC: 生成向量嵌入
    VEC->>GRAPH: 构建知识图谱
    GRAPH->>DB: 存储多模态数据
    DB->>API: 返回处理状态
    API->>FE: WebSocket推送进度
    FE->>U: 实时显示进度
    
    Note over U,DB: 智能问答流程
    U->>FE: 发送问题
    FE->>API: POST /api/v1/chat/autogen
    API->>AG: 启动智能体协作
    AG->>VEC: 语义向量检索
    AG->>GRAPH: 知识图谱检索
    AG->>LLM: 生成综合答案
    LLM->>AG: 返回答案结果
    AG->>API: 智能体协作结果
    API->>FE: 流式返回答案
    FE->>U: 实时显示回答
```

## 🏛️ 微服务模块图

```mermaid
graph LR
    subgraph "认证授权模块"
        A1[JWT认证服务]
        A2[RBAC权限控制]
        A3[用户会话管理]
    end
    
    subgraph "知识库管理模块"
        B1[知识库CRUD]
        B2[权限分配管理]
        B3[知识库统计分析]
    end
    
    subgraph "文档处理模块"
        C1[Marker解析引擎]
        C2[智能分块服务]
        C3[向量化处理]
        C4[知识图谱构建]
    end
    
    subgraph "检索服务模块"
        D1[语义向量检索]
        D2[关键词检索]
        D3[图谱路径检索]
        D4[混合检索融合]
    end
    
    subgraph "智能体协作模块"
        E1[检索智能体]
        E2[分析智能体]
        E3[回答智能体]
        E4[质量控制智能体]
        E5[群聊管理器]
    end
    
    subgraph "对话管理模块"
        F1[会话状态管理]
        F2[消息历史存储]
        F3[多模态处理]
        F4[实时通信]
    end
    
    A1 --> B1
    B1 --> C1
    C1 --> D1
    D1 --> E1
    E1 --> F1
```

## 🚀 部署架构图

```mermaid
graph TB
    subgraph "负载均衡层"
        LB[Nginx负载均衡器<br/>SSL终端]
    end
    
    subgraph "应用服务层"
        FE1[前端应用1<br/>React容器]
        FE2[前端应用2<br/>React容器]
        BE1[后端API1<br/>FastAPI容器]
        BE2[后端API2<br/>FastAPI容器]
    end
    
    subgraph "AI服务层"
        AI1[Marker解析服务<br/>GPU容器]
        AI2[Qwen嵌入服务<br/>GPU容器]
        AI3[AutoGen智能体<br/>CPU容器]
    end
    
    subgraph "数据服务层"
        DB1[MySQL主库<br/>关系数据]
        DB2[MySQL从库<br/>读副本]
        VDB[Milvus集群<br/>向量数据库]
        GDB[Neo4j集群<br/>图数据库]
        CACHE[Redis集群<br/>缓存队列]
    end
    
    subgraph "存储层"
        FS[MinIO对象存储<br/>文件系统]
        BACKUP[备份存储<br/>定期备份]
    end
    
    subgraph "监控层"
        PROM[Prometheus<br/>指标收集]
        GRAF[Grafana<br/>可视化监控]
        ELK[ELK Stack<br/>日志分析]
    end
    
    LB --> FE1
    LB --> FE2
    LB --> BE1
    LB --> BE2
    BE1 --> AI1
    BE2 --> AI2
    AI1 --> AI3
    BE1 --> DB1
    BE2 --> DB2
    AI2 --> VDB
    AI3 --> GDB
    BE1 --> CACHE
    AI1 --> FS
    DB1 --> BACKUP
    BE1 --> PROM
    PROM --> GRAF
    BE1 --> ELK
```

## 📊 技术栈详细说明

### 前端技术栈
- **核心框架**: React 18.2+ + TypeScript 5.0+ + Next.js 14+
- **构建工具**: Vite 4.0+ (快速构建和热重载)
- **UI组件库**: Ant Design 5.12+ (企业级组件)
- **状态管理**: Zustand 4.0+ (轻量级状态管理)
- **样式方案**: TailwindCSS 3.3+ + CSS Modules
- **可视化**: D3.js 7.0+ (知识图谱) + ECharts 5.4+ (统计图表)
- **网络层**: Axios 1.6+ + TanStack Query 4.0+ (数据获取)
- **动画库**: Framer Motion 10.0+ (流畅动画效果)

### 后端技术栈
- **Web框架**: FastAPI 0.104+ + Pydantic 2.0+ (高性能API)
- **异步处理**: Celery 5.3+ + Redis 7.0+ (任务队列)
- **数据库ORM**: SQLAlchemy 2.0+ + Alembic (数据库操作)
- **认证系统**: JWT + OAuth2 + RBAC (安全认证)
- **日志系统**: Loguru + ELK Stack (日志管理)
- **监控系统**: Prometheus + Grafana (性能监控)

### AI技术栈
- **智能体框架**: Microsoft AutoGen 0.2.18+ (多智能体协作)
- **文档解析**: Marker 0.2.15+ (高质量PDF解析)
- **嵌入模型**: Qwen3-8B (ModelScope部署)
- **重排序模型**: Qwen3-Reranker-8B (结果优化)
- **大语言模型**: DeepSeek-Chat API (主要对话模型)
- **多模态模型**: Qwen-VL-Max (图像理解)

### 数据库技术栈
- **关系数据库**: MySQL 8.0+ (用户数据、系统配置)
- **向量数据库**: Milvus 2.3+ (语义检索、HNSW索引)
- **图数据库**: Neo4j 5.x (知识图谱、Cypher查询)
- **缓存数据库**: Redis 7.0+ (会话缓存、任务队列)
- **对象存储**: MinIO (文件存储、备份)

## 🔧 核心组件设计

### 1. AutoGen智能体协作系统
- **检索智能体**: 负责多源检索和结果评估
- **分析智能体**: 负责信息整合和关系分析
- **回答智能体**: 负责答案生成和格式化
- **质量控制智能体**: 负责答案验证和质量评估
- **群聊管理器**: 协调智能体间的协作流程

### 2. 混合检索系统
- **语义检索**: 基于Qwen3-8B的向量相似度搜索
- **关键词检索**: 基于BM25的传统文本检索
- **图谱检索**: 基于Neo4j的实体关系查询
- **结果融合**: 使用Qwen3-Reranker-8B重排序

### 3. 文档处理流水线
- **格式支持**: PDF、DOCX、PPTX、XLSX、MD、TXT
- **解析引擎**: Marker框架高质量解析
- **智能分块**: 语义感知的文档分块
- **向量化**: Qwen3-8B生成高质量嵌入
- **图谱构建**: 自动实体识别和关系抽取

### 4. 实时通信系统
- **WebSocket**: 支持实时消息推送
- **流式响应**: 大语言模型流式输出
- **进度追踪**: 文档处理进度实时更新
- **错误处理**: 完善的异常处理机制

## 📈 性能指标与优化

### 系统性能目标
- **API响应时间**: < 2秒 (95%请求)
- **文档处理速度**: < 30秒/MB
- **并发用户数**: 1000+ 同时在线
- **检索准确率**: > 90% (Top-5)
- **系统可用性**: 99.9% 年度可用性

### 优化策略
- **缓存策略**: Redis多层缓存
- **数据库优化**: 读写分离、索引优化
- **负载均衡**: Nginx反向代理
- **异步处理**: Celery任务队列
- **资源池化**: 数据库连接池

## 🔒 安全架构设计

### 认证授权
- **JWT Token**: 无状态认证机制
- **RBAC权限**: 基于角色的访问控制
- **API密钥**: 第三方服务认证
- **会话管理**: 安全的会话生命周期

### 数据安全
- **数据加密**: 敏感数据AES加密
- **传输安全**: HTTPS/WSS加密传输
- **访问控制**: 细粒度权限控制
- **审计日志**: 完整的操作审计

## 📝 接口设计规范

### RESTful API设计
- **统一前缀**: `/api/v1/`
- **HTTP方法**: GET/POST/PUT/DELETE
- **状态码**: 标准HTTP状态码
- **响应格式**: 统一JSON格式

### WebSocket设计
- **连接管理**: 自动重连机制
- **消息格式**: JSON消息协议
- **心跳检测**: 定期连接检测
- **错误处理**: 优雅的错误处理

这个架构设计文档提供了系统的完整技术视图，为后续的开发和部署提供了详细的指导。所有组件都经过精心设计，确保系统的高性能、高可用性和可扩展性。
