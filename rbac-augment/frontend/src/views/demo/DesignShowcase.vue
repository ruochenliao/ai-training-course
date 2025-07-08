<template>
  <!-- 
    设计风格展示页面
    参考 SuperIntelligentCustomerService 的设计风格
    展示各种组件和交互效果的统一设计
  -->
  <div class="design-showcase">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h2>🎨 设计风格展示</h2>
        <p class="page-description">参考 vue-fastapi-admin 的现代化设计风格</p>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="toggleTheme">
          <el-icon><component :is="isDark ? 'Sunny' : 'Moon'" /></el-icon>
          {{ isDark ? '明亮模式' : '暗色模式' }}
        </el-button>
      </div>
    </div>

    <!-- 颜色系统展示 -->
    <el-card class="showcase-card" shadow="hover">
      <template #header>
        <h3>🎨 颜色系统</h3>
      </template>
      <div class="color-palette">
        <div class="color-group">
          <h4>主色调</h4>
          <div class="color-items">
            <div class="color-item primary">
              <div class="color-block"></div>
              <span>Primary</span>
            </div>
            <div class="color-item success">
              <div class="color-block"></div>
              <span>Success</span>
            </div>
            <div class="color-item warning">
              <div class="color-block"></div>
              <span>Warning</span>
            </div>
            <div class="color-item error">
              <div class="color-block"></div>
              <span>Error</span>
            </div>
            <div class="color-item info">
              <div class="color-block"></div>
              <span>Info</span>
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 按钮组件展示 -->
    <el-card class="showcase-card" shadow="hover">
      <template #header>
        <h3>🔘 按钮组件</h3>
      </template>
      <div class="button-showcase">
        <div class="button-group">
          <h4>基础按钮</h4>
          <div class="buttons">
            <el-button>默认按钮</el-button>
            <el-button type="primary">主要按钮</el-button>
            <el-button type="success">成功按钮</el-button>
            <el-button type="warning">警告按钮</el-button>
            <el-button type="danger">危险按钮</el-button>
            <el-button type="info">信息按钮</el-button>
          </div>
        </div>
        
        <div class="button-group">
          <h4>图标按钮</h4>
          <div class="buttons">
            <el-button type="primary" :icon="Plus">新增</el-button>
            <el-button type="success" :icon="Edit">编辑</el-button>
            <el-button type="warning" :icon="View">查看</el-button>
            <el-button type="danger" :icon="Delete">删除</el-button>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 表单组件展示 -->
    <el-card class="showcase-card" shadow="hover">
      <template #header>
        <h3>📝 表单组件</h3>
      </template>
      <el-form :model="demoForm" label-width="120px" class="demo-form">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="用户名">
              <el-input v-model="demoForm.username" placeholder="请输入用户名" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="邮箱">
              <el-input v-model="demoForm.email" placeholder="请输入邮箱" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="角色">
              <el-select v-model="demoForm.role" placeholder="请选择角色" style="width: 100%">
                <el-option label="管理员" value="admin" />
                <el-option label="用户" value="user" />
                <el-option label="访客" value="guest" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="状态">
              <el-switch v-model="demoForm.status" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="描述">
          <el-input 
            v-model="demoForm.description" 
            type="textarea" 
            :rows="3" 
            placeholder="请输入描述"
          />
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 表格组件展示 -->
    <el-card class="showcase-card" shadow="hover">
      <template #header>
        <h3>📊 表格组件</h3>
      </template>
      <div class="data-table">
        <el-table :data="tableData" style="width: 100%">
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="name" label="姓名" width="120" />
          <el-table-column prop="email" label="邮箱" />
          <el-table-column prop="role" label="角色" width="100">
            <template #default="{ row }">
              <el-tag :type="getRoleTagType(row.role)">{{ row.role }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <div class="status-badge" :class="getStatusClass(row.status)">
                {{ row.status ? '启用' : '禁用' }}
              </div>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200">
            <template #default="{ row }">
              <div class="action-buttons">
                <el-button size="small" type="primary" :icon="View">查看</el-button>
                <el-button size="small" type="warning" :icon="Edit">编辑</el-button>
                <el-button size="small" type="danger" :icon="Delete">删除</el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>

    <!-- 统计卡片展示 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon primary">
              <el-icon><User /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">1,234</div>
              <div class="stat-label">总用户数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon success">
              <el-icon><UserFilled /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">856</div>
              <div class="stat-label">活跃用户</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon warning">
              <el-icon><Lock /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">45</div>
              <div class="stat-label">角色数量</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon info">
              <el-icon><Key /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">128</div>
              <div class="stat-label">权限数量</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
/**
 * 设计风格展示页面逻辑
 * 展示各种组件的使用方法和视觉效果
 */
import { ref, reactive, computed } from 'vue'
import { useAppStore } from '@/stores/app'
import { 
  Plus, Edit, View, Delete, User, UserFilled, Lock, Key,
  Sunny, Moon
} from '@element-plus/icons-vue'

// ==================== 响应式数据 ====================

const appStore = useAppStore()

// 主题切换状态
const isDark = computed(() => appStore.themeMode === 'dark')

// 演示表单数据
const demoForm = reactive({
  username: 'demo_user',
  email: 'demo@example.com',
  role: 'admin',
  status: true,
  description: '这是一个演示用户的描述信息'
})

// 演示表格数据
const tableData = ref([
  {
    id: 1,
    name: '张三',
    email: 'zhangsan@example.com',
    role: '管理员',
    status: true
  },
  {
    id: 2,
    name: '李四',
    email: 'lisi@example.com',
    role: '用户',
    status: true
  },
  {
    id: 3,
    name: '王五',
    email: 'wangwu@example.com',
    role: '访客',
    status: false
  }
])

// ==================== 方法定义 ====================

/**
 * 切换主题模式
 */
const toggleTheme = () => {
  const newTheme = appStore.themeMode === 'light' ? 'dark' : 'light'
  appStore.setThemeMode(newTheme)
}

/**
 * 获取角色标签类型
 * @param role - 角色名称
 * @returns 标签类型
 */
const getRoleTagType = (role: string) => {
  const typeMap: Record<string, string> = {
    '管理员': 'danger',
    '用户': 'primary',
    '访客': 'info'
  }
  return typeMap[role] || 'default'
}

/**
 * 获取状态样式类
 * @param status - 状态值
 * @returns 样式类名
 */
const getStatusClass = (status: boolean) => {
  return status ? 'status-active' : 'status-inactive'
}
</script>

<style lang="scss" scoped>
/**
 * 设计风格展示页面样式
 * 参考 SuperIntelligentCustomerService 的设计规范
 */
@import '@/styles/variables.scss';

.design-showcase {
  padding: $main-padding;
  max-width: 1400px;
  margin: 0 auto;

  // ==================== 展示卡片样式 ====================
  .showcase-card {
    margin-bottom: 24px;
    border-radius: 12px;
    overflow: hidden;
    transition: all 0.3s ease;

    &:hover {
      transform: translateY(-4px);
      box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
    }

    :deep(.el-card__header) {
      background: linear-gradient(135deg, rgba($primary-color, 0.1), rgba($primary-color, 0.05));
      border-bottom: 1px solid $border-color;
      padding: 20px 24px;

      h3 {
        margin: 0;
        font-size: 18px;
        font-weight: 600;
        color: $text-color-1;
      }
    }

    :deep(.el-card__body) {
      padding: 24px;
    }
  }

  // ==================== 颜色系统展示 ====================
  .color-palette {
    .color-group {
      h4 {
        margin-bottom: 16px;
        color: $text-color-1;
        font-weight: 600;
      }

      .color-items {
        display: flex;
        gap: 20px;
        flex-wrap: wrap;

        .color-item {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 8px;

          .color-block {
            width: 60px;
            height: 60px;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            transition: transform 0.3s ease;

            &:hover {
              transform: scale(1.1);
            }
          }

          span {
            font-size: 14px;
            color: $text-color-2;
            font-weight: 500;
          }

          &.primary .color-block { background: $primary-color; }
          &.success .color-block { background: $success-color; }
          &.warning .color-block { background: $warning-color; }
          &.error .color-block { background: $error-color; }
          &.info .color-block { background: $info-color; }
        }
      }
    }
  }

  // ==================== 按钮展示样式 ====================
  .button-showcase {
    .button-group {
      margin-bottom: 24px;

      &:last-child {
        margin-bottom: 0;
      }

      h4 {
        margin-bottom: 16px;
        color: $text-color-1;
        font-weight: 600;
      }

      .buttons {
        display: flex;
        gap: 12px;
        flex-wrap: wrap;
      }
    }
  }

  // ==================== 表单展示样式 ====================
  .demo-form {
    .el-form-item {
      margin-bottom: 20px;
    }
  }

  // ==================== 统计卡片样式 ====================
  .stats-row {
    margin-top: 24px;

    .stat-card {
      border-radius: 12px;
      overflow: hidden;
      transition: all 0.3s ease;

      &:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
      }

      .stat-content {
        display: flex;
        align-items: center;
        gap: 16px;
        padding: 8px;

        .stat-icon {
          width: 60px;
          height: 60px;
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 24px;
          color: white;

          &.primary { background: linear-gradient(135deg, $primary-color, $primary-color-hover); }
          &.success { background: linear-gradient(135deg, $success-color, $success-color-hover); }
          &.warning { background: linear-gradient(135deg, $warning-color, $warning-color-hover); }
          &.info { background: linear-gradient(135deg, $info-color, $info-color-hover); }
        }

        .stat-info {
          flex: 1;

          .stat-value {
            font-size: 28px;
            font-weight: 700;
            color: $text-color-1;
            line-height: 1;
            margin-bottom: 4px;
          }

          .stat-label {
            font-size: 14px;
            color: $text-color-3;
            font-weight: 500;
          }
        }
      }
    }
  }
}
</style>
