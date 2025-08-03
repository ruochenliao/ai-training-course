<template>
  <div class="install-plugin">
    <el-tabs v-model="activeTab">
      <!-- 文件上传安装 -->
      <el-tab-pane label="上传文件" name="upload">
        <div class="upload-section">
          <el-upload
            ref="uploadRef"
            class="upload-dragger"
            drag
            :auto-upload="false"
            :on-change="handleFileChange"
            :before-upload="beforeUpload"
            accept=".zip,.tar.gz"
            :limit="1"
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">
              将插件文件拖到此处，或<em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                支持 .zip 和 .tar.gz 格式的插件包
              </div>
            </template>
          </el-upload>
          
          <div v-if="selectedFile" class="file-info">
            <h4>选中的文件:</h4>
            <div class="file-details">
              <el-icon><Document /></el-icon>
              <span class="file-name">{{ selectedFile.name }}</span>
              <span class="file-size">({{ formatFileSize(selectedFile.size) }})</span>
            </div>
          </div>
        </div>
      </el-tab-pane>
      
      <!-- URL安装 -->
      <el-tab-pane label="从URL安装" name="url">
        <div class="url-section">
          <el-form :model="urlForm" :rules="urlRules" ref="urlFormRef" label-width="100px">
            <el-form-item label="插件URL" prop="url">
              <el-input 
                v-model="urlForm.url" 
                placeholder="https://example.com/plugin.zip"
                clearable
              />
            </el-form-item>
            
            <el-form-item label="认证信息">
              <el-checkbox v-model="urlForm.requireAuth">需要认证</el-checkbox>
            </el-form-item>
            
            <template v-if="urlForm.requireAuth">
              <el-form-item label="用户名" prop="username">
                <el-input v-model="urlForm.username" />
              </el-form-item>
              
              <el-form-item label="密码" prop="password">
                <el-input v-model="urlForm.password" type="password" show-password />
              </el-form-item>
            </template>
          </el-form>
        </div>
      </el-tab-pane>
      
      <!-- 插件市场 -->
      <el-tab-pane label="插件市场" name="market">
        <div class="market-section">
          <div class="market-search">
            <el-input 
              v-model="searchKeyword" 
              placeholder="搜索插件..."
              clearable
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
            
            <el-select v-model="categoryFilter" placeholder="分类" clearable style="width: 150px;">
              <el-option label="全部" value="" />
              <el-option label="智能体" value="agent" />
              <el-option label="工具" value="tool" />
              <el-option label="集成" value="integration" />
              <el-option label="工作流" value="workflow" />
            </el-select>
          </div>
          
          <div class="market-plugins">
            <div 
              v-for="plugin in filteredMarketPlugins" 
              :key="plugin.id"
              class="market-plugin"
              :class="{ selected: selectedMarketPlugin?.id === plugin.id }"
              @click="selectMarketPlugin(plugin)"
            >
              <div class="plugin-icon">
                <el-icon>{{ getPluginIcon(plugin.type) }}</el-icon>
              </div>
              
              <div class="plugin-info">
                <h4>{{ plugin.name }}</h4>
                <p>{{ plugin.description }}</p>
                
                <div class="plugin-meta">
                  <el-tag size="small">{{ plugin.type }}</el-tag>
                  <span class="version">v{{ plugin.version }}</span>
                  <span class="downloads">{{ plugin.downloads }} 下载</span>
                </div>
                
                <div class="plugin-rating">
                  <el-rate v-model="plugin.rating" disabled size="small" />
                  <span class="rating-text">({{ plugin.reviews }})</span>
                </div>
              </div>
              
              <div class="plugin-actions">
                <el-button 
                  size="small" 
                  type="primary"
                  :disabled="plugin.installed"
                >
                  {{ plugin.installed ? '已安装' : '安装' }}
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 安装选项 -->
    <div class="install-options">
      <el-form :model="installForm" label-width="120px">
        <el-form-item label="安装后激活">
          <el-switch v-model="installForm.autoActivate" />
        </el-form-item>
        
        <el-form-item label="覆盖已存在">
          <el-switch v-model="installForm.overwrite" />
        </el-form-item>
        
        <el-form-item label="验证签名">
          <el-switch v-model="installForm.verifySignature" />
        </el-form-item>
      </el-form>
    </div>

    <!-- 安装进度 -->
    <div v-if="installing" class="install-progress">
      <el-progress :percentage="installProgress" :status="installStatus" />
      <p class="progress-text">{{ installProgressText }}</p>
    </div>

    <!-- 操作按钮 -->
    <div class="install-actions">
      <el-button @click="handleCancel">取消</el-button>
      <el-button 
        type="primary" 
        @click="handleInstall"
        :loading="installing"
        :disabled="!canInstall"
      >
        {{ installing ? '安装中...' : '安装插件' }}
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled, Document, Search } from '@element-plus/icons-vue'
import type { FormInstance, FormRules, UploadFile } from 'element-plus'

const emit = defineEmits(['install', 'cancel'])

// 响应式数据
const activeTab = ref('upload')
const installing = ref(false)
const installProgress = ref(0)
const installStatus = ref('')
const installProgressText = ref('')
const selectedFile = ref<File | null>(null)
const selectedMarketPlugin = ref<any>(null)
const searchKeyword = ref('')
const categoryFilter = ref('')

const uploadRef = ref()
const urlFormRef = ref<FormInstance>()

const urlForm = reactive({
  url: '',
  requireAuth: false,
  username: '',
  password: ''
})

const installForm = reactive({
  autoActivate: true,
  overwrite: false,
  verifySignature: true
})

const urlRules: FormRules = {
  url: [
    { required: true, message: '请输入插件URL', trigger: 'blur' },
    { type: 'url', message: '请输入有效的URL', trigger: 'blur' }
  ],
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' }
  ]
}

// 模拟插件市场数据
const marketPlugins = ref([
  {
    id: 'slack-integration',
    name: 'Slack集成',
    description: '与Slack工作空间集成，发送消息和通知',
    type: 'integration',
    version: '1.2.0',
    downloads: 1250,
    rating: 4.5,
    reviews: 89,
    installed: false
  },
  {
    id: 'weather-tool',
    name: '天气查询工具',
    description: '获取实时天气信息和预报',
    type: 'tool',
    version: '2.1.0',
    downloads: 2340,
    rating: 4.8,
    reviews: 156,
    installed: false
  },
  {
    id: 'translation-agent',
    name: '翻译智能体',
    description: '多语言翻译和本地化服务',
    type: 'agent',
    version: '1.5.2',
    downloads: 890,
    rating: 4.3,
    reviews: 67,
    installed: true
  },
  {
    id: 'pdf-processor',
    name: 'PDF处理工具',
    description: 'PDF文档解析、转换和处理',
    type: 'tool',
    version: '3.0.1',
    downloads: 1680,
    rating: 4.6,
    reviews: 123,
    installed: false
  }
])

// 计算属性
const canInstall = computed(() => {
  if (activeTab.value === 'upload') {
    return selectedFile.value !== null
  } else if (activeTab.value === 'url') {
    return urlForm.url !== ''
  } else if (activeTab.value === 'market') {
    return selectedMarketPlugin.value !== null && !selectedMarketPlugin.value.installed
  }
  return false
})

const filteredMarketPlugins = computed(() => {
  let plugins = marketPlugins.value

  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    plugins = plugins.filter(plugin => 
      plugin.name.toLowerCase().includes(keyword) ||
      plugin.description.toLowerCase().includes(keyword)
    )
  }

  if (categoryFilter.value) {
    plugins = plugins.filter(plugin => plugin.type === categoryFilter.value)
  }

  return plugins
})

// 方法
const handleFileChange = (file: UploadFile) => {
  selectedFile.value = file.raw || null
}

const beforeUpload = (file: File) => {
  const isValidType = file.name.endsWith('.zip') || file.name.endsWith('.tar.gz')
  if (!isValidType) {
    ElMessage.error('只支持 .zip 和 .tar.gz 格式的文件')
    return false
  }

  const isLt50M = file.size / 1024 / 1024 < 50
  if (!isLt50M) {
    ElMessage.error('文件大小不能超过 50MB')
    return false
  }

  return false // 阻止自动上传
}

const selectMarketPlugin = (plugin: any) => {
  if (!plugin.installed) {
    selectedMarketPlugin.value = plugin
  }
}

const formatFileSize = (size: number) => {
  if (size < 1024) {
    return size + ' B'
  } else if (size < 1024 * 1024) {
    return (size / 1024).toFixed(1) + ' KB'
  } else {
    return (size / 1024 / 1024).toFixed(1) + ' MB'
  }
}

const getPluginIcon = (type: string) => {
  const icons = {
    agent: 'user',
    tool: 'tools',
    integration: 'link',
    workflow: 'share'
  }
  return icons[type] || 'box'
}

const simulateInstallProgress = () => {
  const steps = [
    { progress: 10, text: '验证插件包...' },
    { progress: 30, text: '检查依赖关系...' },
    { progress: 50, text: '解压插件文件...' },
    { progress: 70, text: '安装插件...' },
    { progress: 90, text: '配置插件...' },
    { progress: 100, text: '安装完成' }
  ]

  let currentStep = 0
  const interval = setInterval(() => {
    if (currentStep < steps.length) {
      const step = steps[currentStep]
      installProgress.value = step.progress
      installProgressText.value = step.text
      currentStep++
    } else {
      clearInterval(interval)
      installStatus.value = 'success'
      setTimeout(() => {
        installing.value = false
        ElMessage.success('插件安装成功')
        
        // 构建安装数据
        let installData = {
          type: activeTab.value,
          options: installForm
        }

        if (activeTab.value === 'upload') {
          installData.file = selectedFile.value
        } else if (activeTab.value === 'url') {
          installData.url = urlForm.url
          installData.auth = urlForm.requireAuth ? {
            username: urlForm.username,
            password: urlForm.password
          } : null
        } else if (activeTab.value === 'market') {
          installData.plugin = selectedMarketPlugin.value
        }

        emit('install', installData)
      }, 1000)
    }
  }, 800)
}

const handleInstall = async () => {
  // 验证表单
  if (activeTab.value === 'url') {
    if (!urlFormRef.value) return
    
    try {
      await urlFormRef.value.validate()
    } catch (error) {
      return
    }
  }

  installing.value = true
  installProgress.value = 0
  installStatus.value = ''
  installProgressText.value = '开始安装...'

  // 模拟安装过程
  simulateInstallProgress()
}

const handleCancel = () => {
  if (installing.value) {
    ElMessage.warning('安装正在进行中，无法取消')
    return
  }
  emit('cancel')
}

// 生命周期
onMounted(() => {
  // 可以在这里加载插件市场数据
})
</script>

<style scoped>
.install-plugin {
  padding: 20px 0;
}

.upload-section {
  padding: 20px 0;
}

.upload-dragger {
  width: 100%;
}

.file-info {
  margin-top: 20px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 6px;
}

.file-info h4 {
  margin: 0 0 12px 0;
  color: #303133;
}

.file-details {
  display: flex;
  align-items: center;
  gap: 8px;
}

.file-name {
  font-weight: 500;
  color: #303133;
}

.file-size {
  color: #909399;
  font-size: 14px;
}

.url-section {
  padding: 20px 0;
}

.market-section {
  padding: 20px 0;
}

.market-search {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.market-plugins {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 400px;
  overflow-y: auto;
}

.market-plugin {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.market-plugin:hover {
  border-color: #409eff;
  background: #f0f9ff;
}

.market-plugin.selected {
  border-color: #409eff;
  background: #e6f7ff;
}

.plugin-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  background: #f0f2f5;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #606266;
  font-size: 20px;
}

.plugin-info {
  flex: 1;
}

.plugin-info h4 {
  margin: 0 0 4px 0;
  color: #303133;
}

.plugin-info p {
  margin: 0 0 8px 0;
  color: #606266;
  font-size: 14px;
}

.plugin-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 4px;
}

.version, .downloads {
  font-size: 12px;
  color: #909399;
}

.plugin-rating {
  display: flex;
  align-items: center;
  gap: 4px;
}

.rating-text {
  font-size: 12px;
  color: #909399;
}

.install-options {
  margin: 24px 0;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 6px;
}

.install-progress {
  margin: 24px 0;
  padding: 16px;
  background: #f0f9ff;
  border-radius: 6px;
  text-align: center;
}

.progress-text {
  margin: 8px 0 0 0;
  color: #606266;
  font-size: 14px;
}

.install-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 20px;
  border-top: 1px solid #e4e7ed;
}

:deep(.el-upload-dragger) {
  width: 100%;
  height: 180px;
}

:deep(.el-rate) {
  height: auto;
}
</style>
