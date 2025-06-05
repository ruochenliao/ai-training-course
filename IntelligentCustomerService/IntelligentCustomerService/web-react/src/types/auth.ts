export interface User {
  id: string
  username: string
  email: string
  avatar?: string
  nickname: string
  roles: string[]
  permissions: string[]
  createTime: string
  updateTime: string
}

export interface LoginParams {
  username: string
  password: string
  rememberMe?: boolean
}

export interface LoginResponse {
  user: User
  token: string
  refreshToken?: string
}

export interface RegisterParams {
  username: string
  password: string
  email: string
  nickname: string
}

export interface ResetPasswordParams {
  email: string
  code: string
  newPassword: string
}

export interface ChangePasswordParams {
  oldPassword: string
  newPassword: string
}