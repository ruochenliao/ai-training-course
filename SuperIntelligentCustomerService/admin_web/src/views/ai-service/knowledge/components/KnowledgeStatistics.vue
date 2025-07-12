<template>
  <div class="statistics-container">
    <n-card title="知识库统计" :bordered="false">
      <template #header-extra>
        <n-button size="small" @click="refresh">
          <template #icon>
            <n-icon :component="renderIcon('material-symbols:refresh')" />
          </template>
          刷新
        </n-button>
      </template>

      <n-spin :show="loading">
        <div v-if="statistics" class="stats-grid">
          <!-- 总体统计 -->
          <div class="stat-section">
            <h4>总体统计</h4>
            <n-grid :cols="2" :x-gap="16" :y-gap="16">
              <n-grid-item>
                <n-statistic label="知识库总数" :value="statistics.total_knowledge_bases">
                  <template #prefix>
                    <n-icon color="#18a058" :component="renderIcon('material-symbols:library-books')" />
                  </template>
                </n-statistic>
              </n-grid-item>
              <n-grid-item>
                <n-statistic label="文件总数" :value="statistics.total_files">
                  <template #prefix>
                    <n-icon color="#2080f0" :component="renderIcon('material-symbols:description')" />
                  </template>
                </n-statistic>
              </n-grid-item>
            </n-grid>
          </div>

          <!-- 权限统计 -->
          <div class="stat-section">
            <h4>权限分布</h4>
            <n-grid :cols="2" :x-gap="16" :y-gap="16">
              <n-grid-item>
                <n-statistic label="公开知识库" :value="statistics.public_knowledge_bases">
                  <template #prefix>
                    <n-icon color="#f0a020" :component="renderIcon('material-symbols:public')" />
                  </template>
                </n-statistic>
              </n-grid-item>
              <n-grid-item>
                <n-statistic label="私有知识库" :value="statistics.private_knowledge_bases">
                  <template #prefix>
                    <n-icon color="#d03050" :component="renderIcon('material-symbols:lock')" />
                  </template>
                </n-statistic>
              </n-grid-item>
            </n-grid>
          </div>

          <!-- 存储统计 -->
          <div class="stat-section">
            <h4>存储使用</h4>
            <n-statistic label="总存储大小" :value="formatFileSize(statistics.total_size)">
              <template #prefix>
                <n-icon color="#7c3aed" :component="renderIcon('material-symbols:storage')" />
              </template>
            </n-statistic>
            
            <!-- 存储使用进度条 -->
            <div class="storage-progress">
              <n-progress
                type="line"
                :percentage="storagePercentage"
                :color="getStorageColor(storagePercentage)"
                :height="8"
                style="margin-top: 8px"
              />
              <div class="storage-info">
                <span>已使用: {{ formatFileSize(statistics.total_size) }}</span>
                <span>限制: {{ formatFileSize(storageLimit) }}</span>
              </div>
            </div>
          </div>

          <!-- 类型分布 -->
          <div class="stat-section" v-if="typeDistribution.length > 0">
            <h4>类型分布</h4>
            <div class="type-chart">
              <div v-for="type in typeDistribution" :key="type.name" class="type-item">
                <div class="type-info">
                  <span class="type-name">{{ type.label }}</span>
                  <span class="type-count">{{ type.count }}</span>
                </div>
                <n-progress
                  type="line"
                  :percentage="type.percentage"
                  :height="6"
                  :show-indicator="false"
                  style="margin-top: 4px"
                />
              </div>
            </div>
          </div>

          <!-- 最近活动 -->
          <div class="stat-section" v-if="recentActivity.length > 0">
            <h4>最近活动</h4>
            <n-timeline>
              <n-timeline-item
                v-for="activity in recentActivity"
                :key="activity.id"
                :type="getActivityType(activity.type)"
              >
                <template #header>
                  <span class="activity-title">{{ activity.title }}</span>
                </template>
                <div class="activity-content">
                  <div>{{ activity.description }}</div>
                  <div class="activity-time">{{ formatTime(activity.time) }}</div>
                </div>
              </n-timeline-item>
            </n-timeline>
          </div>
        </div>

        <n-empty v-else description="暂无统计数据" />
      </n-spin>
    </n-card>
  </div>
</template>

<script setup>
import {computed, onMounted, ref} from 'vue'
import {
  NButton,
  NCard,
  NEmpty,
  NGrid,
  NGridItem,
  NIcon,
  NProgress,
  NSpin,
  NStatistic,
  NTimeline,
  NTimelineItem,
  useMessage
} from 'naive-ui'
import {renderIcon} from '@/utils'
import api from '@/api'

const message = useMessage()
const loading = ref(false)
const statistics = ref(null)

// 存储限制 (1GB)
const storageLimit = 1024 * 1024 * 1024

// 计算属性
const storagePercentage = computed(() => {
  if (!statistics.value) return 0
  return Math.min((statistics.value.total_size / storageLimit) * 100, 100)
})

const typeDistribution = computed(() => {
  if (!statistics.value || !statistics.value.by_type) return []
  
  const total = statistics.value.total_knowledge_bases
  if (total === 0) return []

  const types = [
    { name: 'general', label: '通用', count: 0 },
    { name: 'technical', label: '技术文档', count: 0 },
    { name: 'faq', label: 'FAQ', count: 0 },
    { name: 'policy', label: '政策制度', count: 0 },
    { name: 'product', label: '产品说明', count: 0 }
  ]

  types.forEach(type => {
    type.count = statistics.value.by_type[type.name] || 0
    type.percentage = total > 0 ? (type.count / total) * 100 : 0
  })

  return types.filter(type => type.count > 0)
})

const recentActivity = ref([
  {
    id: 1,
    type: 'create',
    title: '创建知识库',
    description: '创建了新的技术文档知识库',
    time: new Date(Date.now() - 2 * 60 * 60 * 1000)
  },
  {
    id: 2,
    type: 'upload',
    title: '上传文件',
    description: '上传了3个PDF文件到产品说明知识库',
    time: new Date(Date.now() - 5 * 60 * 60 * 1000)
  },
  {
    id: 3,
    type: 'update',
    title: '更新知识库',
    description: '修改了FAQ知识库的配置',
    time: new Date(Date.now() - 24 * 60 * 60 * 1000)
  }
])

// 方法
const loadStatistics = async () => {
  loading.value = true
  try {
    // 分批获取数据，避免超过page_size限制
    let allItems = []
    let page = 1
    const pageSize = 100
    let hasMore = true

    while (hasMore) {
      const response = await api.getKnowledgeBaseList({ page, page_size: pageSize })
      if (response.code === 200) {
        const items = response.data || []
        allItems = allItems.concat(items)

        // 检查是否还有更多数据
        hasMore = items.length === pageSize
        page++
      } else {
        hasMore = false
      }
    }

    // 处理统计数据
    const stats = {
      total_knowledge_bases: allItems.length,
      public_knowledge_bases: allItems.filter(item => item.is_public).length,
      private_knowledge_bases: allItems.filter(item => !item.is_public).length,
      total_files: allItems.reduce((sum, item) => sum + (item.file_count || 0), 0),
      total_size: allItems.reduce((sum, item) => sum + (item.total_size || 0), 0),
      by_type: {}
    }

    // 按类型统计
    allItems.forEach(item => {
      const type = item.knowledge_type || 'general'
      stats.by_type[type] = (stats.by_type[type] || 0) + 1
    })

    statistics.value = stats
  } catch (error) {
    message.error('加载统计数据失败')
    console.error('Load statistics error:', error)
  } finally {
    loading.value = false
  }
}

const refresh = () => {
  loadStatistics()
}

const getStorageColor = (percentage) => {
  if (percentage < 60) return '#18a058'
  if (percentage < 80) return '#f0a020'
  return '#d03050'
}

const getActivityType = (type) => {
  const typeMap = {
    create: 'success',
    upload: 'info',
    update: 'warning',
    delete: 'error'
  }
  return typeMap[type] || 'default'
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

const formatTime = (time) => {
  const now = new Date()
  const diff = now - time
  const hours = Math.floor(diff / (1000 * 60 * 60))
  
  if (hours < 1) return '刚刚'
  if (hours < 24) return `${hours}小时前`
  const days = Math.floor(hours / 24)
  return `${days}天前`
}

onMounted(() => {
  loadStatistics()
})
</script>

<style scoped>
.statistics-container {
  height: 100%;
}

.stats-grid {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.stat-section {
  padding: 16px;
  border: 1px solid var(--n-border-color);
  border-radius: 8px;
  background-color: var(--n-card-color);
}

.stat-section h4 {
  margin: 0 0 16px 0;
  color: var(--n-text-color-base);
  font-weight: 600;
}

.storage-progress {
  margin-top: 12px;
}

.storage-info {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 12px;
  color: var(--n-text-color-disabled);
}

.type-chart {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.type-item {
  padding: 8px 0;
}

.type-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.type-name {
  font-weight: 500;
}

.type-count {
  color: var(--n-text-color-disabled);
  font-size: 14px;
}

.activity-title {
  font-weight: 500;
}

.activity-content {
  margin-top: 4px;
}

.activity-time {
  font-size: 12px;
  color: var(--n-text-color-disabled);
  margin-top: 4px;
}
</style>
