import React from 'react'
import ReactDOM from 'react-dom/client'
import {ConfigProvider, theme} from 'antd'
import zhCN from 'antd/locale/zh_CN'
import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'
import App from './App.tsx'
import './i18n'
import './styles/global.css'
import 'virtual:uno.css'

// 设置dayjs为中文
dayjs.locale('zh-cn')

ReactDOM.createRoot(document.getElementById('root')!).render(
  <ConfigProvider 
    locale={zhCN}
    theme={{
      algorithm: theme.darkAlgorithm,
      token: {
        colorPrimary: '#6366f1',
        colorInfo: '#6366f1',
        colorSuccess: '#22c55e',
        colorWarning: '#f59e0b',
        colorError: '#ef4444',
        borderRadius: 8,
      }
    }}
  >
    <App />
  </ConfigProvider>,
)