<template>
  <div class="workflow-templates">
    <div class="template-categories">
      <el-tabs v-model="activeCategory" @tab-change="handleCategoryChange">
        <el-tab-pane label="推荐模板" name="recommended">
          <div class="template-grid">
            <div 
              v-for="template in recommendedTemplates" 
              :key="template.id"
              class="template-card"
              @click="selectTemplate(template)"
            >
              <div class="template-icon">
                <el-icon>{{ template.icon }}</el-icon>
              </div>
              <h4>{{ template.name }}</h4>
              <p>{{ template.description }}</p>
              <div class="template-meta">
                <el-tag size="small">{{ template.category }}</el-tag>
                <span class="node-count">{{ template.nodeCount }} 个节点</span>
              </div>
            </div>
          </div>
        </el-tab-pane>
        
        <el-tab-pane label="客服自动化" name="customer_service">
          <div class="template-grid">
            <div 
              v-for="template in customerServiceTemplates" 
              :key="template.id"
              class="template-card"
              @click="selectTemplate(template)"
            >
              <div class="template-icon">
                <el-icon>{{ template.icon }}</el-icon>
              </div>
              <h4>{{ template.name }}</h4>
              <p>{{ template.description }}</p>
              <div class="template-meta">
                <el-tag size="small" type="success">{{ template.category }}</el-tag>
                <span class="node-count">{{ template.nodeCount }} 个节点</span>
              </div>
            </div>
          </div>
        </el-tab-pane>
        
        <el-tab-pane label="数据处理" name="data_processing">
          <div class="template-grid">
            <div 
              v-for="template in dataProcessingTemplates" 
              :key="template.id"
              class="template-card"
              @click="selectTemplate(template)"
            >
              <div class="template-icon">
                <el-icon>{{ template.icon }}</el-icon>
              </div>
              <h4>{{ template.name }}</h4>
              <p>{{ template.description }}</p>
              <div class="template-meta">
                <el-tag size="small" type="warning">{{ template.category }}</el-tag>
                <span class="node-count">{{ template.nodeCount }} 个节点</span>
              </div>
            </div>
          </div>
        </el-tab-pane>
        
        <el-tab-pane label="内容创作" name="content_creation">
          <div class="template-grid">
            <div 
              v-for="template in contentCreationTemplates" 
              :key="template.id"
              class="template-card"
              @click="selectTemplate(template)"
            >
              <div class="template-icon">
                <el-icon>{{ template.icon }}</el-icon>
              </div>
              <h4>{{ template.name }}</h4>
              <p>{{ template.description }}</p>
              <div class="template-meta">
                <el-tag size="small" type="info">{{ template.category }}</el-tag>
                <span class="node-count">{{ template.nodeCount }} 个节点</span>
              </div>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'

const emit = defineEmits(['select', 'close'])

// 响应式数据
const activeCategory = ref('recommended')

// 模板数据
const templates = [
  // 推荐模板
  {
    id: 'simple_chat',
    name: '简单对话流程',
    description: '基础的用户对话处理流程，包含路由和响应',
    category: '推荐',
    icon: 'chat-dot-round',
    nodeCount: 3,
    nodes: [
      { id: 'start', type: 'start', name: '开始', x: 100, y: 100 },
      { id: 'router', type: 'router_agent', name: '路由智能体', x: 300, y: 100 },
      { id: 'end', type: 'end', name: '结束', x: 500, y: 100 }
    ],
    connections: [
      { id: 'conn1', from: 'start', to: 'router' },
      { id: 'conn2', from: 'router', to: 'end' }
    ]
  },
  {
    id: 'multi_agent_workflow',
    name: '多智能体协作',
    description: '包含路由、规划和执行的完整智能体协作流程',
    category: '推荐',
    icon: 'connection',
    nodeCount: 6,
    nodes: [
      { id: 'start', type: 'start', name: '开始', x: 100, y: 200 },
      { id: 'router', type: 'router_agent', name: '路由智能体', x: 300, y: 200 },
      { id: 'planner', type: 'planning_agent', name: '规划智能体', x: 500, y: 100 },
      { id: 'executor', type: 'customer_service_agent', name: '执行智能体', x: 500, y: 300 },
      { id: 'condition', type: 'condition', name: '结果判断', x: 700, y: 200 },
      { id: 'end', type: 'end', name: '结束', x: 900, y: 200 }
    ],
    connections: [
      { id: 'conn1', from: 'start', to: 'router' },
      { id: 'conn2', from: 'router', to: 'planner', condition: 'output.type === "planning"' },
      { id: 'conn3', from: 'router', to: 'executor', condition: 'output.type === "execution"' },
      { id: 'conn4', from: 'planner', to: 'condition' },
      { id: 'conn5', from: 'executor', to: 'condition' },
      { id: 'conn6', from: 'condition', to: 'end' }
    ]
  },

  // 客服自动化模板
  {
    id: 'customer_support',
    name: '智能客服流程',
    description: '自动处理客户咨询，包含意图识别和问题解答',
    category: '客服自动化',
    icon: 'service',
    nodeCount: 5,
    nodes: [
      { id: 'start', type: 'start', name: '客户咨询', x: 100, y: 200 },
      { id: 'intent', type: 'router_agent', name: '意图识别', x: 300, y: 200 },
      { id: 'faq', type: 'knowledge_qa_agent', name: 'FAQ问答', x: 500, y: 100 },
      { id: 'human', type: 'customer_service_agent', name: '人工客服', x: 500, y: 300 },
      { id: 'end', type: 'end', name: '结束', x: 700, y: 200 }
    ],
    connections: [
      { id: 'conn1', from: 'start', to: 'intent' },
      { id: 'conn2', from: 'intent', to: 'faq', condition: 'output.confidence > 0.8' },
      { id: 'conn3', from: 'intent', to: 'human', condition: 'output.confidence <= 0.8' },
      { id: 'conn4', from: 'faq', to: 'end' },
      { id: 'conn5', from: 'human', to: 'end' }
    ]
  },
  {
    id: 'complaint_handling',
    name: '投诉处理流程',
    description: '自动化投诉处理，包含情感分析和升级机制',
    category: '客服自动化',
    icon: 'warning',
    nodeCount: 7,
    nodes: [
      { id: 'start', type: 'start', name: '投诉接收', x: 100, y: 200 },
      { id: 'sentiment', type: 'customer_service_agent', name: '情感分析', x: 300, y: 200 },
      { id: 'condition', type: 'condition', name: '严重程度判断', x: 500, y: 200 },
      { id: 'auto_resolve', type: 'customer_service_agent', name: '自动处理', x: 700, y: 100 },
      { id: 'escalate', type: 'customer_service_agent', name: '升级处理', x: 700, y: 300 },
      { id: 'notify', type: 'email_send', name: '通知客户', x: 900, y: 200 },
      { id: 'end', type: 'end', name: '结束', x: 1100, y: 200 }
    ]
  },

  // 数据处理模板
  {
    id: 'data_analysis',
    name: '数据分析流程',
    description: '自动化数据分析，从查询到报告生成',
    category: '数据处理',
    icon: 'data-analysis',
    nodeCount: 6,
    nodes: [
      { id: 'start', type: 'start', name: '分析请求', x: 100, y: 200 },
      { id: 'parse', type: 'text2sql_agent', name: 'SQL生成', x: 300, y: 200 },
      { id: 'query', type: 'database_query', name: '数据查询', x: 500, y: 200 },
      { id: 'analyze', type: 'text2sql_agent', name: '数据分析', x: 700, y: 200 },
      { id: 'report', type: 'content_creation_agent', name: '报告生成', x: 900, y: 200 },
      { id: 'end', type: 'end', name: '结束', x: 1100, y: 200 }
    ]
  },

  // 内容创作模板
  {
    id: 'content_pipeline',
    name: '内容创作流水线',
    description: '从主题到发布的完整内容创作流程',
    category: '内容创作',
    icon: 'edit',
    nodeCount: 8,
    nodes: [
      { id: 'start', type: 'start', name: '创作需求', x: 100, y: 200 },
      { id: 'research', type: 'knowledge_qa_agent', name: '资料研究', x: 300, y: 200 },
      { id: 'outline', type: 'content_creation_agent', name: '大纲生成', x: 500, y: 200 },
      { id: 'draft', type: 'content_creation_agent', name: '初稿创作', x: 700, y: 200 },
      { id: 'review', type: 'condition', name: '质量检查', x: 900, y: 200 },
      { id: 'revise', type: 'content_creation_agent', name: '修改完善', x: 700, y: 350 },
      { id: 'publish', type: 'webhook', name: '发布内容', x: 1100, y: 200 },
      { id: 'end', type: 'end', name: '结束', x: 1300, y: 200 }
    ]
  }
]

// 计算属性
const recommendedTemplates = computed(() => 
  templates.filter(t => t.category === '推荐')
)

const customerServiceTemplates = computed(() => 
  templates.filter(t => t.category === '客服自动化')
)

const dataProcessingTemplates = computed(() => 
  templates.filter(t => t.category === '数据处理')
)

const contentCreationTemplates = computed(() => 
  templates.filter(t => t.category === '内容创作')
)

// 方法
const handleCategoryChange = (category: string) => {
  activeCategory.value = category
}

const selectTemplate = (template: any) => {
  emit('select', {
    name: template.name,
    description: template.description,
    nodes: template.nodes.map(node => ({
      ...node,
      id: `${node.type}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      config: {}
    })),
    connections: template.connections?.map(conn => ({
      ...conn,
      id: `conn_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    })) || []
  })
  
  ElMessage.success(`已加载模板：${template.name}`)
}
</script>

<style scoped>
.workflow-templates {
  height: 500px;
  overflow-y: auto;
}

.template-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
  padding: 16px 0;
}

.template-card {
  padding: 20px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  background: white;
}

.template-card:hover {
  border-color: #409eff;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.15);
}

.template-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  background: linear-gradient(135deg, #409eff, #66b1ff);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 12px;
  color: white;
  font-size: 24px;
}

.template-card h4 {
  margin: 0 0 8px 0;
  font-size: 16px;
  color: #303133;
}

.template-card p {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #606266;
  line-height: 1.5;
}

.template-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.node-count {
  font-size: 12px;
  color: #909399;
}
</style>
