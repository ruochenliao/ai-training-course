import { ref, computed } from 'vue'
import type { Ref } from 'vue'

interface User {
  id: string
  username: string
  email: string
  full_name: string
  role: string
  is_active: boolean
  created_at: string
  updated_at: string
}

interface LoginCredentials {
  username: string
  password: string
}

interface LoginResponse {
  access_token: string
  token_type: string
  user: User
}

export function useAuth() {
  const config = useRuntimeConfig()
  const router = useRouter()
  const { $fetch } = useNuxtApp()
  
  // 状态
  const user = ref<User | null>(null)
  const token = useCookie('auth-token', {
    default: () => null,
    maxAge: 60 * 60 * 24 * 7, // 7天
    secure: true,
    sameSite: 'strict'
  })
  const loading = ref(false)
  const error = ref<string | null>(null)
  
  // 计算属性
  const isAuthenticated = computed(() => !!token.value && !!user.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const isManager = computed(() => user.value?.role === 'manager' || isAdmin.value)
  
  // 登录
  const login = async (credentials: LoginCredentials) => {
    loading.value = true
    error.value = null
    
    try {
      const response = await $fetch<LoginResponse>(`${config.public.apiBase}/auth/login`, {
        method: 'POST',
        body: credentials
      })
      
      // 保存token和用户信息
      token.value = response.access_token
      user.value = response.user
      
      // 跳转到首页
      await router.push('/')
      
      return response
    } catch (err: any) {
      error.value = err.data?.message || '登录失败'
      throw err
    } finally {
      loading.value = false
    }
  }
  
  // 登出
  const logout = async () => {
    loading.value = true
    
    try {
      // 调用登出API
      if (token.value) {
        await $fetch(`${config.public.apiBase}/auth/logout`, {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${token.value}`
          }
        })
      }
    } catch (err) {
      console.error('登出API调用失败:', err)
    } finally {
      // 清除本地状态
      token.value = null
      user.value = null
      loading.value = false
      
      // 跳转到登录页
      await router.push('/login')
    }
  }
  
  // 获取当前用户信息
  const fetchUser = async () => {
    if (!token.value) {
      return null
    }
    
    try {
      const response = await $fetch<User>(`${config.public.apiBase}/auth/me`, {
        headers: {
          Authorization: `Bearer ${token.value}`
        }
      })
      
      user.value = response
      return response
    } catch (err) {
      console.error('获取用户信息失败:', err)
      // 如果token无效，清除认证状态
      token.value = null
      user.value = null
      throw err
    }
  }
  
  // 刷新token
  const refreshToken = async () => {
    if (!token.value) {
      return null
    }
    
    try {
      const response = await $fetch<LoginResponse>(`${config.public.apiBase}/auth/refresh`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token.value}`
        }
      })
      
      token.value = response.access_token
      user.value = response.user
      
      return response
    } catch (err) {
      console.error('刷新token失败:', err)
      // 刷新失败，清除认证状态
      await logout()
      throw err
    }
  }
  
  // 修改密码
  const changePassword = async (oldPassword: string, newPassword: string) => {
    loading.value = true
    error.value = null
    
    try {
      await $fetch(`${config.public.apiBase}/auth/change-password`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token.value}`
        },
        body: {
          old_password: oldPassword,
          new_password: newPassword
        }
      })
      
      return true
    } catch (err: any) {
      error.value = err.data?.message || '修改密码失败'
      throw err
    } finally {
      loading.value = false
    }
  }
  
  // 检查权限
  const hasPermission = (permission: string) => {
    if (!user.value) return false
    
    // 管理员拥有所有权限
    if (user.value.role === 'admin') return true
    
    // 根据角色检查权限
    const rolePermissions = {
      manager: [
        'knowledge_base.read',
        'knowledge_base.write',
        'document.read',
        'document.write',
        'user.read',
        'system.read'
      ],
      user: [
        'knowledge_base.read',
        'document.read'
      ]
    }
    
    const userPermissions = rolePermissions[user.value.role as keyof typeof rolePermissions] || []
    return userPermissions.includes(permission)
  }
  
  // 初始化认证状态
  const initAuth = async () => {
    if (token.value && !user.value) {
      try {
        await fetchUser()
      } catch (err) {
        console.error('初始化认证状态失败:', err)
      }
    }
  }
  
  // 页面加载时初始化
  onMounted(() => {
    initAuth()
  })
  
  return {
    // 状态
    user: readonly(user),
    token: readonly(token),
    loading: readonly(loading),
    error: readonly(error),
    
    // 计算属性
    isAuthenticated,
    isAdmin,
    isManager,
    
    // 方法
    login,
    logout,
    fetchUser,
    refreshToken,
    changePassword,
    hasPermission,
    initAuth
  }
}

// 认证中间件
export function useAuthGuard() {
  const { isAuthenticated } = useAuth()
  const router = useRouter()
  
  const requireAuth = () => {
    if (!isAuthenticated.value) {
      router.push('/login')
      return false
    }
    return true
  }
  
  const requireAdmin = () => {
    const { isAdmin } = useAuth()
    if (!requireAuth() || !isAdmin.value) {
      throw createError({
        statusCode: 403,
        statusMessage: '权限不足'
      })
    }
    return true
  }
  
  const requireManager = () => {
    const { isManager } = useAuth()
    if (!requireAuth() || !isManager.value) {
      throw createError({
        statusCode: 403,
        statusMessage: '权限不足'
      })
    }
    return true
  }
  
  return {
    requireAuth,
    requireAdmin,
    requireManager
  }
}
