# 智能客服系统前端

基于 React + TypeScript + Ant Design 构建的现代化智能客服系统前端应用。

## 🚀 特性

- ⚡️ **现代技术栈**: React 18 + TypeScript + Vite
- 🎨 **UI 组件库**: Ant Design 5.x
- 🌍 **国际化**: 支持中英文切换
- 📱 **响应式设计**: 适配桌面端和移动端
- 🔐 **权限管理**: 基于角色的访问控制
- 📊 **数据可视化**: 丰富的图表和统计功能
- 🔄 **状态管理**: Zustand + React Query
- 🎯 **路由管理**: React Router 6
- 🛠️ **开发工具**: ESLint + Prettier + TypeScript

## 📦 技术栈

### 核心框架
- **React 18** - 用户界面库
- **TypeScript** - 类型安全的 JavaScript
- **Vite** - 快速的构建工具

### UI 和样式
- **Ant Design** - 企业级 UI 设计语言
- **@ant-design/icons** - 图标库

### 状态管理
- **Zustand** - 轻量级状态管理
- **@tanstack/react-query** - 服务端状态管理

### 路由和导航
- **React Router** - 声明式路由

### 国际化
- **react-i18next** - React 国际化框架
- **i18next** - 国际化框架

### 工具库
- **axios** - HTTP 客户端
- **dayjs** - 日期处理库

## 🏗️ 项目结构

```
src/
├── api/                    # API 接口
│   ├── auth.ts            # 认证相关接口
│   ├── user.ts            # 用户管理接口
│   ├── role.ts            # 角色管理接口
│   ├── permission.ts      # 权限管理接口
│   ├── customerService.ts # 客服相关接口
│   ├── analytics.ts       # 分析统计接口
│   └── settings.ts        # 系统设置接口
├── components/             # 通用组件
│   ├── auth/              # 认证相关组件
│   ├── common/            # 通用组件
│   └── layout/            # 布局组件
├── contexts/              # React Context
│   ├── AuthContext.tsx   # 认证上下文
│   └── ThemeContext.tsx  # 主题上下文
├── hooks/                 # 自定义 Hooks
│   ├── useAuth.ts        # 认证 Hook
│   ├── useRequest.ts     # 请求 Hook
│   └── usePermission.ts  # 权限 Hook
├── i18n/                  # 国际化
│   ├── locales/          # 语言包
│   └── index.ts          # 国际化配置
├── pages/                 # 页面组件
│   ├── system/           # 系统管理页面
│   ├── Dashboard.tsx     # 仪表板
│   ├── CustomerService.tsx # 客服页面
│   ├── Analytics.tsx     # 分析页面
│   ├── Login.tsx         # 登录页面
│   ├── Profile.tsx       # 个人资料
│   └── NotFound.tsx      # 404 页面
├── router/                # 路由配置
│   └── index.tsx         # 路由定义
├── store/                 # 状态管理
│   ├── auth.ts           # 认证状态
│   ├── theme.ts          # 主题状态
│   └── user.ts           # 用户状态
├── types/                 # TypeScript 类型定义
│   ├── auth.ts           # 认证类型
│   ├── user.ts           # 用户类型
│   └── api.ts            # API 类型
├── utils/                 # 工具函数
│   ├── request.ts        # HTTP 请求封装
│   ├── auth.ts           # 认证工具
│   ├── storage.ts        # 存储工具
│   └── constants.ts      # 常量定义
├── App.tsx               # 应用根组件
├── main.tsx              # 应用入口
└── vite-env.d.ts         # Vite 类型定义
```

## 🚀 快速开始

### 环境要求

- Node.js >= 16.0.0
- npm >= 8.0.0 或 yarn >= 1.22.0

### 安装依赖

```bash
# 使用 npm
npm install

# 或使用 yarn
yarn install
```

### 启动开发服务器

```bash
# 使用 npm
npm run dev

# 或使用 yarn
yarn dev
```

应用将在 http://localhost:5173 启动

### 构建生产版本

```bash
# 使用 npm
npm run build

# 或使用 yarn
yarn build
```

### 预览生产版本

```bash
# 使用 npm
npm run preview

# 或使用 yarn
yarn preview
```

## 🛠️ 开发工具

### 代码检查

```bash
# 运行 ESLint
npm run lint

# 自动修复 ESLint 错误
npm run lint:fix
```

### 代码格式化

```bash
# 格式化代码
npm run format
```

### 类型检查

```bash
# TypeScript 类型检查
npm run type-check
```

## 📝 开发指南

### 添加新页面

1. 在 `src/pages/` 目录下创建新的页面组件
2. 在 `src/router/index.tsx` 中添加路由配置
3. 如需要权限控制，在路由配置中添加权限检查

### 添加新的 API 接口

1. 在 `src/api/` 目录下创建或修改相应的 API 文件
2. 定义 TypeScript 接口类型
3. 使用 `src/utils/request.ts` 中的请求封装

### 添加新的组件

1. 在 `src/components/` 相应目录下创建组件
2. 遵循组件命名规范（PascalCase）
3. 添加 TypeScript 类型定义
4. 编写组件文档和示例

### 国际化

1. 在 `src/i18n/locales/` 目录下添加翻译文件
2. 使用 `useTranslation` Hook 进行翻译
3. 遵循命名空间规范

## 🔧 配置

### 环境变量

创建 `.env.local` 文件配置环境变量：

```env
# API 基础地址
VITE_API_BASE_URL=http://localhost:3001/api

# WebSocket 地址
VITE_WS_URL=ws://localhost:3001

# 应用标题
VITE_APP_TITLE=智能客服系统
```

### Vite 配置

在 `vite.config.ts` 中可以配置：
- 路径别名
- 代理设置
- 构建选项
- 插件配置

## 📚 主要功能模块

### 1. 认证系统
- 用户登录/登出
- JWT Token 管理
- 权限验证
- 路由守卫

### 2. 用户管理
- 用户列表
- 用户创建/编辑
- 用户权限管理
- 用户状态管理

### 3. 角色权限
- 角色管理
- 权限分配
- 权限树结构
- 动态权限控制

### 4. 客服系统
- 实时聊天
- 会话管理
- 消息历史
- 文件传输

### 5. 数据分析
- 统计图表
- 数据报表
- 实时监控
- 导出功能

### 6. 系统设置
- 基础配置
- 邮件设置
- 存储配置
- 系统监控

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🆘 支持

如果您遇到任何问题或有任何建议，请：

1. 查看 [常见问题](docs/FAQ.md)
2. 搜索现有的 [Issues](../../issues)
3. 创建新的 [Issue](../../issues/new)

## 🔗 相关链接

- [React 官方文档](https://react.dev/)
- [TypeScript 官方文档](https://www.typescriptlang.org/)
- [Ant Design 官方文档](https://ant.design/)
- [Vite 官方文档](https://vitejs.dev/)
- [React Router 官方文档](https://reactrouter.com/)

- **前端框架**: React 18 + TypeScript
- **构建工具**: Vite
- **UI组件库**: Ant Design 5
- **状态管理**: Zustand
- **路由管理**: React Router v6
- **HTTP客户端**: Axios
- **国际化**: react-i18next
- **样式方案**: UnoCSS + CSS Modules
- **代码规范**: ESLint + Prettier
- **包管理器**: npm/yarn/pnpm

## 项目结构

```
src/
├── api/                 # API接口
├── assets/             # 静态资源
├── components/         # 通用组件
│   ├── auth/          # 认证相关组件
│   └── layout/        # 布局组件
├── hooks/             # 自定义Hooks
├── i18n/              # 国际化配置
├── pages/             # 页面组件
├── store/             # 状态管理
├── styles/            # 全局样式
├── types/             # TypeScript类型定义
├── utils/             # 工具函数
├── App.tsx            # 根组件
└── main.tsx           # 应用入口
```

## 开发指南

### 环境要求

- Node.js >= 16.0.0
- npm >= 8.0.0 或 yarn >= 1.22.0

### 安装依赖

```bash
npm install
# 或
yarn install
# 或
pnpm install
```

### 启动开发服务器

```bash
npm run dev
# 或
yarn dev
# 或
pnpm dev
```

访问 http://localhost:3000

### 构建生产版本

```bash
npm run build
# 或
yarn build
# 或
pnpm build
```

### 代码检查和格式化

```bash
# ESLint检查
npm run lint

# ESLint自动修复
npm run lint:fix

# Prettier格式化
npm run format

# Prettier检查
npm run format:check

# TypeScript类型检查
npm run type-check
```

## 功能特性

### 已实现功能

- ✅ 项目基础架构搭建
- ✅ 用户认证系统
- ✅ 路由权限控制
- ✅ 响应式布局
- ✅ 主题切换（明暗模式）
- ✅ 国际化支持
- ✅ 状态管理
- ✅ HTTP请求封装
- ✅ 基础仪表盘

### 待实现功能

- ⏳ 客服会话管理
- ⏳ 知识库管理
- ⏳ 数据分析报表
- ⏳ 用户权限管理
- ⏳ 系统设置
- ⏳ 文件上传下载
- ⏳ 实时消息推送
- ⏳ 移动端适配

## 开发规范

### 代码风格

- 使用TypeScript进行类型检查
- 遵循ESLint和Prettier配置
- 组件使用函数式组件 + Hooks
- 使用命名导出而非默认导出（除页面组件外）

### 文件命名

- 组件文件使用PascalCase：`UserProfile.tsx`
- 工具函数使用camelCase：`formatDate.ts`
- 常量文件使用UPPER_CASE：`API_ENDPOINTS.ts`
- 样式文件使用kebab-case：`user-profile.css`

### 组件开发

- 组件props使用interface定义类型
- 使用React.FC类型注解
- 合理使用useMemo和useCallback优化性能
- 组件内部状态优先使用useState
- 全局状态使用Zustand

### API接口

- 统一使用封装的request函数
- API接口按模块分类
- 使用TypeScript定义请求和响应类型
- 统一错误处理

## 部署说明

### 开发环境

1. 确保后端API服务运行在 http://localhost:8000
2. 启动前端开发服务器：`npm run dev`
3. 访问 http://localhost:3000

### 生产环境

1. 构建生产版本：`npm run build`
2. 将dist目录部署到Web服务器
3. 配置Nginx反向代理API请求

### Docker部署

```bash
# 构建镜像
docker build -t intelligent-customer-service-react .

# 运行容器
docker run -p 3000:80 intelligent-customer-service-react
```

## 贡献指南

1. Fork项目
2. 创建功能分支：`git checkout -b feature/new-feature`
3. 提交更改：`git commit -am 'Add new feature'`
4. 推送分支：`git push origin feature/new-feature`
5. 创建Pull Request

## 许可证

MIT License

## 更新日志

### v1.0.0 (2024-01-15)

- 初始版本发布
- 完成基础架构搭建
- 实现用户认证和权限控制
- 添加响应式布局和主题切换
- 集成国际化支持

## 联系方式

如有问题或建议，请联系开发团队。