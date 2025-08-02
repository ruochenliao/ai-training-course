<template>
  <div class="settings-page">
    <div class="page-header">
      <h2>系统设置</h2>
      <p>配置系统参数和偏好设置</p>
    </div>
    
    <el-card>
      <div class="coming-soon">
        <el-icon size="80" color="#909399">
          <Setting />
        </el-icon>
        <h3>系统设置功能</h3>
        <p>此功能正在开发中，敬请期待...</p>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { Setting } from '@element-plus/icons-vue'
</script>

<style lang="scss" scoped>
.settings-page {
  padding: 24px;
}

.page-header {
  margin-bottom: 24px;
  
  h2 {
    font-size: 24px;
    font-weight: 600;
    color: #303133;
    margin-bottom: 8px;
  }
  
  p {
    color: #606266;
    font-size: 14px;
  }
}

.coming-soon {
  text-align: center;
  padding: 80px 20px;
  
  h3 {
    margin: 20px 0 10px;
    color: #303133;
  }
  
  p {
    color: #909399;
  }
}
</style>
