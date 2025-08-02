import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { authApi, type LoginParams, type RegisterParams, type UserInfo } from '@/api/auth'
import { getToken, setToken, removeToken, getRefreshToken, setRefreshToken, clearAuth } from '@/utils/auth'
import router from '@/router'

export const useUserStore = defineStore('user', () => {
  // 状态
  const userInfo = ref<UserInfo | null>(null)
  const token = ref<string>(getToken() || '')
  const refreshToken = ref<string>(getRefreshToken() || '')

  // 计算属性
  const isLoggedIn = computed(() => !!token.value && !!userInfo.value)
  const userRole = computed(() => userInfo.value?.role || '')
  const userName = computed(() => userInfo.value?.username || '')
  const userAvatar = computed(() => userInfo.value?.avatar || '')
  const avatar = computed(() => userInfo.value?.avatar || '')
  
  // 登录
  const login = async (loginParams: LoginParams) => {
    try {
      const response = await authApi.login(loginParams)
      const { access_token, refresh_token, user } = response.data

      // 保存token和用户信息
      token.value = access_token
      refreshToken.value = refresh_token
      userInfo.value = user

      // 存储到本地
      setToken(access_token)
      setRefreshToken(refresh_token)

      ElMessage.success('登录成功')
      return response
    } catch (error) {
      ElMessage.error('登录失败')
      throw error
    }
  }
  
  // 注册
  const register = async (registerParams: RegisterParams) => {
    try {
      const response = await authApi.register(registerParams)
      ElMessage.success('注册成功，请登录')
      return response
    } catch (error) {
      ElMessage.error('注册失败')
      throw error
    }
  }
  
  // 获取用户信息
  const getUserInfo = async () => {
    try {
      const response = await authApi.getUserInfo()
      userInfo.value = response.data
      return response
    } catch (error) {
      console.error('获取用户信息失败:', error)
      throw error
    }
  }

  // 登出
  const logout = async () => {
    try {
      if (token.value) {
        await authApi.logout()
      }
    } catch (error) {
      console.error('登出请求失败:', error)
    } finally {
      // 清除所有状态和本地存储
      userInfo.value = null
      token.value = ''
      refreshToken.value = ''
      clearAuth()

      ElMessage.success('已退出登录')

      // 跳转到登录页
      if (router.currentRoute.value.path !== '/login') {
        router.push('/login')
      }
    }
  }
  
  // 刷新访问令牌
  const refreshAccessToken = async () => {
    try {
      const currentRefreshToken = getRefreshToken()
      if (!currentRefreshToken) {
        throw new Error('No refresh token available')
      }

      const response = await authApi.refreshToken(currentRefreshToken)
      const { access_token, refresh_token } = response.data

      // 更新token
      token.value = access_token
      refreshToken.value = refresh_token

      // 存储到本地
      setToken(access_token)
      setRefreshToken(refresh_token)

      return response
    } catch (error) {
      console.error('刷新token失败:', error)
      // 刷新失败，清除认证信息并跳转登录
      await logout()
      throw error
    }
  }

  // 初始化认证状态
  const initializeAuth = async () => {
    const storedToken = getToken()
    if (storedToken) {
      token.value = storedToken
      try {
        // 获取用户信息验证token有效性
        await getUserInfo()
      } catch (error) {
        // token无效，清除认证信息
        console.error('Token验证失败:', error)
        clearAuth()
        token.value = ''
        refreshToken.value = ''
      }
    }
  }
  
  // 检查权限
  const hasPermission = (permission: string): boolean => {
    if (!userInfo.value) return false
    // 这里可以根据实际的权限系统实现
    return userInfo.value.role === 'admin' || userInfo.value.role === permission
  }

  // 检查角色
  const hasRole = (role: string): boolean => {
    return userInfo.value?.role === role
  }
  
  return {
    // 状态
    userInfo,
    token,
    refreshToken,

    // 计算属性
    isLoggedIn,
    userRole,
    userName,
    userAvatar,
    avatar,

    // 方法
    login,
    register,
    logout,
    getUserInfo,
    refreshAccessToken,
    initializeAuth,
    hasPermission,
    hasRole
  }
}, {
  persist: {
    key: 'ai-platform-user',
    storage: localStorage,
    paths: ['userInfo']
  }
})
