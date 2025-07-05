<template>
  <div class="audit-log-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>审计日志</h2>
      <p>系统操作审计记录，用于安全监控和合规审查</p>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card class="stats-card">
            <div class="stats-content">
              <div class="stats-icon success">
                <el-icon><Check /></el-icon>
              </div>
              <div class="stats-info">
                <div class="stats-number">{{ stats.result_stats?.success || 0 }}</div>
                <div class="stats-label">成功操作</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stats-card">
            <div class="stats-content">
              <div class="stats-icon danger">
                <el-icon><Close /></el-icon>
              </div>
              <div class="stats-info">
                <div class="stats-number">{{ stats.result_stats?.failure || 0 }}</div>
                <div class="stats-label">失败操作</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stats-card">
            <div class="stats-content">
              <div class="stats-icon warning">
                <el-icon><Warning /></el-icon>
              </div>
              <div class="stats-info">
                <div class="stats-number">{{ stats.high_risk_count || 0 }}</div>
                <div class="stats-label">高风险操作</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stats-card">
            <div class="stats-content">
              <div class="stats-icon info">
                <el-icon><Document /></el-icon>
              </div>
              <div class="stats-info">
                <div class="stats-number">{{ stats.total_logs || 0 }}</div>
                <div class="stats-label">总日志数</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 搜索表单 -->
    <el-card class="search-card">
      <el-form :model="searchForm" inline>
        <el-form-item label="操作类型">
          <el-select
            v-model="searchForm.action"
            placeholder="请选择操作类型"
            clearable
            style="width: 200px"
          >
            <el-option
              v-for="option in AUDIT_ACTION_OPTIONS"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="资源类型">
          <el-select
            v-model="searchForm.resource"
            placeholder="请选择资源类型"
            clearable
            style="width: 150px"
          >
            <el-option
              v-for="option in AUDIT_RESOURCE_OPTIONS"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="级别">
          <el-select
            v-model="searchForm.level"
            placeholder="请选择级别"
            clearable
            style="width: 120px"
          >
            <el-option
              v-for="option in AUDIT_LEVEL_OPTIONS"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="结果">
          <el-select
            v-model="searchForm.result"
            placeholder="请选择结果"
            clearable
            style="width: 120px"
          >
            <el-option
              v-for="option in AUDIT_RESULT_OPTIONS"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="时间范围">
          <el-date-picker
            v-model="timeRange"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            format="YYYY-MM-DD HH:mm:ss"
            value-format="YYYY-MM-DD HH:mm:ss"
            style="width: 350px"
          />
        </el-form-item>

        <el-form-item label="IP地址">
          <el-input
            v-model="searchForm.ip_address"
            placeholder="请输入IP地址"
            clearable
            style="width: 150px"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="handleReset">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
          <el-button type="success" @click="handleExport">
            <el-icon><Download /></el-icon>
            导出
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 数据表格 -->
    <el-card class="table-card">
      <el-table
        v-loading="loading"
        :data="tableData"
        stripe
        border
        style="width: 100%"
        @sort-change="handleSortChange"
      >
        <el-table-column prop="id" label="ID" width="80" sortable="custom" />
        
        <el-table-column prop="action" label="操作类型" width="150">
          <template #default="{ row }">
            <el-tag size="small">{{ formatActionDescription(row.action) }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="resource_type" label="资源类型" width="120">
          <template #default="{ row }">
            {{ formatResourceType(row.resource_type) }}
          </template>
        </el-table-column>

        <el-table-column prop="resource_name" label="资源名称" width="150" show-overflow-tooltip />

        <el-table-column prop="description" label="操作描述" min-width="200" show-overflow-tooltip />

        <el-table-column prop="level" label="级别" width="80">
          <template #default="{ row }">
            <el-tag
              :type="getLevelTagType(row.level)"
              size="small"
            >
              {{ getAuditLevelText(row.level) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="status" label="结果" width="80">
          <template #default="{ row }">
            <el-tag
              :type="row.status === 'success' ? 'success' : 'danger'"
              size="small"
            >
              {{ getAuditResultText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="username" label="操作用户" width="120" />

        <el-table-column prop="user_ip" label="IP地址" width="130" />

        <el-table-column prop="created_at" label="操作时间" width="160" sortable="custom">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="handleViewDetail(row)">
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 详情对话框 -->
    <AuditLogDetail
      v-model:visible="detailVisible"
      :log-data="currentLog"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Search,
  Refresh,
  Download,
  Check,
  Close,
  Warning,
  Document
} from '@element-plus/icons-vue'
import {
  getAuditLogList,
  getAuditLogStats,
  exportAuditLogsCSV,
  AUDIT_LEVEL_OPTIONS,
  AUDIT_RESULT_OPTIONS,
  AUDIT_ACTION_OPTIONS,
  AUDIT_RESOURCE_OPTIONS,
  getAuditLevelText,
  getAuditResultText,
  formatActionDescription,
  formatResourceType
} from '@/api/audit-log'
import { formatDateTime } from '@/utils'
import AuditLogDetail from './components/AuditLogDetail.vue'
import type { AuditLogItem, AuditLogSearchParams, AuditLogStats } from '@/api/audit-log'

// 搜索表单
const searchForm = reactive<AuditLogSearchParams>({
  page: 1,
  page_size: 20,
  action: '',
  resource: '',
  level: '',
  result: '',
  ip_address: ''
})

// 时间范围
const timeRange = ref<[string, string] | null>(null)

// 分页信息
const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

// 表格数据
const tableData = ref<AuditLogItem[]>([])
const loading = ref(false)

// 统计数据
const stats = ref<AuditLogStats>({} as AuditLogStats)

// 详情对话框
const detailVisible = ref(false)
const currentLog = ref<AuditLogItem | null>(null)

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
 * 获取审计日志列表
 */
const fetchAuditLogList = async () => {
  loading.value = true
  try {
    const params = {
      ...searchForm,
      page: pagination.page,
      page_size: pagination.page_size
    }

    // 处理时间范围
    if (timeRange.value) {
      params.start_time = timeRange.value[0]
      params.end_time = timeRange.value[1]
    }

    const response = await getAuditLogList(params)
    tableData.value = response.data.items
    pagination.total = response.data.total
  } catch (error) {
    console.error('Failed to fetch audit logs:', error)
    ElMessage.error('获取审计日志列表失败')
  } finally {
    loading.value = false
  }
}

/**
 * 获取统计数据
 */
const fetchStats = async () => {
  try {
    const response = await getAuditLogStats(7)
    stats.value = response.data
  } catch (error) {
    console.error('Failed to fetch audit log stats:', error)
  }
}

/**
 * 搜索
 */
const handleSearch = () => {
  pagination.page = 1
  fetchAuditLogList()
}

/**
 * 重置
 */
const handleReset = () => {
  Object.assign(searchForm, {
    action: '',
    resource: '',
    level: '',
    result: '',
    ip_address: ''
  })
  timeRange.value = null
  pagination.page = 1
  fetchAuditLogList()
}

/**
 * 导出
 */
const handleExport = async () => {
  try {
    const params: any = {}
    if (timeRange.value) {
      params.start_time = timeRange.value[0]
      params.end_time = timeRange.value[1]
    }

    const blob = await exportAuditLogsCSV(params)
    
    // 创建下载链接
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `audit_logs_${new Date().toISOString().slice(0, 10)}.csv`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('导出成功')
  } catch (error) {
    console.error('Failed to export audit logs:', error)
    ElMessage.error('导出失败')
  }
}

/**
 * 查看详情
 */
const handleViewDetail = (row: AuditLogItem) => {
  currentLog.value = row
  detailVisible.value = true
}

/**
 * 排序变化
 */
const handleSortChange = ({ prop, order }: any) => {
  // TODO: 实现排序逻辑
  console.log('Sort change:', prop, order)
}

/**
 * 页码变化
 */
const handleCurrentChange = (page: number) => {
  pagination.page = page
  fetchAuditLogList()
}

/**
 * 页大小变化
 */
const handleSizeChange = (size: number) => {
  pagination.page_size = size
  pagination.page = 1
  fetchAuditLogList()
}

// 初始化
onMounted(() => {
  fetchAuditLogList()
  fetchStats()
})
</script>

<style scoped>
.audit-log-container {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0 0 8px 0;
  color: #303133;
}

.page-header p {
  margin: 0;
  color: #606266;
  font-size: 14px;
}

.stats-cards {
  margin-bottom: 20px;
}

.stats-card {
  height: 100px;
}

.stats-content {
  display: flex;
  align-items: center;
  height: 100%;
}

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
}

.stats-icon.success {
  background: linear-gradient(135deg, #67C23A, #85CE61);
}

.stats-icon.danger {
  background: linear-gradient(135deg, #F56C6C, #F78989);
}

.stats-icon.warning {
  background: linear-gradient(135deg, #E6A23C, #EEBE77);
}

.stats-icon.info {
  background: linear-gradient(135deg, #409EFF, #66B1FF);
}

.stats-info {
  flex: 1;
}

.stats-number {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
  line-height: 1;
}

.stats-label {
  font-size: 14px;
  color: #606266;
  margin-top: 4px;
}

.search-card {
  margin-bottom: 20px;
}

.table-card {
  margin-bottom: 20px;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}
</style>
