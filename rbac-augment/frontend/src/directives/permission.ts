/**
 * 权限指令
 */

import type { App, Directive } from 'vue'
import { useAuthStore } from '@/stores/auth'

/**
 * 权限验证指令
 * 用法：v-permission="['user:create']" 或 v-permission="'user:read'"
 */
const permission: Directive = {
  mounted(el, binding) {
    const { value } = binding
    const authStore = useAuthStore()

    if (value) {
      const hasPermission = authStore.hasPermission(value)
      
      if (!hasPermission) {
        // 移除元素
        el.parentNode?.removeChild(el)
      }
    } else {
      console.error('权限指令需要传入权限值')
    }
  },
  
  updated(el, binding) {
    const { value } = binding
    const authStore = useAuthStore()

    if (value) {
      const hasPermission = authStore.hasPermission(value)
      
      if (!hasPermission) {
        // 隐藏元素
        el.style.display = 'none'
      } else {
        // 显示元素
        el.style.display = ''
      }
    }
  }
}

/**
 * 角色验证指令
 * 用法：v-role="['admin']" 或 v-role="'user'"
 */
const role: Directive = {
  mounted(el, binding) {
    const { value } = binding
    const authStore = useAuthStore()

    if (value) {
      const hasRole = authStore.hasRole(value)
      
      if (!hasRole) {
        // 移除元素
        el.parentNode?.removeChild(el)
      }
    } else {
      console.error('角色指令需要传入角色值')
    }
  },
  
  updated(el, binding) {
    const { value } = binding
    const authStore = useAuthStore()

    if (value) {
      const hasRole = authStore.hasRole(value)
      
      if (!hasRole) {
        // 隐藏元素
        el.style.display = 'none'
      } else {
        // 显示元素
        el.style.display = ''
      }
    }
  }
}

/**
 * 权限禁用指令
 * 用法：v-permission-disabled="['user:update']"
 */
const permissionDisabled: Directive = {
  mounted(el, binding) {
    const { value } = binding
    const authStore = useAuthStore()

    if (value) {
      const hasPermission = authStore.hasPermission(value)
      
      if (!hasPermission) {
        // 禁用元素
        el.disabled = true
        el.classList.add('is-disabled')
        el.style.cursor = 'not-allowed'
        el.style.opacity = '0.5'
      }
    }
  },
  
  updated(el, binding) {
    const { value } = binding
    const authStore = useAuthStore()

    if (value) {
      const hasPermission = authStore.hasPermission(value)
      
      if (!hasPermission) {
        // 禁用元素
        el.disabled = true
        el.classList.add('is-disabled')
        el.style.cursor = 'not-allowed'
        el.style.opacity = '0.5'
      } else {
        // 启用元素
        el.disabled = false
        el.classList.remove('is-disabled')
        el.style.cursor = ''
        el.style.opacity = ''
      }
    }
  }
}

/**
 * 注册权限指令
 */
export function setupPermissionDirectives(app: App) {
  app.directive('permission', permission)
  app.directive('role', role)
  app.directive('permission-disabled', permissionDisabled)
}

export { permission, role, permissionDisabled }
