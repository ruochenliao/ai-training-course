<template>
  <div class="layout-header">
    <!-- 左侧区域 -->
    <div class="header-left">
      <!-- 折叠按钮 -->
      <el-button
        type="text"
        class="collapse-btn"
        @click="appStore.toggleSidebar"
      >
        <el-icon size="18">
          <Fold v-if="!appStore.sidebarCollapsed" />
          <Expand v-else />
        </el-icon>
      </el-button>

      <!-- 面包屑导航 -->
      <el-breadcrumb separator="/" class="breadcrumb">
        <el-breadcrumb-item
          v-for="item in breadcrumbList"
          :key="item.path"
          :to="item.path === route.path ? undefined : item.path"
        >
          {{ item.title }}
        </el-breadcrumb-item>
      </el-breadcrumb>
    </div>

    <!-- 右侧区域 -->
    <div class="header-right">
      <!-- 全屏按钮 -->
      <el-tooltip content="全屏" placement="bottom">
        <el-button
          type="text"
          class="header-btn"
          @click="toggleFullscreen"
        >
          <el-icon size="18">
            <FullScreen v-if="!isFullscreen" />
            <Aim v-else />
          </el-icon>
        </el-button>
      </el-tooltip>

      <!-- 主题切换 -->
      <el-tooltip content="主题切换" placement="bottom">
        <el-button
          type="text"
          class="header-btn"
          @click="toggleTheme"
        >
          <el-icon size="18">
            <Sunny v-if="appStore.themeMode === 'light'" />
            <Moon v-else />
          </el-icon>
        </el-button>
      </el-tooltip>

      <!-- 用户菜单 -->
      <el-dropdown trigger="click" @command="handleUserCommand">
        <div class="user-info">
          <el-avatar
            :size="32"
            :src="authStore.userInfo?.avatar"
            class="user-avatar"
          >
            <el-icon><User /></el-icon>
          </el-avatar>
          <span class="user-name">{{ authStore.userInfo?.full_name || authStore.userInfo?.username }}</span>
          <el-icon class="dropdown-icon"><ArrowDown /></el-icon>
        </div>
        
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="profile">
              <el-icon><User /></el-icon>
              个人资料
            </el-dropdown-item>
            <el-dropdown-item command="password">
              <el-icon><Lock /></el-icon>
              修改密码
            </el-dropdown-item>
            <el-dropdown-item divided command="logout">
              <el-icon><SwitchButton /></el-icon>
              退出登录
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>

    <!-- 修改密码对话框 -->
    <el-dialog
      v-model="passwordDialogVisible"
      title="修改密码"
      width="400px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="passwordFormRef"
        :model="passwordForm"
        :rules="passwordRules"
        label-width="80px"
      >
        <el-form-item label="旧密码" prop="old_password">
          <el-input
            v-model="passwordForm.old_password"
            type="password"
            show-password
            placeholder="请输入旧密码"
          />
        </el-form-item>
        <el-form-item label="新密码" prop="new_password">
          <el-input
            v-model="passwordForm.new_password"
            type="password"
            show-password
            placeholder="请输入新密码"
          />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirm_password">
          <el-input
            v-model="passwordForm.confirm_password"
            type="password"
            show-password
            placeholder="请确认新密码"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="passwordDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="passwordLoading" @click="handlePasswordSubmit">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { useAppStore } from '@/stores/app'
import { useAuthStore } from '@/stores/auth'
import type { ChangePasswordRequest } from '@/types'

const route = useRoute()
const router = useRouter()
const appStore = useAppStore()
const authStore = useAuthStore()

// 全屏状态
const isFullscreen = ref(false)

// 修改密码对话框
const passwordDialogVisible = ref(false)
const passwordLoading = ref(false)
const passwordFormRef = ref<FormInstance>()

// 修改密码表单
const passwordForm = reactive<ChangePasswordRequest>({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

// 密码表单验证规则
const passwordRules: FormRules = {
  old_password: [
    { required: true, message: '请输入旧密码', trigger: 'blur' }
  ],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, max: 50, message: '密码长度在 6 到 50 个字符', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== passwordForm.new_password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

// 面包屑导航
const breadcrumbList = computed(() => {
  const matched = route.matched.filter(item => item.meta?.title)
  const breadcrumbs = matched.map(item => ({
    title: item.meta?.title as string,
    path: item.path
  }))
  
  return breadcrumbs
})

/**
 * 切换全屏
 */
const toggleFullscreen = () => {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen()
    isFullscreen.value = true
  } else {
    document.exitFullscreen()
    isFullscreen.value = false
  }
}

/**
 * 切换主题
 */
const toggleTheme = () => {
  const newTheme = appStore.themeMode === 'light' ? 'dark' : 'light'
  appStore.setThemeMode(newTheme)
}

/**
 * 处理用户菜单命令
 */
const handleUserCommand = (command: string) => {
  switch (command) {
    case 'profile':
      // 跳转到个人资料页面
      router.push('/profile')
      break
    case 'password':
      // 打开修改密码对话框
      passwordDialogVisible.value = true
      break
    case 'logout':
      // 退出登录
      handleLogout()
      break
  }
}

/**
 * 处理退出登录
 */
const handleLogout = async () => {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await authStore.logout()
    router.push('/login')
  } catch (error) {
    // 用户取消
  }
}

/**
 * 处理密码修改提交
 */
const handlePasswordSubmit = async () => {
  if (!passwordFormRef.value) return
  
  try {
    await passwordFormRef.value.validate()
    
    passwordLoading.value = true
    await authStore.changePassword(passwordForm)
    
    passwordDialogVisible.value = false
    
    // 重置表单
    passwordFormRef.value.resetFields()
    Object.assign(passwordForm, {
      old_password: '',
      new_password: '',
      confirm_password: ''
    })
    
    ElMessage.success('密码修改成功')
  } catch (error) {
    console.error('Change password error:', error)
  } finally {
    passwordLoading.value = false
  }
}

// 监听全屏状态变化
document.addEventListener('fullscreenchange', () => {
  isFullscreen.value = !!document.fullscreenElement
})
</script>

<style lang="scss" scoped>
.layout-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 16px;
  height: 100%;

  .header-left {
    display: flex;
    align-items: center;
    gap: 16px;

    .collapse-btn {
      padding: 8px;
      color: #606266;

      &:hover {
        color: #409eff;
        background-color: #ecf5ff;
      }
    }

    .breadcrumb {
      font-size: 14px;

      :deep(.el-breadcrumb__item) {
        .el-breadcrumb__inner {
          color: #606266;
          font-weight: normal;

          &:hover {
            color: #409eff;
          }
        }

        &:last-child .el-breadcrumb__inner {
          color: #303133;
          font-weight: 500;
        }
      }
    }
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: 8px;

    .header-btn {
      padding: 8px;
      color: #606266;

      &:hover {
        color: #409eff;
        background-color: #ecf5ff;
      }
    }

    .user-info {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      border-radius: 4px;
      cursor: pointer;
      transition: background-color 0.3s;

      &:hover {
        background-color: #f5f7fa;
      }

      .user-avatar {
        flex-shrink: 0;
      }

      .user-name {
        font-size: 14px;
        color: #303133;
        max-width: 100px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .dropdown-icon {
        font-size: 12px;
        color: #909399;
        transition: transform 0.3s;
      }
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .layout-header {
    padding: 0 12px;

    .header-left {
      gap: 8px;

      .breadcrumb {
        display: none;
      }
    }

    .header-right {
      .user-name {
        display: none;
      }
    }
  }
}

// 暗色主题
.dark {
  .layout-header {
    .header-left {
      .collapse-btn {
        color: #a3a6ad;

        &:hover {
          color: #409eff;
          background-color: rgba(64, 158, 255, 0.1);
        }
      }

      .breadcrumb {
        :deep(.el-breadcrumb__item) {
          .el-breadcrumb__inner {
            color: #a3a6ad;

            &:hover {
              color: #409eff;
            }
          }

          &:last-child .el-breadcrumb__inner {
            color: #e5eaf3;
          }
        }
      }
    }

    .header-right {
      .header-btn {
        color: #a3a6ad;

        &:hover {
          color: #409eff;
          background-color: rgba(64, 158, 255, 0.1);
        }
      }

      .user-info {
        &:hover {
          background-color: #2b2b2b;
        }

        .user-name {
          color: #e5eaf3;
        }
      }
    }
  }
}
</style>
