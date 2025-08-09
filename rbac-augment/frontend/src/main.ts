// Copyright (c) 2025 左岚. All rights reserved.

/**
 * 应用入口文件 - 完整重构版本
 */

import { createApp } from 'vue'
import type { App as VueApp } from 'vue'
import App from './App.vue'
import router from './router'
import pinia from './stores'
import i18n from './i18n'

// Element Plus
import ElementPlus from 'element-plus'
import type { ElementPlusOptions, ElementPlusLocale } from '@/types/element-plus'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import enUs from 'element-plus/dist/locale/en.mjs'

// 权限指令
import { setupPermissionDirectives } from '@/directives/permission'

// 环境变量工具
import { getEnvConfig } from '@/utils/env'

// 样式
import '@/styles/index.scss'

/**
 * 获取Element Plus语言包
 */
function getElementPlusLocale(): ElementPlusLocale {
  const language = localStorage.getItem('language') || 'zh-CN'
  return language === 'zh-CN' ? zhCn : enUs
}

/**
 * 配置Element Plus选项
 */
function getElementPlusOptions(): ElementPlusOptions {
  const envConfig = getEnvConfig()

  return {
    locale: getElementPlusLocale(),
    size: 'default',
    zIndex: 3000,
    namespace: 'el'
  }
}

/**
 * 注册Element Plus图标组件
 */
function registerElementPlusIcons(app: VueApp) {
  for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
    app.component(key, component)
  }
}

/**
 * 初始化应用
 */
function initializeApp(): VueApp {
  try {
    // 创建应用实例
    const app = createApp(App)

    // 注册Element Plus图标
    registerElementPlusIcons(app)

    // 使用插件
    app.use(pinia)
    app.use(router)
    app.use(i18n)

    // 配置Element Plus
    const elementPlusOptions = getElementPlusOptions()
    app.use(ElementPlus as any, elementPlusOptions)

    // 设置权限指令
    setupPermissionDirectives(app)

    // 挂载应用
    app.mount('#app')

    return app
  } catch (error) {
    console.error('应用初始化失败:', error)
    throw error
  }
}

/**
 * 全局类型声明
 */
declare global {
  interface Window {
    __APP__?: VueApp
  }
}

// 启动应用
const appInstance = initializeApp()

// 导出应用实例供调试使用
if (import.meta.env.DEV) {
  window.__APP__ = appInstance
}

export default appInstance
