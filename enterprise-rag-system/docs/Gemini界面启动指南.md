# Gemini风格界面启动指南

## 概述

本指南将帮助您启动和使用企业级RAG知识库系统的Gemini风格用户界面。该界面基于React 18、TypeScript和Next.js构建，提供现代化的用户体验。

## 🚀 快速启动

### 1. 环境要求

确保您的系统满足以下要求：

- **Node.js**: 18.0+ 
- **pnpm**: 8.0+ (推荐) 或 npm 9.0+
- **操作系统**: Windows 10+, macOS 10.15+, Ubuntu 20.04+

### 2. 安装依赖

```bash
# 进入前端目录
cd enterprise-rag-system/frontend/user-app

# 安装依赖 (推荐使用pnpm)
pnpm install

# 或使用npm
npm install
```

### 3. 环境配置

创建环境变量文件：

```bash
# 复制环境变量模板
cp .env.example .env.local
```

编辑 `.env.local` 文件：

```env
# API服务地址
NEXT_PUBLIC_API_URL=http://localhost:8000

# WebSocket服务地址
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws

# 应用配置
NEXT_PUBLIC_APP_NAME=企业级RAG知识库系统
NEXT_PUBLIC_APP_VERSION=1.0.0
```

### 4. 启动开发服务器

```bash
# 启动开发服务器
pnpm dev

# 或使用npm
npm run dev
```

访问 http://localhost:3000 查看应用。

## 🎨 界面功能介绍

### 主要模块

#### 1. 智能对话 (Chat)
- **Gemini风格界面**: 仿Google Gemini的对话体验
- **多模态支持**: 文本、图片混合对话
- **流式响应**: 实时显示AI回复
- **消息管理**: 对话历史、导出、分享

**主要功能**：
- 发送文本消息
- 上传图片进行多模态对话
- 查看搜索结果和来源
- 复制、点赞、分享消息
- 新建对话和会话管理

#### 2. 多模式搜索 (Search)
- **语义搜索**: 基于Qwen2.5嵌入模型
- **图谱搜索**: Neo4j知识图谱查询
- **混合搜索**: BM25 + 语义检索融合

**搜索功能**：
- 三种搜索模式切换
- 高级过滤器配置
- 搜索结果排序和分组
- 结果详情查看和操作

#### 3. 知识图谱 (Graph)
- **D3.js可视化**: 交互式图谱展示
- **节点操作**: 拖拽、缩放、点击
- **图谱过滤**: 按类型和关系过滤
- **导出功能**: 图谱截图导出

**图谱特性**：
- 力导向布局算法
- 节点和边的动态渲染
- 实时数据更新
- 多种视图模式

#### 4. 数据分析 (Analytics)
- **使用统计**: 查询频率分析
- **性能监控**: 系统响应时间
- **用户行为**: 操作热力图
- **趋势分析**: 数据变化趋势

### 界面特性

#### 主题系统
- **深色/浅色主题**: 一键切换
- **自动跟随系统**: 根据系统偏好自动切换
- **Material Design 3**: 遵循最新设计规范
- **动态颜色**: 主题色彩动态调整

#### 响应式设计
- **桌面端**: 侧边栏导航，多列布局
- **平板端**: 可折叠侧边栏，自适应布局
- **移动端**: 抽屉导航，单列布局

#### 交互体验
- **流畅动画**: Framer Motion动画效果
- **即时反馈**: 所有操作都有视觉反馈
- **快捷键**: 完整的键盘快捷键支持
- **手势操作**: 移动端手势支持

## ⚙️ 配置选项

### 主题配置

在 `src/styles/themes.ts` 中自定义主题：

```typescript
export const customTheme: Theme = {
  colors: {
    primary: '#your-primary-color',
    secondary: '#your-secondary-color',
    // ... 其他颜色配置
  },
  // ... 其他主题配置
};
```

### API配置

在 `src/utils/api.ts` 中配置API客户端：

```typescript
const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  timeout: 30000,
  // ... 其他配置
});
```

### WebSocket配置

在组件中使用WebSocket：

```typescript
const { isConnected, sendMessage } = useWebSocket(
  '/api/v1/conversations/ws/conversation-id'
);
```

## 🔧 开发指南

### 项目结构

```
src/
├── app/                    # Next.js App Router
├── components/            # 可复用组件
│   ├── chat/              # 聊天组件
│   ├── search/            # 搜索组件
│   └── visualization/     # 可视化组件
├── contexts/              # React上下文
├── hooks/                 # 自定义Hooks
├── styles/                # 样式和主题
└── utils/                 # 工具函数
```

### 添加新组件

1. 在相应目录创建组件文件
2. 使用TypeScript定义Props接口
3. 实现组件逻辑和样式
4. 导出组件供其他模块使用

示例：

```typescript
interface MyComponentProps {
  title: string;
  onAction?: () => void;
}

export function MyComponent({ title, onAction }: MyComponentProps) {
  const { theme } = useTheme();
  
  return (
    <div style={{ color: theme.colors.onSurface }}>
      <h2>{title}</h2>
      <button onClick={onAction}>Action</button>
    </div>
  );
}
```

### 样式开发

使用Tailwind CSS和主题系统：

```tsx
<div 
  className="p-4 rounded-lg shadow-md"
  style={{ 
    backgroundColor: theme.colors.surface,
    borderColor: theme.colors.outline 
  }}
>
  Content
</div>
```

## 🧪 测试

### 运行测试

```bash
# 运行所有测试
pnpm test

# 运行测试并监听变化
pnpm test:watch

# 生成测试覆盖率报告
pnpm test:coverage
```

### 编写测试

```typescript
import { render, screen } from '@testing-library/react';
import { MyComponent } from './MyComponent';

test('renders component correctly', () => {
  render(<MyComponent title="Test Title" />);
  expect(screen.getByText('Test Title')).toBeInTheDocument();
});
```

## 📦 构建和部署

### 构建生产版本

```bash
# 构建生产版本
pnpm build

# 启动生产服务器
pnpm start
```

### Docker部署

```bash
# 构建Docker镜像
docker build -t rag-frontend .

# 运行容器
docker run -p 3000:3000 rag-frontend
```

### 环境变量

生产环境需要配置的环境变量：

```env
NEXT_PUBLIC_API_URL=https://your-api-domain.com
NEXT_PUBLIC_WS_URL=wss://your-api-domain.com/ws
NODE_ENV=production
```

## 🔍 故障排除

### 常见问题

#### 1. 依赖安装失败
```bash
# 清除缓存重新安装
rm -rf node_modules pnpm-lock.yaml
pnpm install
```

#### 2. 主题不生效
- 检查ThemeProvider是否正确包装应用
- 确认CSS变量是否正确设置
- 验证主题配置文件语法

#### 3. WebSocket连接失败
- 检查后端WebSocket服务是否启动
- 验证WebSocket URL配置
- 查看浏览器控制台错误信息

#### 4. 图谱可视化不显示
- 确认D3.js依赖是否正确安装
- 检查图谱数据格式是否正确
- 验证SVG容器是否正确渲染

### 调试技巧

1. **开启详细日志**：
```typescript
// 在开发环境启用详细日志
if (process.env.NODE_ENV === 'development') {
  console.log('Debug info:', data);
}
```

2. **使用React DevTools**：
安装React DevTools浏览器扩展进行组件调试

3. **网络请求调试**：
使用浏览器开发者工具的Network面板查看API请求

## 📞 技术支持

如果遇到问题，请：

1. 查看控制台错误信息
2. 检查网络请求状态
3. 验证环境配置
4. 参考项目文档
5. 提交Issue到项目仓库

## 🎉 开始使用

现在您已经了解了Gemini风格界面的基本使用方法，可以开始探索系统的强大功能了！

- 🤖 尝试与AI进行多模态对话
- 🔍 使用不同模式搜索知识库
- 🕸️ 探索知识图谱的关系网络
- 📊 查看系统使用统计和分析

祝您使用愉快！
