<h2 align="center">
AnythingChat
</h2>
<img width="1041" alt="anythingchat" src="https://github.com/user-attachments/assets/b6ee6a78-5d37-496d-ae10-ce18eee7a1d6">
<h3 align="center">
智能对话平台 - 轻松管理和监控您的AI应用
</h3>

# 关于项目

AnythingChat 是一个开源的 React+Next.js 智能对话应用，旨在为开发者提供一个易于使用的界面来管理和交互他们的AI对话系统。该平台致力于通过提供用户友好的环境来减少开发和迭代时间。

## 核心功能

- **🗂️ 文档管理**: 上传、更新和删除文档及其元数据
- **🛝 对话体验**: 支持多种模型的流式对话响应和可配置设置
- **📊 数据分析**: 查看延迟和指标的聚合统计信息及详细直方图
- **📜 日志记录**: 跟踪用户查询、搜索结果和AI响应
- **🔧 开发工具**: 轻松启动开发服务器、格式化代码和运行检查


# 快速安装

### Install PNPM

PNPM is a fast, disk space-efficient package manager that helps you manage your project dependencies. To install PNPM, visit the [official PNPM installation page](https://pnpm.io/installation) for the latest instructions, or follow the instructions outlined below:

<details>
<summary>PNPM Installation</summary>

For Unix-based systems (Linux, macOS):

```bash
curl -fsSL https://get.pnpm.io/install.sh | sh -
```

For Windows:

```powershell
iwr https://get.pnpm.io/install.ps1 -useb | iex
```

After installing PNPM, you may need to add it to your system's PATH. Follow the instructions provided on the PNPM installation page to ensure it's properly set up.

</details>

1. **Install the project dependencies using PNPM:**

   ```bash
   pnpm install
   ```

2. **Build and start the application for production:**

   ```bash
   pnpm build
   pnpm start
   ```

This will build the application on port 3000. After `pnpm start` runs successfully, the dashboard can be viewed at [http://localhost:3000](http://localhost:3000).

### Developing with the Dashboard

If you'd like to develop the dashboard, you can do so by starting a development server:

1. **Start the development server:**

   ```bash
   pnpm dev
   ```

2. **Pre-commit checks (optional but recommended):**

   Ensure your code is properly formatted and free of linting issues before committing:

   ```bash
   pnpm format
   pnpm lint
   ```
