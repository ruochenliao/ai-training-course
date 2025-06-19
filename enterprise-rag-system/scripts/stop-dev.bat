@echo off
setlocal enabledelayedexpansion

REM 企业级Agent+RAG知识库系统开发环境停止脚本

echo 🛑 停止企业级Agent+RAG知识库系统开发环境
echo ================================================

echo [INFO] 停止所有服务...
docker-compose down

echo [INFO] 清理未使用的容器和网络...
docker system prune -f

echo [INFO] 服务已停止

REM 询问是否清理数据
echo.
set /p cleanup="是否清理所有数据卷? 这将删除数据库数据 (y/N): "
if /i "!cleanup!"=="y" (
    echo [WARNING] 清理数据卷...
    docker-compose down -v
    docker volume prune -f
    echo [INFO] 数据卷已清理
) else (
    echo [INFO] 保留数据卷
)

echo.
echo [INFO] 开发环境已停止 ✅

pause
