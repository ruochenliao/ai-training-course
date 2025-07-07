<template>
  <el-dialog
    v-model="dialogVisible"
    title="部门详情"
    width="800px"
    :close-on-click-modal="false"
  >
    <div v-loading="loading" class="department-detail">
      <div v-if="departmentDetail" class="detail-content">
        <!-- 基本信息 -->
        <div class="info-section">
          <h3 class="section-title">基本信息</h3>
          <el-row :gutter="20">
            <el-col :span="12">
              <div class="info-item">
                <label>部门名称：</label>
                <span>{{ departmentDetail.name }}</span>
              </div>
            </el-col>
            <el-col :span="12">
              <div class="info-item">
                <label>部门编码：</label>
                <span>{{ departmentDetail.code }}</span>
              </div>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="12">
              <div class="info-item">
                <label>上级部门：</label>
                <span>{{ departmentDetail.parent_name || '无' }}</span>
              </div>
            </el-col>
            <el-col :span="12">
              <div class="info-item">
                <label>部门负责人：</label>
                <span>{{ departmentDetail.manager_name || '未设置' }}</span>
              </div>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="12">
              <div class="info-item">
                <label>状态：</label>
                <el-tag :type="departmentDetail.is_active ? 'success' : 'danger'" size="small">
                  {{ departmentDetail.is_active ? '启用' : '禁用' }}
                </el-tag>
              </div>
            </el-col>
            <el-col :span="12">
              <div class="info-item">
                <label>排序：</label>
                <span>{{ departmentDetail.sort_order }}</span>
              </div>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="24">
              <div class="info-item">
                <label>部门描述：</label>
                <span>{{ departmentDetail.description || '无' }}</span>
              </div>
            </el-col>
          </el-row>
        </div>

        <!-- 统计信息 -->
        <div class="info-section">
          <h3 class="section-title">统计信息</h3>
          <el-row :gutter="20">
            <el-col :span="8">
              <div class="stat-item">
                <div class="stat-value">{{ departmentDetail.user_count || 0 }}</div>
                <div class="stat-label">部门人数</div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="stat-item">
                <div class="stat-value">{{ departmentDetail.children_count || 0 }}</div>
                <div class="stat-label">子部门数</div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="stat-item">
                <div class="stat-value">{{ departmentDetail.level || 1 }}</div>
                <div class="stat-label">部门层级</div>
              </div>
            </el-col>
          </el-row>
        </div>

        <!-- 时间信息 -->
        <div class="info-section">
          <h3 class="section-title">时间信息</h3>
          <el-row :gutter="20">
            <el-col :span="12">
              <div class="info-item">
                <label>创建时间：</label>
                <span>{{ formatDateTime(departmentDetail.created_at) }}</span>
              </div>
            </el-col>
            <el-col :span="12">
              <div class="info-item">
                <label>更新时间：</label>
                <span>{{ formatDateTime(departmentDetail.updated_at) }}</span>
              </div>
            </el-col>
          </el-row>
        </div>

        <!-- 部门成员 -->
        <div v-if="departmentUsers.length > 0" class="info-section">
          <h3 class="section-title">部门成员</h3>
          <el-table :data="departmentUsers" style="width: 100%" size="small">
            <el-table-column prop="username" label="用户名" width="120" />
            <el-table-column prop="full_name" label="姓名" width="120" />
            <el-table-column prop="email" label="邮箱" />
            <el-table-column prop="is_active" label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
                  {{ row.is_active ? '激活' : '禁用' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </div>
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
import { ref, computed, watch } from 'vue'
import { getDepartmentDetail, getDepartmentUsers } from '@/api/department'
import { formatDateTime } from '@/utils'
import type { DepartmentDetail } from '@/types'

interface Props {
  visible: boolean
  departmentId?: number
}

const props = withDefaults(defineProps<Props>(), {
  visible: false,
  departmentId: undefined
})

const emit = defineEmits<{
  'update:visible': [value: boolean]
}>()

// 响应式数据
const loading = ref(false)
const departmentDetail = ref<DepartmentDetail | null>(null)
const departmentUsers = ref<any[]>([])

// 计算属性
const dialogVisible = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value)
})

// 监听部门ID变化
watch(() => props.departmentId, (newId) => {
  if (newId && props.visible) {
    fetchDepartmentDetail()
    fetchDepartmentUsers()
  }
}, { immediate: true })

// 监听对话框显示状态
watch(() => props.visible, (visible) => {
  if (visible && props.departmentId) {
    fetchDepartmentDetail()
    fetchDepartmentUsers()
  } else if (!visible) {
    // 清空数据
    departmentDetail.value = null
    departmentUsers.value = []
  }
})

/**
 * 获取部门详情
 */
const fetchDepartmentDetail = async () => {
  if (!props.departmentId) return

  try {
    loading.value = true
    const response = await getDepartmentDetail(props.departmentId)
    departmentDetail.value = response.data
  } catch (error) {
    console.error('获取部门详情失败:', error)
  } finally {
    loading.value = false
  }
}

/**
 * 获取部门成员
 */
const fetchDepartmentUsers = async () => {
  if (!props.departmentId) return

  try {
    const response = await getDepartmentUsers(props.departmentId)
    departmentUsers.value = response.data || []
  } catch (error) {
    console.error('获取部门成员失败:', error)
    departmentUsers.value = []
  }
}

/**
 * 关闭对话框
 */
const handleClose = () => {
  dialogVisible.value = false
}
</script>

<style scoped>
.department-detail {
  .detail-content {
    .info-section {
      margin-bottom: 24px;

      .section-title {
        font-size: 16px;
        font-weight: 600;
        color: #303133;
        margin-bottom: 16px;
        padding-bottom: 8px;
        border-bottom: 1px solid #ebeef5;
      }

      .info-item {
        display: flex;
        align-items: center;
        margin-bottom: 12px;

        label {
          font-weight: 500;
          color: #606266;
          min-width: 80px;
          margin-right: 8px;
        }

        span {
          color: #303133;
        }
      }

      .stat-item {
        text-align: center;
        padding: 16px;
        background: #f8f9fa;
        border-radius: 8px;

        .stat-value {
          font-size: 24px;
          font-weight: 600;
          color: #409eff;
          margin-bottom: 4px;
        }

        .stat-label {
          font-size: 14px;
          color: #909399;
        }
      }
    }
  }
}

.dialog-footer {
  text-align: right;
}
</style>
