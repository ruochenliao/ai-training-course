# 环境
## 安装 pip, python 3.11
    brew install python

## 安装 fastapi 和 uvicorn
pip install fastapi uvicorn

## 安装 node

直接默认安装即可
# 后端管理系统
## 前端：
打开终端，进入006/admin/frontend目录
npm install
## 后端
打开终端，进入006/admin/backend目录
pip install -r requirements.txt

# 用户系统
## 前端：
打开终端，进入006/client/frontend目录
npm install
## 后端
打开终端，进入006/client/backend目录
pip install -r requirements.txt

2025-04-19之前的版本下载：
https://github.com/danwen-ai/development/releases


## 启动后端
cd vanna_update
python -m uvicorn app:app --reload --port 8000
Open your browser and navigate to http://localhost:8000/docs

## 启动前端
cd vanna_update
node server.js
Open your browser and navigate to http://localhost:9000