<template>
  <PageContainer
    title="审计日志"
    description="系统操作审计记录，用于安全监控和合规审查"
    :icon="Document"
    badge="Security"
    badge-type="danger"
  >
    <!-- 操作按钮 -->
    <template #actions>
      <ActionButtons
        :actions="headerActions"
        :permissions="userPermissions"
        @action="handleHeaderAction"
      />
    </template>

    <!-- 统计卡片 -->
    <div class="stats-overview">
      <el-row :gutter="16">
        <el-col :span="6" :xs="12" :sm="6">
          <el-card class="stats-card success" shadow="hover">
            <div class="stats-content">
              <div class="stats-icon">
                <el-icon><CircleCheck /></el-icon>
              </div>
              <div class="stats-info">
                <div class="stats-number">{{ stats.success_count || 0 }}</div>
                <div class="stats-label">成功操作</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6" :xs="12" :sm="6">
          <el-card class="stats-card danger" shadow="hover">
            <div class="stats-content">
              <div class="stats-icon">
                <el-icon><CircleClose /></el-icon>
              </div>
              <div class="stats-info">
                <div class="stats-number">{{ stats.failure_count || 0 }}</div>
                <div class="stats-label">失败操作</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6" :xs="12" :sm="6">
          <el-card class="stats-card warning" shadow="hover">
            <div class="stats-content">
              <div class="stats-icon">
                <el-icon><Warning /></el-icon>
              </div>
              <div class="stats-info">
                <div class="stats-number">{{ stats.high_risk_count || 0 }}</div>
                <div class="stats-label">高风险操作</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6" :xs="12" :sm="6">
          <el-card class="stats-card info" shadow="hover">
            <div class="stats-content">
              <div class="stats-icon">
                <el-icon><Document /></el-icon>
              </div>
              <div class="stats-info">
                <div class="stats-number">{{ stats.total_count || 0 }}</div>
                <div class="stats-label">总日志数</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 搜索筛选区域 -->
    <SearchForm
      v-model="searchForm"
      :fields="searchFields"
      :loading="loading"
      :show-advanced="true"
      @search="handleSearch"
      @reset="handleReset"
    />
    <!-- 审计日志数据表格 -->
    <DataTable
      :data="auditLogs"
      :columns="tableColumns"
      :loading="loading"
      :pagination="pagination"
      :show-selection="true"
      :show-index="true"
      @sort-change="handleSortChange"
      @page-change="handlePageChange"
      @size-change="handleSizeChange"
    >
      <!-- 操作类型列自定义渲染 -->
      <template #action="{ row }">
        <el-tag :type="getActionTagType(row.action)" size="small">
          {{ getActionLabel(row.action) }}
        </el-tag>
      </template>

      <!-- 资源类型列自定义渲染 -->
      <template #resource="{ row }">
        <el-tag type="info" size="small">
          {{ getResourceLabel(row.resource) }}
        </el-tag>
      </template>

      <!-- 级别列自定义渲染 -->
      <template #level="{ row }">
        <StatusTag
          :status="row.level"
          :status-map="levelStatusMap"
          size="small"
        />
      </template>

      <!-- 结果列自定义渲染 -->
      <template #result="{ row }">
        <StatusTag :status="row.result" size="small" />
      </template>

      <!-- 用户信息列自定义渲染 -->
      <template #user_info="{ row }">
        <div class="user-info">
          <div class="user-name">{{ row.user_name || '系统' }}</div>
          <div class="user-ip">{{ row.ip_address }}</div>
        </div>
      </template>

      <!-- 详情列自定义渲染 -->
      <template #details="{ row }">
        <el-button
          type="primary"
          size="small"
          text
          @click="handleViewDetails(row)"
        >
          查看详情
        </el-button>
      </template>
    </DataTable>

    <!-- 日志详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="审计日志详情"
      width="800px"
      :close-on-click-modal="false"
      class="audit-detail-dialog"
    >
      <div v-if="currentLog" class="audit-detail">
        <!-- 基本信息 -->
        <div class="detail-section">
          <h4 class="section-title">基本信息</h4>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="操作类型">
              <el-tag :type="getActionTagType(currentLog.action)" size="small">
                {{ getActionLabel(currentLog.action) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="资源类型">
              <el-tag type="info" size="small">
                {{ getResourceLabel(currentLog.resource) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="操作级别">
              <StatusTag
                :status="currentLog.level"
                :status-map="levelStatusMap"
                size="small"
              />
            </el-descriptions-item>
            <el-descriptions-item label="操作结果">
              <StatusTag :status="currentLog.result" size="small" />
            </el-descriptions-item>
            <el-descriptions-item label="操作用户">
              {{ currentLog.user_name || '系统' }}
            </el-descriptions-item>
            <el-descriptions-item label="IP地址">
              {{ currentLog.ip_address }}
            </el-descriptions-item>
            <el-descriptions-item label="用户代理">
              {{ currentLog.user_agent || '未知' }}
            </el-descriptions-item>
            <el-descriptions-item label="操作时间">
              {{ formatDateTime(currentLog.created_at) }}
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <!-- 操作详情 -->
        <div class="detail-section">
          <h4 class="section-title">操作详情</h4>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="资源ID">
              {{ currentLog.resource_id || '无' }}
            </el-descriptions-item>
            <el-descriptions-item label="操作描述">
              {{ currentLog.description || '无描述' }}
            </el-descriptions-item>
            <el-descriptions-item label="请求参数" v-if="currentLog.request_data">
              <pre class="json-data">{{ formatJson(currentLog.request_data) }}</pre>
            </el-descriptions-item>
            <el-descriptions-item label="响应数据" v-if="currentLog.response_data">
              <pre class="json-data">{{ formatJson(currentLog.response_data) }}</pre>
            </el-descriptions-item>
            <el-descriptions-item label="错误信息" v-if="currentLog.error_message">
              <el-alert
                :title="currentLog.error_message"
                type="error"
                :closable="false"
                show-icon
              />
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </div>

      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </PageContainer>
</template>

<script setup lang="ts">
import { onMounted, ref, reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Document, DocumentCopy, Refresh, CircleCheck, CircleClose,
  Warning, Search, View
} from '@element-plus/icons-vue'
import {
  getAuditLogList,
  getAuditLogStats,
  exportAuditLogsCSV
} from '@/api/audit-log'
import { formatDateTime } from '@/utils'
import { useAuthStore } from '@/stores/auth'
import PageContainer from '@/components/common/PageContainer.vue'
import DataTable from '@/components/common/DataTable.vue'
import SearchForm from '@/components/common/SearchForm.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import ActionButtons from '@/components/common/ActionButtons.vue'
import type { SearchField } from '@/components/common/SearchForm.vue'
import type { ActionButton } from '@/components/common/ActionButtons.vue'

const authStore = useAuthStore()

// 用户权限
const userPermissions = computed(() => authStore.permissions)

// 搜索表单配置
const searchForm = reactive({
  action: '',
  resource: '',
  level: '',
  result: '',
  user_name: '',
  ip_address: '',
  start_time: '',
  end_time: ''
})

const searchFields: SearchField[] = [
  {
    prop: 'action',
    label: '操作类型',
    type: 'select',
    placeholder: '请选择操作类型',
    options: [
      { label: '创建', value: 'create' },
      { label: '更新', value: 'update' },
      { label: '删除', value: 'delete' },
      { label: '查看', value: 'view' },
      { label: '登录', value: 'login' },
      { label: '登出', value: 'logout' }
    ]
  },
  {
    prop: 'resource',
    label: '资源类型',
    type: 'select',
    placeholder: '请选择资源类型',
    options: [
      { label: '用户', value: 'user' },
      { label: '角色', value: 'role' },
      { label: '权限', value: 'permission' },
      { label: '菜单', value: 'menu' },
      { label: '部门', value: 'department' }
    ]
  },
  {
    prop: 'level',
    label: '操作级别',
    type: 'select',
    placeholder: '请选择级别',
    options: [
      { label: '低风险', value: 'low' },
      { label: '中风险', value: 'medium' },
      { label: '高风险', value: 'high' },
      { label: '严重', value: 'critical' }
    ]
  },
  {
    prop: 'result',
    label: '操作结果',
    type: 'select',
    placeholder: '请选择结果',
    options: [
      { label: '成功', value: 'success' },
      { label: '失败', value: 'failure' }
    ]
  },
  {
    prop: 'user_name',
    label: '操作用户',
    type: 'input',
    placeholder: '请输入用户名',
    advanced: true
  },
  {
    prop: 'ip_address',
    label: 'IP地址',
    type: 'input',
    placeholder: '请输入IP地址',
    advanced: true
  },
  {
    prop: 'time_range',
    label: '时间范围',
    type: 'daterange',
    placeholder: '请选择时间范围',
    valueFormat: 'YYYY-MM-DD HH:mm:ss',
    advanced: true
  }
]

// 数据状态
const loading = ref(false)
const auditLogs = ref<any[]>([])
const stats = ref<any>({})

// 分页
const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

// 表格列配置
const tableColumns = [
  { prop: 'id', label: 'ID', width: 80, sortable: true },
  { prop: 'action', label: '操作类型', width: 120, slot: 'action' },
  { prop: 'resource', label: '资源类型', width: 100, slot: 'resource' },
  { prop: 'resource_name', label: '资源名称', minWidth: 150, showOverflowTooltip: true },
  { prop: 'level', label: '级别', width: 100, slot: 'level' },
  { prop: 'result', label: '结果', width: 80, slot: 'result' },
  { prop: 'user_info', label: '用户信息', width: 150, slot: 'user_info' },
  { prop: 'description', label: '操作描述', minWidth: 200, showOverflowTooltip: true },
  { prop: 'created_at', label: '操作时间', width: 160, formatter: (row: any) => formatDateTime(row.created_at), sortable: true },
  { prop: 'details', label: '操作', width: 100, fixed: 'right', slot: 'details' }
]

// 头部操作按钮
const headerActions: ActionButton[] = [
  {
    key: 'refresh',
    label: '刷新数据',
    type: 'primary',
    icon: Refresh
  },
  {
    key: 'export',
    label: '导出日志',
    type: 'success',
    icon: DocumentCopy,
    permission: 'audit:export'
  }
]

// 级别状态映射
const levelStatusMap = {
  low: { text: '低风险', type: 'success' },
  medium: { text: '中风险', type: 'warning' },
  high: { text: '高风险', type: 'danger' },
  critical: { text: '严重', type: 'danger' }
}

// 详情对话框
const detailDialogVisible = ref(false)
const currentLog = ref<any>(null)

/**
 * 获取审计日志列表
 */
const fetchAuditLogs = async () => {
  try {
    loading.value = true
    const params = {
      page: pagination.page,
      page_size: pagination.page_size,
      ...searchForm
    }
    const response = await getAuditLogList(params)
    auditLogs.value = response.data.items
    pagination.total = response.data.total
  } catch (error) {
    console.error('Failed to fetch audit logs:', error)
    ElMessage.error('获取审计日志失败')
  } finally {
    loading.value = false
  }
}

/**
 * 获取统计数据
 */
const fetchStats = async () => {
  try {
    const response = await getAuditLogStats()
    stats.value = response.data
  } catch (error) {
    console.error('Failed to fetch audit stats:', error)
  }
}

/**
 * 搜索处理
 */
const handleSearch = () => {
  pagination.page = 1
  fetchAuditLogs()
}

/**
 * 重置处理
 */
const handleReset = () => {
  Object.assign(searchForm, {
    action: '',
    resource: '',
    level: '',
    result: '',
    user_name: '',
    ip_address: '',
    start_time: '',
    end_time: ''
  })
  pagination.page = 1
  fetchAuditLogs()
}

/**
 * 头部操作处理
 */
const handleHeaderAction = (action: ActionButton) => {
  switch (action.key) {
    case 'refresh':
      handleRefresh()
      break
    case 'export':
      handleExport()
      break
  }
}

/**
 * 刷新数据
 */
const handleRefresh = () => {
  fetchAuditLogs()
  fetchStats()
}

/**
 * 导出日志
 */
const handleExport = async () => {
  try {
    loading.value = true
    const params = { ...searchForm }
    await exportAuditLogsCSV(params)
    ElMessage.success('导出成功')
  } catch (error) {
    console.error('Failed to export audit logs:', error)
    ElMessage.error('导出失败')
  } finally {
    loading.value = false
  }
}

/**
 * 查看详情
 */
const handleViewDetails = (row: any) => {
  currentLog.value = row
  detailDialogVisible.value = true
}

/**
 * 分页处理
 */
const handlePageChange = (page: number) => {
  pagination.page = page
  fetchAuditLogs()
}

/**
 * 页面大小变化处理
 */
const handleSizeChange = (size: number) => {
  pagination.page_size = size
  pagination.page = 1
  fetchAuditLogs()
}

/**
 * 排序变化处理
 */
const handleSortChange = ({ prop, order }: any) => {
  console.log('Sort change:', prop, order)
  // 这里可以添加排序逻辑
}

/**
 * 获取操作类型标签类型
 */
const getActionTagType = (action: string) => {
  const typeMap: Record<string, string> = {
    create: 'success',
    update: 'warning',
    delete: 'danger',
    view: 'info',
    login: 'primary',
    logout: 'info'
  }
  return typeMap[action] || 'default'
}

/**
 * 获取操作类型标签文本
 */
const getActionLabel = (action: string) => {
  const labelMap: Record<string, string> = {
    create: '创建',
    update: '更新',
    delete: '删除',
    view: '查看',
    login: '登录',
    logout: '登出'
  }
  return labelMap[action] || action
}

/**
 * 获取资源类型标签文本
 */
const getResourceLabel = (resource: string) => {
  const labelMap: Record<string, string> = {
    user: '用户',
    role: '角色',
    permission: '权限',
    menu: '菜单',
    department: '部门'
  }
  return labelMap[resource] || resource
}

/**
 * 格式化JSON数据
 */
const formatJson = (data: any) => {
  try {
    return JSON.stringify(data, null, 2)
  } catch {
    return String(data)
  }
}

onMounted(() => {
  fetchAuditLogs()
  fetchStats()
})
</script>
<style lang="scss" scoped>
// 统计概览样式
.stats-overview {
  margin-bottom: 20px;

  .stats-card {
    height: 100px;
    cursor: pointer;
    transition: all 0.3s ease;

    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
    }

    &.success {
      border-left: 4px solid var(--el-color-success);
    }

    &.danger {
      border-left: 4px solid var(--el-color-danger);
    }

    &.warning {
      border-left: 4px solid var(--el-color-warning);
    }

    &.info {
      border-left: 4px solid var(--el-color-info);
    }

    :deep(.el-card__body) {
      padding: 20px;
      height: 100%;
    }

    .stats-content {
      display: flex;
      align-items: center;
      height: 100%;

      .stats-icon {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 16px;
        font-size: 24px;
        color: white;

        .el-icon {
          font-size: 28px;
        }
      }

      .stats-info {
        flex: 1;

        .stats-number {
          font-size: 28px;
          font-weight: bold;
          color: var(--el-text-color-primary);
          line-height: 1;
          margin-bottom: 4px;
        }

        .stats-label {
          font-size: 14px;
          color: var(--el-text-color-regular);
        }
      }
    }
  }

  .success .stats-icon {
    background: linear-gradient(135deg, var(--el-color-success), var(--el-color-success-light-3));
  }

  .danger .stats-icon {
    background: linear-gradient(135deg, var(--el-color-danger), var(--el-color-danger-light-3));
  }

  .warning .stats-icon {
    background: linear-gradient(135deg, var(--el-color-warning), var(--el-color-warning-light-3));
  }

  .info .stats-icon {
    background: linear-gradient(135deg, var(--el-color-info), var(--el-color-info-light-3));
  }
}

// 用户信息样式
.user-info {
  .user-name {
    font-weight: 500;
    color: var(--el-text-color-primary);
    margin-bottom: 2px;
  }

  .user-ip {
    font-size: 12px;
    color: var(--el-text-color-regular);
  }
}

// 审计详情对话框样式
.audit-detail-dialog {
  .audit-detail {
    .detail-section {
      margin-bottom: 24px;

      .section-title {
        font-size: 16px;
        font-weight: 600;
        color: var(--el-text-color-primary);
        margin-bottom: 16px;
        padding-bottom: 8px;
        border-bottom: 1px solid var(--el-border-color-lighter);
      }

      .el-descriptions {
        margin-bottom: 16px;
      }

      .json-data {
        background-color: var(--el-bg-color-page);
        border: 1px solid var(--el-border-color);
        border-radius: 4px;
        padding: 12px;
        font-family: 'Courier New', monospace;
        font-size: 12px;
        line-height: 1.4;
        max-height: 200px;
        overflow-y: auto;
        white-space: pre-wrap;
        word-break: break-all;
      }
    }
  }
}

// 响应式设计
@media (max-width: 1200px) {
  .stats-overview {
    .el-col {
      margin-bottom: 16px;
    }
  }
}

@media (max-width: 768px) {
  .stats-overview {
    .stats-card {
      .stats-content {
        .stats-icon {
          width: 50px;
          height: 50px;
          margin-right: 12px;

          .el-icon {
            font-size: 24px;
          }
        }

        .stats-info {
          .stats-number {
            font-size: 24px;
          }

          .stats-label {
            font-size: 12px;
          }
        }
      }
    }
  }

  .user-info {
    .user-name,
    .user-ip {
      font-size: 12px;
    }
  }

  .audit-detail-dialog {
    :deep(.el-dialog) {
      width: 95% !important;
      margin: 5vh auto;
    }

    .audit-detail {
      .detail-section {
        .json-data {
          font-size: 10px;
          max-height: 150px;
        }
      }
    }
  }
}

// 暗色主题适配
.dark {
  .stats-overview {
    .stats-card {
      background-color: var(--el-bg-color-page);
      border-color: var(--el-border-color);

      &:hover {
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
      }
    }
  }

  .audit-detail-dialog {
    .audit-detail {
      .detail-section {
        .json-data {
          background-color: var(--el-bg-color-overlay);
          border-color: var(--el-border-color);
          color: var(--el-text-color-primary);
        }
      }
    }
  }
}
</style>
