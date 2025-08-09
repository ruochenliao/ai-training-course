<template>
  <!--
    应用头部导航栏组件
    参考 SuperIntelligentCustomerService 的设计风格
    包含侧边栏折叠按钮、面包屑导航、搜索框、通知、用户操作区域等功能
  -->
  <div class="layout-header" style="width: 100%; height: 100%;">
    <!-- 左侧功能区域 -->
    <div class="header-left">
      <!-- 侧边栏折叠/展开按钮 -->
      <el-button
        type="text"
        class="collapse-btn"
        @click="appStore.toggleSidebar"
        :title="appStore.sidebarCollapsed ? '展开侧边栏' : '折叠侧边栏'"
      >
        <el-icon size="18">
          <Fold v-if="!appStore.sidebarCollapsed" />
          <Expand v-else />
        </el-icon>
      </el-button>


    </div>

    <!-- 右侧操作区域 -->
    <div class="header-right">
      <!-- 语言切换 -->
      <LanguageSwitcher class="language-dropdown" />

      <!-- 通知消息 -->
      <el-tooltip content="消息通知" placement="bottom">
        <el-badge :value="notificationCount" :hidden="notificationCount === 0" class="notification-badge">
          <el-button type="link" @click="showNotifications" class="header-btn">
            <el-icon size="18">
              <Bell />
            </el-icon>
          </el-button>
        </el-badge>
      </el-tooltip>

      <!-- 全屏切换按钮 -->
      <el-tooltip content="全屏" placement="bottom">
        <el-button
          type="link"
          class="header-btn"
          @click="toggleFullscreen"
        >
          <el-icon size="18">
            <FullScreen v-if="!isFullscreen" />
            <Aim v-else />
          </el-icon>
        </el-button>
      </el-tooltip>

      <!-- 主题切换按钮 -->
      <el-tooltip content="切换主题" placement="bottom">
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

      <!-- 用户信息下拉菜单 -->
      <el-dropdown trigger="click" @command="handleUserCommand" class="user-dropdown">
        <div class="user-info">
          <el-avatar
            :size="32"
            :src="authStore.userInfo?.avatar"
            class="user-avatar"
          >
            <el-icon><UserIcon /></el-icon>
          </el-avatar>
          <div class="user-details">
            <span class="user-name">{{ displayUserName }}</span>
            <span class="user-role">{{ displayUserRole }}</span>
          </div>
          <el-icon class="dropdown-icon" size="14">
            <ArrowDown />
          </el-icon>
        </div>

        <template #dropdown>
          <el-dropdown-menu class="user-dropdown-menu">
            <el-dropdown-item command="profile" class="dropdown-item">
              <el-icon><UserIcon /></el-icon>
              <span>个人资料</span>
            </el-dropdown-item>
            <el-dropdown-item command="password" class="dropdown-item">
              <el-icon><Lock /></el-icon>
              <span>修改密码</span>
            </el-dropdown-item>
            <el-dropdown-item command="settings" class="dropdown-item">
              <el-icon><Setting /></el-icon>
              <span>系统设置</span>
            </el-dropdown-item>
            <el-dropdown-item divided command="logout" class="dropdown-item logout-item">
              <el-icon><SwitchButton /></el-icon>
              <span>退出登录</span>
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
/**
 * 头部导航栏组件的逻辑处理
 * 包含侧边栏控制、面包屑导航、搜索、通知、主题切换、用户操作等功能
 */
import { computed, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { Search, Bell, FullScreen, Aim, Sunny, Moon, User as UserIcon, Lock, Setting, SwitchButton, Fold, Expand, ArrowDown } from '@element-plus/icons-vue'

// 导入store和组件
import { useAppStore } from '@/stores/app'
import { useAuthStore } from '@/stores/auth'
import type { ChangePasswordRequest, User as UserType } from '@/types'
import type { AuthStoreType, AppStoreType } from '@/types/store-types'
import LanguageSwitcher from '@/components/common/LanguageSwitcher.vue'

// ==================== 响应式数据定义 ====================

const route = useRoute()
const router = useRouter()
const appStore = useAppStore() as AppStoreType
const authStore = useAuthStore() as {
  token: string
  refreshToken: string
  userInfo: UserType | null
  permissions: string[]
  roles: string[]
  menus: any[]
  login: (username: string, password: string) => Promise<void>
  logout: () => Promise<void>
  refreshAccessToken: () => Promise<void>
  fetchUserProfile: () => Promise<void>
  changePassword: (passwordData: ChangePasswordRequest) => Promise<void>
  hasPermission: (permission: string | string[]) => boolean
  hasRole: (role: string | string[]) => boolean
  initAuth: () => Promise<void>
  isLoggedIn: boolean
  isSuperUser: boolean
}

// 全屏状态管理
const isFullscreen = ref(false)

// 搜索功能相关
const searchKeyword = ref('')


// 通知消息相关
const notificationCount = ref(3) // 模拟通知数量

// 修改密码对话框相关
const passwordDialogVisible = ref(false)
const passwordLoading = ref(false)
const passwordFormRef = ref<FormInstance>()

// 修改密码表单数据
const passwordForm = reactive<ChangePasswordRequest>({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

// ==================== 计算属性 ====================

/**
 * 显示用户名
 */
const displayUserName = computed(() => {
  const userInfo = authStore.userInfo
  if (!userInfo) return '用户'

  return userInfo.full_name || userInfo.username || '用户'
})

/**
 * 显示用户角色
 */
const displayUserRole = computed(() => {
  const userInfo = authStore.userInfo
  if (!userInfo) return '访客'

  if (userInfo.is_superuser) {
    return '系统管理员'
  }

  // 如果有角色信息，显示第一个角色
  if (authStore.roles && authStore.roles.length > 0) {
    return authStore.roles[0]
  }

  return '普通用户'
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
      validator: (rule: any, value: any, callback: any) => {
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

// ==================== 计算属性 ====================

/**
 * 面包屑导航列表
 * 根据当前路由生成面包屑导航数据
 */
const breadcrumbList = computed(() => {
  const matched = route.matched.filter(item => item.meta?.title)
  const breadcrumbs = matched.map(item => ({
    title: item.meta?.title as string,
    path: item.path,
    icon: item.meta?.icon
  }))

  return breadcrumbs
})

// ==================== 方法定义 ====================

/**
 * 处理搜索输入
 * @param value - 搜索关键词
 */
const handleSearchInput = (value: string) => {
  // 实时搜索逻辑可以在这里实现
  console.log('搜索关键词:', value)
}

/**
 * 处理搜索提交
 * 当用户按下回车键时触发
 */
const handleSearch = () => {
  if (searchKeyword.value.trim()) {
    ElMessage.info(`搜索: ${searchKeyword.value}`)
    // 这里可以实现具体的搜索逻辑
  }
}

/**
 * 显示通知消息
 * 打开通知消息面板
 */
const showNotifications = () => {
  ElMessage.info('通知功能开发中...')
  // 这里可以实现通知消息的显示逻辑
}

/**
 * 切换全屏模式
 * 进入或退出全屏显示
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
 * 切换主题模式
 * 在明亮和暗黑主题之间切换
 */
const toggleTheme = () => {
  const newTheme = appStore.themeMode === 'light' ? 'dark' : 'light'
  appStore.setThemeMode(newTheme)
}

/**
 * 处理用户下拉菜单命令
 * @param command - 菜单命令类型
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
    case 'settings':
      // 跳转到系统设置页面
      router.push('/settings')
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
/**
 * 头部导航栏样式
 * 参考 SuperIntelligentCustomerService 的设计风格
 * 包含响应式设计和暗色主题支持
 */
@import '@/styles/variables.scss';

.layout-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  height: 100%;
  background: $card-color;
  border-bottom: 1px solid $border-color;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);

  // ==================== 左侧区域样式 ====================
  .header-left {
    display: flex;
    align-items: center;
    gap: 20px;

    // 折叠按钮样式
    .collapse-btn {
      padding: 8px;
      color: $text-color-2;
      border-radius: 6px;
      transition: all 0.3s ease;

      &:hover {
        color: $primary-color;
        background-color: rgba($primary-color, 0.1);
      }
    }

    // 面包屑导航样式
    .breadcrumb {
      font-size: 14px;

      :deep(.el-breadcrumb__item) {
        .el-breadcrumb__inner {
          color: $text-color-2;
          font-weight: normal;
          display: flex;
          align-items: center;
          gap: 4px;
          transition: color 0.3s ease;

          &:hover {
            color: $primary-color;
          }
        }

        &:last-child .el-breadcrumb__inner {
          color: $text-color-1;
          font-weight: 500;
        }
      }

      .breadcrumb-icon {
        font-size: 14px;
      }
    }
  }

  // ==================== 右侧区域样式 ====================
  .header-right {
    display: flex;
    align-items: center;
    gap: 12px;

    // 语言切换样式
    .language-dropdown {
      .header-btn {
        display: flex;
        align-items: center;
        gap: 4px;
        
        .language-text {
          font-size: 14px;
          margin-left: 4px;
        }
      }
      
      :deep(.el-dropdown-menu__item.is-active) {
        color: $primary-color;
        font-weight: 500;
        background-color: rgba($primary-color, 0.1);
      }
    }

    // 搜索框样式
    .search-box {
      .search-input {
        width: 240px;

        :deep(.el-input__wrapper) {
          border-radius: 20px;
          background-color: rgba($text-color-3, 0.1);
          border: 1px solid transparent;
          transition: all 0.3s ease;

          &:hover {
            border-color: $primary-color;
          }

          &.is-focus {
            border-color: $primary-color;
            box-shadow: 0 0 0 2px rgba($primary-color, 0.2);
          }
        }
      }
    }

    // 通知徽章样式
    .notification-badge {
      :deep(.el-badge__content) {
        background-color: $error-color;
        border: none;
      }
    }

    // 头部按钮样式
    .header-btn {
      padding: 8px;
      color: $text-color-2;
      border-radius: 6px;
      transition: all 0.3s ease;

      &:hover {
        color: $primary-color;
        background-color: rgba($primary-color, 0.1);
      }
    }

    // 用户信息下拉菜单样式
    .user-dropdown {
      .user-info {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 8px 16px;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.3s ease;
        border: 1px solid transparent;

        &:hover {
          background-color: rgba($primary-color, 0.05);
          border-color: rgba($primary-color, 0.2);
        }

        .user-avatar {
          flex-shrink: 0;
          border: 2px solid rgba($primary-color, 0.2);
        }

        .user-details {
          display: flex;
          flex-direction: column;
          align-items: flex-start;
          gap: 2px;

          .user-name {
            font-size: 14px;
            font-weight: 500;
            color: $text-color-1;
            max-width: 120px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            line-height: 1.2;
          }

          .user-role {
            font-size: 12px;
            color: $text-color-3;
            line-height: 1.2;
          }
        }

        .dropdown-icon {
          color: $text-color-3;
          transition: transform 0.3s ease;
        }

        &:hover .dropdown-icon {
          transform: rotate(180deg);
        }
      }
    }
  }
}

// ==================== 用户下拉菜单样式 ====================
:deep(.user-dropdown-menu) {
  padding: 8px 0;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);

  .dropdown-item {
    padding: 12px 20px;
    display: flex;
    align-items: center;
    gap: 12px;
    transition: all 0.3s ease;

    .el-icon {
      font-size: 16px;
      color: $text-color-2;
    }

    span {
      font-size: 14px;
      color: $text-color-1;
    }

    &:hover {
      background-color: rgba($primary-color, 0.1);

      .el-icon {
        color: $primary-color;
      }
    }

    &.logout-item {
      &:hover {
        background-color: rgba($error-color, 0.1);

        .el-icon {
          color: $error-color;
        }

        span {
          color: $error-color;
        }
      }
    }
  }
}

// ==================== 响应式设计 ====================

// 平板设备适配
@media (max-width: 992px) {
  .layout-header {
    .header-right {
      .search-box {
        .search-input {
          width: 200px;
        }
      }

      .user-details {
        .user-name {
          max-width: 80px;
        }
      }
    }
  }
}

// 手机设备适配
@media (max-width: 768px) {
  .layout-header {
    padding: 0 16px;

    .header-left {
      gap: 12px;

      .breadcrumb {
        display: none; // 在小屏幕上隐藏面包屑
      }
    }

    .header-right {
      gap: 8px;

      .search-box {
        display: none; // 在小屏幕上隐藏搜索框
      }

      .user-details {
        display: none; // 在小屏幕上隐藏用户详情文字
      }
    }
  }
}

// 超小屏幕适配
@media (max-width: 480px) {
  .layout-header {
    padding: 0 12px;

    .header-right {
      .notification-badge,
      .header-btn:not(:last-child) {
        display: none; // 在超小屏幕上只保留用户菜单
      }
    }
  }
}

// ==================== 暗色主题支持 ====================
.dark {
  .layout-header {
    background: #1a1a1a;
    border-bottom-color: #333;

    .header-left {
      .collapse-btn {
        color: #a3a6ad;

        &:hover {
          color: $primary-color;
          background-color: rgba($primary-color, 0.1);
        }
      }

      .breadcrumb {
        :deep(.el-breadcrumb__item) {
          .el-breadcrumb__inner {
            color: #a3a6ad;

            &:hover {
              color: $primary-color;
            }
          }

          &:last-child .el-breadcrumb__inner {
            color: #e5eaf3;
          }
        }
      }
    }

    .header-right {
      .search-box {
        .search-input {
          :deep(.el-input__wrapper) {
            background-color: rgba(255, 255, 255, 0.1);

            .el-input__inner {
              color: #e5eaf3;

              &::placeholder {
                color: #a3a6ad;
              }
            }
          }
        }
      }

      .header-btn {
        color: #a3a6ad;

        &:hover {
          color: $primary-color;
          background-color: rgba($primary-color, 0.1);
        }
      }

      .user-dropdown {
        .user-info {
          &:hover {
            background-color: rgba(255, 255, 255, 0.05);
          }

          .user-details {
            .user-name {
              color: #e5eaf3;
            }

            .user-role {
              color: #a3a6ad;
            }
          }
        }
      }
    }
  }

  // 暗色主题下的下拉菜单
  :deep(.user-dropdown-menu) {
    background-color: #2a2a2a;
    border-color: #333;

    .dropdown-item {
      .el-icon {
        color: #a3a6ad;
      }

      span {
        color: #e5eaf3;
      }

      &:hover {
        background-color: rgba($primary-color, 0.1);
      }

      &.logout-item:hover {
        background-color: rgba($error-color, 0.1);
      }
    }
  }
}
</style>
