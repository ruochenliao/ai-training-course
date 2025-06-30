// 知识库状态管理

import { create } from 'zustand'
import { knowledgeApi, type KnowledgeBase, type KnowledgeBaseCreateRequest } from '@/api/knowledge'
import { message } from 'antd'

export interface KnowledgeState {
  // 状态
  knowledgeBases: KnowledgeBase[]
  currentKnowledgeBase: KnowledgeBase | null
  loading: boolean
  total: number
  page: number
  size: number
  
  // 操作
  fetchKnowledgeBases: (params?: any) => Promise<void>
  createKnowledgeBase: (data: KnowledgeBaseCreateRequest) => Promise<boolean>
  updateKnowledgeBase: (id: number, data: any) => Promise<boolean>
  deleteKnowledgeBase: (id: number) => Promise<boolean>
  setCurrentKnowledgeBase: (kb: KnowledgeBase | null) => void
  setLoading: (loading: boolean) => void
  resetState: () => void
}

export const useKnowledgeStore = create<KnowledgeState>((set, get) => ({
  // 初始状态
  knowledgeBases: [],
  currentKnowledgeBase: null,
  loading: false,
  total: 0,
  page: 1,
  size: 20,

  // 获取知识库列表
  fetchKnowledgeBases: async (params = {}) => {
    try {
      set({ loading: true })
      
      const response = await knowledgeApi.getKnowledgeBases({
        page: get().page,
        size: get().size,
        ...params
      })
      
      if (response.data) {
        set({
          knowledgeBases: response.data.items,
          total: response.data.total,
          page: response.data.page,
          size: response.data.size,
          loading: false
        })
      }
    } catch (error: any) {
      set({ loading: false })
      message.error(error.response?.data?.message || '获取知识库列表失败')
    }
  },

  // 创建知识库
  createKnowledgeBase: async (data: KnowledgeBaseCreateRequest) => {
    try {
      set({ loading: true })
      
      const response = await knowledgeApi.createKnowledgeBase(data)
      
      if (response.data) {
        // 重新获取列表
        await get().fetchKnowledgeBases()
        message.success('知识库创建成功')
        set({ loading: false })
        return true
      }
      
      set({ loading: false })
      return false
    } catch (error: any) {
      set({ loading: false })
      message.error(error.response?.data?.message || '创建知识库失败')
      return false
    }
  },

  // 更新知识库
  updateKnowledgeBase: async (id: number, data: any) => {
    try {
      set({ loading: true })
      
      const response = await knowledgeApi.updateKnowledgeBase(id, data)
      
      if (response.data) {
        // 更新本地状态
        const knowledgeBases = get().knowledgeBases.map(kb =>
          kb.id === id ? { ...kb, ...response.data } : kb
        )
        
        set({
          knowledgeBases,
          currentKnowledgeBase: get().currentKnowledgeBase?.id === id 
            ? { ...get().currentKnowledgeBase, ...response.data }
            : get().currentKnowledgeBase,
          loading: false
        })
        
        message.success('知识库更新成功')
        return true
      }
      
      set({ loading: false })
      return false
    } catch (error: any) {
      set({ loading: false })
      message.error(error.response?.data?.message || '更新知识库失败')
      return false
    }
  },

  // 删除知识库
  deleteKnowledgeBase: async (id: number) => {
    try {
      set({ loading: true })
      
      await knowledgeApi.deleteKnowledgeBase(id)
      
      // 从本地状态中移除
      const knowledgeBases = get().knowledgeBases.filter(kb => kb.id !== id)
      
      set({
        knowledgeBases,
        currentKnowledgeBase: get().currentKnowledgeBase?.id === id 
          ? null 
          : get().currentKnowledgeBase,
        total: get().total - 1,
        loading: false
      })
      
      message.success('知识库删除成功')
      return true
    } catch (error: any) {
      set({ loading: false })
      message.error(error.response?.data?.message || '删除知识库失败')
      return false
    }
  },

  // 设置当前知识库
  setCurrentKnowledgeBase: (kb: KnowledgeBase | null) => {
    set({ currentKnowledgeBase: kb })
  },

  // 设置加载状态
  setLoading: (loading: boolean) => {
    set({ loading })
  },

  // 重置状态
  resetState: () => {
    set({
      knowledgeBases: [],
      currentKnowledgeBase: null,
      loading: false,
      total: 0,
      page: 1,
      size: 20
    })
  }
}))
