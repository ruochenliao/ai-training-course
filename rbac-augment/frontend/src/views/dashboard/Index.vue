<template>
  <div class="dashboard-page">
    <!-- 欢迎信息 -->
    <div class="welcome-card">
      <div class="welcome-content">
        <h2 class="welcome-title">
          欢迎回来，{{ displayUserName }}！
        </h2>
        <p class="welcome-subtitle">
          今天是 {{ currentDate }}，祝您工作愉快！
        </p>
      </div>
      <div class="welcome-avatar">
        <el-avatar :size="80" :src="authStore.userInfo?.avatar">
          <el-icon size="40"><User /></el-icon>
        </el-avatar>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="dashboard-stats">
      <div class="stat-card primary">
        <div class="stat-icon">
          <el-icon size="32"><User /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.userCount }}</div>
          <div class="stat-label">用户总数</div>
        </div>
      </div>

      <div class="stat-card success">
        <div class="stat-icon">
          <el-icon size="32"><UserFilled /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.roleCount }}</div>
          <div class="stat-label">角色总数</div>
        </div>
      </div>

      <div class="stat-card warning">
        <div class="stat-icon">
          <el-icon size="32"><Key /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.permissionCount }}</div>
          <div class="stat-label">权限总数</div>
        </div>
      </div>

      <div class="stat-card danger">
        <div class="stat-icon">
          <el-icon size="32"><Menu /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.menuCount }}</div>
          <div class="stat-label">菜单总数</div>
        </div>
      </div>
    </div>

    <!-- 图表区域 -->
    <div class="dashboard-charts">
      <div class="chart-card">
        <div class="card-header">
          <h3 class="card-title">用户增长趋势</h3>
        </div>
        <div class="chart-container" ref="userChartRef"></div>
      </div>

      <div class="chart-card">
        <div class="card-header">
          <h3 class="card-title">权限分布</h3>
        </div>
        <div class="chart-container" ref="permissionChartRef"></div>
      </div>
    </div>

    <!-- 快捷操作 -->
    <div class="quick-actions">
      <div class="action-card">
        <div class="card-header">
          <h3 class="card-title">快捷操作</h3>
        </div>
        <div class="action-grid">
          <div 
            v-permission="['user:create']"
            class="action-item"
            @click="$router.push('/system/users')"
          >
            <el-icon size="24"><Plus /></el-icon>
            <span>新增用户</span>
          </div>
          <div 
            v-permission="['role:create']"
            class="action-item"
            @click="$router.push('/system/roles')"
          >
            <el-icon size="24"><Plus /></el-icon>
            <span>新增角色</span>
          </div>
          <div 
            v-permission="['permission:create']"
            class="action-item"
            @click="$router.push('/system/permissions')"
          >
            <el-icon size="24"><Plus /></el-icon>
            <span>新增权限</span>
          </div>
          <div 
            v-permission="['menu:create']"
            class="action-item"
            @click="$router.push('/system/menus')"
          >
            <el-icon size="24"><Plus /></el-icon>
            <span>新增菜单</span>
          </div>
        </div>
      </div>

      <!-- 最近活动 -->
      <div class="activity-card">
        <div class="card-header">
          <h3 class="card-title">最近活动</h3>
        </div>
        <div class="activity-list">
          <div 
            v-for="activity in recentActivities"
            :key="activity.id"
            class="activity-item"
          >
            <div class="activity-icon">
              <el-icon><component :is="activity.icon" /></el-icon>
            </div>
            <div class="activity-content">
              <div class="activity-title">{{ activity.title }}</div>
              <div class="activity-time">{{ activity.time }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { formatDate } from '@/utils'

const authStore = useAuthStore()

// 计算属性
const displayUserName = computed(() => {
  const userInfo = authStore.userInfo
  if (!userInfo) return '用户'

  return userInfo.full_name || userInfo.username || '用户'
})

// 图表容器引用
const userChartRef = ref<HTMLElement>()
const permissionChartRef = ref<HTMLElement>()

// 当前日期
const currentDate = formatDate(new Date())

// 统计数据
const stats = reactive({
  userCount: 0,
  roleCount: 0,
  permissionCount: 0,
  menuCount: 0
})

// 最近活动
const recentActivities = ref([
  {
    id: 1,
    title: '用户 admin 登录系统',
    time: '2分钟前',
    icon: 'User'
  },
  {
    id: 2,
    title: '创建了新角色 "编辑者"',
    time: '1小时前',
    icon: 'UserFilled'
  },
  {
    id: 3,
    title: '更新了权限配置',
    time: '3小时前',
    icon: 'Key'
  },
  {
    id: 4,
    title: '新增菜单 "数据分析"',
    time: '1天前',
    icon: 'Menu'
  }
])

/**
 * 获取统计数据
 */
const fetchStats = async () => {
  try {
    // 这里应该调用实际的API获取统计数据
    // 暂时使用模拟数据
    stats.userCount = 156
    stats.roleCount = 8
    stats.permissionCount = 32
    stats.menuCount = 15
  } catch (error) {
    console.error('Failed to fetch stats:', error)
  }
}

/**
 * 初始化图表
 */
const initCharts = () => {
  // 这里可以使用 ECharts 或其他图表库
  // 暂时留空，实际项目中可以添加图表实现
  console.log('Initialize charts')
}

onMounted(() => {
  fetchStats()
  initCharts()
})
</script>

<style lang="scss" scoped>
.dashboard-page {
  padding: 24px;
  min-height: calc(100vh - 60px);

  .welcome-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 12px;
    padding: 32px;
    margin-bottom: 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;

    .welcome-content {
      .welcome-title {
        font-size: 24px;
        font-weight: 600;
        margin-bottom: 8px;
      }

      .welcome-subtitle {
        font-size: 16px;
        opacity: 0.9;
      }
    }

    .welcome-avatar {
      .el-avatar {
        border: 3px solid rgba(255, 255, 255, 0.3);
      }
    }
  }

  .dashboard-stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 24px;
    margin-bottom: 24px;

    .stat-card {
      background: white;
      border-radius: 12px;
      padding: 24px;
      box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
      display: flex;
      align-items: center;
      gap: 16px;
      transition: transform 0.3s ease;

      &:hover {
        transform: translateY(-4px);
      }

      .stat-icon {
        width: 60px;
        height: 60px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
      }

      .stat-content {
        .stat-value {
          font-size: 28px;
          font-weight: 700;
          color: #303133;
          margin-bottom: 4px;
        }

        .stat-label {
          font-size: 14px;
          color: #909399;
        }
      }

      &.primary .stat-icon {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      }

      &.success .stat-icon {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
      }

      &.warning .stat-icon {
        background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
      }

      &.danger .stat-icon {
        background: linear-gradient(135deg, #ff6b6b 0%, #ffa726 100%);
      }
    }
  }

  .dashboard-charts {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 24px;
    margin-bottom: 24px;

    .chart-card {
      background: white;
      border-radius: 12px;
      padding: 24px;
      box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);

      .card-header {
        margin-bottom: 20px;

        .card-title {
          font-size: 18px;
          font-weight: 600;
          color: #303133;
        }
      }

      .chart-container {
        height: 300px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #909399;
        background-color: #f5f7fa;
        border-radius: 8px;
      }
    }
  }

  .quick-actions {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 24px;

    .action-card,
    .activity-card {
      background: white;
      border-radius: 12px;
      padding: 24px;
      box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);

      .card-header {
        margin-bottom: 20px;

        .card-title {
          font-size: 18px;
          font-weight: 600;
          color: #303133;
        }
      }
    }

    .action-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 16px;

      .action-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 8px;
        padding: 20px;
        border: 2px dashed #e4e7ed;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.3s ease;
        color: #606266;

        &:hover {
          border-color: #409eff;
          color: #409eff;
          background-color: #ecf5ff;
        }

        span {
          font-size: 14px;
        }
      }
    }

    .activity-list {
      .activity-item {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px 0;
        border-bottom: 1px solid #f0f0f0;

        &:last-child {
          border-bottom: none;
        }

        .activity-icon {
          width: 32px;
          height: 32px;
          border-radius: 50%;
          background-color: #f5f7fa;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #409eff;
        }

        .activity-content {
          flex: 1;

          .activity-title {
            font-size: 14px;
            color: #303133;
            margin-bottom: 4px;
          }

          .activity-time {
            font-size: 12px;
            color: #909399;
          }
        }
      }
    }
  }
}

// 响应式设计
@media (max-width: 1200px) {
  .dashboard-page {
    .dashboard-charts {
      grid-template-columns: 1fr;
    }
  }
}

@media (max-width: 768px) {
  .dashboard-page {
    padding: 16px;

    .welcome-card {
      flex-direction: column;
      text-align: center;
      gap: 16px;
    }

    .dashboard-stats {
      grid-template-columns: 1fr;
    }

    .quick-actions {
      grid-template-columns: 1fr;

      .action-grid {
        grid-template-columns: 1fr;
      }
    }
  }
}

// 暗色主题
.dark {
  .dashboard-page {
    .stat-card,
    .chart-card,
    .action-card,
    .activity-card {
      background-color: #2b2b2b;
      color: #e5eaf3;

      .card-title {
        color: #e5eaf3;
      }

      .stat-value {
        color: #e5eaf3;
      }

      .chart-container {
        background-color: #1d1e1f;
        color: #a3a6ad;
      }
    }

    .action-grid {
      .action-item {
        border-color: #4c4d4f;
        color: #a3a6ad;

        &:hover {
          border-color: #409eff;
          color: #409eff;
          background-color: rgba(64, 158, 255, 0.1);
        }
      }
    }

    .activity-list {
      .activity-item {
        border-bottom-color: #4c4d4f;

        .activity-icon {
          background-color: #1d1e1f;
        }

        .activity-title {
          color: #e5eaf3;
        }
      }
    }
  }
}
</style>
