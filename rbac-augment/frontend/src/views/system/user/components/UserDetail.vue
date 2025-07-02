<template>
  <el-dialog
    v-model="dialogVisible"
    title="用户详情"
    width="800px"
    :close-on-click-modal="false"
  >
    <div v-loading="loading" class="user-detail">
      <div v-if="userDetail" class="detail-content">
        <!-- 基本信息 -->
        <div class="info-section">
          <h3 class="section-title">基本信息</h3>
          <el-row :gutter="20">
            <el-col :span="12">
              <div class="info-item">
                <label>用户名：</label>
                <span>{{ userDetail.username }}</span>
              </div>
            </el-col>
            <el-col :span="12">
              <div class="info-item">
                <label>邮箱：</label>
                <span>{{ userDetail.email }}</span>
              </div>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="12">
              <div class="info-item">
                <label>姓名：</label>
                <span>{{ userDetail.full_name || '-' }}</span>
              </div>
            </el-col>
            <el-col :span="12">
              <div class="info-item">
                <label>手机号：</label>
                <span>{{ userDetail.phone || '-' }}</span>
              </div>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="12">
              <div class="info-item">
                <label>状态：</label>
                <el-tag :type="userDetail.is_active ? 'success' : 'danger'" size="small">
                  {{ userDetail.is_active ? '激活' : '禁用' }}
                </el-tag>
              </div>
            </el-col>
            <el-col :span="12">
              <div class="info-item">
                <label>超级用户：</label>
                <el-tag :type="userDetail.is_superuser ? 'warning' : 'info'" size="small">
                  {{ userDetail.is_superuser ? '是' : '否' }}
                </el-tag>
              </div>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="12">
              <div class="info-item">
                <label>最后登录：</label>
                <span>{{ userDetail.last_login_at ? formatDateTime(userDetail.last_login_at) : '-' }}</span>
              </div>
            </el-col>
            <el-col :span="12">
              <div class="info-item">
                <label>创建时间：</label>
                <span>{{ formatDateTime(userDetail.created_at) }}</span>
              </div>
            </el-col>
          </el-row>
        </div>

        <!-- 角色信息 -->
        <div class="info-section">
          <h3 class="section-title">角色信息</h3>
          <div class="role-list">
            <el-tag
              v-for="role in userDetail.roles"
              :key="role.id"
              size="default"
              style="margin-right: 8px; margin-bottom: 8px"
            >
              {{ role.name }}
            </el-tag>
            <span v-if="!userDetail.roles.length" class="empty-text">暂无角色</span>
          </div>
        </div>

        <!-- 权限信息 -->
        <div class="info-section">
          <h3 class="section-title">权限信息</h3>
          <div class="permission-list">
            <el-tag
              v-for="permission in userDetail.permissions"
              :key="permission"
              type="info"
              size="small"
              style="margin-right: 4px; margin-bottom: 4px"
            >
              {{ permission }}
            </el-tag>
            <span v-if="!userDetail.permissions.length" class="empty-text">暂无权限</span>
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="dialogVisible = false">关闭</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { getUserDetail } from '@/api/user'
import { formatDateTime } from '@/utils'
import type { UserDetail } from '@/types'

interface Props {
  visible: boolean
  userId?: number
}

interface Emits {
  (e: 'update:visible', value: boolean): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 对话框显示状态
const dialogVisible = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value)
})

// 加载状态
const loading = ref(false)

// 用户详情
const userDetail = ref<UserDetail>()

/**
 * 获取用户详情
 */
const fetchUserDetail = async () => {
  if (!props.userId) return

  try {
    loading.value = true
    const response = await getUserDetail(props.userId)
    userDetail.value = response.data
  } catch (error) {
    console.error('Failed to fetch user detail:', error)
  } finally {
    loading.value = false
  }
}

// 监听用户ID变化
watch(
  () => props.userId,
  (userId) => {
    if (userId && props.visible) {
      fetchUserDetail()
    }
  },
  { immediate: true }
)

// 监听对话框显示状态
watch(
  () => props.visible,
  (visible) => {
    if (visible && props.userId) {
      fetchUserDetail()
    }
  }
)
</script>

<style lang="scss" scoped>
.user-detail {
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
        }

        span {
          color: #303133;
        }
      }

      .role-list,
      .permission-list {
        .empty-text {
          color: #909399;
          font-style: italic;
        }
      }

      .permission-list {
        max-height: 200px;
        overflow-y: auto;
      }
    }
  }
}

.dialog-footer {
  text-align: right;
}

// 暗色主题
.dark {
  .user-detail {
    .detail-content {
      .info-section {
        .section-title {
          color: #e5eaf3;
          border-bottom-color: #4c4d4f;
        }

        .info-item {
          label {
            color: #a3a6ad;
          }

          span {
            color: #e5eaf3;
          }
        }

        .empty-text {
          color: #a3a6ad;
        }
      }
    }
  }
}
</style>
