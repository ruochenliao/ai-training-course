// token存放到localStorage和cookie
import Cookies from 'js-cookie'

const TokenKey = 'ai-platform-token'
const RefreshTokenKey = 'ai-platform-refresh-token'

// Token相关操作
export const getToken = (): string | undefined => {
  return Cookies.get(TokenKey) || localStorage.getItem(TokenKey) || undefined
}

export const setToken = (token: string, cookieExpires?: number): void => {
  // 同时存储到cookie和localStorage
  Cookies.set(TokenKey, token, { expires: cookieExpires || 1 })
  localStorage.setItem(TokenKey, token)
}

export const removeToken = (): void => {
  Cookies.remove(TokenKey)
  localStorage.removeItem(TokenKey)
}

// Refresh Token相关操作
export const getRefreshToken = (): string | undefined => {
  return Cookies.get(RefreshTokenKey) || localStorage.getItem(RefreshTokenKey) || undefined
}

export const setRefreshToken = (refreshToken: string, cookieExpires?: number): void => {
  Cookies.set(RefreshTokenKey, refreshToken, { expires: cookieExpires || 7 })
  localStorage.setItem(RefreshTokenKey, refreshToken)
}

export const removeRefreshToken = (): void => {
  Cookies.remove(RefreshTokenKey)
  localStorage.removeItem(RefreshTokenKey)
}

// 清除所有认证信息
export const clearAuth = (): void => {
  removeToken()
  removeRefreshToken()
}

// 检查是否已登录
export const isAuthenticated = (): boolean => {
  const token = getToken()
  return !!token
}
