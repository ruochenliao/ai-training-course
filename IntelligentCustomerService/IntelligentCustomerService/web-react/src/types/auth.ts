export interface User {
  id: number
  username: string
  email: string
  is_active: boolean
  is_superuser: boolean
  avatar?: string
  last_login?: string
  created_at: string
  updated_at: string
  dept_id?: number
  roles?: Role[]
}

export interface Role {
  id: number
  name: string
  remark?: string
}

export interface LoginParams {
  username: string
  password: string
  rememberMe?: boolean
}

export interface LoginResponse {
  access_token: string
  username: string
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
  old_password: string
  new_password: string
}