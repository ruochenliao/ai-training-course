<template>
  <div class="system-management">
    <!-- 系统状态概览 -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
      <!-- 系统健康状态 -->
      <div class="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-gray-900">系统健康状态</h3>
          <button
            @click="refreshSystemHealth"
            :disabled="loading.health"
            class="p-2 text-gray-400 hover:text-gray-600 disabled:opacity-50"
          >
            <svg :class="{ 'animate-spin': loading.health }" class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
            </svg>
          </button>
        </div>

        <div class="space-y-3">
          <div v-for="(status, service) in systemHealth" :key="service" class="flex items-center justify-between">
            <span class="text-sm text-gray-600">{{ getServiceName(service) }}</span>
            <span :class="getHealthStatusClass(status)" class="px-2 py-1 text-xs font-medium rounded-full">
              {{ getHealthStatusText(status) }}
            </span>
          </div>
        </div>
      </div>

      <!-- 系统信息 -->
      <div class="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
        <h3 class="text-lg font-semibold text-gray-900 mb-4">系统信息</h3>
        <div class="space-y-3">
          <div class="flex justify-between">
            <span class="text-sm text-gray-600">版本</span>
            <span class="text-sm font-medium">{{ systemInfo.version }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-sm text-gray-600">运行时间</span>
            <span class="text-sm font-medium">{{ formatUptime(systemInfo.uptime) }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-sm text-gray-600">CPU核心</span>
            <span class="text-sm font-medium">{{ systemInfo.cpu_count }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-sm text-gray-600">内存使用</span>
            <span class="text-sm font-medium">{{ formatMemoryUsage(systemInfo) }}</span>
          </div>
        </div>
      </div>

      <!-- 快速操作 -->
      <div class="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
        <h3 class="text-lg font-semibold text-gray-900 mb-4">快速操作</h3>
        <div class="space-y-3">
          <button
            @click="createBackup"
            :disabled="loading.backup"
            class="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center gap-2"
          >
            <svg v-if="loading.backup" class="animate-spin h-4 w-4" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
            </svg>
            <svg v-else class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10"/>
            </svg>
            创建备份
          </button>

          <button
            @click="showConfigModal = true"
            class="w-full px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 flex items-center justify-center gap-2"
          >
            <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/>
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
            </svg>
            系统配置
          </button>

          <button
            @click="showPluginModal = true"
            class="w-full px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 flex items-center justify-center gap-2"
          >
            <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/>
            </svg>
            插件管理
          </button>
        </div>
      </div>
    </div>

    <!-- 管理标签页 -->
    <div class="bg-white rounded-lg shadow-sm border border-gray-200">
      <div class="border-b border-gray-200">
        <nav class="flex space-x-8 px-6" aria-label="Tabs">
          <button
            v-for="tab in managementTabs"
            :key="tab.key"
            @click="activeTab = tab.key"
            :class="[
              'py-4 px-1 border-b-2 font-medium text-sm',
              activeTab === tab.key
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            ]"
          >
            {{ tab.label }}
          </button>
        </nav>
      </div>

      <div class="p-6">
        <!-- 备份管理 -->
        <div v-if="activeTab === 'backup'" class="space-y-6">
          <div class="flex items-center justify-between">
            <h3 class="text-lg font-semibold text-gray-900">备份管理</h3>
            <button
              @click="refreshBackups"
              :disabled="loading.backups"
              class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              刷新列表
            </button>
          </div>

          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-50">
                <tr>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    文件名
                  </th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    大小
                  </th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    创建时间
                  </th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    操作
                  </th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-200">
                <tr v-for="backup in backups" :key="backup.filename">
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {{ backup.filename }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {{ formatFileSize(backup.size) }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {{ formatDate(backup.created_at) }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                    <button
                      @click="restoreBackup(backup.filename)"
                      class="text-blue-600 hover:text-blue-900"
                    >
                      恢复
                    </button>
                    <button
                      @click="deleteBackup(backup.filename)"
                      class="text-red-600 hover:text-red-900"
                    >
                      删除
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- 安全监控 -->
        <div v-if="activeTab === 'security'" class="space-y-6">
          <h3 class="text-lg font-semibold text-gray-900">安全监控</h3>

          <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <!-- 限流统计 -->
            <div class="bg-gray-50 rounded-lg p-4">
              <h4 class="font-medium text-gray-900 mb-3">API限流统计</h4>
              <div class="space-y-2">
                <div class="flex justify-between">
                  <span class="text-sm text-gray-600">总请求数</span>
                  <span class="text-sm font-medium">{{ rateLimitStats.total_requests || 0 }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-sm text-gray-600">被阻止请求</span>
                  <span class="text-sm font-medium text-red-600">{{ rateLimitStats.blocked_requests || 0 }}</span>
                </div>
              </div>
            </div>

            <!-- 安全事件 -->
            <div class="bg-gray-50 rounded-lg p-4">
              <h4 class="font-medium text-gray-900 mb-3">最近安全事件</h4>
              <div class="space-y-2">
                <div v-for="event in securityEvents.slice(0, 3)" :key="event.id" class="text-sm">
                  <div class="flex justify-between">
                    <span class="text-gray-600">{{ event.event_type }}</span>
                    <span :class="getThreatLevelClass(event.threat_level)" class="px-2 py-1 text-xs rounded-full">
                      {{ event.threat_level }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 通知管理 -->
        <div v-if="activeTab === 'notifications'" class="space-y-6">
          <h3 class="text-lg font-semibold text-gray-900">通知管理</h3>

          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-50">
                <tr>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    标题
                  </th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    类型
                  </th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    优先级
                  </th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    时间
                  </th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    状态
                  </th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-200">
                <tr v-for="notification in notifications" :key="notification.id">
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {{ notification.title }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {{ notification.type }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap">
                    <span :class="getPriorityClass(notification.priority)" class="px-2 py-1 text-xs font-medium rounded-full">
                      {{ notification.priority }}
                    </span>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {{ formatDate(notification.created_at) }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap">
                    <span :class="notification.read ? 'text-gray-500' : 'text-blue-600'" class="text-sm">
                      {{ notification.read ? '已读' : '未读' }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- 配置管理模态框 -->
    <div v-if="showConfigModal" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div class="relative top-20 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-1/2 shadow-lg rounded-md bg-white">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-gray-900">系统配置</h3>
          <button
            @click="showConfigModal = false"
            class="text-gray-400 hover:text-gray-600"
          >
            <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>

        <div class="max-h-96 overflow-y-auto">
          <div v-for="(value, key) in systemConfigs" :key="key" class="mb-4">
            <label class="block text-sm font-medium text-gray-700 mb-1">
              {{ key }}
            </label>
            <input
              v-model="systemConfigs[key].value"
              :type="getInputType(value.type)"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
              :readonly="value.readonly"
            />
            <p v-if="value.description" class="text-xs text-gray-500 mt-1">
              {{ value.description }}
            </p>
          </div>
        </div>

        <div class="flex justify-end space-x-3 mt-6">
          <button
            @click="showConfigModal = false"
            class="px-4 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300"
          >
            取消
          </button>
          <button
            @click="saveConfigs"
            :disabled="loading.config"
            class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            保存
          </button>
        </div>
      </div>
    </div>

    <!-- 插件管理模态框 -->
    <div v-if="showPluginModal" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div class="relative top-20 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-2/3 shadow-lg rounded-md bg-white">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-gray-900">插件管理</h3>
          <button
            @click="showPluginModal = false"
            class="text-gray-400 hover:text-gray-600"
          >
            <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>

        <div class="mb-4">
          <input
            type="file"
            ref="pluginFileInput"
            @change="handlePluginUpload"
            accept=".zip"
            class="hidden"
          />
          <button
            @click="$refs.pluginFileInput.click()"
            class="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
          >
            安装插件
          </button>
        </div>

        <div class="max-h-96 overflow-y-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  插件名称
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  版本
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  状态
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  操作
                </th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="plugin in plugins" :key="plugin.id">
                <td class="px-6 py-4 whitespace-nowrap">
                  <div>
                    <div class="text-sm font-medium text-gray-900">{{ plugin.name }}</div>
                    <div class="text-sm text-gray-500">{{ plugin.description }}</div>
                  </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {{ plugin.version }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span :class="getPluginStatusClass(plugin.status)" class="px-2 py-1 text-xs font-medium rounded-full">
                    {{ getPluginStatusText(plugin.status) }}
                  </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                  <button
                    v-if="plugin.status === 'disabled'"
                    @click="enablePlugin(plugin.id)"
                    class="text-green-600 hover:text-green-900"
                  >
                    启用
                  </button>
                  <button
                    v-if="plugin.status === 'enabled'"
                    @click="disablePlugin(plugin.id)"
                    class="text-yellow-600 hover:text-yellow-900"
                  >
                    禁用
                  </button>
                  <button
                    @click="uninstallPlugin(plugin.id)"
                    class="text-red-600 hover:text-red-900"
                  >
                    卸载
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import {onMounted, reactive, ref} from 'vue'
import {useToast} from 'vue-toastification'

const toast = useToast()

// 响应式数据
const loading = reactive({
  health: false,
  backup: false,
  backups: false,
  config: false
})

const activeTab = ref('backup')
const showConfigModal = ref(false)
const showPluginModal = ref(false)

// 系统数据
const systemHealth = ref({
  database: 'healthy',
  redis: 'healthy',
  milvus: 'healthy',
  neo4j: 'healthy'
})

const systemInfo = ref({
  version: '1.0.0',
  uptime: new Date().toISOString(),
  cpu_count: 8,
  memory_total: 16 * 1024 * 1024 * 1024,
  memory_available: 8 * 1024 * 1024 * 1024
})

const backups = ref([])
const rateLimitStats = ref({})
const securityEvents = ref([])
const notifications = ref([])
const systemConfigs = ref({})
const plugins = ref([])

// 管理标签页
const managementTabs = [
  { key: 'backup', label: '备份管理' },
  { key: 'security', label: '安全监控' },
  { key: 'notifications', label: '通知管理' }
]

// 方法
const refreshSystemHealth = async () => {
  loading.health = true
  try {
    const response = await $fetch('/api/v1/system/health')
    if (response.success) {
      systemHealth.value = response.data
    }
  } catch (error) {
    console.error('获取系统健康状态失败:', error)
    toast.error('获取系统健康状态失败')
  } finally {
    loading.health = false
  }
}

const createBackup = async () => {
  loading.backup = true
  try {
    const response = await $fetch('/api/v1/system/backup/create', {
      method: 'POST',
      body: {
        backup_type: 'full',
        name: `manual_backup_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}`
      }
    })

    if (response.success) {
      toast.success('备份任务已创建')
      await refreshBackups()
    }
  } catch (error) {
    console.error('创建备份失败:', error)
    toast.error('创建备份失败')
  } finally {
    loading.backup = false
  }
}

const refreshBackups = async () => {
  loading.backups = true
  try {
    const response = await $fetch('/api/v1/system/backup/list')
    if (response.success) {
      backups.value = response.data
    }
  } catch (error) {
    console.error('获取备份列表失败:', error)
    toast.error('获取备份列表失败')
  } finally {
    loading.backups = false
  }
}

const restoreBackup = async (filename) => {
  if (!confirm(`确定要恢复备份 ${filename} 吗？此操作将覆盖当前数据。`)) {
    return
  }

  try {
    const response = await $fetch('/api/v1/system/backup/restore', {
      method: 'POST',
      body: { backup_file: filename }
    })

    if (response.success) {
      toast.success('恢复任务已创建')
    }
  } catch (error) {
    console.error('恢复备份失败:', error)
    toast.error('恢复备份失败')
  }
}

const deleteBackup = async (filename) => {
  if (!confirm(`确定要删除备份 ${filename} 吗？`)) {
    return
  }

  try {
    const response = await $fetch(`/api/v1/system/backup/delete/${filename}`, {
      method: 'DELETE'
    })

    if (response.success) {
      toast.success('备份已删除')
      await refreshBackups()
    }
  } catch (error) {
    console.error('删除备份失败:', error)
    toast.error('删除备份失败')
  }
}

const loadSystemConfigs = async () => {
  try {
    const response = await $fetch('/api/v1/system/config/all')
    if (response.success) {
      systemConfigs.value = response.data
    }
  } catch (error) {
    console.error('加载系统配置失败:', error)
  }
}

const saveConfigs = async () => {
  loading.config = true
  try {
    const promises = Object.entries(systemConfigs.value).map(([key, config]) => {
      return $fetch(`/api/v1/system/config/${key}`, {
        method: 'PUT',
        body: { value: config.value }
      })
    })

    await Promise.all(promises)
    toast.success('配置已保存')
    showConfigModal.value = false
  } catch (error) {
    console.error('保存配置失败:', error)
    toast.error('保存配置失败')
  } finally {
    loading.config = false
  }
}

const loadPlugins = async () => {
  try {
    const response = await $fetch('/api/v1/system/plugins')
    if (response.success) {
      plugins.value = response.data
    }
  } catch (error) {
    console.error('加载插件列表失败:', error)
  }
}

const handlePluginUpload = async (event) => {
  const file = event.target.files[0]
  if (!file) return

  const formData = new FormData()
  formData.append('file', file)

  try {
    const response = await $fetch('/api/v1/system/plugins/install', {
      method: 'POST',
      body: formData
    })

    if (response.success) {
      toast.success('插件安装成功')
      await loadPlugins()
    }
  } catch (error) {
    console.error('安装插件失败:', error)
    toast.error('安装插件失败')
  }
}

const enablePlugin = async (pluginId) => {
  try {
    const response = await $fetch(`/api/v1/system/plugins/${pluginId}/enable`, {
      method: 'POST'
    })

    if (response.success) {
      toast.success('插件已启用')
      await loadPlugins()
    }
  } catch (error) {
    console.error('启用插件失败:', error)
    toast.error('启用插件失败')
  }
}

const disablePlugin = async (pluginId) => {
  try {
    const response = await $fetch(`/api/v1/system/plugins/${pluginId}/disable`, {
      method: 'POST'
    })

    if (response.success) {
      toast.success('插件已禁用')
      await loadPlugins()
    }
  } catch (error) {
    console.error('禁用插件失败:', error)
    toast.error('禁用插件失败')
  }
}

const uninstallPlugin = async (pluginId) => {
  if (!confirm('确定要卸载此插件吗？')) {
    return
  }

  try {
    const response = await $fetch(`/api/v1/system/plugins/${pluginId}`, {
      method: 'DELETE'
    })

    if (response.success) {
      toast.success('插件已卸载')
      await loadPlugins()
    }
  } catch (error) {
    console.error('卸载插件失败:', error)
    toast.error('卸载插件失败')
  }
}

// 工具函数
const getServiceName = (service) => {
  const names = {
    database: '数据库',
    redis: 'Redis',
    milvus: 'Milvus',
    neo4j: 'Neo4j'
  }
  return names[service] || service
}

const getHealthStatusClass = (status) => {
  const classes = {
    healthy: 'bg-green-100 text-green-800',
    warning: 'bg-yellow-100 text-yellow-800',
    error: 'bg-red-100 text-red-800'
  }
  return classes[status] || 'bg-gray-100 text-gray-800'
}

const getHealthStatusText = (status) => {
  const texts = {
    healthy: '正常',
    warning: '警告',
    error: '错误'
  }
  return texts[status] || status
}

const formatUptime = (uptime) => {
  const now = new Date()
  const start = new Date(uptime)
  const diff = now - start
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
  return `${hours}小时${minutes}分钟`
}

const formatMemoryUsage = (info) => {
  const used = info.memory_total - info.memory_available
  const usedGB = (used / (1024 * 1024 * 1024)).toFixed(1)
  const totalGB = (info.memory_total / (1024 * 1024 * 1024)).toFixed(1)
  return `${usedGB}GB / ${totalGB}GB`
}

const formatFileSize = (bytes) => {
  const sizes = ['B', 'KB', 'MB', 'GB']
  if (bytes === 0) return '0 B'
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i]
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleString('zh-CN')
}

const getThreatLevelClass = (level) => {
  const classes = {
    low: 'bg-green-100 text-green-800',
    medium: 'bg-yellow-100 text-yellow-800',
    high: 'bg-red-100 text-red-800',
    critical: 'bg-red-200 text-red-900'
  }
  return classes[level] || 'bg-gray-100 text-gray-800'
}

const getPriorityClass = (priority) => {
  const classes = {
    low: 'bg-gray-100 text-gray-800',
    normal: 'bg-blue-100 text-blue-800',
    high: 'bg-yellow-100 text-yellow-800',
    urgent: 'bg-red-100 text-red-800'
  }
  return classes[priority] || 'bg-gray-100 text-gray-800'
}

const getInputType = (type) => {
  const types = {
    string: 'text',
    integer: 'number',
    float: 'number',
    boolean: 'checkbox',
    password: 'password'
  }
  return types[type] || 'text'
}

const getPluginStatusClass = (status) => {
  const classes = {
    installed: 'bg-gray-100 text-gray-800',
    enabled: 'bg-green-100 text-green-800',
    disabled: 'bg-yellow-100 text-yellow-800',
    error: 'bg-red-100 text-red-800'
  }
  return classes[status] || 'bg-gray-100 text-gray-800'
}

const getPluginStatusText = (status) => {
  const texts = {
    installed: '已安装',
    enabled: '已启用',
    disabled: '已禁用',
    error: '错误'
  }
  return texts[status] || status
}

// 生命周期
onMounted(async () => {
  await Promise.all([
    refreshSystemHealth(),
    refreshBackups(),
    loadSystemConfigs(),
    loadPlugins()
  ])
})
</script>

<style scoped>
.system-management {
  max-width: 100%;
  margin: 0 auto;
}
</style>