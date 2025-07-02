#!/bin/bash

# 设置颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================"
echo -e "   RBAC权限管理系统 - 停止服务脚本"
echo -e "========================================${NC}"
echo

# 停止后端服务
if [ -f "backend.pid" ]; then
    BACKEND_PID=$(cat backend.pid)
    if ps -p $BACKEND_PID > /dev/null; then
        echo -e "${YELLOW}停止后端服务 (PID: $BACKEND_PID)...${NC}"
        kill $BACKEND_PID
        echo -e "${GREEN}✅ 后端服务已停止${NC}"
    else
        echo -e "${YELLOW}后端服务未运行${NC}"
    fi
    rm -f backend.pid
else
    echo -e "${YELLOW}未找到后端服务PID文件${NC}"
fi

# 停止前端服务
if [ -f "frontend.pid" ]; then
    FRONTEND_PID=$(cat frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null; then
        echo -e "${YELLOW}停止前端服务 (PID: $FRONTEND_PID)...${NC}"
        kill $FRONTEND_PID
        echo -e "${GREEN}✅ 前端服务已停止${NC}"
    else
        echo -e "${YELLOW}前端服务未运行${NC}"
    fi
    rm -f frontend.pid
else
    echo -e "${YELLOW}未找到前端服务PID文件${NC}"
fi

# 清理可能残留的进程
echo -e "${YELLOW}清理残留进程...${NC}"

# 查找并停止可能的Python进程（FastAPI）
PYTHON_PIDS=$(ps aux | grep "python.*main.py" | grep -v grep | awk '{print $2}')
if [ ! -z "$PYTHON_PIDS" ]; then
    echo -e "${YELLOW}发现残留的Python进程，正在停止...${NC}"
    echo $PYTHON_PIDS | xargs kill -9 2>/dev/null
fi

# 查找并停止可能的Node.js进程（Vue dev server）
NODE_PIDS=$(ps aux | grep "node.*vite" | grep -v grep | awk '{print $2}')
if [ ! -z "$NODE_PIDS" ]; then
    echo -e "${YELLOW}发现残留的Node.js进程，正在停止...${NC}"
    echo $NODE_PIDS | xargs kill -9 2>/dev/null
fi

echo
echo -e "${GREEN}========================================"
echo -e "🛑 所有服务已停止"
echo -e "========================================${NC}"
