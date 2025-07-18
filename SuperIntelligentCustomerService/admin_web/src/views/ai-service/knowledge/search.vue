<template>
  <div class="knowledge-search">
    <n-card title="知识库搜索" :bordered="false" size="small" class="rounded-16px shadow-sm">
      <!-- 搜索区域 -->
      <n-space vertical size="large">
        <!-- 搜索输入 -->
        <n-space vertical>
          <n-input
            v-model:value="searchQuery"
            type="textarea"
            placeholder="请输入要搜索的内容..."
            :rows="3"
            clearable
            @keyup.ctrl.enter="handleSearch"
          >
            <template #suffix>
              <n-button
                type="primary"
                :loading="searching"
                @click="handleSearch"
                :disabled="!searchQuery.trim()"
              >
                <icon-ic-round-search class="mr-4px text-16px" />
                搜索
              </n-button>
            </template>
          </n-input>
          
          <!-- 搜索选项 -->
          <n-space>
            <n-select
              v-model:value="selectedKnowledgeBases"
              multiple
              placeholder="选择知识库（不选则搜索全部）"
              :options="knowledgeBaseOptions"
              clearable
              class="w-300px"
            />
            <n-input-number
              v-model:value="searchLimit"
              placeholder="结果数量"
              :min="1"
              :max="50"
              class="w-120px"
            />
            <n-input-number
              v-model:value="scoreThreshold"
              placeholder="相似度阈值"
              :min="0"
              :max="1"
              :step="0.1"
              class="w-140px"
            />
          </n-space>
        </n-space>

        <!-- 搜索结果 -->
        <div v-if="searchResults.length > 0 || hasSearched">
          <n-divider>
            搜索结果 ({{ searchResults.length }} 条，耗时 {{ searchTook.toFixed(3) }}s)
          </n-divider>
          
          <n-empty v-if="searchResults.length === 0 && hasSearched" description="未找到相关内容">
            <template #extra>
              <n-button size="small" @click="handleSearch">
                重新搜索
              </n-button>
            </template>
          </n-empty>
          
          <n-space v-else vertical size="medium">
            <n-card
              v-for="(result, index) in searchResults"
              :key="index"
              size="small"
              hoverable
              class="search-result-card"
            >
              <template #header>
                <n-space justify="space-between" align="center">
                  <n-space align="center">
                    <n-tag type="info" size="small">
                      {{ result.knowledge_base_name }}
                    </n-tag>
                    <n-text depth="3">{{ result.file_name }}</n-text>
                  </n-space>
                  <n-space align="center">
                    <n-tag
                      :type="getScoreType(result.score)"
                      size="small"
                    >
                      相似度: {{ (result.score * 100).toFixed(1) }}%
                    </n-tag>
                    <n-text depth="3" class="text-12px">
                      块 #{{ result.chunk_index + 1 }}
                    </n-text>
                  </n-space>
                </n-space>
              </template>
              
              <div class="search-result-content">
                <n-text>{{ result.content }}</n-text>
              </div>
              
              <template #footer>
                <n-space justify="end">
                  <n-button size="small" @click="viewFileDetail(result)">
                    查看文件
                  </n-button>
                  <n-button size="small" type="primary" @click="copyContent(result.content)">
                    复制内容
                  </n-button>
                </n-space>
              </template>
            </n-card>
          </n-space>
        </div>

        <!-- 搜索统计 -->
        <n-card title="搜索统计" size="small" v-if="searchStats">
          <n-descriptions :column="3" size="small">
            <n-descriptions-item label="可访问知识库">
              {{ searchStats.accessible_knowledge_bases }}
            </n-descriptions-item>
            <n-descriptions-item label="拥有的知识库">
              {{ searchStats.owned_knowledge_bases }}
            </n-descriptions-item>
            <n-descriptions-item label="公开知识库">
              {{ searchStats.public_knowledge_bases }}
            </n-descriptions-item>
            <n-descriptions-item label="总文件数">
              {{ searchStats.total_files }}
            </n-descriptions-item>
            <n-descriptions-item label="拥有的文件">
              {{ searchStats.owned_files }}
            </n-descriptions-item>
            <n-descriptions-item label="公开文件">
              {{ searchStats.public_files }}
            </n-descriptions-item>
          </n-descriptions>
        </n-card>
      </n-space>
    </n-card>

    <!-- 相似内容搜索弹窗 -->
    <n-modal
      v-model:show="similarModalVisible"
      title="相似内容搜索"
      preset="card"
      class="w-800px"
    >
      <n-space vertical>
        <n-input
          v-model:value="similarContent"
          type="textarea"
          placeholder="请输入参考内容..."
          :rows="4"
        />
        <n-space>
          <n-select
            v-model:value="similarKnowledgeBaseId"
            placeholder="选择知识库"
            :options="knowledgeBaseOptions"
            class="w-200px"
          />
          <n-input-number
            v-model:value="similarLimit"
            placeholder="结果数量"
            :min="1"
            :max="20"
            class="w-120px"
          />
        </n-space>
      </n-space>

      <template #footer>
        <n-space justify="end">
          <n-button @click="similarModalVisible = false">取消</n-button>
          <n-button
            type="primary"
            :loading="searchingSimilar"
            @click="handleSimilarSearch"
            :disabled="!similarContent.trim() || !similarKnowledgeBaseId"
          >
            搜索相似内容
          </n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useMessage } from 'naive-ui'
import api from '@/api'

defineOptions({
  name: 'KnowledgeSearch'
})

interface SearchResult {
  content: string
  score: number
  file_id: number
  file_name: string
  knowledge_base_id: number
  knowledge_base_name: string
  chunk_index: number
  metadata: Record<string, any>
}

interface SearchStats {
  accessible_knowledge_bases: number
  owned_knowledge_bases: number
  public_knowledge_bases: number
  total_files: number
  owned_files: number
  public_files: number
}

const message = useMessage()

// 搜索相关
const searchQuery = ref('')
const selectedKnowledgeBases = ref<number[]>([])
const searchLimit = ref(10)
const scoreThreshold = ref(0.3)
const searching = ref(false)
const hasSearched = ref(false)
const searchResults = ref<SearchResult[]>([])
const searchTook = ref(0)

// 知识库选项
const knowledgeBaseOptions = ref([])

// 搜索统计
const searchStats = ref<SearchStats | null>(null)

// 相似内容搜索
const similarModalVisible = ref(false)
const similarContent = ref('')
const similarKnowledgeBaseId = ref<number | null>(null)
const similarLimit = ref(5)
const searchingSimilar = ref(false)

// 方法
const handleSearch = async () => {
  if (!searchQuery.value.trim()) {
    message.warning('请输入搜索内容')
    return
  }

  searching.value = true
  hasSearched.value = true

  try {
    const params = {
      query: searchQuery.value,
      knowledge_base_ids: selectedKnowledgeBases.value.length > 0 ? selectedKnowledgeBases.value : undefined,
      limit: searchLimit.value,
      score_threshold: scoreThreshold.value
    }

    const response = await api.searchKnowledge(params)
    
    if (response.success) {
      searchResults.value = response.data.results
      searchTook.value = response.data.took
      message.success(`搜索完成，找到 ${response.data.results.length} 条结果`)
    } else {
      message.error(response.msg || '搜索失败')
    }
  } catch (error) {
    console.error('搜索失败:', error)
    message.error('搜索失败，请重试')
  } finally {
    searching.value = false
  }
}

const handleSimilarSearch = async () => {
  searchingSimilar.value = true

  try {
    const response = await api.searchSimilarContent({
      content: similarContent.value,
      knowledge_base_id: similarKnowledgeBaseId.value,
      limit: similarLimit.value
    })

    if (response.success) {
      // 将相似内容结果添加到主搜索结果中
      const similarResults = response.data.similar_contents.map(item => ({
        content: item.content,
        score: item.score,
        file_id: item.file_id,
        file_name: `相似内容 - 文件${item.file_id}`,
        knowledge_base_id: response.data.knowledge_base_id,
        knowledge_base_name: response.data.knowledge_base_name,
        chunk_index: item.chunk_index,
        metadata: item.metadata
      }))

      searchResults.value = similarResults
      hasSearched.value = true
      similarModalVisible.value = false
      message.success(`找到 ${similarResults.length} 条相似内容`)
    } else {
      message.error(response.msg || '相似内容搜索失败')
    }
  } catch (error) {
    console.error('相似内容搜索失败:', error)
    message.error('相似内容搜索失败，请重试')
  } finally {
    searchingSimilar.value = false
  }
}

const getScoreType = (score: number) => {
  if (score >= 0.8) return 'success'
  if (score >= 0.6) return 'warning'
  return 'default'
}

const viewFileDetail = (result: SearchResult) => {
  // 跳转到文件详情页面
  console.log('查看文件详情:', result)
  message.info('文件详情功能开发中...')
}

const copyContent = async (content: string) => {
  try {
    await navigator.clipboard.writeText(content)
    message.success('内容已复制到剪贴板')
  } catch (error) {
    console.error('复制失败:', error)
    message.error('复制失败')
  }
}

// 加载知识库列表
const loadKnowledgeBases = async () => {
  try {
    const response = await api.getSearchableKnowledgeBases()
    if (response.success) {
      const options = []
      
      // 添加拥有的知识库
      response.data.owned.forEach(kb => {
        options.push({
          label: `${kb.name} (我的)`,
          value: kb.id
        })
      })
      
      // 添加公开的知识库
      response.data.public.forEach(kb => {
        options.push({
          label: `${kb.name} (公开)`,
          value: kb.id
        })
      })
      
      knowledgeBaseOptions.value = options
    }
  } catch (error) {
    console.error('加载知识库列表失败:', error)
  }
}

// 加载搜索统计
const loadSearchStats = async () => {
  try {
    const response = await api.getSearchStats()
    if (response.success) {
      searchStats.value = response.data
    }
  } catch (error) {
    console.error('加载搜索统计失败:', error)
  }
}

// 初始化
onMounted(() => {
  loadKnowledgeBases()
  loadSearchStats()
})
</script>

<style scoped>
.knowledge-search {
  padding: 16px;
}

.search-result-card {
  border-left: 4px solid var(--primary-color);
}

.search-result-content {
  max-height: 200px;
  overflow-y: auto;
  line-height: 1.6;
  white-space: pre-wrap;
}
</style>
