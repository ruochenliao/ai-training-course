<template>
  <el-dialog
    v-model="dialogVisible"
    title="角色详情"
    width="700px"
    :close-on-click-modal="false"
    destroy-on-close
  >
    <div v-loading="loading" class="role-detail">
      <el-descriptions
        v-if="roleData"
        :column="2"
        border
        class="detail-descriptions"
      >
        <el-descriptions-item label="角色ID">
          <el-tag type="info" size="small">{{ roleData.id }}</el-tag>
        </el-descriptions-item>
        
        <el-descriptions-item label="角色名称">
          <span class="detail-value">{{ roleData.name }}</span>
        </el-descriptions-item>
        
        <el-descriptions-item label="角色代码">
          <el-tag type="primary" size="small">{{ roleData.code }}</el-tag>
        </el-descriptions-item>
        
        <el-descriptions-item label="状态">
          <el-tag :type="roleData.is_active ? 'success' : 'danger'" size="small">
            {{ roleData.is_active ? '启用' : '禁用' }}
          </el-tag>
        </el-descriptions-item>
        
        <el-descriptions-item label="用户数量">
          <el-tag type="warning" size="small">{{ roleData.user_count || 0 }} 个用户</el-tag>
        </el-descriptions-item>
        
        <el-descriptions-item label="权限数量">
          <el-tag type="success" size="small">{{ roleData.permission_count || 0 }} 个权限</el-tag>
        </el-descriptions-item>
        
        <el-descriptions-item label="排序">
          <span class="detail-value">{{ roleData.sort_order || 0 }}</span>
        </el-descriptions-item>
        
        <el-descriptions-item label="创建时间">
          <span class="detail-value">{{ formatDateTime(roleData.created_at) }}</span>
        </el-descriptions-item>
        
        <el-descriptions-item label="角色描述" :span="2">
          <span v-if="roleData.description" class="detail-value">
            {{ roleData.description }}
          </span>
          <el-text v-else type="info">暂无描述</el-text>
        </el-descriptions-item>
      </el-descriptions>

      <!-- 权限列表 -->
      <div v-if="permissions.length > 0" class="permissions-section">
        <el-divider content-position="left">
          <el-icon><Key /></el-icon>
          拥有权限
        </el-divider>
        
        <div class="permissions-grid">
          <el-tag
            v-for="permission in permissions"
            :key="permission.id"
            type="primary"
            size="small"
            class="permission-tag"
          >
            {{ permission.name }}
          </el-tag>
        </div>
      </div>

      <!-- 用户列表 -->
      <div v-if="users.length > 0" class="users-section">
        <el-divider content-position="left">
          <el-icon><User /></el-icon>
          关联用户
        </el-divider>
        
        <el-table
          :data="users"
          size="small"
          class="users-table"
        >
          <el-table-column prop="username" label="用户名" min-width="120" />
          <el-table-column prop="nickname" label="昵称" min-width="120" />
          <el-table-column prop="email" label="邮箱" min-width="150" />
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
import { Key, User } from '@element-plus/icons-vue'
import { getRoleDetail, getRolePermissions, getRoleUsers } from '@/api/role'
import { formatDateTime } from '@/utils'
import type { Role, Permission, User as UserType } from '@/types'

interface Props {
  visible: boolean
  roleId?: number
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
const roleData = ref<Role | null>(null)
const permissions = ref<Permission[]>([])
const users = ref<UserType[]>([])

// 对话框显示状态
const dialogVisible = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value)
})

/**
 * 获取角色详情
 */
const fetchRoleDetail = async () => {
  if (!props.roleId) return

  try {
    loading.value = true
    
    // 获取角色详情
    const detailResponse = await getRoleDetail(props.roleId)
    roleData.value = detailResponse.data

    // 获取角色权限
    try {
      const permissionsResponse = await getRolePermissions(props.roleId)
      permissions.value = permissionsResponse.data || []
    } catch (error) {
      permissions.value = []
    }

    // 获取角色用户
    try {
      const usersResponse = await getRoleUsers(props.roleId)
      users.value = usersResponse.data || []
    } catch (error) {
      users.value = []
    }
  } catch (error) {
    console.error('Failed to fetch role detail:', error)
    ElMessage.error('获取角色详情失败')
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

// 监听角色ID变化
watch(
  () => props.roleId,
  (newId) => {
    if (newId && props.visible) {
      fetchRoleDetail()
    }
  },
  { immediate: true }
)

// 监听对话框显示状态
watch(
  () => props.visible,
  (visible) => {
    if (visible && props.roleId) {
      fetchRoleDetail()
    } else if (!visible) {
      // 清空数据
      roleData.value = null
      permissions.value = []
      users.value = []
    }
  }
)
</script>

<style lang="scss" scoped>
.role-detail {
  .detail-descriptions {
    margin-bottom: 20px;

    .detail-value {
      font-weight: 500;
      color: var(--el-text-color-primary);
    }
  }

  .permissions-section,
  .users-section {
    margin-top: 20px;
  }

  .permissions-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 16px;

    .permission-tag {
      margin: 0;
    }
  }

  .users-table {
    margin-top: 16px;
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
