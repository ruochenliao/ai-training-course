import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import NProgress from 'nprogress'
import 'nprogress/nprogress.css'

// 配置NProgress
NProgress.configure({ showSpinner: false })

const routes: Array<RouteRecordRaw> = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/Login.vue'),
    meta: {
      title: '登录',
      requiresAuth: false
    }
  },
  {
    path: '/',
    component: () => import('@/components/Layout.vue'),
    meta: {
      requiresAuth: true
    },
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: {
          title: '仪表盘',
          requiresAuth: true
        }
      },
      {
        path: 'agents',
        name: 'AgentList',
        component: () => import('@/views/agents/AgentList.vue'),
        meta: {
          title: '智能体管理',
          requiresAuth: true
        }
      },
      {
        path: 'agents/create',
        name: 'AgentCreate',
        component: () => import('@/views/agents/AgentCreate.vue'),
        meta: {
          title: '创建智能体',
          requiresAuth: true
        }
      },
      {
        path: 'agents/:id/edit',
        name: 'AgentEdit',
        component: () => import('@/views/agents/AgentEdit.vue'),
        meta: {
          title: '编辑智能体',
          requiresAuth: true
        }
      },
      {
        path: 'agents/:id',
        name: 'AgentDetail',
        component: () => import('@/views/agents/AgentDetail.vue'),
        meta: {
          title: '智能体详情',
          requiresAuth: true
        }
      },
      {
        path: 'knowledge',
        name: 'KnowledgeList',
        component: () => import('@/views/knowledge/KnowledgeList.vue'),
        meta: {
          title: '知识库管理',
          requiresAuth: true
        }
      },
      {
        path: 'knowledge/create',
        name: 'KnowledgeCreate',
        component: () => import('@/views/knowledge/KnowledgeCreate.vue'),
        meta: {
          title: '创建知识库',
          requiresAuth: true
        }
      },
      {
        path: 'knowledge/:id/upload',
        name: 'KnowledgeUpload',
        component: () => import('@/views/knowledge/KnowledgeUpload.vue'),
        meta: {
          title: '文件上传',
          requiresAuth: true
        }
      },
      {
        path: 'chat',
        name: 'Chat',
        component: () => import('@/views/Chat.vue'),
        meta: {
          title: '对话管理',
          requiresAuth: true
        }
      },
      {
        path: 'analytics',
        name: 'Analytics',
        component: () => import('@/views/Analytics.vue'),
        meta: {
          title: '数据分析',
          requiresAuth: true
        }
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/Settings.vue'),
        meta: {
          title: '系统设置',
          requiresAuth: true
        }
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('@/views/Profile.vue'),
        meta: {
          title: '个人资料',
          requiresAuth: true
        }
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/error/NotFound.vue'),
    meta: {
      title: '页面不存在'
    }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  NProgress.start()

  const userStore = useUserStore()

  // 设置页面标题
  if (to.meta.title) {
    document.title = `${to.meta.title} - 智能体应用综合平台`
  }

  // 如果有token但没有用户信息，先初始化认证状态
  if (userStore.token && !userStore.userInfo) {
    try {
      await userStore.initializeAuth()
    } catch (error) {
      console.error('初始化认证状态失败:', error)
    }
  }

  // 检查是否需要认证
  if (to.meta.requiresAuth) {
    if (!userStore.isLoggedIn) {
      ElMessage.warning('请先登录')
      next({
        path: '/login',
        query: { redirect: to.fullPath }
      })
      return
    }

    // 如果已登录但没有用户信息，尝试获取
    if (!userStore.userInfo) {
      try {
        await userStore.getUserInfo()
      } catch (error) {
        console.error('获取用户信息失败:', error)
        ElMessage.error('登录状态已过期，请重新登录')
        next('/login')
        return
      }
    }
  }

  // 如果已登录用户访问登录页，重定向到仪表盘
  if (userStore.isLoggedIn && to.path === '/login') {
    next('/dashboard')
    return
  }

  next()
})

router.afterEach(() => {
  NProgress.done()
})

export default router
