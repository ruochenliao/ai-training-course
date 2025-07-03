/**
 * 前后端API集成测试工具
 */

import * as authApi from '@/api/auth'
import * as userApi from '@/api/user'
import * as roleApi from '@/api/role'
import * as permissionApi from '@/api/permission'
import * as menuApi from '@/api/menu'
import * as departmentApi from '@/api/department'
import { ElMessage } from 'element-plus'

interface TestResult {
  name: string
  success: boolean
  message: string
  data?: any
}

class APITester {
  private results: TestResult[] = []

  private logResult(name: string, success: boolean, message: string, data?: any) {
    const result = { name, success, message, data }
    this.results.push(result)
    
    const status = success ? '✅' : '❌'
    console.log(`${status} ${name}: ${message}`)
    
    if (success) {
      ElMessage.success(`${name}: ${message}`)
    } else {
      ElMessage.error(`${name}: ${message}`)
    }
  }

  async testAuth() {
    console.log('\n🔐 测试认证模块...')
    
    try {
      // 测试登录
      const loginResult = await authApi.login({
        username: 'admin',
        password: 'admin123'
      })
      
      this.logResult('用户登录', true, '登录成功', loginResult.data)
      
      // 测试获取用户资料
      const profileResult = await authApi.getUserProfile()
      this.logResult('获取用户资料', true, '获取成功', profileResult.data)
      
      // 测试获取用户权限
      const permissionsResult = await authApi.getUserPermissions()
      this.logResult('获取用户权限', true, '获取成功', permissionsResult.data)
      
      // 测试获取用户菜单
      const menusResult = await authApi.getUserMenus()
      this.logResult('获取用户菜单', true, '获取成功', menusResult.data)
      
    } catch (error: any) {
      this.logResult('认证模块测试', false, error.message || '测试失败')
    }
  }

  async testUser() {
    console.log('\n👥 测试用户管理模块...')
    
    try {
      // 测试获取用户列表
      const userListResult = await userApi.getUserList({
        page: 1,
        page_size: 10
      })
      this.logResult('获取用户列表', true, '获取成功', userListResult.data)
      
      // 测试创建用户
      const createUserResult = await userApi.createUser({
        username: `test_user_${Date.now()}`,
        email: `test_${Date.now()}@example.com`,
        password: 'test123456',
        full_name: '测试用户',
        phone: '13800138000'
      })
      this.logResult('创建用户', true, '创建成功', createUserResult.data)
      
      // 如果创建成功，测试获取用户详情
      if (createUserResult.data?.id) {
        const userDetailResult = await userApi.getUserDetail(createUserResult.data.id)
        this.logResult('获取用户详情', true, '获取成功', userDetailResult.data)
      }
      
    } catch (error: any) {
      this.logResult('用户管理模块测试', false, error.message || '测试失败')
    }
  }

  async testRole() {
    console.log('\n🎭 测试角色管理模块...')
    
    try {
      // 测试获取角色列表
      const roleListResult = await roleApi.getRoleList({
        page: 1,
        page_size: 10
      })
      this.logResult('获取角色列表', true, '获取成功', roleListResult.data)
      
      // 测试创建角色
      const createRoleResult = await roleApi.createRole({
        name: `测试角色_${Date.now()}`,
        code: `test_role_${Date.now()}`,
        description: '这是一个测试角色'
      })
      this.logResult('创建角色', true, '创建成功', createRoleResult.data)
      
    } catch (error: any) {
      this.logResult('角色管理模块测试', false, error.message || '测试失败')
    }
  }

  async testPermission() {
    console.log('\n🔑 测试权限管理模块...')
    
    try {
      // 测试获取权限列表
      const permissionListResult = await permissionApi.getPermissionList({
        page: 1,
        page_size: 10
      })
      this.logResult('获取权限列表', true, '获取成功', permissionListResult.data)
      
      // 测试创建权限
      const createPermissionResult = await permissionApi.createPermission({
        name: `测试权限_${Date.now()}`,
        code: `test:permission:${Date.now()}`,
        description: '这是一个测试权限',
        resource: 'test',
        action: 'read',
        group: '测试组'
      })
      this.logResult('创建权限', true, '创建成功', createPermissionResult.data)
      
    } catch (error: any) {
      this.logResult('权限管理模块测试', false, error.message || '测试失败')
    }
  }

  async testMenu() {
    console.log('\n📋 测试菜单管理模块...')
    
    try {
      // 测试获取菜单列表
      const menuListResult = await menuApi.getMenuList({
        page: 1,
        page_size: 10
      })
      this.logResult('获取菜单列表', true, '获取成功', menuListResult.data)
      
      // 测试获取菜单树
      const menuTreeResult = await menuApi.getMenuTree()
      this.logResult('获取菜单树', true, '获取成功', menuTreeResult.data)
      
      // 测试创建菜单
      const createMenuResult = await menuApi.createMenu({
        name: `test_menu_${Date.now()}`,
        title: `测试菜单_${Date.now()}`,
        path: `/test-menu-${Date.now()}`,
        component: 'TestMenu',
        icon: 'test-icon',
        sort_order: 100,
        is_visible: true,
        is_external: false
      })
      this.logResult('创建菜单', true, '创建成功', createMenuResult.data)
      
    } catch (error: any) {
      this.logResult('菜单管理模块测试', false, error.message || '测试失败')
    }
  }

  async testDepartment() {
    console.log('\n🏢 测试部门管理模块...')
    
    try {
      // 测试获取部门树
      const departmentTreeResult = await departmentApi.getDepartmentTree()
      this.logResult('获取部门树', true, '获取成功', departmentTreeResult.data)
      
      // 测试获取部门列表
      const departmentListResult = await departmentApi.getDepartmentList({
        page: 1,
        page_size: 10
      })
      this.logResult('获取部门列表', true, '获取成功', departmentListResult.data)
      
    } catch (error: any) {
      this.logResult('部门管理模块测试', false, error.message || '测试失败')
    }
  }

  async runAllTests() {
    console.log('🚀 开始前后端API集成测试...')
    console.log('=' * 50)
    
    this.results = []
    
    await this.testAuth()
    await this.testUser()
    await this.testRole()
    await this.testPermission()
    await this.testMenu()
    await this.testDepartment()
    
    // 统计结果
    const totalTests = this.results.length
    const successfulTests = this.results.filter(r => r.success).length
    const failedTests = totalTests - successfulTests
    
    console.log('\n' + '=' * 50)
    console.log('📊 测试结果统计:')
    console.log(`总测试数: ${totalTests}`)
    console.log(`成功: ${successfulTests}`)
    console.log(`失败: ${failedTests}`)
    console.log(`成功率: ${((successfulTests / totalTests) * 100).toFixed(1)}%`)
    
    if (failedTests > 0) {
      console.log('\n❌ 失败的测试:')
      this.results.filter(r => !r.success).forEach(result => {
        console.log(`  - ${result.name}: ${result.message}`)
      })
    }
    
    const allSuccess = failedTests === 0
    if (allSuccess) {
      console.log('\n🎉 所有API接口测试通过！')
      ElMessage.success('所有API接口测试通过！')
    } else {
      console.log('\n⚠️ 部分API接口测试失败，请检查日志')
      ElMessage.warning('部分API接口测试失败，请检查日志')
    }
    
    return {
      total: totalTests,
      success: successfulTests,
      failed: failedTests,
      successRate: (successfulTests / totalTests) * 100,
      results: this.results
    }
  }
}

export const apiTester = new APITester()

// 在开发环境下暴露到全局，方便调试
if (import.meta.env.DEV) {
  (window as any).apiTester = apiTester
}
