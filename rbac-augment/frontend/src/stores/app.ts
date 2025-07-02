/**
 * 应用状态管理
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import { storage } from '@/utils/storage'
import type { ComponentSize, ThemeMode, Language } from '@/types'

export const useAppStore = defineStore('app', () => {
  // 状态
  const sidebarCollapsed = ref<boolean>(storage.get('sidebarCollapsed') || false)
  const componentSize = ref<ComponentSize>(storage.get('componentSize') || 'default')
  const themeMode = ref<ThemeMode>(storage.get('themeMode') || 'light')
  const language = ref<Language>(storage.get('language') || 'zh-CN')
  const loading = ref<boolean>(false)

  /**
   * 切换侧边栏折叠状态
   */
  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
    storage.set('sidebarCollapsed', sidebarCollapsed.value)
  }

  /**
   * 设置组件尺寸
   */
  function setComponentSize(size: ComponentSize) {
    componentSize.value = size
    storage.set('componentSize', size)
  }

  /**
   * 设置主题模式
   */
  function setThemeMode(mode: ThemeMode) {
    themeMode.value = mode
    storage.set('themeMode', mode)
    
    // 应用主题
    if (mode === 'dark') {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }

  /**
   * 设置语言
   */
  function setLanguage(lang: Language) {
    language.value = lang
    storage.set('language', lang)
  }

  /**
   * 设置加载状态
   */
  function setLoading(isLoading: boolean) {
    loading.value = isLoading
  }

  /**
   * 初始化应用设置
   */
  function initApp() {
    // 应用主题
    setThemeMode(themeMode.value)
  }

  return {
    // 状态
    sidebarCollapsed,
    componentSize,
    themeMode,
    language,
    loading,
    
    // 方法
    toggleSidebar,
    setComponentSize,
    setThemeMode,
    setLanguage,
    setLoading,
    initApp
  }
})
