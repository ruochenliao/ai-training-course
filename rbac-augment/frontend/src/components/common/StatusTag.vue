<template>
  <el-tag
    :type="tagType"
    :effect="effect"
    :size="size"
    :round="round"
    :closable="closable"
    :disable-transitions="disableTransitions"
    :hit="hit"
    :color="customColor"
    :class="[
      'status-tag',
      `status-tag--${status}`,
      {
        'status-tag--with-icon': showIcon,
        'status-tag--clickable': clickable
      }
    ]"
    @click="handleClick"
    @close="handleClose"
  >
    <el-icon v-if="showIcon && iconComponent" class="status-icon">
      <component :is="iconComponent" />
    </el-icon>
    <span class="status-text">{{ displayText }}</span>
  </el-tag>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import {
  Check,
  Close,
  Warning,
  InfoFilled,
  Clock,
  Lock,
  Unlock,
  User,
  UserFilled,
  CircleCheck,
  CircleClose,
  QuestionFilled
} from '@element-plus/icons-vue'

export interface StatusConfig {
  text: string
  type?: 'success' | 'info' | 'warning' | 'danger' | ''
  icon?: any
  color?: string
}

interface Props {
  status: string | number | boolean
  statusMap?: Record<string | number, StatusConfig>
  showIcon?: boolean
  size?: 'large' | 'default' | 'small'
  effect?: 'dark' | 'light' | 'plain'
  round?: boolean
  closable?: boolean
  disableTransitions?: boolean
  hit?: boolean
  clickable?: boolean
  customColor?: string
}

const props = withDefaults(defineProps<Props>(), {
  showIcon: true,
  size: 'default',
  effect: 'light',
  round: false,
  closable: false,
  disableTransitions: false,
  hit: false,
  clickable: false
})

const emit = defineEmits<{
  click: [status: string | number | boolean]
  close: [status: string | number | boolean]
}>()

// 默认状态映射
const defaultStatusMap: Record<string | number, StatusConfig> = {
  // 通用状态
  true: { text: '启用', type: 'success', icon: Check },
  false: { text: '禁用', type: 'danger', icon: Close },
  1: { text: '启用', type: 'success', icon: Check },
  0: { text: '禁用', type: 'danger', icon: Close },
  
  // 用户状态
  active: { text: '激活', type: 'success', icon: CircleCheck },
  inactive: { text: '未激活', type: 'warning', icon: Clock },
  locked: { text: '锁定', type: 'danger', icon: Lock },
  pending: { text: '待审核', type: 'warning', icon: Clock },
  
  // 角色状态
  enabled: { text: '启用', type: 'success', icon: Check },
  disabled: { text: '禁用', type: 'info', icon: Close },
  
  // 权限状态
  granted: { text: '已授权', type: 'success', icon: Unlock },
  denied: { text: '已拒绝', type: 'danger', icon: Lock },
  
  // 菜单状态
  visible: { text: '显示', type: 'success', icon: Check },
  hidden: { text: '隐藏', type: 'info', icon: Close },
  
  // 部门状态
  normal: { text: '正常', type: 'success', icon: Check },
  suspended: { text: '暂停', type: 'warning', icon: Warning },
  
  // 审计日志状态
  success: { text: '成功', type: 'success', icon: CircleCheck },
  failed: { text: '失败', type: 'danger', icon: CircleClose },
  error: { text: '错误', type: 'danger', icon: Close },
  
  // 数据权限状态
  all: { text: '全部数据', type: 'primary', icon: InfoFilled },
  dept: { text: '部门数据', type: 'warning', icon: User },
  self: { text: '个人数据', type: 'info', icon: UserFilled },
  custom: { text: '自定义', type: '', icon: QuestionFilled },
  
  // 在线状态
  online: { text: '在线', type: 'success', icon: CircleCheck },
  offline: { text: '离线', type: 'info', icon: CircleClose },
  
  // 任务状态
  running: { text: '运行中', type: 'primary', icon: Clock },
  completed: { text: '已完成', type: 'success', icon: Check },
  cancelled: { text: '已取消', type: 'info', icon: Close },
  
  // 审批状态
  approved: { text: '已通过', type: 'success', icon: Check },
  rejected: { text: '已拒绝', type: 'danger', icon: Close },
  reviewing: { text: '审核中', type: 'warning', icon: Clock }
}

// 合并状态映射
const statusMap = computed(() => ({
  ...defaultStatusMap,
  ...props.statusMap
}))

// 获取当前状态配置
const currentConfig = computed(() => {
  const key = String(props.status)
  return statusMap.value[key] || statusMap.value[props.status] || {
    text: String(props.status),
    type: '',
    icon: QuestionFilled
  }
})

// 计算标签类型
const tagType = computed(() => {
  if (props.customColor) return ''
  return currentConfig.value.type || ''
})

// 计算显示文本
const displayText = computed(() => currentConfig.value.text)

// 计算图标组件
const iconComponent = computed(() => currentConfig.value.icon)

// 点击处理
const handleClick = () => {
  if (props.clickable) {
    emit('click', props.status)
  }
}

// 关闭处理
const handleClose = () => {
  emit('close', props.status)
}
</script>

<style lang="scss" scoped>
.status-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  
  &--with-icon {
    .status-icon {
      font-size: 12px;
    }
  }
  
  &--clickable {
    cursor: pointer;
    transition: all 0.2s ease;
    
    &:hover {
      transform: translateY(-1px);
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
  }
  
  .status-text {
    font-weight: 500;
  }
}

// 自定义状态样式
.status-tag--active,
.status-tag--enabled,
.status-tag--granted,
.status-tag--visible,
.status-tag--normal,
.status-tag--success,
.status-tag--online,
.status-tag--completed,
.status-tag--approved {
  &.el-tag {
    --el-tag-bg-color: var(--el-color-success-light-9);
    --el-tag-border-color: var(--el-color-success-light-7);
    --el-tag-text-color: var(--el-color-success);
  }
}

.status-tag--inactive,
.status-tag--pending,
.status-tag--suspended,
.status-tag--reviewing {
  &.el-tag {
    --el-tag-bg-color: var(--el-color-warning-light-9);
    --el-tag-border-color: var(--el-color-warning-light-7);
    --el-tag-text-color: var(--el-color-warning);
  }
}

.status-tag--locked,
.status-tag--denied,
.status-tag--failed,
.status-tag--error,
.status-tag--rejected {
  &.el-tag {
    --el-tag-bg-color: var(--el-color-danger-light-9);
    --el-tag-border-color: var(--el-color-danger-light-7);
    --el-tag-text-color: var(--el-color-danger);
  }
}

.status-tag--disabled,
.status-tag--hidden,
.status-tag--offline,
.status-tag--cancelled {
  &.el-tag {
    --el-tag-bg-color: var(--el-color-info-light-9);
    --el-tag-border-color: var(--el-color-info-light-7);
    --el-tag-text-color: var(--el-color-info);
  }
}

.status-tag--all,
.status-tag--running {
  &.el-tag {
    --el-tag-bg-color: var(--el-color-primary-light-9);
    --el-tag-border-color: var(--el-color-primary-light-7);
    --el-tag-text-color: var(--el-color-primary);
  }
}

// 响应式设计
@media (max-width: 768px) {
  .status-tag {
    font-size: 12px;
    
    .status-icon {
      font-size: 10px;
    }
  }
}
</style>
