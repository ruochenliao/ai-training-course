/**
 * 路由配置
 */

import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { setupRouterGuards } from './guards'

// 基础路由（不需要权限验证）
const constantRoutes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/Login.vue'),
    meta: {
      title: '登录',
      hidden: true
    }
  },
  {
    path: '/404',
    name: 'NotFound',
    component: () => import('@/views/error/404.vue'),
    meta: {
      title: '页面不存在',
      hidden: true
    }
  },
  {
    path: '/403',
    name: 'Forbidden',
    component: () => import('@/views/error/403.vue'),
    meta: {
      title: '权限不足',
      hidden: true
    }
  }
]

// 动态路由（需要权限验证）
const asyncRoutes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Layout',
    component: () => import('@/components/layout/Layout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/Index.vue'),
        meta: {
          title: '仪表板',
          icon: 'el-icon-odometer',
          cache: true
        }
      }
    ]
  },
  {
    path: '/system',
    name: 'System',
    component: () => import('@/components/layout/Layout.vue'),
    meta: {
      title: '系统管理',
      icon: 'el-icon-setting'
    },
    children: [
      {
        path: 'users',
        name: 'SystemUser',
        component: () => import('@/views/system/user/Index.vue'),
        meta: {
          title: '用户管理',
          icon: 'el-icon-user',
          permissions: ['user:read']
        }
      },
      {
        path: 'roles',
        name: 'SystemRole',
        component: () => import('@/views/system/role/Index.vue'),
        meta: {
          title: '角色管理',
          icon: 'el-icon-s-custom',
          permissions: ['role:read']
        }
      },
      {
        path: 'permissions',
        name: 'SystemPermission',
        component: () => import('@/views/system/permission/Index.vue'),
        meta: {
          title: '权限管理',
          icon: 'el-icon-key',
          permissions: ['permission:read']
        }
      },
      {
        path: 'menus',
        name: 'SystemMenu',
        component: () => import('@/views/system/menu/Index.vue'),
        meta: {
          title: '菜单管理',
          icon: 'el-icon-menu',
          permissions: ['menu:read']
        }
      }
    ]
  }
]

// 创建路由实例
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [...constantRoutes, ...asyncRoutes],
  scrollBehavior: () => ({ left: 0, top: 0 })
})

// 设置路由守卫
setupRouterGuards(router)

export default router
export { constantRoutes, asyncRoutes }
