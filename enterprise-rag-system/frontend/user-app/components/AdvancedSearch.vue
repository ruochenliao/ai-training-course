<template>
  <div class="advanced-search">
    <!-- 搜索表单 -->
    <div class="search-form bg-white rounded-lg shadow-sm p-6 mb-6">
      <div class="flex gap-4 mb-4">
        <div class="flex-1">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="输入您的搜索查询..."
            class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            @keyup.enter="handleSearch"
          />
        </div>
        <button
          @click="handleSearch"
          :disabled="loading || !searchQuery.trim()"
          class="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          <svg v-if="loading" class="animate-spin h-5 w-5" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
          </svg>
          <svg v-else class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
          </svg>
          搜索
        </button>
      </div>
      
      <!-- 高级选项 -->
      <div v-if="showAdvancedOptions" class="border-t pt-4">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">搜索类型</label>
            <select
              v-model="searchConfig.searchType"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
            >
              <option value="hybrid">混合搜索</option>
              <option value="vector">向量搜索</option>
              <option value="graph">图谱搜索</option>
              <option value="semantic">语义搜索</option>
              <option value="keyword">关键词搜索</option>
            </select>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">结果数量</label>
            <select
              v-model="searchConfig.topK"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
            >
              <option :value="5">5个结果</option>
              <option :value="10">10个结果</option>
              <option :value="20">20个结果</option>
              <option :value="50">50个结果</option>
            </select>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">知识库</label>
            <select
              v-model="searchConfig.knowledgeBaseId"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
            >
              <option value="">全部知识库</option>
              <option
                v-for="kb in knowledgeBases"
                :key="kb.id"
                :value="kb.id"
              >
                {{ kb.name }}
              </option>
            </select>
          </div>
        </div>
        
        <div class="mt-4 flex items-center gap-4">
          <label class="flex items-center">
            <input
              v-model="searchConfig.enableRerank"
              type="checkbox"
              class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span class="ml-2 text-sm text-gray-700">启用重排序</span>
          </label>
          
          <label class="flex items-center">
            <input
              v-model="searchConfig.enableExpansion"
              type="checkbox"
              class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span class="ml-2 text-sm text-gray-700">查询扩展</span>
          </label>
        </div>
      </div>
      
      <div class="mt-4 flex justify-between items-center">
        <button
          @click="showAdvancedOptions = !showAdvancedOptions"
          class="text-blue-600 hover:text-blue-800 text-sm flex items-center gap-1"
        >
          <svg
            :class="{ 'rotate-180': showAdvancedOptions }"
            class="h-4 w-4 transition-transform"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
          </svg>
          {{ showAdvancedOptions ? '隐藏' : '显示' }}高级选项
        </button>
        
        <div v-if="searchResults.length > 0" class="text-sm text-gray-500">
          找到 {{ searchResults.length }} 个结果，用时 {{ executionTime }}ms
        </div>
      </div>
    </div>
    
    <!-- 搜索结果 -->
    <div v-if="searchResults.length > 0" class="search-results">
      <div class="mb-4 flex justify-between items-center">
        <h3 class="text-lg font-semibold text-gray-900">搜索结果</h3>
        <div class="flex gap-2">
          <button
            @click="sortBy = 'score'"
            :class="[
              'px-3 py-1 text-sm rounded',
              sortBy === 'score' ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-600'
            ]"
          >
            按相关性
          </button>
          <button
            @click="sortBy = 'source'"
            :class="[
              'px-3 py-1 text-sm rounded',
              sortBy === 'source' ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-600'
            ]"
          >
            按来源
          </button>
        </div>
      </div>
      
      <div class="space-y-4">
        <div
          v-for="result in sortedResults"
          :key="result.id"
          class="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow"
        >
          <div class="flex justify-between items-start mb-3">
            <div class="flex items-center gap-2">
              <span
                :class="[
                  'px-2 py-1 text-xs rounded-full',
                  getSourceColor(result.source)
                ]"
              >
                {{ getSourceLabel(result.source) }}
              </span>
              <span class="text-sm text-gray-500">
                相关性: {{ (result.score * 100).toFixed(1) }}%
              </span>
            </div>
            <div class="flex gap-2">
              <button
                @click="copyResult(result)"
                class="text-gray-400 hover:text-gray-600"
                title="复制内容"
              >
                <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"/>
                </svg>
              </button>
              <button
                @click="viewDocument(result)"
                class="text-gray-400 hover:text-gray-600"
                title="查看文档"
              >
                <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                </svg>
              </button>
            </div>
          </div>
          
          <div class="text-gray-900 mb-3 leading-relaxed">
            <span v-html="highlightQuery(result.content, searchQuery)"></span>
          </div>
          
          <div v-if="result.metadata" class="text-sm text-gray-500">
            <div v-if="result.metadata.document_name" class="mb-1">
              文档: {{ result.metadata.document_name }}
            </div>
            <div v-if="result.metadata.chunk_index !== undefined" class="mb-1">
              片段: {{ result.metadata.chunk_index + 1 }}
            </div>
            <div v-if="result.metadata.created_at" class="mb-1">
              创建时间: {{ formatDate(result.metadata.created_at) }}
            </div>
          </div>
        </div>
      </div>
      
      <!-- 加载更多 -->
      <div v-if="hasMore" class="mt-6 text-center">
        <button
          @click="loadMore"
          :disabled="loadingMore"
          class="px-6 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50"
        >
          {{ loadingMore ? '加载中...' : '加载更多' }}
        </button>
      </div>
    </div>
    
    <!-- 空状态 -->
    <div v-else-if="hasSearched && !loading" class="text-center py-12">
      <svg class="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
      </svg>
      <h3 class="text-lg font-medium text-gray-900 mb-2">未找到相关结果</h3>
      <p class="text-gray-500">尝试使用不同的关键词或调整搜索选项</p>
    </div>
  </div>
</template>

<script setup>
import {computed, onMounted, reactive, ref} from 'vue'
import {useToast} from 'vue-toastification'

const toast = useToast()

// 响应式数据
const searchQuery = ref('')
const loading = ref(false)
const loadingMore = ref(false)
const hasSearched = ref(false)
const showAdvancedOptions = ref(false)
const searchResults = ref([])
const knowledgeBases = ref([])
const executionTime = ref(0)
const hasMore = ref(false)
const sortBy = ref('score')

// 搜索配置
const searchConfig = reactive({
  searchType: 'hybrid',
  topK: 10,
  knowledgeBaseId: '',
  enableRerank: true,
  enableExpansion: true,
  scoreThreshold: 0.0
})

// 计算属性
const sortedResults = computed(() => {
  const results = [...searchResults.value]
  
  if (sortBy.value === 'score') {
    return results.sort((a, b) => b.score - a.score)
  } else if (sortBy.value === 'source') {
    return results.sort((a, b) => a.source.localeCompare(b.source))
  }
  
  return results
})

// 方法
const handleSearch = async () => {
  if (!searchQuery.value.trim()) return
  
  loading.value = true
  hasSearched.value = true
  
  try {
    const startTime = Date.now()
    
    const response = await $fetch('/api/v1/advanced-search/search', {
      method: 'POST',
      body: {
        query: searchQuery.value,
        knowledge_base_id: searchConfig.knowledgeBaseId || 1, // 默认知识库
        search_type: searchConfig.searchType,
        top_k: searchConfig.topK,
        enable_rerank: searchConfig.enableRerank,
        enable_expansion: searchConfig.enableExpansion,
        score_threshold: searchConfig.scoreThreshold
      }
    })
    
    searchResults.value = response.results
    executionTime.value = Date.now() - startTime
    hasMore.value = response.results.length === searchConfig.topK
    
  } catch (error) {
    console.error('搜索失败:', error)
    toast.error('搜索失败，请重试')
  } finally {
    loading.value = false
  }
}

const loadMore = async () => {
  // 实现加载更多逻辑
  loadingMore.value = true
  // ... 加载更多的实现
  loadingMore.value = false
}

const copyResult = async (result) => {
  try {
    await navigator.clipboard.writeText(result.content)
    toast.success('内容已复制到剪贴板')
  } catch (error) {
    toast.error('复制失败')
  }
}

const viewDocument = (result) => {
  if (result.document_id) {
    // 跳转到文档详情页
    navigateTo(`/documents/${result.document_id}`)
  }
}

const highlightQuery = (text, query) => {
  if (!query.trim()) return text
  
  const regex = new RegExp(`(${query.trim()})`, 'gi')
  return text.replace(regex, '<mark class="bg-yellow-200">$1</mark>')
}

const getSourceColor = (source) => {
  const colors = {
    vector: 'bg-blue-100 text-blue-800',
    graph: 'bg-green-100 text-green-800',
    keyword: 'bg-purple-100 text-purple-800',
    hybrid: 'bg-orange-100 text-orange-800'
  }
  return colors[source] || 'bg-gray-100 text-gray-800'
}

const getSourceLabel = (source) => {
  const labels = {
    vector: '向量',
    graph: '图谱',
    keyword: '关键词',
    hybrid: '混合'
  }
  return labels[source] || source
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('zh-CN')
}

// 生命周期
onMounted(async () => {
  // 加载知识库列表
  try {
    const response = await $fetch('/api/v1/knowledge-bases')
    knowledgeBases.value = response.items || []
  } catch (error) {
    console.error('加载知识库失败:', error)
  }
})
</script>

<style scoped>
.advanced-search {
  max-width: 4xl;
  margin: 0 auto;
}

mark {
  padding: 0.1em 0.2em;
  border-radius: 0.2em;
}
</style>
