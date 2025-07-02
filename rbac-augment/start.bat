@echo off
chcp 65001 >nul
echo ========================================
echo    RBAC权限管理系统 - 快速启动脚本
echo ========================================
echo.

echo [1/4] 检查Python环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python未安装或未添加到PATH
    echo 请先安装Python 3.11+
    pause
    exit /b 1
)
echo ✅ Python环境检查通过

echo.
echo [2/4] 检查Node.js环境...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js未安装或未添加到PATH
    echo 请先安装Node.js 18+
    pause
    exit /b 1
)
echo ✅ Node.js环境检查通过

echo.
echo [3/4] 启动后端服务...
cd backend
if not exist venv (
    echo 创建Python虚拟环境...
    python -m venv venv
)

echo 激活虚拟环境...
call venv\Scripts\activate

echo 安装Python依赖...
pip install -r requirements.txt

echo 初始化数据库...
python init_db.py

echo 启动FastAPI服务器...
start "RBAC Backend" cmd /k "python main.py"

cd ..

echo.
echo [4/4] 启动前端服务...
cd frontend

if not exist node_modules (
    echo 安装前端依赖...
    npm install
)

echo 启动Vue开发服务器...
start "RBAC Frontend" cmd /k "npm run dev"

cd ..

echo.
echo ========================================
echo 🚀 服务启动完成！
echo.
echo 📍 后端服务: http://localhost:8000
echo 📍 前端服务: http://localhost:5173
echo 📍 API文档: http://localhost:8000/docs
echo.
echo 📋 演示账户:
echo    超级管理员: admin / admin123
echo    系统管理员: manager / manager123
echo    普通用户: user / user123
echo ========================================
echo.
echo 按任意键退出...
pause >nul
