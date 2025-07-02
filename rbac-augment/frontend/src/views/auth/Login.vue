<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-header">
        <h1 class="login-title">RBAC管理系统</h1>
        <p class="login-subtitle">基于Vue3 + FastAPI的权限管理系统</p>
      </div>

      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        class="login-form"
        @keyup.enter="handleLogin"
      >
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="请输入用户名"
            size="large"
            prefix-icon="User"
            clearable
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            size="large"
            prefix-icon="Lock"
            show-password
            clearable
          />
        </el-form-item>

        <el-form-item>
          <div class="login-options">
            <el-checkbox v-model="loginForm.remember_me">
              记住我
            </el-checkbox>
          </div>
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            class="login-button"
            :loading="loading"
            @click="handleLogin"
          >
            {{ loading ? '登录中...' : '登录' }}
          </el-button>
        </el-form-item>
      </el-form>

      <div class="login-footer">
        <p>演示账户：</p>
        <p>超级管理员：admin / admin123</p>
        <p>系统管理员：manager / manager123</p>
        <p>普通用户：user / user123</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import type { LoginRequest } from '@/types'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

// 表单引用
const loginFormRef = ref<FormInstance>()

// 加载状态
const loading = ref(false)

// 登录表单
const loginForm = reactive<LoginRequest>({
  username: '',
  password: '',
  remember_me: false
})

// 表单验证规则
const loginRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度在 3 到 50 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 50, message: '密码长度在 6 到 50 个字符', trigger: 'blur' }
  ]
}

/**
 * 处理登录
 */
const handleLogin = async () => {
  if (!loginFormRef.value) return

  try {
    // 验证表单
    await loginFormRef.value.validate()
    
    loading.value = true
    
    // 执行登录
    await authStore.login(loginForm)
    
    // 获取重定向路径
    const redirect = (route.query.redirect as string) || '/'
    
    // 跳转到目标页面
    await router.push(redirect)
    
    ElMessage.success('登录成功')
  } catch (error) {
    console.error('Login error:', error)
  } finally {
    loading.value = false
  }
}

/**
 * 快速登录（演示用）
 */
const quickLogin = (username: string, password: string) => {
  loginForm.username = username
  loginForm.password = password
  handleLogin()
}

// 暴露方法供模板使用
defineExpose({
  quickLogin
})
</script>

<style lang="scss" scoped>
.login-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  position: relative;

  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="50" cy="50" r="1" fill="rgba(255,255,255,0.1)"/></pattern></defs><rect width="100" height="100" fill="url(%23grain)"/></svg>');
    opacity: 0.3;
  }

  .login-container {
    position: relative;
    z-index: 1;
    width: 420px;
    padding: 40px;
    background-color: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    border-radius: 12px;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);

    .login-header {
      text-align: center;
      margin-bottom: 32px;

      .login-title {
        font-size: 28px;
        font-weight: 600;
        color: #303133;
        margin-bottom: 8px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
      }

      .login-subtitle {
        color: #909399;
        font-size: 14px;
        line-height: 1.5;
      }
    }

    .login-form {
      .el-form-item {
        margin-bottom: 24px;
      }

      .login-options {
        display: flex;
        justify-content: space-between;
        align-items: center;
        width: 100%;
      }

      .login-button {
        width: 100%;
        height: 44px;
        font-size: 16px;
        font-weight: 500;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
        border-radius: 6px;
        transition: all 0.3s ease;

        &:hover {
          transform: translateY(-1px);
          box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
        }

        &:active {
          transform: translateY(0);
        }
      }
    }

    .login-footer {
      text-align: center;
      margin-top: 24px;
      padding-top: 24px;
      border-top: 1px solid #ebeef5;
      color: #909399;
      font-size: 12px;
      line-height: 1.6;

      p {
        margin: 4px 0;
      }
    }
  }
}

// 响应式设计
@media (max-width: 480px) {
  .login-page {
    padding: 20px;

    .login-container {
      width: 100%;
      padding: 24px;
    }
  }
}

// 暗色主题
.dark {
  .login-page {
    .login-container {
      background-color: rgba(45, 45, 45, 0.95);
      color: #e5eaf3;

      .login-header {
        .login-title {
          color: #e5eaf3;
        }
      }

      .login-footer {
        border-top-color: #4c4d4f;
        color: #a3a6ad;
      }
    }
  }
}
</style>
