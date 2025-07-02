/**
 * Pinia状态管理入口文件
 */

import { createPinia } from 'pinia'

const pinia = createPinia()

export default pinia

// 导出所有store
export * from './auth'
export * from './user'
export * from './permission'
export * from './menu'
export * from './app'
