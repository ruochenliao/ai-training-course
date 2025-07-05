<template>
  <el-dialog
    :model-value="visible"
    title="审计日志详情"
    width="800px"
    :before-close="handleClose"
    @update:model-value="$emit('update:visible', $event)"
  >
    <div v-if="logData" class="log-detail">
      <!-- 基本信息 -->
      <div class="detail-section">
        <h4>基本信息</h4>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="日志ID">
            {{ logData.id }}
          </el-descriptions-item>
          <el-descriptions-item label="操作时间">
            {{ formatDateTime(logData.created_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="操作类型">
            <el-tag size="small">{{ formatActionDescription(logData.action) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="操作结果">
            <el-tag
              :type="logData.status === 'success' ? 'success' : 'danger'"
              size="small"
            >
              {{ getAuditResultText(logData.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="审计级别">
            <el-tag
              :type="getLevelTagType(logData.level)"
              size="small"
            >
              {{ getAuditLevelText(logData.level) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="资源类型">
            {{ formatResourceType(logData.resource_type) }}
          </el-descriptions-item>
          <el-descriptions-item label="资源ID" :span="2">
            {{ logData.resource_id || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="资源名称" :span="2">
            {{ logData.resource_name || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="操作描述" :span="2">
            {{ logData.description }}
          </el-descriptions-item>
        </el-descriptions>
      </div>

      <!-- 用户信息 -->
      <div class="detail-section">
        <h4>用户信息</h4>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="用户ID">
            {{ logData.user_id || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="用户名">
            {{ logData.username || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="IP地址">
            {{ logData.user_ip || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="用户代理" :span="2">
            <div class="user-agent">
              {{ logData.user_agent || '-' }}
            </div>
          </el-descriptions-item>
        </el-descriptions>
      </div>

      <!-- 请求信息 -->
      <div class="detail-section">
        <h4>请求信息</h4>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="请求方法">
            <el-tag v-if="logData.request_method" size="small" type="info">
              {{ logData.request_method }}
            </el-tag>
            <span v-else>-</span>
          </el-descriptions-item>
          <el-descriptions-item label="响应状态">
            <el-tag
              v-if="logData.response_status"
              size="small"
              :type="getStatusTagType(logData.response_status)"
            >
              {{ logData.response_status }}
            </el-tag>
            <span v-else>-</span>
          </el-descriptions-item>
          <el-descriptions-item label="响应时间">
            {{ logData.response_time ? `${logData.response_time}ms` : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="请求URL" :span="2">
            <div class="url-text">
              {{ logData.request_url || '-' }}
            </div>
          </el-descriptions-item>
        </el-descriptions>
      </div>

      <!-- 请求参数 -->
      <div v-if="logData.request_params" class="detail-section">
        <h4>请求参数</h4>
        <el-card class="json-card">
          <pre class="json-content">{{ formatJSON(logData.request_params) }}</pre>
        </el-card>
      </div>

      <!-- 数据变更 -->
      <div v-if="logData.old_values || logData.new_values" class="detail-section">
        <h4>数据变更</h4>
        <el-row :gutter="20">
          <el-col :span="12" v-if="logData.old_values">
            <div class="change-section">
              <h5>变更前</h5>
              <el-card class="json-card">
                <pre class="json-content">{{ formatJSON(logData.old_values) }}</pre>
              </el-card>
            </div>
          </el-col>
          <el-col :span="12" v-if="logData.new_values">
            <div class="change-section">
              <h5>变更后</h5>
              <el-card class="json-card">
                <pre class="json-content">{{ formatJSON(logData.new_values) }}</pre>
              </el-card>
            </div>
          </el-col>
        </el-row>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">关闭</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import {
  getAuditLevelText,
  getAuditResultText,
  formatActionDescription,
  formatResourceType
} from '@/api/audit-log'
import { formatDateTime } from '@/utils'
import type { AuditLogItem } from '@/api/audit-log'

interface Props {
  visible: boolean
  logData?: AuditLogItem | null
}

interface Emits {
  (e: 'update:visible', value: boolean): void
}

const props = withDefaults(defineProps<Props>(), {
  logData: null
})

const emit = defineEmits<Emits>()

/**
 * 获取级别标签类型
 */
const getLevelTagType = (level: string) => {
  const typeMap: Record<string, string> = {
    low: '',
    medium: 'warning',
    high: 'danger',
    critical: 'danger'
  }
  return typeMap[level] || ''
}

/**
 * 获取状态码标签类型
 */
const getStatusTagType = (status: number) => {
  if (status >= 200 && status < 300) return 'success'
  if (status >= 300 && status < 400) return 'warning'
  if (status >= 400) return 'danger'
  return 'info'
}

/**
 * 格式化JSON
 */
const formatJSON = (obj: any) => {
  if (!obj) return ''
  try {
    return JSON.stringify(obj, null, 2)
  } catch (error) {
    return String(obj)
  }
}

/**
 * 关闭对话框
 */
const handleClose = () => {
  emit('update:visible', false)
}
</script>

<style scoped>
.log-detail {
  max-height: 600px;
  overflow-y: auto;
}

.detail-section {
  margin-bottom: 24px;
}

.detail-section h4 {
  margin: 0 0 12px 0;
  color: #303133;
  font-size: 16px;
  font-weight: 600;
}

.detail-section h5 {
  margin: 0 0 8px 0;
  color: #606266;
  font-size: 14px;
  font-weight: 500;
}

.user-agent {
  word-break: break-all;
  line-height: 1.5;
}

.url-text {
  word-break: break-all;
  line-height: 1.5;
  color: #409EFF;
}

.json-card {
  background-color: #f8f9fa;
}

.json-content {
  margin: 0;
  padding: 0;
  background: transparent;
  border: none;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 12px;
  line-height: 1.5;
  color: #333;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 300px;
  overflow-y: auto;
}

.change-section {
  height: 100%;
}

.dialog-footer {
  text-align: right;
}

/* 滚动条样式 */
.log-detail::-webkit-scrollbar,
.json-content::-webkit-scrollbar {
  width: 6px;
}

.log-detail::-webkit-scrollbar-track,
.json-content::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.log-detail::-webkit-scrollbar-thumb,
.json-content::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.log-detail::-webkit-scrollbar-thumb:hover,
.json-content::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>
