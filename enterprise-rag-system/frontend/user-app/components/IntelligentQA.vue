<template>
  <div class="intelligent-qa">
    <!-- 问答界面 -->
    <div class="qa-container bg-white rounded-lg shadow-sm">
      <!-- 对话历史 -->
      <div ref="messagesContainer" class="messages-container p-6 h-96 overflow-y-auto border-b">
        <div v-if="messages.length === 0" class="text-center text-gray-500 mt-20">
          <svg class="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
          </svg>
          <h3 class="text-lg font-medium text-gray-900 mb-2">开始智能问答</h3>
          <p class="text-gray-500">输入您的问题，我将基于知识库为您提供准确的答案</p>
        </div>
        
        <div v-else class="space-y-6">
          <div
            v-for="(message, index) in messages"
            :key="index"
            :class="[
              'flex',
              message.type === 'user' ? 'justify-end' : 'justify-start'
            ]"
          >
            <!-- 用户消息 -->
            <div
              v-if="message.type === 'user'"
              class="max-w-xs lg:max-w-md px-4 py-2 bg-blue-600 text-white rounded-lg"
            >
              {{ message.content }}
            </div>
            
            <!-- AI回答 -->
            <div
              v-else
              class="max-w-2xl bg-gray-100 rounded-lg p-4"
            >
              <div class="flex items-start gap-3">
                <div class="flex-shrink-0">
                  <div class="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                    <svg class="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                    </svg>
                  </div>
                </div>
                
                <div class="flex-1">
                  <!-- 答案内容 -->
                  <div class="prose prose-sm max-w-none mb-3">
                    <div v-html="formatAnswer(message.content)"></div>
                  </div>
                  
                  <!-- 置信度 -->
                  <div v-if="message.confidence" class="mb-3">
                    <div class="flex items-center gap-2 text-sm text-gray-600">
                      <span>置信度:</span>
                      <div class="flex-1 bg-gray-200 rounded-full h-2 max-w-20">
                        <div
                          class="bg-blue-600 h-2 rounded-full"
                          :style="{ width: `${message.confidence * 100}%` }"
                        ></div>
                      </div>
                      <span>{{ (message.confidence * 100).toFixed(1) }}%</span>
                    </div>
                  </div>
                  
                  <!-- 来源文档 -->
                  <div v-if="message.sources && message.sources.length > 0" class="mb-3">
                    <button
                      @click="message.showSources = !message.showSources"
                      class="text-sm text-blue-600 hover:text-blue-800 flex items-center gap-1"
                    >
                      <svg
                        :class="{ 'rotate-180': message.showSources }"
                        class="w-4 h-4 transition-transform"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
                      </svg>
                      参考来源 ({{ message.sources.length }})
                    </button>
                    
                    <div v-if="message.showSources" class="mt-2 space-y-2">
                      <div
                        v-for="(source, sourceIndex) in message.sources"
                        :key="sourceIndex"
                        class="bg-white border border-gray-200 rounded p-3 text-sm"
                      >
                        <div class="font-medium text-gray-900 mb-1">
                          {{ source.metadata?.document_name || `文档 ${sourceIndex + 1}` }}
                        </div>
                        <div class="text-gray-600 text-xs mb-2">
                          相关性: {{ (source.score * 100).toFixed(1) }}%
                        </div>
                        <div class="text-gray-700 line-clamp-3">
                          {{ source.content }}
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <!-- 推理过程 -->
                  <div v-if="message.reasoning" class="mb-3">
                    <button
                      @click="message.showReasoning = !message.showReasoning"
                      class="text-sm text-gray-600 hover:text-gray-800 flex items-center gap-1"
                    >
                      <svg
                        :class="{ 'rotate-180': message.showReasoning }"
                        class="w-4 h-4 transition-transform"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
                      </svg>
                      推理过程
                    </button>
                    
                    <div v-if="message.showReasoning" class="mt-2 bg-gray-50 border border-gray-200 rounded p-3 text-sm text-gray-700">
                      {{ message.reasoning }}
                    </div>
                  </div>
                  
                  <!-- 建议和相关问题 -->
                  <div v-if="message.suggestions && message.suggestions.length > 0" class="mb-3">
                    <div class="text-sm text-gray-600 mb-2">建议:</div>
                    <ul class="text-sm text-gray-700 space-y-1">
                      <li v-for="suggestion in message.suggestions" :key="suggestion" class="flex items-start gap-2">
                        <span class="text-blue-600">•</span>
                        <span>{{ suggestion }}</span>
                      </li>
                    </ul>
                  </div>
                  
                  <div v-if="message.relatedQuestions && message.relatedQuestions.length > 0">
                    <div class="text-sm text-gray-600 mb-2">相关问题:</div>
                    <div class="space-y-1">
                      <button
                        v-for="question in message.relatedQuestions"
                        :key="question"
                        @click="askRelatedQuestion(question)"
                        class="block text-sm text-blue-600 hover:text-blue-800 hover:underline text-left"
                      >
                        {{ question }}
                      </button>
                    </div>
                  </div>
                  
                  <!-- 操作按钮 -->
                  <div class="flex gap-2 mt-3">
                    <button
                      @click="copyAnswer(message.content)"
                      class="text-gray-400 hover:text-gray-600"
                      title="复制答案"
                    >
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"/>
                      </svg>
                    </button>
                    <button
                      @click="rateAnswer(message, 'good')"
                      :class="[
                        'hover:text-green-600',
                        message.rating === 'good' ? 'text-green-600' : 'text-gray-400'
                      ]"
                      title="好评"
                    >
                      <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M2 10.5a1.5 1.5 0 113 0v6a1.5 1.5 0 01-3 0v-6zM6 10.333v5.43a2 2 0 001.106 1.79l.05.025A4 4 0 008.943 18h5.416a2 2 0 001.962-1.608l1.2-6A2 2 0 0015.56 8H12V4a2 2 0 00-2-2 1 1 0 00-1 1v.667a4 4 0 01-.8 2.4L6.8 7.933a4 4 0 00-.8 2.4z"/>
                      </svg>
                    </button>
                    <button
                      @click="rateAnswer(message, 'bad')"
                      :class="[
                        'hover:text-red-600',
                        message.rating === 'bad' ? 'text-red-600' : 'text-gray-400'
                      ]"
                      title="差评"
                    >
                      <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M18 9.5a1.5 1.5 0 11-3 0v-6a1.5 1.5 0 013 0v6zM14 9.667v-5.43a2 2 0 00-1.106-1.79l-.05-.025A4 4 0 0011.057 2H5.64a2 2 0 00-1.962 1.608l-1.2 6A2 2 0 004.44 12H8v4a2 2 0 002 2 1 1 0 001-1v-.667a4 4 0 01.8-2.4l1.4-1.866a4 4 0 00.8-2.4z"/>
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 正在输入指示器 -->
          <div v-if="isTyping" class="flex justify-start">
            <div class="max-w-2xl bg-gray-100 rounded-lg p-4">
              <div class="flex items-center gap-3">
                <div class="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                  <svg class="w-4 h-4 text-white animate-pulse" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                  </svg>
                </div>
                <div class="flex space-x-1">
                  <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
                  <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 输入区域 -->
      <div class="input-area p-6">
        <div class="flex gap-4">
          <div class="flex-1">
            <textarea
              v-model="currentQuestion"
              placeholder="输入您的问题..."
              class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
              rows="3"
              @keydown.enter.exact.prevent="handleAsk"
              @keydown.enter.shift.exact="currentQuestion += '\n'"
            ></textarea>
          </div>
          <div class="flex flex-col gap-2">
            <button
              @click="handleAsk"
              :disabled="!currentQuestion.trim() || isAsking"
              class="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <svg v-if="isAsking" class="animate-spin h-5 w-5" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"/>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
              </svg>
              <svg v-else class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/>
              </svg>
              发送
            </button>
            <button
              @click="clearConversation"
              class="px-4 py-2 text-gray-600 hover:text-gray-800 text-sm"
              title="清空对话"
            >
              清空
            </button>
          </div>
        </div>
        
        <!-- 快捷问题 -->
        <div v-if="quickQuestions.length > 0 && messages.length === 0" class="mt-4">
          <div class="text-sm text-gray-600 mb-2">快捷问题:</div>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="question in quickQuestions"
              :key="question"
              @click="askQuickQuestion(question)"
              class="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200"
            >
              {{ question }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import {nextTick, onMounted, ref} from 'vue'
import {useToast} from 'vue-toastification'

const toast = useToast()

// Props
const props = defineProps({
  knowledgeBaseId: {
    type: Number,
    default: 1
  }
})

// 响应式数据
const currentQuestion = ref('')
const messages = ref([])
const isAsking = ref(false)
const isTyping = ref(false)
const messagesContainer = ref(null)
const sessionId = ref(`session_${Date.now()}`)

const quickQuestions = ref([
  '什么是人工智能？',
  '如何使用这个系统？',
  '有哪些功能特性？',
  '如何上传文档？',
  '支持哪些文件格式？'
])

// 方法
const handleAsk = async () => {
  if (!currentQuestion.value.trim() || isAsking.value) return
  
  const question = currentQuestion.value.trim()
  currentQuestion.value = ''
  
  // 添加用户消息
  messages.value.push({
    type: 'user',
    content: question,
    timestamp: new Date()
  })
  
  // 滚动到底部
  await nextTick()
  scrollToBottom()
  
  // 显示正在输入
  isAsking.value = true
  isTyping.value = true
  
  try {
    const response = await $fetch('/api/v1/qa/ask', {
      method: 'POST',
      body: {
        question,
        knowledge_base_id: props.knowledgeBaseId,
        session_id: sessionId.value,
        history: messages.value.slice(-10).map(msg => ({
          role: msg.type === 'user' ? 'user' : 'assistant',
          content: msg.content
        }))
      }
    })
    
    // 添加AI回答
    messages.value.push({
      type: 'assistant',
      content: response.answer,
      confidence: response.confidence,
      sources: response.sources,
      reasoning: response.reasoning,
      suggestions: response.suggestions,
      relatedQuestions: response.related_questions,
      questionType: response.question_type,
      timestamp: new Date(),
      showSources: false,
      showReasoning: false
    })
    
  } catch (error) {
    console.error('问答失败:', error)
    messages.value.push({
      type: 'assistant',
      content: '抱歉，我无法回答这个问题。请稍后重试。',
      timestamp: new Date(),
      error: true
    })
    toast.error('问答失败，请重试')
  } finally {
    isAsking.value = false
    isTyping.value = false
    await nextTick()
    scrollToBottom()
  }
}

const askQuickQuestion = (question) => {
  currentQuestion.value = question
  handleAsk()
}

const askRelatedQuestion = (question) => {
  currentQuestion.value = question
  handleAsk()
}

const clearConversation = () => {
  messages.value = []
  sessionId.value = `session_${Date.now()}`
}

const copyAnswer = async (content) => {
  try {
    await navigator.clipboard.writeText(content)
    toast.success('答案已复制到剪贴板')
  } catch (error) {
    toast.error('复制失败')
  }
}

const rateAnswer = (message, rating) => {
  message.rating = rating
  // 这里可以发送评分到后端
  toast.success(rating === 'good' ? '感谢您的好评！' : '感谢您的反馈！')
}

const formatAnswer = (content) => {
  // 简单的Markdown格式化
  return content
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br>')
}

const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// 生命周期
onMounted(() => {
  // 可以在这里加载历史对话
})
</script>

<style scoped>
.intelligent-qa {
  max-width: 4xl;
  margin: 0 auto;
}

.messages-container {
  scroll-behavior: smooth;
}

.line-clamp-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.prose {
  color: inherit;
}

.prose strong {
  font-weight: 600;
}

.prose em {
  font-style: italic;
}
</style>
