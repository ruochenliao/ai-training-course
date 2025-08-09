// Copyright (c) 2025 左岚. All rights reserved.

/**
 * Store类型定义 - 解决类型推断问题
 */

import type { 
  User, 
  LoginRequest, 
  ChangePasswordRequest, 
  MenuRoute,
  Language,
  ThemeMode,
  ComponentSize
} from '@/types'

// Auth Store 类型定义
export interface AuthStoreType {
  // 状态
  token: string
  refreshToken: string
  userInfo: User | null
  permissions: string[]
  roles: string[]
  menus: MenuRoute[]
  
  // 计算属性
  readonly isLoggedIn: boolean
  readonly isSuperUser: boolean
  
  // 方法
  login: (loginData: LoginRequest) => Promise<void>
  logout: () => Promise<void>
  refreshAccessToken: () => Promise<void>
  fetchUserProfile: () => Promise<void>
  changePassword: (passwordData: ChangePasswordRequest) => Promise<void>
  hasPermission: (permission: string | string[]) => boolean
  hasRole: (role: string | string[]) => boolean
  initAuth: () => Promise<void>
}

// App Store 类型定义
export interface AppStoreType {
  // 状态
  sidebarCollapsed: boolean
  componentSize: ComponentSize
  themeMode: ThemeMode
  language: Language
  loading: boolean
  
  // 方法
  toggleSidebar: () => void
  setComponentSize: (size: ComponentSize) => void
  toggleThemeMode: () => void
  setThemeMode: (mode: ThemeMode) => void
  setLanguage: (lang: Language) => void
  setLoading: (status: boolean) => void
  initApp: () => void
}

// Menu Store 类型定义
export interface MenuStoreType {
  // 状态
  menus: MenuRoute[]
  activeMenu: string
  openedMenus: string[]
  
  // 方法
  setMenus: (menus: MenuRoute[]) => void
  setActiveMenu: (path: string) => void
  addOpenedMenu: (path: string) => void
  removeOpenedMenu: (path: string) => void
  clearOpenedMenus: () => void
  getMenuByPath: (path: string) => MenuRoute | null
  getMenuBreadcrumb: (path: string) => MenuRoute[]
}

// Permission Store 类型定义
export interface PermissionStoreType {
  // 状态
  routes: MenuRoute[]
  dynamicRoutes: MenuRoute[]
  isRoutesGenerated: boolean
  
  // 方法
  generateRoutes: (roles: string[], permissions: string[]) => Promise<MenuRoute[]>
  addDynamicRoute: (route: MenuRoute) => void
  removeDynamicRoute: (name: string) => void
  clearDynamicRoutes: () => void
  resetRoutes: () => void
}

// User Store 类型定义
export interface UserStoreType {
  // 状态
  currentUser: User | null
  userList: User[]
  userProfile: any | null
  
  // 方法
  setCurrentUser: (user: User | null) => void
  setUserList: (users: User[]) => void
  setUserProfile: (profile: any | null) => void
  updateUserInfo: (userInfo: Partial<User>) => void
  clearUserData: () => void
}
