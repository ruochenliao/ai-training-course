<template>
  <div class="analytics-page">
    <div class="page-header">
      <h2>数据分析</h2>
      <p>查看平台使用情况和数据统计</p>
    </div>
    
    <el-card>
      <div class="coming-soon">
        <el-icon size="80" color="#909399">
          <DataAnalysis />
        </el-icon>
        <h3>数据分析功能</h3>
        <p>此功能正在开发中，敬请期待...</p>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { DataAnalysis } from '@element-plus/icons-vue'
</script>

<style lang="scss" scoped>
.analytics-page {
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
