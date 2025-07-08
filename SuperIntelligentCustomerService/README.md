<p align="center">
  <a href="#">
    <img alt="超级智能客服 Logo" width="200" src="./deploy/sample-picture/logo.svg">
  </a>
</p>

<h1 align="center">超级智能客服</h1>

[English](README-en.md) | 简体中文

基于 FastAPI + Vue3 + Naive UI 的现代化超级智能客服系统，融合了 RBAC 权限管理、动态路由和 JWT 鉴权，为企业提供全面的智能客服解决方案。

### 特性
- **最流行技术栈**：基于 Python 3.11 和 FastAPI 高性能异步框架，结合 Vue3 和 Vite 等前沿技术进行开发，同时使用高效的 npm 包管理器 pnpm。
- **代码规范**：项目内置丰富的规范插件，确保代码质量和一致性，有效提高团队协作效率。
- **动态路由**：后端动态路由，结合 RBAC（Role-Based Access Control）权限模型，提供精细的菜单路由控制。
- **JWT鉴权**：使用 JSON Web Token（JWT）进行身份验证和授权，增强应用的安全性。
- **细粒度权限控制**：实现按钮和接口级别的权限控制，确保不同用户或角色在界面操作和接口访问时具有不同的权限限制。

### 在线预览
- http://47.111.145.81:3000
- username: admin
- password: 123456

### 登录页

![image](./deploy/sample-picture/login.jpg)
### 工作台

![image](./deploy/sample-picture/workbench.jpg)

### 用户管理

![image](./deploy/sample-picture/user.jpg)
### 角色管理

![image](./deploy/sample-picture/role.jpg)

### 菜单管理

![image](./deploy/sample-picture/menu.jpg)

### API管理

![image](./deploy/sample-picture/api.jpg)

### 快速开始
#### 方法一：dockerhub拉取镜像

```sh
docker pull mizhexiaoxiao/SuperIntelligentCustomerService:latest 
docker run -d --restart=always --name=SuperIntelligentCustomerService -p 9999:80 mizhexiaoxiao/SuperIntelligentCustomerService
```

#### 方法二：dockerfile构建镜像
##### docker安装(版本17.05+)

```sh
yum install -y docker-ce
systemctl start docker
```

##### 构建镜像

```sh
git clone https://github.com/your-repo/SuperIntelligentCustomerService.git
cd SuperIntelligentCustomerService
docker build --no-cache . -t SuperIntelligentCustomerService
```

##### 启动容器

```sh
docker run -d --restart=always --name=SuperIntelligentCustomerService -p 9999:80 SuperIntelligentCustomerService
```

##### 访问

http://localhost:9999

username：admin

password：123456

### 本地启动
#### 后端
启动项目需要以下环境：
- Python 3.11

#### 方法一（推荐）：使用 uv 安装依赖
1. 安装 uv
```sh
pip install uv
```

2. 创建并激活虚拟环境
```sh
uv venv
source .venv/bin/activate  # Linux/Mac
# 或
.\.venv\Scripts\activate  # Windows
```

3. 安装依赖
```sh
uv add pyproject.toml
```

4. 启动服务
```sh
python run.py
```

#### 方法二：使用 Pip 安装依赖
1. 创建虚拟环境
```sh
python3 -m venv venv
```

2. 激活虚拟环境
```sh
source venv/bin/activate  # Linux/Mac
# 或
.\venv\Scripts\activate  # Windows
```

3. 安装依赖
```sh
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

4. 启动服务
```sh
python run.py
```

服务现在应该正在运行，访问 http://localhost:9999/docs 查看API文档

#### 前端
启动项目需要以下环境：
- node v18.8.0+

1. 进入前端目录
```sh
cd admin_web
```

2. 安装依赖(建议使用pnpm: https://pnpm.io/zh/installation)
```sh
npm i -g pnpm # 已安装可忽略
pnpm i # 或者 npm i
```

3. 启动
```sh
pnpm dev
```

### 目录说明

```
├── app                   // 应用程序目录
│   ├── api               // API接口目录
│   │   └── v1            // 版本1的API接口
│   │       ├── apis      // API相关接口
│   │       ├── base      // 基础信息接口
│   │       ├── menus     // 菜单相关接口
│   │       ├── roles     // 角色相关接口
│   │       └── users     // 用户相关接口
│   ├── controllers       // 控制器目录
│   ├── core              // 核心功能模块
│   ├── log               // 日志目录
│   ├── models            // 数据模型目录
│   ├── schemas           // 数据模式/结构定义
│   ├── settings          // 配置设置目录
│   └── utils             // 工具类目录
├── deploy                // 部署相关目录
│   └── sample-picture    // 示例图片目录
└── web                   // 前端网页目录
    ├── build             // 构建脚本和配置目录
    │   ├── config        // 构建配置
    │   ├── plugin        // 构建插件
    │   └── script        // 构建脚本
    ├── public            // 公共资源目录
    │   └── resource      // 公共资源文件
    ├── settings          // 前端项目配置
    └── src               // 源代码目录
        ├── api           // API接口定义
        ├── assets        // 静态资源目录
        │   ├── images    // 图片资源
        │   ├── js        // JavaScript文件
        │   └── svg       // SVG矢量图文件
        ├── components    // 组件目录
        │   ├── common    // 通用组件
        │   ├── icon      // 图标组件
        │   ├── page      // 页面组件
        │   ├── query-bar // 查询栏组件
        │   └── table     // 表格组件
        ├── composables   // 可组合式功能块
        ├── directives    // 指令目录
        ├── layout        // 布局目录
        │   └── components // 布局组件
        ├── router        // 路由目录
        │   ├── guard     // 路由守卫
        │   └── routes    // 路由定义
        ├── store         // 状态管理(pinia)
        │   └── modules   // 状态模块
        ├── styles        // 样式文件目录
        ├── utils         // 工具类目录
        │   ├── auth      // 认证相关工具
        │   ├── common    // 通用工具
        │   ├── http      // 封装axios
        │   └── storage   // 封装localStorage和sessionStorage
        └── views         // 视图/页面目录
            ├── error-page // 错误页面
            ├── login      // 登录页面
            ├── profile    // 个人资料页面
            ├── system     // 系统管理页面
            └── workbench  // 工作台页面
```

### 技术支持
如果您在使用超级智能客服系统过程中遇到任何问题，欢迎提交Issue或联系技术支持团队。

我们致力于为用户提供最优质的智能客服解决方案。

## 定制开发
如果有基于该项目的定制需求或其他合作，请添加下方微信，备注来意

<img width="300" src="https://gitee.com/mizhexiaoxiao/vue-fastapi-admin/raw/main/deploy/sample-picture/3.jpg">

### Visitors Count

<img align="left" src = "https://profile-counter.glitch.me/vue-fastapi-admin/count.svg" alt="Loading">
