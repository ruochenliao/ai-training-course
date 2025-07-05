<template>
  <PageContainer title="企业级功能演示" description="展示新增的表单验证、错误处理、性能优化等功能">
    <el-row :gutter="24">
      <!-- 表单验证演示 -->
      <el-col :span="12">
        <el-card header="表单验证演示" shadow="never">
          <EnhancedForm
            v-model="formData"
            :rules="formRules"
            :real-time-validate="true"
            @submit="handleFormSubmit"
          >
            <el-form-item label="用户名" prop="username">
              <el-input v-model="formData.username" placeholder="请输入用户名" />
            </el-form-item>
            
            <el-form-item label="邮箱" prop="email">
              <el-input v-model="formData.email" placeholder="请输入邮箱" />
            </el-form-item>
            
            <el-form-item label="手机号" prop="phone">
              <el-input v-model="formData.phone" placeholder="请输入手机号" />
            </el-form-item>
            
            <el-form-item label="密码" prop="password">
              <el-input 
                v-model="formData.password" 
                type="password" 
                placeholder="请输入密码"
                show-password
              />
            </el-form-item>
          </EnhancedForm>
        </el-card>
      </el-col>
      
      <!-- 加载状态演示 -->
      <el-col :span="12">
        <el-card header="加载状态演示" shadow="never">
          <div class="demo-section">
            <h4>加载类型选择</h4>
            <el-radio-group v-model="loadingType">
              <el-radio label="skeleton">骨架屏</el-radio>
              <el-radio label="spinner">旋转加载</el-radio>
              <el-radio label="progress">进度条</el-radio>
              <el-radio label="dots">点状加载</el-radio>
              <el-radio label="pulse">脉冲加载</el-radio>
            </el-radio-group>
            
            <div class="loading-demo">
              <LoadingState
                :type="loadingType"
                :text="loadingText"
                :progress="progress"
                :skeleton-rows="3"
                :show-avatar="true"
              />
            </div>
            
            <el-button @click="simulateLoading">模拟加载</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="24" style="margin-top: 24px;">
      <!-- 动画演示 -->
      <el-col :span="12">
        <el-card header="动画效果演示" shadow="never">
          <div class="demo-section">
            <h4>动画类型选择</h4>
            <el-radio-group v-model="animationType">
              <el-radio label="fade">淡入淡出</el-radio>
              <el-radio label="slide-up">向上滑动</el-radio>
              <el-radio label="slide-down">向下滑动</el-radio>
              <el-radio label="zoom">缩放</el-radio>
              <el-radio label="bounce">弹跳</el-radio>
            </el-radio-group>
            
            <div class="animation-demo">
              <AnimatedTransition :type="animationType">
                <div v-if="showAnimationDemo" class="demo-box">
                  <h3>动画演示内容</h3>
                  <p>这是一个动画演示框，展示不同的过渡效果。</p>
                </div>
              </AnimatedTransition>
            </div>
            
            <el-button @click="toggleAnimation">切换动画</el-button>
          </div>
        </el-card>
      </el-col>
      
      <!-- 错误处理演示 -->
      <el-col :span="12">
        <el-card header="错误处理演示" shadow="never">
          <div class="demo-section">
            <h4>错误类型选择</h4>
            <el-radio-group v-model="errorType">
              <el-radio label="network">网络错误</el-radio>
              <el-radio label="validation">验证错误</el-radio>
              <el-radio label="business">业务错误</el-radio>
              <el-radio label="system">系统错误</el-radio>
            </el-radio-group>
            
            <div class="error-demo">
              <el-button @click="simulateError" type="danger">模拟错误</el-button>
              <el-button @click="testRetry" type="warning">测试重试</el-button>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 性能监控演示 -->
    <el-row style="margin-top: 24px;">
      <el-col :span="24">
        <el-card header="性能监控演示" shadow="never">
          <div class="demo-section">
            <el-button @click="testPerformance">测试性能监控</el-button>
            <el-button @click="testCache">测试缓存</el-button>
            <el-button @click="clearCache">清除缓存</el-button>
            
            <div v-if="performanceResults.length > 0" class="performance-results">
              <h4>性能监控结果</h4>
              <el-table :data="performanceResults" style="width: 100%">
                <el-table-column prop="name" label="操作名称" />
                <el-table-column prop="duration" label="耗时(ms)" />
                <el-table-column prop="timestamp" label="时间戳" />
              </el-table>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </PageContainer>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import PageContainer from '@/components/common/PageContainer.vue'
import EnhancedForm from '@/components/common/EnhancedForm.vue'
import LoadingState from '@/components/common/LoadingState.vue'
import AnimatedTransition from '@/components/common/AnimatedTransition.vue'
import { commonRules } from '@/utils/validation'
import { 
  errorHandler, 
  NetworkError, 
  ValidationError, 
  BusinessError, 
  AppError, 
  ErrorType, 
  ErrorLevel 
} from '@/utils/errorHandler'
import { 
  performanceMonitor, 
  cacheManager, 
  loadingManager, 
  retry 
} from '@/utils/performance'

// 表单数据
const formData = reactive({
  username: '',
  email: '',
  phone: '',
  password: ''
})

// 表单验证规则
const formRules = {
  username: commonRules.username(),
  email: commonRules.email(),
  phone: commonRules.phone(false),
  password: commonRules.password()
}

// 加载状态演示
const loadingType = ref<'skeleton' | 'spinner' | 'progress' | 'dots' | 'pulse'>('skeleton')
const loadingText = ref('加载中...')
const progress = ref(0)

// 动画演示
const animationType = ref<'fade' | 'slide-up' | 'slide-down' | 'zoom' | 'bounce'>('fade')
const showAnimationDemo = ref(true)

// 错误处理演示
const errorType = ref<'network' | 'validation' | 'business' | 'system'>('network')

// 性能监控结果
const performanceResults = ref<Array<{ name: string; duration: number; timestamp: string }>>([])

/**
 * 处理表单提交
 */
const handleFormSubmit = async (data: any) => {
  console.log('表单提交数据:', data)
  ElMessage.success('表单验证通过，提交成功！')
}

/**
 * 模拟加载
 */
const simulateLoading = () => {
  if (loadingType.value === 'progress') {
    progress.value = 0
    const timer = setInterval(() => {
      progress.value += 10
      if (progress.value >= 100) {
        clearInterval(timer)
        ElMessage.success('加载完成！')
      }
    }, 200)
  } else {
    loadingManager.show('demo-loading')
    setTimeout(() => {
      loadingManager.hide('demo-loading')
      ElMessage.success('加载完成！')
    }, 2000)
  }
}

/**
 * 切换动画
 */
const toggleAnimation = () => {
  showAnimationDemo.value = !showAnimationDemo.value
}

/**
 * 模拟错误
 */
const simulateError = () => {
  let error: Error
  
  switch (errorType.value) {
    case 'network':
      error = new NetworkError('网络连接超时')
      break
    case 'validation':
      error = new ValidationError('表单验证失败', [
        { field: 'username', message: '用户名不能为空' },
        { field: 'email', message: '邮箱格式不正确' }
      ])
      break
    case 'business':
      error = new BusinessError('用户名已存在')
      break
    case 'system':
      error = new AppError('系统内部错误', ErrorType.SYSTEM, ErrorLevel.ERROR)
      break
    default:
      error = new Error('未知错误')
  }
  
  errorHandler.handleError(error)
}

/**
 * 测试重试机制
 */
const testRetry = async () => {
  try {
    await retry(async () => {
      // 模拟可能失败的操作
      if (Math.random() < 0.7) {
        throw new Error('模拟网络错误')
      }
      return '操作成功'
    }, 3, 1000)
    
    ElMessage.success('重试成功！')
  } catch (error) {
    ElMessage.error('重试失败，已达到最大重试次数')
  }
}

/**
 * 测试性能监控
 */
const testPerformance = async () => {
  const result = await performanceMonitor.monitor('demo-operation', async () => {
    // 模拟耗时操作
    await new Promise(resolve => setTimeout(resolve, Math.random() * 1000 + 500))
    return '操作完成'
  })
  
  const duration = performanceMonitor.getMeasure('demo-operation')
  if (duration) {
    performanceResults.value.unshift({
      name: '演示操作',
      duration: Math.round(duration),
      timestamp: new Date().toLocaleTimeString()
    })
  }
  
  ElMessage.success(`操作完成，耗时: ${Math.round(duration || 0)}ms`)
}

/**
 * 测试缓存
 */
const testCache = () => {
  const key = 'demo-data'
  const cachedData = cacheManager.get(key)
  
  if (cachedData) {
    ElMessage.info(`从缓存获取数据: ${cachedData}`)
  } else {
    const newData = `数据-${Date.now()}`
    cacheManager.set(key, newData, 10000) // 10秒缓存
    ElMessage.success(`数据已缓存: ${newData}`)
  }
}

/**
 * 清除缓存
 */
const clearCache = () => {
  cacheManager.clear()
  ElMessage.success('缓存已清除')
}
</script>

<style lang="scss" scoped>
.demo-section {
  margin-bottom: 24px;
  
  h4 {
    margin-bottom: 12px;
    color: var(--el-text-color-primary);
  }
}

.loading-demo {
  height: 200px;
  border: 1px dashed var(--el-border-color);
  border-radius: 4px;
  margin: 16px 0;
}

.animation-demo {
  height: 200px;
  border: 1px dashed var(--el-border-color);
  border-radius: 4px;
  margin: 16px 0;
  display: flex;
  align-items: center;
  justify-content: center;
  
  .demo-box {
    padding: 24px;
    background: var(--el-color-primary-light-9);
    border-radius: 8px;
    text-align: center;
    
    h3 {
      margin: 0 0 12px 0;
      color: var(--el-color-primary);
    }
    
    p {
      margin: 0;
      color: var(--el-text-color-regular);
    }
  }
}

.error-demo {
  margin: 16px 0;
  
  .el-button {
    margin-right: 12px;
  }
}

.performance-results {
  margin-top: 24px;
  
  h4 {
    margin-bottom: 16px;
  }
}
</style>
