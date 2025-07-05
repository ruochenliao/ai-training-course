<template>
  <div class="action-buttons" :class="[`action-buttons--${layout}`, { 'action-buttons--compact': compact }]">
    <template v-for="(action, index) in visibleActions" :key="action.key || index">
      <!-- 普通按钮 -->
      <el-button
        v-if="!action.dropdown"
        :type="action.type || 'default'"
        :size="action.size || size"
        :icon="action.icon"
        :loading="action.loading"
        :disabled="action.disabled"
        :plain="action.plain"
        :round="action.round"
        :circle="action.circle"
        :text="action.text"
        :bg="action.bg"
        :link="action.link"
        :class="action.class"
        @click="handleAction(action)"
      >
        {{ action.label }}
      </el-button>
      
      <!-- 下拉按钮 -->
      <el-dropdown
        v-else
        :size="action.size || size"
        :split-button="action.splitButton"
        :type="action.type || 'default'"
        :disabled="action.disabled"
        :placement="action.placement || 'bottom'"
        :trigger="action.trigger || 'hover'"
        @click="action.splitButton && handleAction(action)"
        @command="(command: string) => handleDropdownAction(action, command)"
      >
        <el-button
          :type="action.type || 'default'"
          :size="action.size || size"
          :icon="action.icon"
          :loading="action.loading"
          :disabled="action.disabled"
          :class="action.class"
        >
          {{ action.label }}
          <el-icon v-if="!action.splitButton" class="el-icon--right">
            <ArrowDown />
          </el-icon>
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item
              v-for="item in action.items"
              :key="item.key || item.command"
              :command="item.command"
              :disabled="item.disabled"
              :divided="item.divided"
              :icon="item.icon"
            >
              {{ item.label }}
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
      
      <!-- 分隔符 -->
      <el-divider
        v-if="action.divider && index < visibleActions.length - 1"
        direction="vertical"
      />
    </template>
    
    <!-- 更多操作按钮 -->
    <el-dropdown
      v-if="hasMoreActions"
      :size="size"
      trigger="click"
      placement="bottom-end"
      @command="handleMoreAction"
    >
      <el-button :size="size" :icon="MoreFilled" circle />
      <template #dropdown>
        <el-dropdown-menu>
          <el-dropdown-item
            v-for="action in moreActions"
            :key="action.key"
            :command="action.key"
            :disabled="action.disabled"
            :divided="action.divided"
            :icon="action.icon"
          >
            {{ action.label }}
          </el-dropdown-item>
        </el-dropdown-menu>
      </template>
    </el-dropdown>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ArrowDown, MoreFilled } from '@element-plus/icons-vue'

export interface DropdownItem {
  key?: string
  command: string
  label: string
  icon?: any
  disabled?: boolean
  divided?: boolean
}

export interface ActionButton {
  key?: string
  label: string
  type?: 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'default'
  size?: 'large' | 'default' | 'small'
  icon?: any
  loading?: boolean
  disabled?: boolean
  plain?: boolean
  round?: boolean
  circle?: boolean
  text?: boolean
  bg?: boolean
  link?: boolean
  class?: string
  permission?: string | string[]
  visible?: boolean
  divider?: boolean
  // 下拉按钮特有属性
  dropdown?: boolean
  splitButton?: boolean
  placement?: 'top' | 'top-start' | 'top-end' | 'bottom' | 'bottom-start' | 'bottom-end'
  trigger?: 'hover' | 'click'
  items?: DropdownItem[]
  // 事件处理
  onClick?: (action: ActionButton) => void
}

interface Props {
  actions: ActionButton[]
  size?: 'large' | 'default' | 'small'
  layout?: 'horizontal' | 'vertical'
  compact?: boolean
  maxVisible?: number
  permissions?: string[]
}

const props = withDefaults(defineProps<Props>(), {
  size: 'default',
  layout: 'horizontal',
  compact: false,
  maxVisible: 5,
  permissions: () => []
})

const emit = defineEmits<{
  action: [action: ActionButton]
  dropdownAction: [action: ActionButton, command: string]
}>()

// 检查权限
const hasPermission = (permission?: string | string[]) => {
  if (!permission) return true
  if (typeof permission === 'string') {
    return props.permissions.includes(permission)
  }
  return permission.some(p => props.permissions.includes(p))
}

// 过滤可见的操作
const filteredActions = computed(() => {
  return props.actions.filter(action => {
    // 检查可见性
    if (action.visible === false) return false
    // 检查权限
    if (!hasPermission(action.permission)) return false
    return true
  })
})

// 可见的操作（不超过最大显示数量）
const visibleActions = computed(() => {
  return filteredActions.value.slice(0, props.maxVisible)
})

// 更多操作
const moreActions = computed(() => {
  return filteredActions.value.slice(props.maxVisible)
})

// 是否有更多操作
const hasMoreActions = computed(() => {
  return moreActions.value.length > 0
})

// 处理操作点击
const handleAction = (action: ActionButton) => {
  if (action.disabled || action.loading) return
  
  if (action.onClick) {
    action.onClick(action)
  } else {
    emit('action', action)
  }
}

// 处理下拉操作
const handleDropdownAction = (action: ActionButton, command: string) => {
  emit('dropdownAction', action, command)
}

// 处理更多操作
const handleMoreAction = (command: string) => {
  const action = moreActions.value.find(a => a.key === command)
  if (action) {
    handleAction(action)
  }
}
</script>

<style lang="scss" scoped>
.action-buttons {
  display: flex;
  align-items: center;
  gap: 8px;
  
  &--vertical {
    flex-direction: column;
    align-items: stretch;
    
    .el-button {
      width: 100%;
    }
  }
  
  &--compact {
    gap: 4px;
  }
  
  .el-divider--vertical {
    height: 20px;
    margin: 0 4px;
  }
}

// 响应式设计
@media (max-width: 768px) {
  .action-buttons {
    gap: 4px;
    
    &--horizontal {
      flex-wrap: wrap;
    }
    
    .el-button {
      font-size: 12px;
      padding: 6px 12px;
      
      &.el-button--small {
        padding: 4px 8px;
      }
    }
  }
}

// 按钮组样式优化
.action-buttons {
  .el-button + .el-button {
    margin-left: 0;
  }
  
  // 主要操作按钮突出显示
  .el-button--primary {
    font-weight: 500;
  }
  
  // 危险操作按钮样式
  .el-button--danger {
    &:hover {
      transform: translateY(-1px);
      box-shadow: 0 2px 4px rgba(245, 108, 108, 0.3);
    }
  }
  
  // 文本按钮样式
  .el-button--text {
    padding: 4px 8px;
    
    &:hover {
      background-color: var(--el-color-primary-light-9);
    }
  }
  
  // 圆形按钮样式
  .el-button.is-circle {
    &:hover {
      transform: scale(1.05);
    }
  }
}

// 下拉按钮样式
.el-dropdown {
  .el-button {
    .el-icon--right {
      margin-left: 4px;
      transition: transform 0.2s ease;
    }
  }
  
  &.is-opened {
    .el-icon--right {
      transform: rotate(180deg);
    }
  }
}

// 加载状态样式
.el-button.is-loading {
  pointer-events: none;
  
  .el-icon {
    animation: rotating 2s linear infinite;
  }
}

@keyframes rotating {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}
</style>
