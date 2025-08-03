/**
 * 工作流管理API
 */

import request from './request'
import type { ApiResponse } from './request'
import { API_PATHS } from './baseUrl'

// 工作流节点接口
export interface WorkflowNode {
  id: string
  type: string
  name: string
  x: number
  y: number
  width?: number
  height?: number
  config: Record<string, any>
  inputs?: Array<{
    name: string
    type: string
    required?: boolean
  }>
  outputs?: Array<{
    name: string
    type: string
  }>
}

// 工作流连接接口
export interface WorkflowConnection {
  id: string
  sourceNodeId: string
  sourceOutput: string
  targetNodeId: string
  targetInput: string
  config?: Record<string, any>
}

// 工作流接口
export interface Workflow {
  id?: string
  name: string
  description?: string
  version?: string
  status: 'draft' | 'active' | 'inactive' | 'error'
  nodes: WorkflowNode[]
  connections: WorkflowConnection[]
  config?: Record<string, any>
  createdAt?: string
  updatedAt?: string
}

// 工作流模板接口
export interface WorkflowTemplate {
  id: string
  name: string
  description: string
  category: string
  workflow: Workflow
  preview?: string
}

// 验证结果接口
export interface ValidationResult {
  type: 'error' | 'warning' | 'info'
  message: string
  nodeId?: string
  connectionId?: string
}

export const workflowApi = {
  /**
   * 获取工作流列表
   */
  getList(params?: {
    status?: string
    keyword?: string
    page?: number
    pageSize?: number
  }) {
    return request<{
      items: Workflow[]
      total: number
      page: number
      pageSize: number
    }>({
      url: '/api/v1/workflows',
      method: 'GET',
      params
    })
  },

  /**
   * 获取工作流详情
   */
  getDetail(id: string) {
    return request<Workflow>({
      url: `/api/v1/workflows/${id}`,
      method: 'GET'
    })
  },

  /**
   * 创建工作流
   */
  create(workflow: Omit<Workflow, 'id'>) {
    return request<Workflow>({
      url: '/api/v1/workflows',
      method: 'POST',
      data: workflow
    })
  },

  /**
   * 更新工作流
   */
  update(id: string, workflow: Partial<Workflow>) {
    return request<Workflow>({
      url: `/api/v1/workflows/${id}`,
      method: 'PUT',
      data: workflow
    })
  },

  /**
   * 删除工作流
   */
  delete(id: string) {
    return request({
      url: `/api/v1/workflows/${id}`,
      method: 'DELETE'
    })
  },

  /**
   * 验证工作流
   */
  validate(workflow: Workflow) {
    return request<ValidationResult[]>({
      url: '/api/v1/workflows/validate',
      method: 'POST',
      data: workflow
    })
  },

  /**
   * 部署工作流
   */
  deploy(id: string) {
    return request({
      url: `/api/v1/workflows/${id}/deploy`,
      method: 'POST'
    })
  },

  /**
   * 停止工作流
   */
  stop(id: string) {
    return request({
      url: `/api/v1/workflows/${id}/stop`,
      method: 'POST'
    })
  },

  /**
   * 执行工作流
   */
  execute(id: string, inputs?: Record<string, any>) {
    return request({
      url: `/api/v1/workflows/${id}/execute`,
      method: 'POST',
      data: { inputs }
    })
  },

  /**
   * 获取工作流执行历史
   */
  getExecutionHistory(id: string, params?: {
    page?: number
    pageSize?: number
  }) {
    return request({
      url: `/api/v1/workflows/${id}/executions`,
      method: 'GET',
      params
    })
  },

  /**
   * 获取工作流模板列表
   */
  getTemplates(params?: {
    category?: string
    keyword?: string
  }) {
    return request<WorkflowTemplate[]>({
      url: '/api/v1/workflow-templates',
      method: 'GET',
      params
    })
  },

  /**
   * 从模板创建工作流
   */
  createFromTemplate(templateId: string, name: string) {
    return request<Workflow>({
      url: '/api/v1/workflow-templates/create',
      method: 'POST',
      data: { templateId, name }
    })
  },

  /**
   * 导出工作流
   */
  export(id: string) {
    return request({
      url: `/api/v1/workflows/${id}/export`,
      method: 'GET',
      responseType: 'blob'
    })
  },

  /**
   * 导入工作流
   */
  import(file: File) {
    const formData = new FormData()
    formData.append('file', file)

    return request<Workflow>({
      url: '/api/v1/workflows/import',
      method: 'POST',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  /**
   * 获取可用节点类型
   */
  getNodeTypes() {
    return request<Array<{
      type: string
      name: string
      category: string
      description: string
      icon?: string
      inputs?: Array<{
        name: string
        type: string
        required?: boolean
      }>
      outputs?: Array<{
        name: string
        type: string
      }>
      config?: Record<string, any>
    }>>({
      url: '/api/v1/workflow-nodes/types',
      method: 'GET'
    })
  },

  /**
   * 获取工作流统计信息
   */
  getStats() {
    return request({
      url: '/api/v1/workflows/stats',
      method: 'GET'
    })
  }
}
