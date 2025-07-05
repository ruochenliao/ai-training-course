<template>
  <el-dialog
    :model-value="visible"
    title="分配数据权限"
    width="800px"
    :before-close="handleClose"
    @update:model-value="$emit('update:visible', $event)"
  >
    <div class="assign-container">
      <!-- 权限信息 -->
      <div class="permission-info">
        <h4>权限信息</h4>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="权限名称">
            {{ permission?.name }}
          </el-descriptions-item>
          <el-descriptions-item label="权限编码">
            {{ permission?.code }}
          </el-descriptions-item>
          <el-descriptions-item label="权限类型">
            {{ getPermissionTypeText(permission?.permission_type) }}
          </el-descriptions-item>
          <el-descriptions-item label="数据范围">
            {{ getDataScopeText(permission?.data_scope) }}
          </el-descriptions-item>
        </el-descriptions>
      </div>

      <!-- 分配选项卡 -->
      <el-tabs v-model="activeTab" class="assign-tabs">
        <!-- 分配给用户 -->
        <el-tab-pane label="分配给用户" name="users">
          <div class="assign-section">
            <div class="search-bar">
              <el-input
                v-model="userSearch"
                placeholder="搜索用户"
                clearable
                style="width: 300px"
                @input="handleUserSearch"
              >
                <template #prefix>
                  <el-icon><Search /></el-icon>
                </template>
              </el-input>
              <el-button type="primary" @click="handleAssignUsers">
                分配选中用户
              </el-button>
            </div>

            <div class="transfer-container">
              <el-transfer
                v-model="selectedUserIds"
                :data="userOptions"
                :titles="['可选用户', '已分配用户']"
                :button-texts="['移除', '分配']"
                :format="{
                  noChecked: '${total}',
                  hasChecked: '${checked}/${total}'
                }"
                filterable
                filter-placeholder="搜索用户"
                style="text-align: left; display: inline-block"
              >
                <template #default="{ option }">
                  <span>{{ option.label }} ({{ option.username }})</span>
                </template>
              </el-transfer>
            </div>
          </div>
        </el-tab-pane>

        <!-- 分配给角色 -->
        <el-tab-pane label="分配给角色" name="roles">
          <div class="assign-section">
            <div class="search-bar">
              <el-input
                v-model="roleSearch"
                placeholder="搜索角色"
                clearable
                style="width: 300px"
                @input="handleRoleSearch"
              >
                <template #prefix>
                  <el-icon><Search /></el-icon>
                </template>
              </el-input>
              <el-button type="primary" @click="handleAssignRoles">
                分配选中角色
              </el-button>
            </div>

            <div class="transfer-container">
              <el-transfer
                v-model="selectedRoleIds"
                :data="roleOptions"
                :titles="['可选角色', '已分配角色']"
                :button-texts="['移除', '分配']"
                :format="{
                  noChecked: '${total}',
                  hasChecked: '${checked}/${total}'
                }"
                filterable
                filter-placeholder="搜索角色"
                style="text-align: left; display: inline-block"
              >
                <template #default="{ option }">
                  <span>{{ option.label }} ({{ option.code }})</span>
                </template>
              </el-transfer>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">关闭</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { assignDataPermissionToUsers, assignDataPermissionToRoles } from '@/api/data-permission'
import { getUserOptions } from '@/api/user'
import { getRoleOptions } from '@/api/role'

interface Props {
  visible: boolean
  permission?: any
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'success'): void
}

const props = withDefaults(defineProps<Props>(), {
  permission: () => ({})
})

const emit = defineEmits<Emits>()

// 选项卡
const activeTab = ref('users')

// 用户相关
const userSearch = ref('')
const userOptions = ref<any[]>([])
const selectedUserIds = ref<number[]>([])

// 角色相关
const roleSearch = ref('')
const roleOptions = ref<any[]>([])
const selectedRoleIds = ref<number[]>([])

// 监听弹窗显示状态
watch(
  () => props.visible,
  (newVal) => {
    if (newVal) {
      nextTick(() => {
        loadUserOptions()
        loadRoleOptions()
        loadAssignedData()
      })
    }
  }
)

/**
 * 获取权限类型文本
 */
const getPermissionTypeText = (type: string) => {
  const typeMap: Record<string, string> = {
    department: '部门权限',
    role: '角色权限',
    user: '用户权限',
    custom: '自定义权限'
  }
  return typeMap[type] || type
}

/**
 * 获取数据范围文本
 */
const getDataScopeText = (scope: string) => {
  const scopeMap: Record<string, string> = {
    all: '全部数据',
    department: '本部门数据',
    department_and_children: '本部门及下级部门数据',
    self: '仅本人数据',
    custom: '自定义数据'
  }
  return scopeMap[scope] || scope
}

/**
 * 加载用户选项
 */
const loadUserOptions = async () => {
  try {
    const response = await getUserOptions()
    userOptions.value = response.data.map((user: any) => ({
      key: user.id,
      label: user.real_name || user.username,
      username: user.username,
      disabled: false
    }))
  } catch (error) {
    console.error('Failed to load user options:', error)
    ElMessage.error('加载用户列表失败')
  }
}

/**
 * 加载角色选项
 */
const loadRoleOptions = async () => {
  try {
    const response = await getRoleOptions()
    roleOptions.value = response.data.map((role: any) => ({
      key: role.id,
      label: role.name,
      code: role.code,
      disabled: false
    }))
  } catch (error) {
    console.error('Failed to load role options:', error)
    ElMessage.error('加载角色列表失败')
  }
}

/**
 * 加载已分配的数据
 */
const loadAssignedData = async () => {
  // TODO: 实现加载已分配的用户和角色
  selectedUserIds.value = []
  selectedRoleIds.value = []
}

/**
 * 用户搜索
 */
const handleUserSearch = (value: string) => {
  // Transfer组件自带搜索功能，这里可以扩展其他逻辑
}

/**
 * 角色搜索
 */
const handleRoleSearch = (value: string) => {
  // Transfer组件自带搜索功能，这里可以扩展其他逻辑
}

/**
 * 分配给用户
 */
const handleAssignUsers = async () => {
  if (!props.permission?.id) {
    ElMessage.error('权限信息不完整')
    return
  }

  try {
    await assignDataPermissionToUsers(props.permission.id, {
      user_ids: selectedUserIds.value
    })
    ElMessage.success('分配用户成功')
    emit('success')
  } catch (error) {
    console.error('Failed to assign users:', error)
    ElMessage.error('分配用户失败')
  }
}

/**
 * 分配给角色
 */
const handleAssignRoles = async () => {
  if (!props.permission?.id) {
    ElMessage.error('权限信息不完整')
    return
  }

  try {
    await assignDataPermissionToRoles(props.permission.id, {
      role_ids: selectedRoleIds.value
    })
    ElMessage.success('分配角色成功')
    emit('success')
  } catch (error) {
    console.error('Failed to assign roles:', error)
    ElMessage.error('分配角色失败')
  }
}

/**
 * 关闭弹窗
 */
const handleClose = () => {
  emit('update:visible', false)
}
</script>

<style scoped>
.assign-container {
  padding: 20px 0;
}

.permission-info {
  margin-bottom: 20px;
}

.permission-info h4 {
  margin-bottom: 10px;
  color: #303133;
}

.assign-tabs {
  margin-top: 20px;
}

.assign-section {
  padding: 20px 0;
}

.search-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.transfer-container {
  display: flex;
  justify-content: center;
}

.dialog-footer {
  text-align: right;
}
</style>
