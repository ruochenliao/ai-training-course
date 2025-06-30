// 前后端API连接测试脚本
import axios from 'axios'

const API_BASE_URL = 'http://localhost:8000/api/v1'

// 测试配置
const testConfig = {
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
}

// 测试项目
const tests = [
  {
    name: '系统健康检查',
    method: 'GET',
    url: '/system/health',
    auth: false
  },
  {
    name: '系统信息',
    method: 'GET', 
    url: '/system/info',
    auth: false
  },
  {
    name: '用户登录',
    method: 'POST',
    url: '/auth/login/json',
    auth: false,
    data: {
      username: 'admin',
      password: 'admin123'
    }
  }
]

// 执行测试
async function runTests() {
  console.log('🚀 开始前后端API连接测试...\n')
  
  let token = null
  let successCount = 0
  let totalCount = tests.length

  for (const test of tests) {
    try {
      console.log(`📡 测试: ${test.name}`)
      
      const config = {
        method: test.method.toLowerCase(),
        url: `${API_BASE_URL}${test.url}`,
        ...testConfig
      }

      // 添加认证头
      if (test.auth && token) {
        config.headers.Authorization = `Bearer ${token}`
      }

      // 添加请求数据
      if (test.data) {
        config.data = test.data
      }

      const startTime = Date.now()
      const response = await axios(config)
      const responseTime = Date.now() - startTime

      console.log(`   ✅ 成功 (${response.status}) - ${responseTime}ms`)
      
      // 如果是登录接口，保存token
      if (test.url === '/auth/login/json' && response.data?.access_token) {
        token = response.data.access_token
        console.log(`   🔑 获取到访问令牌`)
      }

      successCount++
      
    } catch (error) {
      console.log(`   ❌ 失败: ${error.response?.status || 'Network Error'} - ${error.response?.data?.message || error.message}`)
    }
    
    console.log('')
  }

  // 如果有token，测试需要认证的接口
  if (token) {
    const authTests = [
      {
        name: '获取当前用户信息',
        method: 'GET',
        url: '/users/me'
      },
      {
        name: '获取知识库列表',
        method: 'GET',
        url: '/knowledge-bases?page=1&size=5'
      },
      {
        name: '获取文档列表',
        method: 'GET',
        url: '/documents?page=1&size=5'
      }
    ]

    console.log('🔐 测试需要认证的接口...\n')
    
    for (const test of authTests) {
      try {
        console.log(`📡 测试: ${test.name}`)
        
        const config = {
          method: test.method.toLowerCase(),
          url: `${API_BASE_URL}${test.url}`,
          ...testConfig,
          headers: {
            ...testConfig.headers,
            Authorization: `Bearer ${token}`
          }
        }

        const startTime = Date.now()
        const response = await axios(config)
        const responseTime = Date.now() - startTime

        console.log(`   ✅ 成功 (${response.status}) - ${responseTime}ms`)
        successCount++
        totalCount++
        
      } catch (error) {
        console.log(`   ❌ 失败: ${error.response?.status || 'Network Error'} - ${error.response?.data?.message || error.message}`)
        totalCount++
      }
      
      console.log('')
    }
  }

  // 输出测试结果
  console.log('📊 测试结果汇总:')
  console.log(`   总测试数: ${totalCount}`)
  console.log(`   成功: ${successCount}`)
  console.log(`   失败: ${totalCount - successCount}`)
  console.log(`   成功率: ${((successCount / totalCount) * 100).toFixed(1)}%`)
  
  if (successCount === totalCount) {
    console.log('\n🎉 所有测试通过！前后端连接正常。')
  } else {
    console.log('\n⚠️  部分测试失败，请检查后端服务状态。')
  }
}

// 运行测试
runTests().catch(error => {
  console.error('❌ 测试执行失败:', error.message)
  process.exit(1)
})
