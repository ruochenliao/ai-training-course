<template>
  <div class="plugin-management">
    <div class="page-header">
      <h1>插件管理</h1>
      <p>管理系统插件，扩展平台功能</p>
      
      <div class="header-actions">
        <el-button @click="refreshPlugins" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        <el-button type="primary" @click="showInstallDialog = true">
          <el-icon><Plus /></el-icon>
          安装插件
        </el-button>
      </div>
    </div>

    <!-- 插件统计 -->
    <div class="plugin-stats">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon total">
                <el-icon><Box /></el-icon>
              </div>
              <div class="stat-info">
                <h3>{{ stats.total }}</h3>
                <p>总插件数</p>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon active">
                <el-icon><CircleCheckFilled /></el-icon>
              </div>
              <div class="stat-info">
                <h3>{{ stats.active }}</h3>
                <p>已激活</p>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon inactive">
                <el-icon><CirclePlusFilled /></el-icon>
              </div>
              <div class="stat-info">
                <h3>{{ stats.inactive }}</h3>
                <p>未激活</p>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon error">
                <el-icon><WarningFilled /></el-icon>
              </div>
              <div class="stat-info">
                <h3>{{ stats.error }}</h3>
                <p>错误状态</p>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 插件过滤 -->
    <el-card class="filter-card">
      <div class="filter-controls">
        <div class="filter-group">
          <el-select v-model="filters.type" placeholder="插件类型" clearable style="width: 150px;">
            <el-option label="全部类型" value="" />
            <el-option label="智能体" value="agent" />
            <el-option label="工具" value="tool" />
            <el-option label="集成" value="integration" />
            <el-option label="中间件" value="middleware" />
            <el-option label="工作流" value="workflow" />
            <el-option label="UI组件" value="ui_component" />
          </el-select>
          
          <el-select v-model="filters.status" placeholder="状态" clearable style="width: 120px;">
            <el-option label="全部状态" value="" />
            <el-option label="已激活" value="active" />
            <el-option label="未激活" value="inactive" />
            <el-option label="错误" value="error" />
          </el-select>
          
          <el-input 
            v-model="filters.search" 
            placeholder="搜索插件名称或描述"
            style="width: 250px;"
            clearable
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
        
        <div class="view-controls">
          <el-radio-group v-model="viewMode" size="small">
            <el-radio-button label="grid">
              <el-icon><Grid /></el-icon>
            </el-radio-button>
            <el-radio-button label="list">
              <el-icon><List /></el-icon>
            </el-radio-button>
          </el-radio-group>
        </div>
      </div>
    </el-card>

    <!-- 插件列表 -->
    <div class="plugins-container">
      <!-- 网格视图 -->
      <div v-if="viewMode === 'grid'" class="plugins-grid">
        <div 
          v-for="plugin in filteredPlugins" 
          :key="plugin.name"
          class="plugin-card"
          :class="{ disabled: plugin.status === 'error' }"
        >
          <div class="plugin-header">
            <div class="plugin-icon">
              <el-icon>{{ getPluginIcon(plugin.type) }}</el-icon>
            </div>
            <div class="plugin-status">
              <el-tag :type="getStatusType(plugin.status)" size="small">
                {{ getStatusText(plugin.status) }}
              </el-tag>
            </div>
          </div>
          
          <div class="plugin-content">
            <h4 class="plugin-name">{{ plugin.name }}</h4>
            <p class="plugin-description">{{ plugin.description }}</p>
            
            <div class="plugin-meta">
              <div class="meta-item">
                <span class="label">版本:</span>
                <span class="value">{{ plugin.version }}</span>
              </div>
              <div class="meta-item">
                <span class="label">作者:</span>
                <span class="value">{{ plugin.author }}</span>
              </div>
              <div class="meta-item">
                <span class="label">类型:</span>
                <span class="value">{{ getTypeText(plugin.type) }}</span>
              </div>
            </div>
            
            <div v-if="plugin.tags.length > 0" class="plugin-tags">
              <el-tag 
                v-for="tag in plugin.tags.slice(0, 3)" 
                :key="tag"
                size="small"
                type="info"
              >
                {{ tag }}
              </el-tag>
              <span v-if="plugin.tags.length > 3" class="more-tags">
                +{{ plugin.tags.length - 3 }}
              </span>
            </div>
          </div>
          
          <div class="plugin-actions">
            <el-button 
              size="small" 
              @click="viewPluginDetails(plugin)"
            >
              详情
            </el-button>
            <el-button 
              size="small" 
              :type="plugin.status === 'active' ? 'warning' : 'success'"
              @click="togglePluginStatus(plugin)"
              :loading="plugin.loading"
            >
              {{ plugin.status === 'active' ? '停用' : '激活' }}
            </el-button>
            <el-dropdown @command="handlePluginAction" trigger="click">
              <el-button size="small" text>
                <el-icon><MoreFilled /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item :command="`config_${plugin.name}`">
                    配置
                  </el-dropdown-item>
                  <el-dropdown-item :command="`reload_${plugin.name}`">
                    重新加载
                  </el-dropdown-item>
                  <el-dropdown-item :command="`uninstall_${plugin.name}`" divided>
                    卸载
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </div>
      
      <!-- 列表视图 -->
      <el-card v-else class="plugins-table">
        <el-table :data="filteredPlugins" stripe>
          <el-table-column prop="name" label="插件名称" min-width="150">
            <template #default="{ row }">
              <div class="plugin-name-cell">
                <div class="plugin-icon-small">
                  <el-icon>{{ getPluginIcon(row.type) }}</el-icon>
                </div>
                <div>
                  <div class="name">{{ row.name }}</div>
                  <div class="version">v{{ row.version }}</div>
                </div>
              </div>
            </template>
          </el-table-column>
          
          <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
          
          <el-table-column prop="type" label="类型" width="100">
            <template #default="{ row }">
              {{ getTypeText(row.type) }}
            </template>
          </el-table-column>
          
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getStatusType(row.status)" size="small">
                {{ getStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          
          <el-table-column prop="author" label="作者" width="120" />
          
          <el-table-column label="标签" width="150">
            <template #default="{ row }">
              <el-tag 
                v-for="tag in row.tags.slice(0, 2)" 
                :key="tag"
                size="small"
                type="info"
                style="margin-right: 4px;"
              >
                {{ tag }}
              </el-tag>
              <span v-if="row.tags.length > 2" class="more-tags">
                +{{ row.tags.length - 2 }}
              </span>
            </template>
          </el-table-column>
          
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
              <el-button size="small" @click="viewPluginDetails(row)">
                详情
              </el-button>
              <el-button 
                size="small" 
                :type="row.status === 'active' ? 'warning' : 'success'"
                @click="togglePluginStatus(row)"
                :loading="row.loading"
              >
                {{ row.status === 'active' ? '停用' : '激活' }}
              </el-button>
              <el-dropdown @command="handlePluginAction" trigger="click">
                <el-button size="small" text>
                  <el-icon><MoreFilled /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item :command="`config_${row.name}`">
                      配置
                    </el-dropdown-item>
                    <el-dropdown-item :command="`reload_${row.name}`">
                      重新加载
                    </el-dropdown-item>
                    <el-dropdown-item :command="`uninstall_${row.name}`" divided>
                      卸载
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>

    <!-- 插件详情对话框 -->
    <el-dialog v-model="showDetailsDialog" title="插件详情" width="800px">
      <PluginDetails 
        v-if="selectedPlugin" 
        :plugin="selectedPlugin" 
        @configure="configurePlugin"
        @execute="executePluginAction"
      />
    </el-dialog>

    <!-- 插件配置对话框 -->
    <el-dialog v-model="showConfigDialog" title="插件配置" width="600px">
      <PluginConfig 
        v-if="selectedPlugin" 
        :plugin="selectedPlugin" 
        @save="handleConfigSave"
        @cancel="showConfigDialog = false"
      />
    </el-dialog>

    <!-- 安装插件对话框 -->
    <el-dialog v-model="showInstallDialog" title="安装插件" width="500px">
      <InstallPlugin 
        @install="handlePluginInstall"
        @cancel="showInstallDialog = false"
      />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Refresh, Plus, Box, CircleCheckFilled, CirclePlusFilled, WarningFilled,
  Search, Grid, List, MoreFilled
} from '@element-plus/icons-vue'
import PluginDetails from '@/components/Plugin/PluginDetails.vue'
import PluginConfig from '@/components/Plugin/PluginConfig.vue'
import InstallPlugin from '@/components/Plugin/InstallPlugin.vue'
import { pluginApi } from '@/api/plugin'

// 接口定义
interface Plugin {
  name: string
  version: string
  description: string
  author: string
  type: string
  status: string
  dependencies: string[]
  permissions: string[]
  config: Record<string, any>
  tags: string[]
  loading?: boolean
}

// 响应式数据
const loading = ref(false)
const viewMode = ref('grid')
const plugins = ref<Plugin[]>([])
const selectedPlugin = ref<Plugin | null>(null)
const showDetailsDialog = ref(false)
const showConfigDialog = ref(false)
const showInstallDialog = ref(false)

const filters = reactive({
  type: '',
  status: '',
  search: ''
})

const stats = computed(() => ({
  total: plugins.value.length,
  active: plugins.value.filter(p => p.status === 'active').length,
  inactive: plugins.value.filter(p => p.status === 'inactive').length,
  error: plugins.value.filter(p => p.status === 'error').length
}))

const filteredPlugins = computed(() => {
  return plugins.value.filter(plugin => {
    if (filters.type && plugin.type !== filters.type) return false
    if (filters.status && plugin.status !== filters.status) return false
    if (filters.search) {
      const search = filters.search.toLowerCase()
      return plugin.name.toLowerCase().includes(search) ||
             plugin.description.toLowerCase().includes(search) ||
             plugin.tags.some(tag => tag.toLowerCase().includes(search))
    }
    return true
  })
})

// 方法
const refreshPlugins = async () => {
  loading.value = true
  try {
    const response = await pluginApi.getList()
    plugins.value = response.data.map(plugin => ({
      ...plugin,
      loading: false
    }))
  } catch (error) {
    ElMessage.error('获取插件列表失败')
  } finally {
    loading.value = false
  }
}

const viewPluginDetails = (plugin: Plugin) => {
  selectedPlugin.value = plugin
  showDetailsDialog.value = true
}

const configurePlugin = (plugin: Plugin) => {
  selectedPlugin.value = plugin
  showConfigDialog.value = true
}

const togglePluginStatus = async (plugin: Plugin) => {
  plugin.loading = true
  try {
    const action = plugin.status === 'active' ? 'deactivate' : 'activate'
    const actionText = plugin.status === 'active' ? '停用' : '激活'
    
    await ElMessageBox.confirm(
      `确定要${actionText}插件 "${plugin.name}" 吗？`,
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    if (action === 'activate') {
      await pluginApi.activate(plugin.name)
    } else {
      await pluginApi.deactivate(plugin.name)
    }

    plugin.status = plugin.status === 'active' ? 'inactive' : 'active'
    ElMessage.success(`插件已${actionText}`)
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(`${plugin.status === 'active' ? '停用' : '激活'}插件失败`)
    }
  } finally {
    plugin.loading = false
  }
}

const handlePluginAction = async (command: string) => {
  const [action, pluginName] = command.split('_')
  const plugin = plugins.value.find(p => p.name === pluginName)
  
  if (!plugin) return

  switch (action) {
    case 'config':
      configurePlugin(plugin)
      break
    case 'reload':
      await reloadPlugin(plugin)
      break
    case 'uninstall':
      await uninstallPlugin(plugin)
      break
  }
}

const reloadPlugin = async (plugin: Plugin) => {
  try {
    await ElMessageBox.confirm(
      `确定要重新加载插件 "${plugin.name}" 吗？`,
      '确认重新加载',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await pluginApi.reload(plugin.name)
    ElMessage.success('插件重新加载成功')
    await refreshPlugins()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('重新加载插件失败')
    }
  }
}

const uninstallPlugin = async (plugin: Plugin) => {
  try {
    await ElMessageBox.confirm(
      `确定要卸载插件 "${plugin.name}" 吗？此操作不可恢复。`,
      '确认卸载',
      {
        confirmButtonText: '卸载',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await pluginApi.uninstall(plugin.name)
    ElMessage.success('插件卸载成功')
    await refreshPlugins()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('卸载插件失败')
    }
  }
}

const handleConfigSave = async (config: any) => {
  if (!selectedPlugin.value) return

  try {
    await pluginApi.updateConfig(selectedPlugin.value.name, config)
    selectedPlugin.value.config = config
    ElMessage.success('配置保存成功')
    showConfigDialog.value = false
  } catch (error) {
    ElMessage.error('保存配置失败')
  }
}

const executePluginAction = async (action: string, parameters: any) => {
  if (!selectedPlugin.value) return

  try {
    const result = await pluginApi.execute(selectedPlugin.value.name, action, parameters)
    ElMessage.success('操作执行成功')
    return result
  } catch (error) {
    ElMessage.error('执行操作失败')
    throw error
  }
}

const handlePluginInstall = async (installData: any) => {
  try {
    await pluginApi.install(installData)
    ElMessage.success('插件安装成功')
    showInstallDialog.value = false
    await refreshPlugins()
  } catch (error) {
    ElMessage.error('安装插件失败')
  }
}

const getPluginIcon = (type: string) => {
  const icons = {
    agent: 'user',
    tool: 'tools',
    integration: 'link',
    middleware: 'connection',
    workflow: 'share',
    ui_component: 'grid'
  }
  return icons[type] || 'box'
}

const getStatusType = (status: string) => {
  const types = {
    active: 'success',
    inactive: 'info',
    error: 'danger',
    loading: 'warning'
  }
  return types[status] || 'info'
}

const getStatusText = (status: string) => {
  const texts = {
    active: '已激活',
    inactive: '未激活',
    error: '错误',
    loading: '加载中'
  }
  return texts[status] || '未知'
}

const getTypeText = (type: string) => {
  const texts = {
    agent: '智能体',
    tool: '工具',
    integration: '集成',
    middleware: '中间件',
    workflow: '工作流',
    ui_component: 'UI组件'
  }
  return texts[type] || type
}

// 生命周期
onMounted(() => {
  refreshPlugins()
})
</script>

<style scoped>
.plugin-management {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.page-header h1 {
  margin: 0 0 8px 0;
  font-size: 24px;
  color: #303133;
}

.page-header p {
  margin: 0;
  color: #606266;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.plugin-stats {
  margin-bottom: 24px;
}

.stat-card {
  height: 100px;
}

.stat-content {
  display: flex;
  align-items: center;
  height: 100%;
}

.stat-icon {
  width: 50px;
  height: 50px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
  font-size: 20px;
  color: white;
}

.stat-icon.total {
  background: linear-gradient(135deg, #667eea, #764ba2);
}

.stat-icon.active {
  background: linear-gradient(135deg, #67c23a, #85ce61);
}

.stat-icon.inactive {
  background: linear-gradient(135deg, #909399, #a6a9ad);
}

.stat-icon.error {
  background: linear-gradient(135deg, #f56c6c, #f78989);
}

.stat-info h3 {
  margin: 0 0 4px 0;
  font-size: 20px;
  font-weight: bold;
  color: #303133;
}

.stat-info p {
  margin: 0;
  font-size: 14px;
  color: #606266;
}

.filter-card {
  margin-bottom: 24px;
}

.filter-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-group {
  display: flex;
  gap: 12px;
  align-items: center;
}

.plugins-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

.plugin-card {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 20px;
  background: white;
  transition: all 0.3s;
}

.plugin-card:hover {
  border-color: #409eff;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.15);
}

.plugin-card.disabled {
  opacity: 0.6;
}

.plugin-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.plugin-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: #f0f2f5;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #606266;
  font-size: 20px;
}

.plugin-name {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.plugin-description {
  margin: 0 0 16px 0;
  font-size: 14px;
  color: #606266;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.plugin-meta {
  margin-bottom: 12px;
}

.meta-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
  font-size: 12px;
}

.meta-item .label {
  color: #909399;
}

.meta-item .value {
  color: #303133;
  font-weight: 500;
}

.plugin-tags {
  margin-bottom: 16px;
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.more-tags {
  font-size: 12px;
  color: #909399;
}

.plugin-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.plugin-name-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.plugin-icon-small {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  background: #f0f2f5;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #606266;
}

.plugin-name-cell .name {
  font-weight: 500;
  color: #303133;
}

.plugin-name-cell .version {
  font-size: 12px;
  color: #909399;
}
</style>
