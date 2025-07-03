<template>
  <div class="api-test-container">
    <el-card class="test-card">
      <template #header>
        <div class="card-header">
          <h2>🧪 前后端API集成测试</h2>
          <el-button 
            type="primary" 
            @click="runTests"
            :loading="testing"
            :disabled="testing"
          >
            {{ testing ? '测试中...' : '开始测试' }}
          </el-button>
        </div>
      </template>

      <div class="test-content">
        <!-- 测试进度 -->
        <div v-if="testing" class="test-progress">
          <el-progress 
            :percentage="progress" 
            :status="progress === 100 ? 'success' : undefined"
          />
          <p class="progress-text">{{ currentTest }}</p>
        </div>

        <!-- 测试结果统计 -->
        <div v-if="testResults" class="test-summary">
          <el-row :gutter="20">
            <el-col :span="6">
              <el-statistic title="总测试数" :value="testResults.total" />
            </el-col>
            <el-col :span="6">
              <el-statistic 
                title="成功" 
                :value="testResults.success" 
                value-style="color: #67C23A"
              />
            </el-col>
            <el-col :span="6">
              <el-statistic 
                title="失败" 
                :value="testResults.failed" 
                value-style="color: #F56C6C"
              />
            </el-col>
            <el-col :span="6">
              <el-statistic 
                title="成功率" 
                :value="testResults.successRate" 
                suffix="%" 
                :precision="1"
                :value-style="testResults.successRate === 100 ? 'color: #67C23A' : 'color: #E6A23C'"
              />
            </el-col>
          </el-row>
        </div>

        <!-- 详细测试结果 -->
        <div v-if="testResults && testResults.results.length > 0" class="test-details">
          <h3>详细测试结果</h3>
          <el-table :data="testResults.results" style="width: 100%">
            <el-table-column prop="name" label="测试项" width="200" />
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.success ? 'success' : 'danger'">
                  {{ row.success ? '成功' : '失败' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="message" label="结果信息" />
            <el-table-column label="操作" width="120">
              <template #default="{ row }">
                <el-button 
                  v-if="row.data" 
                  size="small" 
                  @click="showDetails(row)"
                >
                  查看详情
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <!-- 快速API测试 -->
        <div class="quick-test">
          <h3>快速API测试</h3>
          <el-row :gutter="20">
            <el-col :span="8">
              <el-button @click="testLogin" :loading="quickTesting.login">
                测试登录
              </el-button>
            </el-col>
            <el-col :span="8">
              <el-button @click="testUserList" :loading="quickTesting.userList">
                测试用户列表
              </el-button>
            </el-col>
            <el-col :span="8">
              <el-button @click="testDepartmentTree" :loading="quickTesting.departmentTree">
                测试部门树
              </el-button>
            </el-col>
          </el-row>
        </div>
      </div>
    </el-card>

    <!-- 详情对话框 -->
    <el-dialog v-model="detailDialogVisible" title="测试详情" width="60%">
      <pre class="detail-content">{{ JSON.stringify(selectedDetail, null, 2) }}</pre>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { apiTester } from '@/utils/api-test'
import * as authApi from '@/api/auth'
import * as userApi from '@/api/user'
import * as departmentApi from '@/api/department'

// 响应式数据
const testing = ref(false)
const progress = ref(0)
const currentTest = ref('')
const testResults = ref<any>(null)
const detailDialogVisible = ref(false)
const selectedDetail = ref<any>(null)

const quickTesting = reactive({
  login: false,
  userList: false,
  departmentTree: false
})

// 运行完整测试
const runTests = async () => {
  testing.value = true
  progress.value = 0
  currentTest.value = '准备开始测试...'
  
  try {
    // 模拟测试进度
    const testSteps = [
      '测试认证模块...',
      '测试用户管理模块...',
      '测试角色管理模块...',
      '测试权限管理模块...',
      '测试菜单管理模块...',
      '测试部门管理模块...',
      '生成测试报告...'
    ]
    
    for (let i = 0; i < testSteps.length; i++) {
      currentTest.value = testSteps[i]
      progress.value = Math.round(((i + 1) / testSteps.length) * 100)
      await new Promise(resolve => setTimeout(resolve, 500))
    }
    
    // 运行实际测试
    const results = await apiTester.runAllTests()
    testResults.value = results
    
  } catch (error: any) {
    ElMessage.error('测试过程中发生错误: ' + error.message)
  } finally {
    testing.value = false
    currentTest.value = '测试完成'
  }
}

// 显示详情
const showDetails = (row: any) => {
  selectedDetail.value = row.data
  detailDialogVisible.value = true
}

// 快速测试方法
const testLogin = async () => {
  quickTesting.login = true
  try {
    const result = await authApi.login({
      username: 'admin',
      password: 'admin123'
    })
    ElMessage.success('登录测试成功')
    console.log('登录结果:', result)
  } catch (error: any) {
    ElMessage.error('登录测试失败: ' + error.message)
  } finally {
    quickTesting.login = false
  }
}

const testUserList = async () => {
  quickTesting.userList = true
  try {
    const result = await userApi.getUserList({
      page: 1,
      page_size: 10
    })
    ElMessage.success('用户列表测试成功')
    console.log('用户列表结果:', result)
  } catch (error: any) {
    ElMessage.error('用户列表测试失败: ' + error.message)
  } finally {
    quickTesting.userList = false
  }
}

const testDepartmentTree = async () => {
  quickTesting.departmentTree = true
  try {
    const result = await departmentApi.getDepartmentTree()
    ElMessage.success('部门树测试成功')
    console.log('部门树结果:', result)
  } catch (error: any) {
    ElMessage.error('部门树测试失败: ' + error.message)
  } finally {
    quickTesting.departmentTree = false
  }
}
</script>

<style scoped lang="scss">
.api-test-container {
  padding: 20px;
  
  .test-card {
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      
      h2 {
        margin: 0;
        color: #303133;
      }
    }
  }
  
  .test-content {
    .test-progress {
      margin-bottom: 30px;
      
      .progress-text {
        margin-top: 10px;
        text-align: center;
        color: #606266;
      }
    }
    
    .test-summary {
      margin-bottom: 30px;
      padding: 20px;
      background-color: #f8f9fa;
      border-radius: 8px;
    }
    
    .test-details {
      margin-bottom: 30px;
      
      h3 {
        margin-bottom: 15px;
        color: #303133;
      }
    }
    
    .quick-test {
      padding: 20px;
      background-color: #f0f9ff;
      border-radius: 8px;
      
      h3 {
        margin-bottom: 15px;
        color: #303133;
      }
    }
  }
  
  .detail-content {
    background-color: #f5f5f5;
    padding: 15px;
    border-radius: 4px;
    font-family: 'Courier New', monospace;
    font-size: 12px;
    line-height: 1.4;
    max-height: 400px;
    overflow-y: auto;
  }
}
</style>
