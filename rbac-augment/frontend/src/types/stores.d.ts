// Copyright (c) 2025 左岚. All rights reserved.

/**
 * Store模块类型声明 - 完整重构版本
 */

// 声明App Store模块
declare module '@/stores/app' {
  import type { Language, ThemeMode, ComponentSize } from '@/types'

  export interface AppState {
    sidebarCollapsed: boolean
    componentSize: ComponentSize
    themeMode: ThemeMode
    language: Language
    loading: boolean
  }

  export interface AppStore extends AppState {
    toggleSidebar: () => void
    setComponentSize: (size: ComponentSize) => void
    toggleThemeMode: () => void
    setThemeMode: (mode: ThemeMode) => void
    setLanguage: (lang: Language) => void
    setLoading: (status: boolean) => void
    initApp: () => void
  }

  export function useAppStore(): AppStore
}

// 声明Auth Store模块
declare module '@/stores/auth' {
  import type {
    User,
    LoginRequest,
    ChangePasswordRequest,
    UserProfile,
    MenuRoute
  } from '@/types'

  export interface AuthState {
    token: string
    refreshToken: string
    userInfo: User | null
    permissions: string[]
    roles: string[]
    menus: MenuRoute[]
  }

  export interface AuthStore extends AuthState {
    // 计算属性
    readonly isLoggedIn: boolean
    readonly isSuperUser: boolean

    // 认证方法
    login: (loginData: LoginRequest) => Promise<void>
    logout: () => Promise<void>
    initAuth: () => Promise<void>

    // Token管理
    refreshAccessToken: () => Promise<void>
    setToken: (token: string, refreshToken: string) => void
    clearToken: () => void

    // 用户信息管理
    fetchUserProfile: () => Promise<void>
    refreshUserInfo: () => Promise<void>
    changePassword: (passwordData: ChangePasswordRequest) => Promise<void>

    // 权限检查
    hasPermission: (permission: string | string[]) => boolean
    hasRole: (role: string | string[]) => boolean
  }

  export function useAuthStore(): AuthStore
}

// 声明Menu Store模块
declare module '@/stores/menu' {
  import type { MenuRoute } from '@/types'

  export interface MenuState {
    menus: MenuRoute[]
    activeMenu: string
    openedMenus: string[]
  }

  export interface MenuStore extends MenuState {
    setMenus: (menus: MenuRoute[]) => void
    setActiveMenu: (path: string) => void
    addOpenedMenu: (path: string) => void
    removeOpenedMenu: (path: string) => void
    clearOpenedMenus: () => void
    getMenuByPath: (path: string) => MenuRoute | null
    getMenuBreadcrumb: (path: string) => MenuRoute[]
  }

  export function useMenuStore(): MenuStore
}

// 声明Permission Store模块
declare module '@/stores/permission' {
  import type { MenuRoute } from '@/types'

  export interface PermissionState {
    routes: MenuRoute[]
    dynamicRoutes: MenuRoute[]
    isRoutesGenerated: boolean
  }

  export interface PermissionStore extends PermissionState {
    generateRoutes: (roles: string[], permissions: string[]) => Promise<MenuRoute[]>
    addDynamicRoute: (route: MenuRoute) => void
    removeDynamicRoute: (name: string) => void
    clearDynamicRoutes: () => void
    resetRoutes: () => void
  }

  export function usePermissionStore(): PermissionStore
}

// 声明User Store模块
declare module '@/stores/user' {
  import type { User, UserProfile } from '@/types'

  export interface UserState {
    currentUser: User | null
    userList: User[]
    userProfile: UserProfile | null
  }

  export interface UserStore extends UserState {
    setCurrentUser: (user: User | null) => void
    setUserList: (users: User[]) => void
    setUserProfile: (profile: UserProfile | null) => void
    updateUserInfo: (userInfo: Partial<User>) => void
    clearUserData: () => void
  }

  export function useUserStore(): UserStore
}