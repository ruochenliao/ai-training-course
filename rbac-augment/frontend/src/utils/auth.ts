/**
 * 认证相关工具函数
 */

import Cookies from 'js-cookie'

// Token存储键名
const TOKEN_KEY = 'rbac_access_token'
const REFRESH_TOKEN_KEY = 'rbac_refresh_token'
const USER_INFO_KEY = 'rbac_user_info'

/**
 * 获取访问令牌
 */
export function getToken(): string | undefined {
  return Cookies.get(TOKEN_KEY)
}

/**
 * 设置访问令牌
 */
export function setToken(token: string): void {
  Cookies.set(TOKEN_KEY, token, { expires: 1 }) // 1天过期
}

/**
 * 移除访问令牌
 */
export function removeToken(): void {
  Cookies.remove(TOKEN_KEY)
}

/**
 * 获取刷新令牌
 */
export function getRefreshToken(): string | undefined {
  return Cookies.get(REFRESH_TOKEN_KEY)
}

/**
 * 设置刷新令牌
 */
export function setRefreshToken(token: string): void {
  Cookies.set(REFRESH_TOKEN_KEY, token, { expires: 7 }) // 7天过期
}

/**
 * 移除刷新令牌
 */
export function removeRefreshToken(): void {
  Cookies.remove(REFRESH_TOKEN_KEY)
}

/**
 * 获取用户信息
 */
export function getUserInfo(): any {
  const userInfo = localStorage.getItem(USER_INFO_KEY)
  return userInfo ? JSON.parse(userInfo) : null
}

/**
 * 设置用户信息
 */
export function setUserInfo(userInfo: any): void {
  localStorage.setItem(USER_INFO_KEY, JSON.stringify(userInfo))
}

/**
 * 移除用户信息
 */
export function removeUserInfo(): void {
  localStorage.removeItem(USER_INFO_KEY)
}

/**
 * 清除所有认证信息
 */
export function clearAuth(): void {
  removeToken()
  removeRefreshToken()
  removeUserInfo()
}

/**
 * 检查是否已登录
 */
export function isLoggedIn(): boolean {
  return !!getToken()
}

/**
 * 解析JWT Token
 */
export function parseJWT(token: string): any {
  try {
    const base64Url = token.split('.')[1]
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    )
    return JSON.parse(jsonPayload)
  } catch (error) {
    console.error('Failed to parse JWT token:', error)
    return null
  }
}

/**
 * 检查Token是否即将过期
 */
export function isTokenExpiringSoon(token: string, threshold = 5 * 60 * 1000): boolean {
  const payload = parseJWT(token)
  if (!payload || !payload.exp) {
    return true
  }
  
  const expirationTime = payload.exp * 1000
  const currentTime = Date.now()
  
  return expirationTime - currentTime < threshold
}
