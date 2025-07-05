<template>
  <div class="error-page">
    <div class="error-content">
      <div class="error-illustration">
        <svg
          width="200"
          height="200"
          viewBox="0 0 200 200"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <!-- 403插图 -->
          <circle cx="100" cy="100" r="80" fill="#fff2f0" stroke="#ffccc7" stroke-width="2"/>
          <path
            d="M70 80 L130 80 M70 100 L130 100 M70 120 L130 120"
            stroke="#ff4d4f"
            stroke-width="3"
            stroke-linecap="round"
          />
          <circle cx="100" cy="100" r="90" fill="none" stroke="#ff4d4f" stroke-width="4"/>
          <path
            d="M75 75 L125 125 M125 75 L75 125"
            stroke="#ff4d4f"
            stroke-width="4"
            stroke-linecap="round"
          />
        </svg>
      </div>
      
      <div class="error-info">
        <h1 class="error-code">403</h1>
        <h2 class="error-message">权限不足</h2>
        <p class="error-description">
          抱歉，您没有权限访问此页面。
          <br>
          请联系管理员获取相应权限，或返回首页继续浏览。
        </p>
        
        <div class="error-actions">
          <el-button type="primary" @click="goHome">
            <el-icon><House /></el-icon>
            返回首页
          </el-button>
          <el-button @click="goBack">
            <el-icon><Back /></el-icon>
            返回上页
          </el-button>
          <el-button type="warning" @click="contactAdmin">
            <el-icon><Message /></el-icon>
            联系管理员
          </el-button>
        </div>
      </div>
    </div>
    
    <!-- 背景装饰 -->
    <div class="error-bg">
      <div class="floating-shape shape-1"></div>
      <div class="floating-shape shape-2"></div>
      <div class="floating-shape shape-3"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { House, Back, Message } from '@element-plus/icons-vue'

const router = useRouter()

/**
 * 返回首页
 */
const goHome = () => {
  router.push('/')
}

/**
 * 返回上一页
 */
const goBack = () => {
  if (window.history.length > 1) {
    router.go(-1)
  } else {
    router.push('/')
  }
}

/**
 * 联系管理员
 */
const contactAdmin = () => {
  ElMessage.info('请联系系统管理员获取权限')
}
</script>

<style lang="scss" scoped>
.error-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #ff6b6b 0%, #ffa726 100%);
  position: relative;
  overflow: hidden;

  .error-content {
    display: flex;
    align-items: center;
    gap: 60px;
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    border-radius: 20px;
    padding: 60px;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    z-index: 1;

    .error-illustration {
      flex-shrink: 0;
    }

    .error-info {
      text-align: center;

      .error-code {
        font-size: 120px;
        font-weight: 900;
        color: #ff4d4f;
        margin: 0;
        line-height: 1;
        background: linear-gradient(135deg, #ff6b6b 0%, #ffa726 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
      }

      .error-message {
        font-size: 32px;
        font-weight: 600;
        color: #303133;
        margin: 20px 0 16px;
      }

      .error-description {
        font-size: 16px;
        color: #606266;
        line-height: 1.6;
        margin-bottom: 40px;
        max-width: 400px;
      }

      .error-actions {
        display: flex;
        justify-content: center;
        gap: 16px;
        flex-wrap: wrap;

        .el-button {
          padding: 12px 24px;
          font-size: 16px;
          border-radius: 8px;
        }
      }
    }
  }

  .error-bg {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    pointer-events: none;

    .floating-shape {
      position: absolute;
      border-radius: 50%;
      background: rgba(255, 255, 255, 0.1);
      animation: float 6s ease-in-out infinite;

      &.shape-1 {
        width: 80px;
        height: 80px;
        top: 20%;
        left: 10%;
        animation-delay: 0s;
      }

      &.shape-2 {
        width: 120px;
        height: 120px;
        top: 60%;
        right: 15%;
        animation-delay: 2s;
      }

      &.shape-3 {
        width: 60px;
        height: 60px;
        bottom: 20%;
        left: 20%;
        animation-delay: 4s;
      }
    }
  }
}

@keyframes float {
  0%, 100% {
    transform: translateY(0px);
  }
  50% {
    transform: translateY(-20px);
  }
}

// 响应式设计
@media (max-width: 768px) {
  .error-page {
    padding: 20px;

    .error-content {
      flex-direction: column;
      gap: 40px;
      padding: 40px 30px;

      .error-info {
        .error-code {
          font-size: 80px;
        }

        .error-message {
          font-size: 24px;
        }

        .error-description {
          font-size: 14px;
        }

        .error-actions {
          flex-direction: column;

          .el-button {
            width: 100%;
          }
        }
      }
    }
  }
}

// 暗色主题
.dark {
  .error-page {
    .error-content {
      background: rgba(45, 45, 45, 0.95);
      color: #e5eaf3;

      .error-info {
        .error-message {
          color: #e5eaf3;
        }

        .error-description {
          color: #a3a6ad;
        }
      }
    }
  }
}
</style>
