<template>
  <el-dialog
    v-model="dialogVisible"
    title="权限详情"
    width="600px"
    :close-on-click-modal="false"
    destroy-on-close
  >
    <div v-loading="loading" class="permission-detail">
      <el-descriptions
        v-if="permissionData"
        :column="2"
        border
        class="detail-descriptions"
      >
        <el-descriptions-item label="权限ID">
          <el-tag type="info" size="small">{{ permissionData.id }}</el-tag>
        </el-descriptions-item>
        
        <el-descriptions-item label="权限名称">
          <span class="detail-value">{{ permissionData.name }}</span>
        </el-descriptions-item>
        
        <el-descriptions-item label="权限代码">
          <el-tag type="primary" size="small">{{ permissionData.code }}</el-tag>
        </el-descriptions-item>
        
        <el-descriptions-item label="资源">
          <el-tag type="success" size="small">{{ permissionData.resource }}</el-tag>
        </el-descriptions-item>
        
        <el-descriptions-item label="动作">
          <el-tag :type="getActionTagType(permissionData.action)" size="small">
            {{ permissionData.action }}
          </el-tag>
        </el-descriptions-item>
        
        <el-descriptions-item label="状态">
          <el-tag :type="permissionData.is_active ? 'success' : 'danger'" size="small">
            {{ permissionData.is_active ? '启用' : '禁用' }}
          </el-tag>
        </el-descriptions-item>
        
        <el-descriptions-item label="父级权限" :span="2">
          <span v-if="permissionData.parent_name" class="detail-value">
            {{ permissionData.parent_name }}
          </span>
          <el-text v-else type="info">无</el-text>
        </el-descriptions-item>
        
        <el-descriptions-item label="排序">
          <span class="detail-value">{{ permissionData.sort_order || 0 }}</span>
        </el-descriptions-item>
        
        <el-descriptions-item label="角色数量">
          <el-tag type="warning" size="small">{{ permissionData.role_count || 0 }} 个角色</el-tag>
        </el-descriptions-item>
        
        <el-descriptions-item label="权限描述" :span="2">
          <span v-if="permissionData.description" class="detail-value">
            {{ permissionData.description }}
          </span>
          <el-text v-else type="info">暂无描述</el-text>
        </el-descriptions-item>
        
        <el-descriptions-item label="创建时间">
          <span class="detail-value">{{ formatDateTime(permissionData.created_at) }}</span>
        </el-descriptions-item>
        
        <el-descriptions-item label="更新时间">
          <span class="detail-value">{{ formatDateTime(permissionData.updated_at) }}</span>
        </el-descriptions-item>
      </el-descriptions>

      <!-- 子权限列表 -->
      <div v-if="childrenPermissions.length > 0" class="children-section">
        <el-divider content-position="left">
          <el-icon><Menu /></el-icon>
          子权限列表
        </el-divider>
        
        <el-table
          :data="childrenPermissions"
          size="small"
          class="children-table"
        >
          <el-table-column prop="name" label="权限名称" min-width="120" />
          <el-table-column prop="code" label="权限代码" min-width="120">
            <template #default="{ row }">
              <el-tag type="info" size="small">{{ row.code }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="action" label="动作" width="100">
            <template #default="{ row }">
              <el-tag :type="getActionTagType(row.action)" size="small">
                {{ row.action }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="is_active" label="状态" width="80" align="center">
            <template #default="{ row }">
              <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
                {{ row.is_active ? '启用' : '禁用' }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <template #footer>
      <el-button @click="handleClose">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Menu } from '@element-plus/icons-vue'
import { getPermissionDetail, getPermissionChildren } from '@/api/permission'
import { formatDateTime } from '@/utils'
import type { Permission } from '@/types'

interface Props {
  visible: boolean
  permissionId?: number
}

interface Emits {
  (e: 'update:visible', visible: boolean): void
}

const props = withDefaults(defineProps<Props>(), {
  visible: false
})

const emit = defineEmits<Emits>()

// 数据状态
const loading = ref(false)
const permissionData = ref<Permission | null>(null)
const childrenPermissions = ref<Permission[]>([])

// 对话框显示状态
const dialogVisible = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value)
})

/**
 * 获取动作标签类型
 */
const getActionTagType = (action: string) => {
  switch (action) {
    case 'read':
    case 'view':
      return 'primary'
    case 'create':
    case 'add':
      return 'success'
    case 'update':
    case 'edit':
      return 'warning'
    case 'delete':
      return 'danger'
    case 'manage':
    case 'config':
      return 'info'
    default:
      return ''
  }
}

/**
 * 获取权限详情
 */
const fetchPermissionDetail = async () => {
  if (!props.permissionId) return

  try {
    loading.value = true
    
    // 获取权限详情
    const detailResponse = await getPermissionDetail(props.permissionId)
    permissionData.value = detailResponse.data

    // 获取子权限
    try {
      const childrenResponse = await getPermissionChildren(props.permissionId)
      childrenPermissions.value = childrenResponse.data || []
    } catch (error) {
      // 如果没有子权限或接口不存在，忽略错误
      childrenPermissions.value = []
    }
  } catch (error) {
    console.error('Failed to fetch permission detail:', error)
    ElMessage.error('获取权限详情失败')
  } finally {
    loading.value = false
  }
}

/**
 * 处理关闭
 */
const handleClose = () => {
  emit('update:visible', false)
}

// 监听权限ID变化
watch(
  () => props.permissionId,
  (newId) => {
    if (newId && props.visible) {
      fetchPermissionDetail()
    }
  },
  { immediate: true }
)

// 监听对话框显示状态
watch(
  () => props.visible,
  (visible) => {
    if (visible && props.permissionId) {
      fetchPermissionDetail()
    } else if (!visible) {
      // 清空数据
      permissionData.value = null
      childrenPermissions.value = []
    }
  }
)
</script>

<style lang="scss" scoped>
.permission-detail {
  .detail-descriptions {
    margin-bottom: 20px;

    .detail-value {
      font-weight: 500;
      color: var(--el-text-color-primary);
    }
  }

  .children-section {
    margin-top: 20px;

    .children-table {
      margin-top: 16px;
    }
  }
}

:deep(.el-descriptions__label) {
  font-weight: 600;
  color: var(--el-text-color-regular);
}

:deep(.el-descriptions__content) {
  color: var(--el-text-color-primary);
}
</style>
