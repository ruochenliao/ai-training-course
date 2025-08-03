<template>
  <div class="validation-results">
    <div v-if="results.length === 0" class="no-issues">
      <el-result
        icon="success"
        title="验证通过"
        sub-title="工作流配置正确，没有发现问题"
      />
    </div>
    
    <div v-else class="issues-list">
      <div class="summary">
        <h4>验证结果</h4>
        <div class="issue-counts">
          <el-tag v-if="errorCount > 0" type="danger" size="small">
            {{ errorCount }} 个错误
          </el-tag>
          <el-tag v-if="warningCount > 0" type="warning" size="small">
            {{ warningCount }} 个警告
          </el-tag>
          <el-tag v-if="infoCount > 0" type="info" size="small">
            {{ infoCount }} 个提示
          </el-tag>
        </div>
      </div>
      
      <div class="issues">
        <div 
          v-for="(result, index) in results" 
          :key="index"
          class="issue-item"
          :class="`issue-${result.type}`"
        >
          <div class="issue-icon">
            <el-icon v-if="result.type === 'error'"><Close /></el-icon>
            <el-icon v-else-if="result.type === 'warning'"><Warning /></el-icon>
            <el-icon v-else><InfoFilled /></el-icon>
          </div>
          
          <div class="issue-content">
            <div class="issue-message">{{ result.message }}</div>
            <div v-if="result.suggestion" class="issue-suggestion">
              建议：{{ result.suggestion }}
            </div>
            <div v-if="result.nodeId" class="issue-location">
              节点：{{ getNodeName(result.nodeId) }}
            </div>
          </div>
          
          <div class="issue-actions">
            <el-button 
              v-if="result.fixable" 
              size="small" 
              type="primary" 
              text
              @click="fixIssue(result)"
            >
              修复
            </el-button>
            <el-button 
              v-if="result.nodeId" 
              size="small" 
              text
              @click="locateNode(result.nodeId)"
            >
              定位
            </el-button>
          </div>
        </div>
      </div>
      
      <div class="validation-actions">
        <el-button @click="revalidate">
          <el-icon><Refresh /></el-icon>
          重新验证
        </el-button>
        <el-button type="primary" @click="fixAllIssues" :disabled="!hasFixableIssues">
          <el-icon><Tools /></el-icon>
          修复所有问题
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Close, Warning, InfoFilled, Refresh, Tools } from '@element-plus/icons-vue'

// Props
interface ValidationResult {
  type: 'error' | 'warning' | 'info'
  message: string
  suggestion?: string
  nodeId?: string
  fixable?: boolean
  fix?: () => void
}

interface Props {
  results: ValidationResult[]
}

const props = defineProps<Props>()
const emit = defineEmits(['revalidate', 'locate-node', 'fix-issue'])

// 计算属性
const errorCount = computed(() => 
  props.results.filter(r => r.type === 'error').length
)

const warningCount = computed(() => 
  props.results.filter(r => r.type === 'warning').length
)

const infoCount = computed(() => 
  props.results.filter(r => r.type === 'info').length
)

const hasFixableIssues = computed(() => 
  props.results.some(r => r.fixable)
)

// 方法
const getNodeName = (nodeId: string) => {
  // 这里应该从工作流设计器获取节点名称
  return nodeId
}

const fixIssue = (result: ValidationResult) => {
  if (result.fix) {
    result.fix()
    ElMessage.success('问题已修复')
  } else {
    emit('fix-issue', result)
  }
}

const locateNode = (nodeId: string) => {
  emit('locate-node', nodeId)
}

const revalidate = () => {
  emit('revalidate')
}

const fixAllIssues = () => {
  const fixableIssues = props.results.filter(r => r.fixable)
  let fixedCount = 0
  
  fixableIssues.forEach(result => {
    if (result.fix) {
      result.fix()
      fixedCount++
    }
  })
  
  if (fixedCount > 0) {
    ElMessage.success(`已修复 ${fixedCount} 个问题`)
    revalidate()
  }
}
</script>

<style scoped>
.validation-results {
  padding: 16px;
}

.no-issues {
  text-align: center;
  padding: 40px 20px;
}

.summary {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e4e7ed;
}

.summary h4 {
  margin: 0;
  color: #303133;
}

.issue-counts {
  display: flex;
  gap: 8px;
}

.issues {
  margin-bottom: 20px;
}

.issue-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  border-radius: 6px;
  margin-bottom: 8px;
}

.issue-error {
  background: #fef0f0;
  border-left: 4px solid #f56c6c;
}

.issue-warning {
  background: #fdf6ec;
  border-left: 4px solid #e6a23c;
}

.issue-info {
  background: #f0f9ff;
  border-left: 4px solid #409eff;
}

.issue-icon {
  margin-top: 2px;
}

.issue-error .issue-icon {
  color: #f56c6c;
}

.issue-warning .issue-icon {
  color: #e6a23c;
}

.issue-info .issue-icon {
  color: #409eff;
}

.issue-content {
  flex: 1;
}

.issue-message {
  font-weight: 500;
  color: #303133;
  margin-bottom: 4px;
}

.issue-suggestion {
  font-size: 12px;
  color: #606266;
  margin-bottom: 4px;
}

.issue-location {
  font-size: 12px;
  color: #909399;
}

.issue-actions {
  display: flex;
  gap: 8px;
}

.validation-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
  padding-top: 16px;
  border-top: 1px solid #e4e7ed;
}
</style>
