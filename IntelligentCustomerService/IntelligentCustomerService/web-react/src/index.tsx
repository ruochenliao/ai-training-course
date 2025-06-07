import React from 'react';
import {createRoot} from 'react-dom/client';
import App from './App';
import './index.css';

// 获取根元素
const container = document.getElementById('root');
if (!container) {
  throw new Error('Root element not found');
}

// 创建 React 根实例
const root = createRoot(container);

// 渲染应用
root.render(
  <App />
);

// 如果你想开始测量应用的性能，可以传递一个函数
// 来记录结果（例如：reportWebVitals(console.log)）
// 或发送到分析端点。了解更多：https://bit.ly/CRA-vitals
// reportWebVitals();