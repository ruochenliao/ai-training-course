/**
 * 路由守卫
 */

import type { Router } from 'vue-router'
import NProgress from 'nprogress'
import 'nprogress/nprogress.css'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { checkRoutePermission } from '@/utils/permission'

// 配置NProgress
NProgress.configure({ showSpinner: false })

// 白名单路由（不需要登录）
const whiteList = ['/login', '/404', '/403']

/**
 * 设置路由守卫
 */
export function setupRouterGuards(router: Router) {
  // 全局前置守卫
  router.beforeEach(async (to, from, next) => {
    // 开始进度条
    NProgress.start()

    const authStore = useAuthStore()

    // 设置页面标题
    document.title = to.meta.title 
      ? `${to.meta.title} - ${import.meta.env.VITE_APP_TITLE}`
      : import.meta.env.VITE_APP_TITLE

    // 检查是否已登录
    if (authStore.isLoggedIn) {
      if (to.path === '/login') {
        // 已登录用户访问登录页，重定向到首页
        next({ path: '/' })
      } else {
        // 检查是否已获取用户信息
        if (!authStore.userInfo) {
          try {
            // 获取用户信息
            await authStore.fetchUserProfile()
          } catch (error) {
            // 获取用户信息失败，清除登录状态
            await authStore.logout()
            ElMessage.error('获取用户信息失败，请重新登录')
            next(`/login?redirect=${to.path}`)
            return
          }
        }

        // 检查路由权限
        if (checkRoutePermission(to)) {
          next()
        } else {
          // 权限不足
          ElMessage.error('权限不足，无法访问该页面')
          next('/403')
        }
      }
    } else {
      // 未登录
      if (whiteList.includes(to.path)) {
        // 在白名单中，直接通过
        next()
      } else {
        // 重定向到登录页
        next(`/login?redirect=${to.path}`)
      }
    }
  })

  // 全局后置守卫
  router.afterEach((to, from) => {
    // 结束进度条
    NProgress.done()

    // 记录路由跳转日志
    if (import.meta.env.DEV) {
      console.log(`Route changed: ${from.path} -> ${to.path}`)
    }
  })

  // 路由错误处理
  router.onError((error) => {
    console.error('Router error:', error)
    NProgress.done()
    ElMessage.error('页面加载失败')
  })
}
