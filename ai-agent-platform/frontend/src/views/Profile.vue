<template>
  <div class="profile-page">
    <div class="page-header">
      <h2>个人资料</h2>
      <p>查看和编辑个人信息</p>
    </div>
    
    <el-card>
      <div class="coming-soon">
        <el-icon size="80" color="#909399">
          <User />
        </el-icon>
        <h3>个人资料功能</h3>
        <p>此功能正在开发中，敬请期待...</p>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { User } from '@element-plus/icons-vue'
</script>

<style lang="scss" scoped>
.profile-page {
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
