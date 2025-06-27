import {defineStore} from 'pinia'
import axios from 'axios'

interface User {
  id: string
  username: string
  email: string
  full_name: string
  role: 'admin' | 'manager' | 'user'
  department?: string
  is_active: boolean
  last_login_at?: string
  created_at: string
  updated_at: string
}

interface CreateUserData {
  username: string
  email: string
  full_name: string
  password: string
  role: string
  department?: string
}

interface UpdateUserData {
  email?: string
  full_name?: string
  role?: string
  department?: string
  is_active?: boolean
}

export const useUserStore = defineStore('user', {
  state: () => ({
    users: [] as User[],
    currentUser: null as User | null,
    loading: false,
    error: null as string | null
  }),

  getters: {
    getUserById: (state) => (id: string) => {
      return state.users.find(user => user.id === id)
    },
    
    getUsersByRole: (state) => (role: string) => {
      return state.users.filter(user => user.role === role)
    },
    
    getActiveUsers: (state) => {
      return state.users.filter(user => user.is_active)
    },
    
    getTotalUsers: (state) => {
      return state.users.length
    },
    
    getAdminUsers: (state) => {
      return state.users.filter(user => user.role === 'admin' || user.role === 'manager')
    }
  },

  actions: {
    // 获取用户列表
    async fetchUsers() {
      this.loading = true
      this.error = null

      try {
        // 模拟数据，实际应该调用 API
        await new Promise(resolve => setTimeout(resolve, 500))

        this.users = [
          {
            id: '1',
            username: 'admin',
            email: 'admin@company.com',
            full_name: '系统管理员',
            role: 'admin',
            department: 'IT部门',
            is_active: true,
            last_login_at: '2024-01-18T10:30:00Z',
            created_at: '2024-01-01T00:00:00Z',
            updated_at: '2024-01-18T10:30:00Z'
          },
          {
            id: '2',
            username: 'manager1',
            email: 'manager1@company.com',
            full_name: '张经理',
            role: 'manager',
            department: '产品部',
            is_active: true,
            last_login_at: '2024-01-17T16:45:00Z',
            created_at: '2024-01-05T00:00:00Z',
            updated_at: '2024-01-17T16:45:00Z'
          },
          {
            id: '3',
            username: 'user1',
            email: 'user1@company.com',
            full_name: '李小明',
            role: 'user',
            department: '销售部',
            is_active: true,
            last_login_at: '2024-01-18T09:15:00Z',
            created_at: '2024-01-10T00:00:00Z',
            updated_at: '2024-01-18T09:15:00Z'
          },
          {
            id: '4',
            username: 'user2',
            email: 'user2@company.com',
            full_name: '王小红',
            role: 'user',
            department: '客服部',
            is_active: false,
            created_at: '2024-01-12T00:00:00Z',
            updated_at: '2024-01-15T00:00:00Z'
          },
          {
            id: '5',
            username: 'user3',
            email: 'user3@company.com',
            full_name: '刘小强',
            role: 'user',
            department: '技术部',
            is_active: true,
            last_login_at: '2024-01-16T14:20:00Z',
            created_at: '2024-01-14T00:00:00Z',
            updated_at: '2024-01-16T14:20:00Z'
          }
        ]

        return this.users
      } catch (error) {
        this.error = '获取用户列表失败'
        throw error
      } finally {
        this.loading = false
      }
    },

    // 获取当前用户信息
    async getCurrentUser() {
      try {
        const response = await axios.get('/api/v1/users/me')
        this.currentUser = response.data
        return this.currentUser
      } catch (error) {
        this.error = error.response?.data?.message || '获取用户信息失败'
        throw error
      }
    },

    // 创建用户
    async createUser(userData: CreateUserData) {
      try {
        const response = await axios.post('/api/v1/users', userData)
        const newUser = response.data
        
        // 添加到本地状态
        this.users.unshift(newUser)
        
        return newUser
      } catch (error) {
        this.error = error.response?.data?.message || '创建用户失败'
        throw error
      }
    },

    // 更新用户
    async updateUser(id: string, userData: UpdateUserData) {
      try {
        const response = await axios.put(`/api/v1/users/${id}`, userData)
        const updatedUser = response.data
        
        // 更新本地状态
        const index = this.users.findIndex(user => user.id === id)
        if (index !== -1) {
          this.users[index] = updatedUser
        }
        
        return updatedUser
      } catch (error) {
        this.error = error.response?.data?.message || '更新用户失败'
        throw error
      }
    },

    // 删除用户
    async deleteUser(id: string) {
      try {
        await axios.delete(`/api/v1/users/${id}`)
        
        // 从本地状态中移除
        this.users = this.users.filter(user => user.id !== id)
      } catch (error) {
        this.error = error.response?.data?.message || '删除用户失败'
        throw error
      }
    },

    // 批量删除用户
    async batchDeleteUsers(ids: string[]) {
      try {
        await axios.post('/api/v1/users/batch-delete', { ids })
        
        // 从本地状态中移除
        this.users = this.users.filter(user => !ids.includes(user.id))
      } catch (error) {
        this.error = error.response?.data?.message || '批量删除失败'
        throw error
      }
    },

    // 启用用户
    async enableUser(id: string) {
      try {
        const response = await axios.post(`/api/v1/users/${id}/enable`)
        
        // 更新本地状态
        const user = this.users.find(user => user.id === id)
        if (user) {
          user.is_active = true
        }
        
        return response.data
      } catch (error) {
        this.error = error.response?.data?.message || '启用用户失败'
        throw error
      }
    },

    // 禁用用户
    async disableUser(id: string) {
      try {
        const response = await axios.post(`/api/v1/users/${id}/disable`)
        
        // 更新本地状态
        const user = this.users.find(user => user.id === id)
        if (user) {
          user.is_active = false
        }
        
        return response.data
      } catch (error) {
        this.error = error.response?.data?.message || '禁用用户失败'
        throw error
      }
    },

    // 批量启用用户
    async batchEnableUsers(ids: string[]) {
      try {
        await axios.post('/api/v1/users/batch-enable', { ids })
        
        // 更新本地状态
        this.users.forEach(user => {
          if (ids.includes(user.id)) {
            user.is_active = true
          }
        })
      } catch (error) {
        this.error = error.response?.data?.message || '批量启用失败'
        throw error
      }
    },

    // 批量禁用用户
    async batchDisableUsers(ids: string[]) {
      try {
        await axios.post('/api/v1/users/batch-disable', { ids })
        
        // 更新本地状态
        this.users.forEach(user => {
          if (ids.includes(user.id)) {
            user.is_active = false
          }
        })
      } catch (error) {
        this.error = error.response?.data?.message || '批量禁用失败'
        throw error
      }
    },

    // 重置密码
    async resetPassword(id: string, newPassword: string) {
      try {
        const response = await axios.post(`/api/v1/users/${id}/reset-password`, {
          password: newPassword
        })
        
        return response.data
      } catch (error) {
        this.error = error.response?.data?.message || '重置密码失败'
        throw error
      }
    },

    // 修改密码
    async changePassword(oldPassword: string, newPassword: string) {
      try {
        const response = await axios.post('/api/v1/users/change-password', {
          old_password: oldPassword,
          new_password: newPassword
        })
        
        return response.data
      } catch (error) {
        this.error = error.response?.data?.message || '修改密码失败'
        throw error
      }
    },

    // 搜索用户
    async searchUsers(query: string, filters?: any) {
      try {
        const params = { q: query, ...filters }
        const response = await axios.get('/api/v1/users/search', { params })
        return response.data.items || []
      } catch (error) {
        this.error = error.response?.data?.message || '搜索失败'
        throw error
      }
    },

    // 获取用户统计信息
    async getUserStats() {
      try {
        const response = await axios.get('/api/v1/users/stats')
        return response.data
      } catch (error) {
        this.error = error.response?.data?.message || '获取统计信息失败'
        throw error
      }
    },

    // 获取用户活动日志
    async getUserActivityLog(id: string, page = 1, pageSize = 20) {
      try {
        const response = await axios.get(`/api/v1/users/${id}/activity-log`, {
          params: { page, page_size: pageSize }
        })
        return response.data
      } catch (error) {
        this.error = error.response?.data?.message || '获取活动日志失败'
        throw error
      }
    },

    // 导出用户列表
    async exportUsers(format = 'xlsx') {
      try {
        const response = await axios.get('/api/v1/users/export', {
          params: { format },
          responseType: 'blob'
        })
        
        // 创建下载链接
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', `users-${Date.now()}.${format}`)
        document.body.appendChild(link)
        link.click()
        link.remove()
        window.URL.revokeObjectURL(url)
      } catch (error) {
        this.error = error.response?.data?.message || '导出失败'
        throw error
      }
    },

    // 清除错误状态
    clearError() {
      this.error = null
    },

    // 重置状态
    reset() {
      this.users = []
      this.currentUser = null
      this.loading = false
      this.error = null
    }
  }
})
