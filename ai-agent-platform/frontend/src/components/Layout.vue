<template>
  <div class="layout">
    <!-- 顶部导航栏 -->
    <el-header class="layout-header">
      <div class="header-left">
        <h2 class="logo">AI智能体平台</h2>
      </div>
      
      <div class="header-right">
        <!-- 用户信息和菜单 -->
        <el-dropdown @command="handleCommand">
          <div class="user-info">
            <el-avatar :size="32" :src="userStore.avatar">
              <el-icon><User /></el-icon>
            </el-avatar>
            <span class="username">{{ userStore.userName }}</span>
            <el-icon class="dropdown-icon"><ArrowDown /></el-icon>
          </div>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="profile">
                <el-icon><User /></el-icon>
                个人资料
              </el-dropdown-item>
              <el-dropdown-item command="settings">
                <el-icon><Setting /></el-icon>
                系统设置
              </el-dropdown-item>
              <el-dropdown-item divided command="logout">
                <el-icon><SwitchButton /></el-icon>
                退出登录
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </el-header>

    <!-- 主要内容区域 -->
    <el-container class="layout-container">
      <!-- 侧边导航栏 -->
      <el-aside class="layout-aside" width="240px">
        <el-menu
          :default-active="activeMenu"
          class="sidebar-menu"
          router
          unique-opened
        >
          <el-menu-item index="/dashboard">
            <el-icon><House /></el-icon>
            <span>仪表盘</span>
          </el-menu-item>
          
          <el-menu-item index="/agents">
            <el-icon><Avatar /></el-icon>
            <span>智能体列表</span>
          </el-menu-item>

          <el-menu-item index="/agent-management">
            <el-icon><Cpu /></el-icon>
            <span>智能体管理</span>
          </el-menu-item>
          
          <el-menu-item index="/knowledge">
            <el-icon><Document /></el-icon>
            <span>知识库管理</span>
          </el-menu-item>
          
          <el-menu-item index="/chat">
            <el-icon><ChatDotRound /></el-icon>
            <span>对话管理</span>
          </el-menu-item>

          <el-menu-item index="/workflow-designer">
            <el-icon><Share /></el-icon>
            <span>工作流设计器</span>
          </el-menu-item>

          <el-menu-item index="/plugin-management">
            <el-icon><Grid /></el-icon>
            <span>插件管理</span>
          </el-menu-item>

          <el-menu-item index="/system-monitor">
            <el-icon><Monitor /></el-icon>
            <span>系统监控</span>
          </el-menu-item>
          
          <el-menu-item index="/analytics">
            <el-icon><DataAnalysis /></el-icon>
            <span>数据分析</span>
          </el-menu-item>
          
          <el-menu-item index="/settings">
            <el-icon><Setting /></el-icon>
            <span>系统设置</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <!-- 主内容区 -->
      <el-main class="layout-main">
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  User,
  ArrowDown,
  Setting,
  SwitchButton,
  House,
  Avatar,
  Document,
  ChatDotRound,
  DataAnalysis,
  Cpu,  // 使用 Cpu 图标替代 Robot
  Share,
  Grid,
  Monitor
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

// 当前激活的菜单项
const activeMenu = computed(() => {
  return route.path
})

// 处理下拉菜单命令
const handleCommand = async (command: string) => {
  switch (command) {
    case 'profile':
      // 跳转到个人资料页面
      router.push('/profile')
      break
      
    case 'settings':
      // 跳转到设置页面
      router.push('/settings')
      break
      
    case 'logout':
      // 退出登录
      await handleLogout()
      break
  }
}

// 处理退出登录
const handleLogout = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要退出登录吗？',
      '退出确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    // 执行退出登录
    await userStore.logout()
    
    ElMessage.success('已成功退出登录')
    
    // 跳转到登录页面
    router.push('/login')
  } catch (error) {
    // 用户取消退出或退出失败
    if (error !== 'cancel') {
      console.error('退出登录失败:', error)
      ElMessage.error('退出登录失败，请重试')
    }
  }
}
</script>

<style lang="scss" scoped>
.layout {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.layout-header {
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 60px;
  
  .header-left {
    .logo {
      font-size: 20px;
      font-weight: 600;
      color: #303133;
      margin: 0;
    }
  }
  
  .header-right {
    .user-info {
      display: flex;
      align-items: center;
      cursor: pointer;
      padding: 8px 12px;
      border-radius: 6px;
      transition: background-color 0.3s;
      
      &:hover {
        background-color: #f5f7fa;
      }
      
      .username {
        margin: 0 8px;
        font-size: 14px;
        color: #303133;
      }
      
      .dropdown-icon {
        font-size: 12px;
        color: #909399;
      }
    }
  }
}

.layout-container {
  flex: 1;
  height: calc(100vh - 60px);
}

.layout-aside {
  background: #fff;
  border-right: 1px solid #e4e7ed;
  
  .sidebar-menu {
    border-right: none;
    height: 100%;
    
    .el-menu-item {
      height: 48px;
      line-height: 48px;
      
      &.is-active {
        background-color: #ecf5ff;
        color: #409eff;
        
        &::before {
          content: '';
          position: absolute;
          left: 0;
          top: 0;
          bottom: 0;
          width: 3px;
          background-color: #409eff;
        }
      }
      
      .el-icon {
        margin-right: 8px;
      }
    }
  }
}

.layout-main {
  background: #f5f7fa;
  overflow-y: auto;
  padding: 0;
}

// 响应式设计
@media (max-width: 768px) {
  .layout-aside {
    width: 200px !important;
  }
  
  .layout-header {
    padding: 0 16px;
    
    .header-left .logo {
      font-size: 18px;
    }
  }
}
</style>
