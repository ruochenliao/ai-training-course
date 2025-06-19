# 企业级Agent+RAG知识库系统技术蓝图

## 🎯 项目愿景与核心目标

构建一个基于语言大模型（LLM）和多模态大模型（VLM）的下一代智能知识库系统。该系统以多智能体（Agent）为核心协调器，深度融合向量检索、关键词检索与图谱检索，为用户提供精准、全面、可溯源的智能问答体验。

### 核心特性
- 🤖 **多智能体协作**：基于AutoGen的智能体编排和协调
- 🔍 **多模态检索**：向量检索 + 图谱检索 + 混合检索
- 📊 **智能融合**：多路径检索结果的智能分析和融合
- 🎨 **现代化界面**：参考Gemini的用户体验设计
- 🔒 **企业级安全**：完整的权限管理和数据安全保障

## 🏗️ 整体系统架构设计

### 系统架构图

```mermaid
graph TB
    subgraph "前端层 Frontend Layer"
        UI[用户界面 - Next.js/React]
        Admin[管理后台 - Vue3/Nuxt.js]
    end
    
    subgraph "API网关层 API Gateway"
        Gateway[FastAPI Gateway]
        Auth[JWT认证]
        RateLimit[限流控制]
    end
    
    subgraph "智能体协调层 Agent Orchestration"
        AutoGen[AutoGen协调器]
        GraphFlow[Graph Flow引擎]
        
        subgraph "检索智能体 Retrieval Agents"
            VectorAgent[向量检索Agent]
            GraphAgent[图谱检索Agent]
            HybridAgent[混合检索Agent]
        end
        
        subgraph "处理智能体 Processing Agents"
            RerankerAgent[重排Agent]
            FusionAgent[融合Agent]
            AnswerAgent[答案生成Agent]
        end
    end
    
    subgraph "模型服务层 Model Services"
        LLMService[LLM服务 - DeepSeek-Chat]
        VLMService[VLM服务 - Qwen-VL-Max]
        EmbedService[嵌入服务 - 通义千问3-8B]
        RerankerService[重排服务 - 通义千问3-Reranker-8B]
    end
    
    subgraph "数据处理层 Data Processing"
        MarkerService[Marker文档解析]
        ChunkService[智能分块服务]
        GraphExtract[图谱抽取服务]
    end
    
    subgraph "存储层 Storage Layer"
        MySQL[(MySQL - 关系数据)]
        Milvus[(Milvus - 向量数据)]
        Neo4j[(Neo4j - 图谱数据)]
        MinIO[(MinIO - 文件存储)]
    end
    
    UI --> Gateway
    Admin --> Gateway
    Gateway --> AutoGen
    AutoGen --> VectorAgent
    AutoGen --> GraphAgent
    AutoGen --> HybridAgent
    VectorAgent --> Milvus
    GraphAgent --> Neo4j
    HybridAgent --> Milvus
    HybridAgent --> Neo4j
    
    AutoGen --> LLMService
    AutoGen --> VLMService
    VectorAgent --> EmbedService
    RerankerAgent --> RerankerService
    
    MarkerService --> ChunkService
    ChunkService --> Milvus
    GraphExtract --> Neo4j
    
    Gateway --> MySQL
    MarkerService --> MinIO
```

### 数据流图

#### 1. 数据入库流程（Ingestion Pipeline）

```mermaid
sequenceDiagram
    participant User as 用户
    participant Admin as 管理后台
    participant Marker as Marker服务
    participant Chunk as 分块服务
    participant Embed as 嵌入服务
    participant Graph as 图谱抽取
    participant Milvus as Milvus
    participant Neo4j as Neo4j
    participant MySQL as MySQL
    
    User->>Admin: 上传文档
    Admin->>Marker: 文档解析请求
    Marker->>Marker: 解析文档(表格/图片)
    Marker->>Chunk: 返回结构化内容
    
    par 并行处理
        Chunk->>Embed: 文本向量化
        Embed->>Milvus: 存储向量
        and
        Chunk->>Graph: 实体关系抽取
        Graph->>Neo4j: 存储图谱
    end
    
    Chunk->>MySQL: 存储元数据
    Admin->>User: 处理完成通知
```

#### 2. 查询处理流程（Query Pipeline）

```mermaid
sequenceDiagram
    participant User as 用户
    participant UI as 对话界面
    participant AutoGen as AutoGen协调器
    participant VAgent as 向量检索Agent
    participant GAgent as 图谱检索Agent
    participant Fusion as 融合Agent
    participant LLM as LLM服务
    
    User->>UI: 输入问题
    UI->>AutoGen: 发送查询请求
    
    AutoGen->>AutoGen: 分析检索策略
    
    par 并行检索
        AutoGen->>VAgent: 语义检索
        VAgent->>VAgent: Milvus查询+重排
        and
        AutoGen->>GAgent: 图谱检索
        GAgent->>GAgent: Cypher查询
    end
    
    VAgent->>Fusion: 返回向量结果
    GAgent->>Fusion: 返回图谱结果
    
    Fusion->>Fusion: 结果分析与融合
    Fusion->>LLM: 生成最终答案
    LLM->>UI: 流式返回答案
    UI->>User: 显示答案和来源
```

## 🛠️ 技术栈选型

### 后端技术栈
- **语言**: Python 3.10+
- **Web框架**: FastAPI (高性能异步框架)
- **智能体框架**: AutoGen (ConversableAgent + Graph Flow)
- **ORM**: Tortoise ORM (异步ORM)
- **任务队列**: Celery + Redis
- **缓存**: Redis
- **日志**: Loguru
- **监控**: Prometheus + Grafana

### 前端技术栈
- **语言**: TypeScript
- **框架**: 
  - 用户端: Next.js 14 + React 18
  - 管理端: Vue 3 + Nuxt.js 3
- **UI组件库**: 
  - React: Ant Design + Tailwind CSS
  - Vue: Naive UI + UnoCSS
- **状态管理**: 
  - React: Zustand
  - Vue: Pinia
- **图表库**: ECharts + D3.js
- **Markdown**: ReactMarkdown + Prism

### AI模型服务
- **LLM**: DeepSeek-Chat (主要推理模型)
- **VLM**: Qwen-VL-Max (多模态理解)
- **嵌入模型**: 通义千问3-8B (向量化)
- **重排模型**: 通义千问3-Reranker-8B (结果重排)
- **部署方式**: ModelScope本地化部署

### 数据库选型
- **关系型数据库**: MySQL 8.0
  - 用户信息、权限管理
  - 知识库元数据
  - 会话记录
- **向量数据库**: Milvus 2.4+
  - 文档向量存储
  - 混合检索支持
- **图数据库**: Neo4j 5.x
  - 实体关系存储
  - 知识图谱查询
- **文件存储**: MinIO
  - 原始文档存储
  - 图片资源存储

### 文档处理
- **解析引擎**: Marker (二次封装)
  - 支持PDF、Word、PPT等格式
  - 表格和图片智能识别
  - 结构化内容提取

## 📊 数据库设计

### MySQL核心表结构

```sql
-- 用户表
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 知识库表
CREATE TABLE knowledge_bases (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    knowledge_type ENUM('customer_service', 'text_sql', 'rag', 'content_creation') DEFAULT 'rag',
    is_public BOOLEAN DEFAULT FALSE,
    owner_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_owner_type (owner_id, knowledge_type),
    INDEX idx_public (is_public)
);

-- 文档表
CREATE TABLE documents (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size BIGINT NOT NULL,
    file_type VARCHAR(100) NOT NULL,
    processing_status ENUM('pending', 'processing', 'completed', 'failed') DEFAULT 'pending',
    processing_error TEXT,
    knowledge_base_id INT NOT NULL,
    uploaded_by INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (knowledge_base_id) REFERENCES knowledge_bases(id) ON DELETE CASCADE,
    FOREIGN KEY (uploaded_by) REFERENCES users(id),
    INDEX idx_kb_status (knowledge_base_id, processing_status)
);

-- 会话表
CREATE TABLE conversations (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    title VARCHAR(200),
    knowledge_base_ids JSON, -- 使用的知识库ID列表
    retrieval_strategy JSON, -- 检索策略配置
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_created (user_id, created_at)
);

-- 消息表
CREATE TABLE messages (
    id INT PRIMARY KEY AUTO_INCREMENT,
    conversation_id INT NOT NULL,
    role ENUM('user', 'assistant') NOT NULL,
    content TEXT NOT NULL,
    metadata JSON, -- 存储来源信息、检索结果等
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
    INDEX idx_conversation_created (conversation_id, created_at)
);
```

### Milvus集合设计

```python
# 向量集合Schema
collection_schema = {
    "collection_name": "knowledge_vectors",
    "fields": [
        {"name": "id", "type": "varchar", "max_length": 100, "is_primary": True},
        {"name": "vector", "type": "float_vector", "dim": 1024},  # 嵌入维度
        {"name": "knowledge_base_id", "type": "int64"},
        {"name": "document_id", "type": "int64"},
        {"name": "chunk_index", "type": "int64"},
        {"name": "content", "type": "varchar", "max_length": 65535},
        {"name": "metadata", "type": "json"}
    ],
    "indexes": [
        {"field": "vector", "index_type": "HNSW", "metric_type": "COSINE"},
        {"field": "knowledge_base_id", "index_type": "STL_SORT"},
        {"field": "document_id", "index_type": "STL_SORT"}
    ]
}
```

### Neo4j图谱设计

```cypher
// 实体节点
CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE;

// 文档节点
CREATE CONSTRAINT document_id IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE;

// 知识库节点
CREATE CONSTRAINT kb_id IF NOT EXISTS FOR (k:KnowledgeBase) REQUIRE k.id IS UNIQUE;

// 关系类型
// (:Entity)-[:RELATED_TO]->(:Entity)
// (:Entity)-[:MENTIONED_IN]->(:Document)
// (:Document)-[:BELONGS_TO]->(:KnowledgeBase)
```

## 🔧 API端点设计

### 核心API端点

```python
# 用户认证
POST   /api/v1/auth/login
POST   /api/v1/auth/logout
POST   /api/v1/auth/refresh
GET    /api/v1/auth/me

# 知识库管理
GET    /api/v1/knowledge-bases/
POST   /api/v1/knowledge-bases/
GET    /api/v1/knowledge-bases/{id}
PUT    /api/v1/knowledge-bases/{id}
DELETE /api/v1/knowledge-bases/{id}

# 文档管理
POST   /api/v1/knowledge-bases/{kb_id}/documents/upload
GET    /api/v1/knowledge-bases/{kb_id}/documents/
GET    /api/v1/documents/{id}
DELETE /api/v1/documents/{id}
GET    /api/v1/documents/{id}/chunks

# 智能对话
POST   /api/v1/chat/conversations/
GET    /api/v1/chat/conversations/
GET    /api/v1/chat/conversations/{id}
DELETE /api/v1/chat/conversations/{id}
POST   /api/v1/chat/conversations/{id}/messages
GET    /api/v1/chat/conversations/{id}/messages
POST   /api/v1/chat/stream  # WebSocket流式对话

# 检索服务
POST   /api/v1/search/vector
POST   /api/v1/search/graph
POST   /api/v1/search/hybrid

# 图谱可视化
GET    /api/v1/graph/entities
GET    /api/v1/graph/relationships
GET    /api/v1/graph/subgraph/{entity_id}
POST   /api/v1/graph/query  # Cypher查询

# 系统管理
GET    /api/v1/admin/stats
GET    /api/v1/admin/health
GET    /api/v1/admin/logs
```

## 🎨 前端界面设计

### 用户对话界面（参考Gemini设计）

#### 布局结构
```typescript
interface ChatLayoutProps {
  sidebar: {
    conversations: Conversation[];
    knowledgeBases: KnowledgeBase[];
    searchHistory: SearchHistory[];
  };
  mainArea: {
    messages: Message[];
    inputArea: ChatInput;
    retrievalSettings: RetrievalSettings;
  };
  rightPanel?: {
    sources: SourceReference[];
    graphVisualization: GraphView;
  };
}

// 检索策略选择器
interface RetrievalSettings {
  semanticSearch: boolean;
  hybridSearch: boolean;
  graphSearch: boolean;
  knowledgeBaseIds: number[];
  searchDepth: number;
  maxResults: number;
}
```

#### 核心组件设计
```typescript
// 消息组件
const MessageComponent: React.FC<{
  message: Message;
  sources?: SourceReference[];
}> = ({ message, sources }) => {
  return (
    <div className="message-container">
      <div className="message-content">
        <ReactMarkdown
          components={{
            code: CodeBlock,
            table: TableComponent,
            img: ImageComponent
          }}
        >
          {message.content}
        </ReactMarkdown>
      </div>
      {sources && (
        <SourcePanel sources={sources} />
      )}
    </div>
  );
};

// 流式输入组件
const StreamingInput: React.FC = () => {
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamContent, setStreamContent] = useState('');

  const handleStream = useCallback(async (query: string) => {
    setIsStreaming(true);
    const response = await fetch('/api/v1/chat/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, settings: retrievalSettings })
    });

    const reader = response.body?.getReader();
    // 处理流式响应...
  }, [retrievalSettings]);

  return (
    <div className="streaming-input">
      <textarea
        placeholder="请输入您的问题..."
        onKeyDown={handleKeyDown}
      />
      <RetrievalSettingsPanel />
      <button onClick={() => handleStream(inputValue)}>
        发送
      </button>
    </div>
  );
};
```

### 管理后台界面

#### 知识库管理
```vue
<template>
  <div class="knowledge-base-management">
    <!-- 知识库列表 -->
    <n-data-table
      :columns="columns"
      :data="knowledgeBases"
      :pagination="pagination"
      :loading="loading"
    />

    <!-- 文件上传区域 -->
    <n-upload
      multiple
      directory-dnd
      :custom-request="handleFileUpload"
      :show-file-list="false"
    >
      <n-upload-dragger>
        <div>
          <n-icon size="48" :depth="3">
            <CloudUploadOutline />
          </n-icon>
        </div>
        <n-text style="font-size: 16px">
          点击或者拖动文件到该区域来上传
        </n-text>
        <n-p depth="3" style="margin: 8px 0 0 0">
          支持 PDF、Word、PPT、Markdown 等格式
        </n-p>
      </n-upload-dragger>
    </n-upload>

    <!-- 处理进度监控 -->
    <ProcessingMonitor :files="processingFiles" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useKnowledgeBaseStore } from '@/stores/knowledgeBase';

const knowledgeBaseStore = useKnowledgeBaseStore();
const loading = ref(false);
const processingFiles = ref<ProcessingFile[]>([]);

const handleFileUpload = async (options: UploadCustomRequestOptions) => {
  const { file, onProgress, onFinish, onError } = options;

  try {
    const formData = new FormData();
    formData.append('file', file.file as File);
    formData.append('knowledge_base_id', selectedKnowledgeBaseId.value);

    const response = await fetch('/api/v1/knowledge-bases/upload', {
      method: 'POST',
      body: formData,
      onUploadProgress: (progressEvent) => {
        const progress = Math.round(
          (progressEvent.loaded * 100) / progressEvent.total
        );
        onProgress({ percent: progress });
      }
    });

    if (response.ok) {
      onFinish();
      // 开始监控处理进度
      startProcessingMonitor(file.id);
    } else {
      onError();
    }
  } catch (error) {
    onError();
  }
};
</script>
```

#### 图谱可视化组件
```typescript
// 使用ECharts实现图谱可视化
const GraphVisualization: React.FC<{
  graphData: GraphData;
  onNodeClick: (node: GraphNode) => void;
}> = ({ graphData, onNodeClick }) => {
  const chartRef = useRef<HTMLDivElement>(null);
  const [chart, setChart] = useState<echarts.ECharts>();

  useEffect(() => {
    if (chartRef.current) {
      const chartInstance = echarts.init(chartRef.current);

      const option: echarts.EChartsOption = {
        title: {
          text: '知识图谱',
          left: 'center'
        },
        tooltip: {
          trigger: 'item',
          formatter: (params: any) => {
            if (params.dataType === 'node') {
              return `实体: ${params.data.name}<br/>类型: ${params.data.category}`;
            } else {
              return `关系: ${params.data.name}`;
            }
          }
        },
        series: [{
          type: 'graph',
          layout: 'force',
          data: graphData.nodes.map(node => ({
            id: node.id,
            name: node.name,
            category: node.type,
            symbolSize: node.importance * 20,
            itemStyle: {
              color: getNodeColor(node.type)
            }
          })),
          links: graphData.edges.map(edge => ({
            source: edge.source,
            target: edge.target,
            name: edge.relationship,
            lineStyle: {
              color: getEdgeColor(edge.relationship)
            }
          })),
          categories: getCategories(graphData.nodes),
          roam: true,
          force: {
            repulsion: 1000,
            edgeLength: 100
          },
          emphasis: {
            focus: 'adjacency'
          }
        }]
      };

      chartInstance.setOption(option);
      chartInstance.on('click', (params) => {
        if (params.dataType === 'node') {
          onNodeClick(params.data);
        }
      });

      setChart(chartInstance);
    }
  }, [graphData, onNodeClick]);

  return (
    <div
      ref={chartRef}
      style={{ width: '100%', height: '600px' }}
    />
  );
};
```

## 🤖 AutoGen智能体架构设计

### 智能体定义
```python
from autogen import ConversableAgent, GroupChat, GroupChatManager
from autogen.agentchat.contrib.graph_flow import GraphFlow

class RAGOrchestrator:
    """RAG系统的主协调器"""

    def __init__(self, config: RAGConfig):
        self.config = config
        self.agents = self._initialize_agents()
        self.graph_flow = self._setup_graph_flow()

    def _initialize_agents(self) -> Dict[str, ConversableAgent]:
        """初始化所有智能体"""

        # 查询分析智能体
        query_analyzer = ConversableAgent(
            name="query_analyzer",
            system_message="""你是查询分析专家。分析用户查询的意图、实体和检索需求。
            输出格式：
            {
                "intent": "问答/搜索/分析",
                "entities": ["实体1", "实体2"],
                "query_type": "factual/analytical/procedural",
                "retrieval_strategy": ["vector", "graph", "hybrid"]
            }""",
            llm_config=self.config.llm_config
        )

        # 向量检索智能体
        vector_retriever = ConversableAgent(
            name="vector_retriever",
            system_message="""你是向量检索专家。基于语义相似度检索相关文档片段。
            使用工具：vector_search, rerank_results""",
            llm_config=self.config.llm_config,
            function_map={
                "vector_search": self._vector_search,
                "rerank_results": self._rerank_results
            }
        )

        # 图谱检索智能体
        graph_retriever = ConversableAgent(
            name="graph_retriever",
            system_message="""你是知识图谱检索专家。通过实体关系查找相关信息。
            使用工具：entity_search, relationship_query, subgraph_extraction""",
            llm_config=self.config.llm_config,
            function_map={
                "entity_search": self._entity_search,
                "relationship_query": self._relationship_query,
                "subgraph_extraction": self._subgraph_extraction
            }
        )

        # 结果融合智能体
        result_fusion = ConversableAgent(
            name="result_fusion",
            system_message="""你是结果融合专家。分析和融合来自不同检索路径的结果。
            任务：
            1. 去重和一致性检查
            2. 重要性评分
            3. 互补性分析
            4. 生成融合后的上下文""",
            llm_config=self.config.llm_config
        )

        # 答案生成智能体
        answer_generator = ConversableAgent(
            name="answer_generator",
            system_message="""你是答案生成专家。基于融合后的上下文生成准确、全面的答案。
            要求：
            1. 答案准确且有依据
            2. 提供明确的来源引用
            3. 结构化和易读性
            4. 处理多模态内容""",
            llm_config=self.config.llm_config
        )

        return {
            "query_analyzer": query_analyzer,
            "vector_retriever": vector_retriever,
            "graph_retriever": graph_retriever,
            "result_fusion": result_fusion,
            "answer_generator": answer_generator
        }

    def _setup_graph_flow(self) -> GraphFlow:
        """设置智能体协作流程"""

        # 定义工作流图
        workflow = {
            "query_analyzer": {
                "next": ["vector_retriever", "graph_retriever"],
                "condition": "parallel"
            },
            "vector_retriever": {
                "next": ["result_fusion"],
                "condition": "always"
            },
            "graph_retriever": {
                "next": ["result_fusion"],
                "condition": "always"
            },
            "result_fusion": {
                "next": ["answer_generator"],
                "condition": "always"
            },
            "answer_generator": {
                "next": [],
                "condition": "terminal"
            }
        }

        return GraphFlow(
            agents=list(self.agents.values()),
            workflow=workflow,
            max_rounds=10
        )

    async def process_query(self, query: str, context: Dict) -> Dict:
        """处理用户查询"""

        # 启动工作流
        result = await self.graph_flow.run(
            initial_message=query,
            context=context
        )

        return {
            "answer": result.final_answer,
            "sources": result.sources,
            "reasoning": result.reasoning_chain,
            "confidence": result.confidence_score
        }
```

### 检索工具实现
```python
class RetrievalTools:
    """检索工具集合"""

    def __init__(self, milvus_client, neo4j_client, reranker_service):
        self.milvus = milvus_client
        self.neo4j = neo4j_client
        self.reranker = reranker_service

    async def vector_search(self, query: str, kb_ids: List[int], limit: int = 10) -> List[Dict]:
        """向量检索"""
        # 查询向量化
        query_vector = await self.embedding_service.embed(query)

        # Milvus检索
        search_params = {
            "metric_type": "COSINE",
            "params": {"nprobe": 16}
        }

        results = self.milvus.search(
            collection_name="knowledge_vectors",
            data=[query_vector],
            anns_field="vector",
            param=search_params,
            limit=limit,
            expr=f"knowledge_base_id in {kb_ids}"
        )

        return [
            {
                "id": hit.id,
                "content": hit.entity.get("content"),
                "score": hit.score,
                "metadata": hit.entity.get("metadata"),
                "source": "vector"
            }
            for hit in results[0]
        ]

    async def graph_search(self, entities: List[str], kb_ids: List[int]) -> List[Dict]:
        """图谱检索"""
        cypher_query = """
        MATCH (e:Entity)-[r]->(related:Entity)
        WHERE e.name IN $entities
        AND e.knowledge_base_id IN $kb_ids
        RETURN e, r, related,
               e.name as entity_name,
               type(r) as relationship,
               related.name as related_entity,
               r.confidence as confidence
        ORDER BY r.confidence DESC
        LIMIT 50
        """

        results = self.neo4j.run(
            cypher_query,
            entities=entities,
            kb_ids=kb_ids
        )

        return [
            {
                "entity": record["entity_name"],
                "relationship": record["relationship"],
                "related_entity": record["related_entity"],
                "confidence": record["confidence"],
                "source": "graph"
            }
            for record in results
        ]

    async def rerank_results(self, query: str, results: List[Dict]) -> List[Dict]:
        """结果重排"""
        if not results:
            return results

        # 准备重排输入
        passages = [result["content"] for result in results]

        # 调用重排服务
        scores = await self.reranker.rerank(
            query=query,
            passages=passages
        )

        # 更新分数并重新排序
        for i, result in enumerate(results):
            result["rerank_score"] = scores[i]

        return sorted(results, key=lambda x: x["rerank_score"], reverse=True)
```

## 📄 文档处理服务设计

### Marker服务封装
```python
class MarkerDocumentProcessor:
    """Marker文档处理服务封装"""

    def __init__(self, config: MarkerConfig):
        self.config = config
        self.supported_formats = {
            '.pdf': self._process_pdf,
            '.docx': self._process_docx,
            '.pptx': self._process_pptx,
            '.md': self._process_markdown,
            '.txt': self._process_text
        }

    async def process_document(self, file_path: str, file_type: str) -> ProcessingResult:
        """处理文档并返回结构化内容"""

        try:
            # 根据文件类型选择处理方法
            processor = self.supported_formats.get(file_type.lower())
            if not processor:
                raise ValueError(f"不支持的文件类型: {file_type}")

            # 执行处理
            result = await processor(file_path)

            # 后处理：清理和优化
            result = await self._post_process(result)

            return ProcessingResult(
                success=True,
                content=result.content,
                metadata=result.metadata,
                tables=result.tables,
                images=result.images,
                processing_time=result.processing_time
            )

        except Exception as e:
            logger.error(f"文档处理失败: {file_path}, 错误: {e}")
            return ProcessingResult(
                success=False,
                error=str(e)
            )

    async def _process_pdf(self, file_path: str) -> RawProcessingResult:
        """处理PDF文件"""
        from marker.convert import convert_single_pdf
        from marker.models import load_all_models

        # 加载模型（可以缓存以提高性能）
        model_lst = load_all_models()

        # 转换PDF
        full_text, images, out_meta = convert_single_pdf(
            fname=file_path,
            model_lst=model_lst,
            max_pages=self.config.max_pages,
            langs=self.config.languages
        )

        # 提取表格
        tables = self._extract_tables_from_markdown(full_text)

        return RawProcessingResult(
            content=full_text,
            metadata=out_meta,
            tables=tables,
            images=images,
            processing_time=time.time() - start_time
        )

    async def _extract_tables_from_markdown(self, markdown_text: str) -> List[Table]:
        """从Markdown中提取表格"""
        tables = []
        table_pattern = r'\|.*?\|.*?\n(?:\|.*?\|.*?\n)*'

        for match in re.finditer(table_pattern, markdown_text, re.MULTILINE):
            table_md = match.group()
            table_data = self._parse_markdown_table(table_md)

            tables.append(Table(
                content=table_md,
                data=table_data,
                position=match.span()
            ))

        return tables

    async def _post_process(self, result: RawProcessingResult) -> RawProcessingResult:
        """后处理：清理和优化内容"""

        # 清理文本
        cleaned_content = self._clean_text(result.content)

        # 优化表格格式
        optimized_tables = [
            self._optimize_table(table) for table in result.tables
        ]

        # 处理图片
        processed_images = await self._process_images(result.images)

        return RawProcessingResult(
            content=cleaned_content,
            metadata=result.metadata,
            tables=optimized_tables,
            images=processed_images,
            processing_time=result.processing_time
        )

class DocumentChunker:
    """智能文档分块器"""

    def __init__(self, config: ChunkingConfig):
        self.config = config
        self.text_splitter = self._initialize_text_splitter()

    def _initialize_text_splitter(self):
        """初始化文本分割器"""
        if self.config.chunking_strategy == "semantic":
            from langchain.text_splitter import SemanticChunker
            return SemanticChunker(
                embeddings=self.config.embedding_model,
                breakpoint_threshold_type="percentile"
            )
        elif self.config.chunking_strategy == "recursive":
            from langchain.text_splitter import RecursiveCharacterTextSplitter
            return RecursiveCharacterTextSplitter(
                chunk_size=self.config.chunk_size,
                chunk_overlap=self.config.chunk_overlap,
                separators=["\n\n", "\n", " ", ""]
            )
        else:
            raise ValueError(f"不支持的分块策略: {self.config.chunking_strategy}")

    async def chunk_document(self, content: str, metadata: Dict) -> List[DocumentChunk]:
        """对文档进行智能分块"""

        # 预处理：保护特殊块
        protected_blocks = self._identify_protected_blocks(content)
        processed_content = self._protect_special_blocks(content, protected_blocks)

        # 执行分块
        chunks = self.text_splitter.split_text(processed_content)

        # 后处理：恢复特殊块
        processed_chunks = []
        for i, chunk in enumerate(chunks):
            restored_chunk = self._restore_special_blocks(chunk, protected_blocks)

            chunk_metadata = {
                **metadata,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "chunk_size": len(restored_chunk),
                "chunk_type": self._classify_chunk_type(restored_chunk)
            }

            processed_chunks.append(DocumentChunk(
                content=restored_chunk,
                metadata=chunk_metadata,
                embedding=None  # 将在后续步骤中生成
            ))

        return processed_chunks

    def _identify_protected_blocks(self, content: str) -> List[ProtectedBlock]:
        """识别需要保护的特殊块（代码、表格、公式等）"""
        protected_blocks = []

        # 代码块
        code_pattern = r'```[\s\S]*?```'
        for match in re.finditer(code_pattern, content):
            protected_blocks.append(ProtectedBlock(
                type="code",
                content=match.group(),
                start=match.start(),
                end=match.end()
            ))

        # 表格
        table_pattern = r'\|.*?\|.*?\n(?:\|.*?\|.*?\n)*'
        for match in re.finditer(table_pattern, content, re.MULTILINE):
            protected_blocks.append(ProtectedBlock(
                type="table",
                content=match.group(),
                start=match.start(),
                end=match.end()
            ))

        # LaTeX公式
        latex_pattern = r'\$\$[\s\S]*?\$\$|\$[^$]*?\$'
        for match in re.finditer(latex_pattern, content):
            protected_blocks.append(ProtectedBlock(
                type="formula",
                content=match.group(),
                start=match.start(),
                end=match.end()
            ))

        return protected_blocks

class GraphExtractor:
    """知识图谱抽取服务"""

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        self.entity_types = [
            "PERSON", "ORGANIZATION", "LOCATION", "PRODUCT",
            "CONCEPT", "EVENT", "DATE", "MONEY", "TECHNOLOGY"
        ]

    async def extract_entities_and_relations(self, chunks: List[DocumentChunk]) -> GraphData:
        """从文档块中抽取实体和关系"""

        all_entities = []
        all_relations = []

        for chunk in chunks:
            # 实体抽取
            entities = await self._extract_entities(chunk.content)

            # 关系抽取
            relations = await self._extract_relations(chunk.content, entities)

            # 添加元数据
            for entity in entities:
                entity.source_chunk_id = chunk.id
                entity.confidence = self._calculate_entity_confidence(entity, chunk)

            for relation in relations:
                relation.source_chunk_id = chunk.id
                relation.confidence = self._calculate_relation_confidence(relation, chunk)

            all_entities.extend(entities)
            all_relations.extend(relations)

        # 实体消歧和合并
        merged_entities = await self._merge_duplicate_entities(all_entities)

        # 关系验证和过滤
        validated_relations = await self._validate_relations(all_relations, merged_entities)

        return GraphData(
            entities=merged_entities,
            relations=validated_relations
        )

    async def _extract_entities(self, text: str) -> List[Entity]:
        """使用LLM抽取实体"""

        prompt = f"""
        从以下文本中抽取实体，并分类到指定类型中。

        实体类型：{', '.join(self.entity_types)}

        文本：
        {text}

        请以JSON格式返回结果：
        {{
            "entities": [
                {{
                    "name": "实体名称",
                    "type": "实体类型",
                    "description": "实体描述",
                    "mentions": ["提及1", "提及2"]
                }}
            ]
        }}
        """

        response = await self.llm_service.generate(prompt)
        result = json.loads(response)

        entities = []
        for entity_data in result["entities"]:
            entities.append(Entity(
                name=entity_data["name"],
                type=entity_data["type"],
                description=entity_data.get("description", ""),
                mentions=entity_data.get("mentions", [])
            ))

        return entities

    async def _extract_relations(self, text: str, entities: List[Entity]) -> List[Relation]:
        """抽取实体间的关系"""

        entity_names = [entity.name for entity in entities]

        prompt = f"""
        从以下文本中抽取实体间的关系。

        已识别的实体：{', '.join(entity_names)}

        文本：
        {text}

        请以JSON格式返回关系：
        {{
            "relations": [
                {{
                    "subject": "主体实体",
                    "predicate": "关系类型",
                    "object": "客体实体",
                    "description": "关系描述"
                }}
            ]
        }}
        """

        response = await self.llm_service.generate(prompt)
        result = json.loads(response)

        relations = []
        for relation_data in result["relations"]:
            relations.append(Relation(
                subject=relation_data["subject"],
                predicate=relation_data["predicate"],
                object=relation_data["object"],
                description=relation_data.get("description", "")
            ))

        return relations
```

## 🚀 部署架构设计

### Docker容器化
```dockerfile
# 后端服务Dockerfile
FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  # 后端API服务
  api:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=mysql://user:password@mysql:3306/ragdb
      - MILVUS_HOST=milvus
      - NEO4J_URI=bolt://neo4j:7687
      - REDIS_URL=redis://redis:6379
    depends_on:
      - mysql
      - milvus
      - neo4j
      - redis
    volumes:
      - ./uploads:/app/uploads
      - ./logs:/app/logs

  # 前端服务
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    depends_on:
      - api

  # MySQL数据库
  mysql:
    image: mysql:8.0
    environment:
      - MYSQL_ROOT_PASSWORD=rootpassword
      - MYSQL_DATABASE=ragdb
      - MYSQL_USER=user
      - MYSQL_PASSWORD=password
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql

  # Milvus向量数据库
  milvus:
    image: milvusdb/milvus:v2.4.0
    command: ["milvus", "run", "standalone"]
    environment:
      - ETCD_ENDPOINTS=etcd:2379
      - MINIO_ADDRESS=minio:9000
    ports:
      - "19530:19530"
    depends_on:
      - etcd
      - minio
    volumes:
      - milvus_data:/var/lib/milvus

  # Neo4j图数据库
  neo4j:
    image: neo4j:5.15
    environment:
      - NEO4J_AUTH=neo4j/password
      - NEO4J_PLUGINS=["apoc"]
    ports:
      - "7474:7474"
      - "7687:7687"
    volumes:
      - neo4j_data:/data

  # Redis缓存
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  # MinIO对象存储
  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      - MINIO_ROOT_USER=minioadmin
      - MINIO_ROOT_PASSWORD=minioadmin
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data

  # Etcd (Milvus依赖)
  etcd:
    image: quay.io/coreos/etcd:v3.5.5
    environment:
      - ETCD_AUTO_COMPACTION_MODE=revision
      - ETCD_AUTO_COMPACTION_RETENTION=1000
      - ETCD_QUOTA_BACKEND_BYTES=4294967296
      - ETCD_SNAPSHOT_COUNT=50000
    command: etcd -advertise-client-urls=http://127.0.0.1:2379 -listen-client-urls http://0.0.0.0:2379 --data-dir /etcd
    volumes:
      - etcd_data:/etcd

volumes:
  mysql_data:
  milvus_data:
  neo4j_data:
  redis_data:
  minio_data:
  etcd_data:
```

### Kubernetes生产部署
```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rag-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: rag-api
  template:
    metadata:
      labels:
        app: rag-api
    spec:
      containers:
      - name: api
        image: rag-system/api:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: rag-api-service
spec:
  selector:
    app: rag-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```
```
