<template>
  <n-drawer
    :show="visible"
    @update:show="$emit('update:visible', $event)"
    :width="600"
    placement="right"
    :mask-closable="false"
  >
    <n-drawer-content title="知识库详情" closable>
      <n-spin :show="loading">
        <div v-if="knowledgeBase" class="detail-container">
          <!-- 基本信息 -->
          <n-card title="基本信息" :bordered="false" class="detail-section">
            <n-descriptions :column="1" label-placement="left">
              <n-descriptions-item label="名称">
                <n-text strong>{{ knowledgeBase.name }}</n-text>
              </n-descriptions-item>
              <n-descriptions-item label="类型">
                <n-tag :type="getTypeColor(knowledgeBase.knowledge_type)" size="small">
                  {{ getTypeLabel(knowledgeBase.knowledge_type) }}
                </n-tag>
              </n-descriptions-item>
              <n-descriptions-item label="访问权限">
                <n-tag :type="knowledgeBase.is_public ? 'success' : 'info'" size="small">
                  {{ knowledgeBase.is_public ? '公开' : '私有' }}
                </n-tag>
              </n-descriptions-item>
              <n-descriptions-item label="描述">
                <n-text depth="3">
                  {{ knowledgeBase.description || '暂无描述' }}
                </n-text>
              </n-descriptions-item>
              <n-descriptions-item label="创建时间">
                {{ formatDate(knowledgeBase.created_at) }}
              </n-descriptions-item>
              <n-descriptions-item label="更新时间">
                {{ formatDate(knowledgeBase.updated_at) }}
              </n-descriptions-item>
            </n-descriptions>
          </n-card>

          <!-- 统计信息 -->
          <n-card title="统计信息" :bordered="false" class="detail-section">
            <n-grid :cols="2" :x-gap="16" :y-gap="16">
              <n-grid-item>
                <n-statistic label="文件数量" :value="knowledgeBase.file_count || 0">
                  <template #prefix>
                    <n-icon color="#2080f0" :component="renderIcon('material-symbols:description')" />
                  </template>
                </n-statistic>
              </n-grid-item>
              <n-grid-item>
                <n-statistic label="总大小" :value="formatFileSize(knowledgeBase.total_size || 0)">
                  <template #prefix>
                    <n-icon color="#18a058" :component="renderIcon('material-symbols:storage')" />
                  </template>
                </n-statistic>
              </n-grid-item>
            </n-grid>

            <!-- 文件状态统计 -->
            <div v-if="knowledgeBase.status_stats" class="status-stats">
              <n-divider>文件处理状态</n-divider>
              <n-grid :cols="2" :x-gap="16" :y-gap="8">
                <n-grid-item v-for="(count, status) in knowledgeBase.status_stats" :key="status">
                  <div class="status-item">
                    <n-tag :type="getStatusColor(status)" size="small">
                      {{ getStatusLabel(status) }}
                    </n-tag>
                    <span class="status-count">{{ count }}</span>
                  </div>
                </n-grid-item>
              </n-grid>
            </div>
          </n-card>

          <!-- 配置信息 -->
          <n-card title="配置信息" :bordered="false" class="detail-section">
            <n-descriptions :column="1" label-placement="left">
              <n-descriptions-item label="最大文件大小">
                {{ formatFileSize(knowledgeBase.max_file_size || 0) }}
              </n-descriptions-item>
              <n-descriptions-item label="允许文件类型">
                <n-space>
                  <n-tag
                    v-for="type in knowledgeBase.allowed_file_types"
                    :key="type"
                    size="small"
                    type="info"
                  >
                    {{ type.toUpperCase() }}
                  </n-tag>
                </n-space>
              </n-descriptions-item>
              <n-descriptions-item label="嵌入模型">
                <n-text code>{{ knowledgeBase.embedding_model || 'BAAI/bge-small-zh-v1.5' }}</n-text>
              </n-descriptions-item>
              <n-descriptions-item label="分块大小">
                {{ knowledgeBase.chunk_size || 1024 }} 字符
              </n-descriptions-item>
              <n-descriptions-item label="分块重叠">
                {{ knowledgeBase.chunk_overlap || 100 }} 字符
              </n-descriptions-item>
            </n-descriptions>
          </n-card>


        </div>

        <n-empty v-else description="加载失败" />
      </n-spin>
    </n-drawer-content>
  </n-drawer>
</template>

<script setup>
import {ref, watch} from 'vue'
import {
  NCard,
  NDescriptions,
  NDescriptionsItem,
  NDivider,
  NDrawer,
  NDrawerContent,
  NEmpty,
  NGrid,
  NGridItem,
  NIcon,
  NSpace,
  NSpin,
  NStatistic,
  NTag,
  NText,
  useDialog,
  useMessage
} from 'naive-ui'
import {renderIcon} from '@/utils'
import api from '@/api'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  knowledgeBaseId: {
    type: [String, Number],
    default: null
  }
})

const emit = defineEmits(['update:visible', 'refresh'])

const message = useMessage()
const dialog = useDialog()

const loading = ref(false)
const knowledgeBase = ref(null)

// 监听visible和knowledgeBaseId变化
watch([() => props.visible, () => props.knowledgeBaseId], ([visible, id]) => {
  if (visible && id) {
    loadKnowledgeBase()
  }
})

// 加载知识库详情
const loadKnowledgeBase = async () => {
  if (!props.knowledgeBaseId) return

  loading.value = true
  try {
    const response = await api.getKnowledgeBaseById(props.knowledgeBaseId)
    if (response.code === 200) {
      knowledgeBase.value = response.data
    } else {
      message.error(response.msg || '加载失败')
    }
  } catch (error) {
    message.error('加载知识库详情失败')
    console.error('Load knowledge base error:', error)
  } finally {
    loading.value = false
  }
}





// 工具函数
const getTypeLabel = (type) => {
  const typeMap = {
    'general': '通用',
    'technical': '技术文档',
    'faq': 'FAQ',
    'policy': '政策制度',
    'product': '产品说明'
  }
  return typeMap[type] || type
}

const getTypeColor = (type) => {
  const colorMap = {
    'general': 'default',
    'technical': 'info',
    'faq': 'success',
    'policy': 'warning',
    'product': 'error'
  }
  return colorMap[type] || 'default'
}

const getStatusLabel = (status) => {
  const statusMap = {
    'pending': '待处理',
    'processing': '处理中',
    'completed': '已完成',
    'failed': '失败'
  }
  return statusMap[status] || status
}

const getStatusColor = (status) => {
  const colorMap = {
    'pending': 'default',
    'processing': 'info',
    'completed': 'success',
    'failed': 'error'
  }
  return colorMap[status] || 'default'
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString('zh-CN')
}
</script>

<style scoped>
.detail-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.detail-section {
  margin-bottom: 16px;
}

.status-stats {
  margin-top: 16px;
}

.status-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
}

.status-count {
  font-weight: 600;
  color: var(--n-text-color-base);
}

.action-buttons {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid var(--n-border-color);
}
</style>
