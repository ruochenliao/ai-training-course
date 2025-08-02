import request from './request'
import type { User, ChangePasswordForm } from '@/types/user'

export const userApi = {
  // 获取当前用户信息
  getCurrentUser(): Promise<User> {
    return request.get('/users/me')
  },
  
  // 更新用户信息
  updateProfile(data: Partial<User>): Promise<User> {
    return request.put('/users/me', data)
  },
  
  // 修改密码
  changePassword(data: ChangePasswordForm): Promise<void> {
    return request.post('/users/change-password', data)
  },
  
  // 获取用户列表（管理员）
  getUserList(params: {
    skip?: number
    limit?: number
    search?: string
  }): Promise<User[]> {
    return request.get('/users/', { params })
  },
  
  // 获取指定用户信息
  getUser(userId: number): Promise<User> {
    return request.get(`/users/${userId}`)
  },
  
  // 更新用户状态（管理员）
  updateUserStatus(userId: number, isActive: boolean): Promise<void> {
    return request.put(`/users/${userId}/status`, { is_active: isActive })
  }
}
