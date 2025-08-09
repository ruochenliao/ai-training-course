/**
 * 国际化配置
 */

import { createI18n } from 'vue-i18n'
import { storage } from '@/utils/storage'

// 导入语言包
import zhCN from './locales/zh-CN'
import enUS from './locales/en-US'

// 获取当前语言
const currentLanguage = storage.get('language') || 'zh-CN'

// 创建i18n实例
const i18n = createI18n({
  legacy: false, // 使用组合式API
  globalInjection: true, // 全局注入 $t 函数
  locale: currentLanguage,
  fallbackLocale: 'zh-CN', // 回退语言
  messages: {
    'zh-CN': zhCN,
    'en-US': enUS
  }
})

export default i18n