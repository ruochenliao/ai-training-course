import React from 'react'
import ReactDOM from 'react-dom/client'
import {ConfigProvider, theme} from 'antd'
import zhCN from 'antd/locale/zh_CN'
import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'
import App from './App.tsx'
import '@/i18n/index.ts'

// 样式引入顺序 - 对应Vue版本的main.js样式引入顺序
import '@/styles/reset.css' // 1. CSS重置
import '@/styles/unocss-like.css' // 2. UnoCSS风格样式（对应uno.css）
import '@/styles/global.css' // 3. 全局样式
import '@/styles/chat.css' // 4. 聊天页面样式

// 设置dayjs为中文
dayjs.locale('zh-cn')

ReactDOM.createRoot(document.getElementById('root')!).render(
  <ConfigProvider
    locale={zhCN}
    theme={{
      algorithm: theme.defaultAlgorithm, // 使用默认算法，对应Vue版本的亮色主题
      token: {
        // 对应Vue版本theme.json的主题色彩
        colorPrimary: '#F4511E', // 主色调
        colorInfo: '#2080F0', // 信息色
        colorSuccess: '#18A058', // 成功色
        colorWarning: '#F0A020', // 警告色
        colorError: '#D03050', // 错误色
        borderRadius: 6, // 圆角
        fontSize: 14, // 字体大小
      },
    }}
  >
    <App />
  </ConfigProvider>,
)
