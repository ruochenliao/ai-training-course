/**
 * 插件管理API
 */

import request from './request'
import type { ApiResponse } from './request'
import { API_PATHS } from './baseUrl'

export interface Plugin {
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
}

export interface PluginConfig {
  config: Record<string, any>
}

export interface PluginAction {
  action: string
  parameters: Record<string, any>
}

export const pluginApi = {
  /**
   * 获取插件列表
   */
  getList(params?: {
    type?: string
    status?: string
  }) {
    return request<Plugin[]>({
      url: '/api/v1/plugins',
      method: 'GET',
      params
    })
  },

  /**
   * 获取插件详情
   */
  getDetail(pluginName: string) {
    return request<Plugin>({
      url: `/api/v1/plugins/${pluginName}`,
      method: 'GET'
    })
  },

  /**
   * 激活插件
   */
  activate(pluginName: string) {
    return request({
      url: `/api/v1/plugins/${pluginName}/activate`,
      method: 'POST'
    })
  },

  /**
   * 停用插件
   */
  deactivate(pluginName: string) {
    return request({
      url: `/api/v1/plugins/${pluginName}/deactivate`,
      method: 'POST'
    })
  },

  /**
   * 更新插件配置
   */
  updateConfig(pluginName: string, config: Record<string, any>) {
    return request({
      url: `/api/v1/plugins/${pluginName}/config`,
      method: 'PUT',
      data: { config }
    })
  },

  /**
   * 重新加载插件
   */
  reload(pluginName: string) {
    return request({
      url: `/api/v1/plugins/${pluginName}/reload`,
      method: 'POST'
    })
  },

  /**
   * 执行插件操作
   */
  execute(pluginName: string, action: string, parameters: Record<string, any> = {}) {
    return request({
      url: `/api/v1/plugins/${pluginName}/execute`,
      method: 'POST',
      data: { action, parameters }
    })
  },

  /**
   * 安装插件
   */
  install(installData: {
    type: 'upload' | 'url' | 'market'
    file?: File
    url?: string
    auth?: { username: string; password: string }
    plugin?: any
    options?: {
      autoActivate?: boolean
      overwrite?: boolean
      verifySignature?: boolean
    }
  }) {
    if (installData.type === 'upload' && installData.file) {
      const formData = new FormData()
      formData.append('file', installData.file)
      
      if (installData.options) {
        formData.append('options', JSON.stringify(installData.options))
      }

      return request({
        url: '/api/v1/plugins/install',
        method: 'POST',
        data: formData,
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
    } else {
      return request({
        url: '/api/v1/plugins/install',
        method: 'POST',
        data: installData
      })
    }
  },

  /**
   * 卸载插件
   */
  uninstall(pluginName: string) {
    return request({
      url: `/api/v1/plugins/${pluginName}`,
      method: 'DELETE'
    })
  },

  /**
   * 获取插件类型列表
   */
  getTypes() {
    return request<string[]>({
      url: '/api/v1/plugins/types/available',
      method: 'GET'
    })
  },

  /**
   * 获取插件状态列表
   */
  getStatuses() {
    return request<string[]>({
      url: '/api/v1/plugins/status/available',
      method: 'GET'
    })
  },

  /**
   * 搜索插件市场
   */
  searchMarket(params: {
    keyword?: string
    category?: string
    page?: number
    pageSize?: number
  }) {
    return request({
      url: '/api/v1/plugins/market/search',
      method: 'GET',
      params
    })
  },

  /**
   * 获取插件市场详情
   */
  getMarketDetail(pluginId: string) {
    return request({
      url: `/api/v1/plugins/market/${pluginId}`,
      method: 'GET'
    })
  },

  /**
   * 从市场安装插件
   */
  installFromMarket(pluginId: string, options?: {
    autoActivate?: boolean
    overwrite?: boolean
  }) {
    return request({
      url: `/api/v1/plugins/market/${pluginId}/install`,
      method: 'POST',
      data: { options }
    })
  },

  /**
   * 获取插件日志
   */
  getLogs(pluginName: string, params?: {
    level?: string
    limit?: number
    offset?: number
  }) {
    return request({
      url: `/api/v1/plugins/${pluginName}/logs`,
      method: 'GET',
      params
    })
  },

  /**
   * 清空插件日志
   */
  clearLogs(pluginName: string) {
    return request({
      url: `/api/v1/plugins/${pluginName}/logs`,
      method: 'DELETE'
    })
  },

  /**
   * 获取插件统计信息
   */
  getStats() {
    return request({
      url: '/api/v1/plugins/stats',
      method: 'GET'
    })
  },

  /**
   * 导出插件配置
   */
  exportConfig(pluginName: string) {
    return request({
      url: `/api/v1/plugins/${pluginName}/export`,
      method: 'GET',
      responseType: 'blob'
    })
  },

  /**
   * 导入插件配置
   */
  importConfig(pluginName: string, configFile: File) {
    const formData = new FormData()
    formData.append('config', configFile)

    return request({
      url: `/api/v1/plugins/${pluginName}/import`,
      method: 'POST',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  /**
   * 验证插件
   */
  validate(pluginName: string) {
    return request({
      url: `/api/v1/plugins/${pluginName}/validate`,
      method: 'POST'
    })
  },

  /**
   * 获取插件依赖关系
   */
  getDependencies(pluginName: string) {
    return request({
      url: `/api/v1/plugins/${pluginName}/dependencies`,
      method: 'GET'
    })
  },

  /**
   * 检查插件更新
   */
  checkUpdates(pluginName?: string) {
    const url = pluginName 
      ? `/api/v1/plugins/${pluginName}/check-updates`
      : '/api/v1/plugins/check-updates'
    
    return request({
      url,
      method: 'GET'
    })
  },

  /**
   * 更新插件
   */
  update(pluginName: string, version?: string) {
    return request({
      url: `/api/v1/plugins/${pluginName}/update`,
      method: 'POST',
      data: { version }
    })
  },

  /**
   * 批量操作插件
   */
  batchOperation(operation: 'activate' | 'deactivate' | 'update' | 'uninstall', pluginNames: string[]) {
    return request({
      url: '/api/v1/plugins/batch',
      method: 'POST',
      data: { operation, plugins: pluginNames }
    })
  }
}
