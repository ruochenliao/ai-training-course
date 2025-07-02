#!/bin/bash

# 设置颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================"
echo -e "   RBAC权限管理系统 - 快速启动脚本"
echo -e "========================================${NC}"
echo

# 检查Python环境
echo -e "${YELLOW}[1/4] 检查Python环境...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3未安装或未添加到PATH${NC}"
    echo -e "${RED}请先安装Python 3.11+${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python环境检查通过${NC}"

echo
# 检查Node.js环境
echo -e "${YELLOW}[2/4] 检查Node.js环境...${NC}"
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js未安装或未添加到PATH${NC}"
    echo -e "${RED}请先安装Node.js 18+${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Node.js环境检查通过${NC}"

echo
# 启动后端服务
echo -e "${YELLOW}[3/4] 启动后端服务...${NC}"
cd backend

if [ ! -d "venv" ]; then
    echo "创建Python虚拟环境..."
    python3 -m venv venv
fi

echo "激活虚拟环境..."
source venv/bin/activate

echo "安装Python依赖..."
pip install -r requirements.txt

echo "初始化数据库..."
python init_db.py

echo "启动FastAPI服务器..."
# 在后台启动后端服务
nohup python main.py > ../backend.log 2>&1 &
BACKEND_PID=$!
echo "后端服务PID: $BACKEND_PID"

cd ..

echo
# 启动前端服务
echo -e "${YELLOW}[4/4] 启动前端服务...${NC}"
cd frontend

if [ ! -d "node_modules" ]; then
    echo "安装前端依赖..."
    npm install
fi

echo "启动Vue开发服务器..."
# 在后台启动前端服务
nohup npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
echo "前端服务PID: $FRONTEND_PID"

cd ..

# 保存PID到文件，方便后续停止服务
echo $BACKEND_PID > backend.pid
echo $FRONTEND_PID > frontend.pid

echo
echo -e "${GREEN}========================================"
echo -e "🚀 服务启动完成！"
echo
echo -e "📍 后端服务: http://localhost:8000"
echo -e "📍 前端服务: http://localhost:5173"
echo -e "📍 API文档: http://localhost:8000/docs"
echo
echo -e "📋 演示账户:"
echo -e "   超级管理员: admin / admin123"
echo -e "   系统管理员: manager / manager123"
echo -e "   普通用户: user / user123"
echo
echo -e "📝 日志文件:"
echo -e "   后端日志: backend.log"
echo -e "   前端日志: frontend.log"
echo
echo -e "🛑 停止服务:"
echo -e "   ./stop.sh"
echo -e "========================================${NC}"

# 等待服务启动
echo -e "${YELLOW}等待服务启动...${NC}"
sleep 5

# 检查服务是否正常启动
if ps -p $BACKEND_PID > /dev/null; then
    echo -e "${GREEN}✅ 后端服务启动成功${NC}"
else
    echo -e "${RED}❌ 后端服务启动失败，请检查 backend.log${NC}"
fi

if ps -p $FRONTEND_PID > /dev/null; then
    echo -e "${GREEN}✅ 前端服务启动成功${NC}"
else
    echo -e "${RED}❌ 前端服务启动失败，请检查 frontend.log${NC}"
fi

echo
echo -e "${BLUE}按 Ctrl+C 退出监控，服务将继续在后台运行${NC}"

# 监控服务状态
while true; do
    sleep 10
    if ! ps -p $BACKEND_PID > /dev/null; then
        echo -e "${RED}⚠️  后端服务已停止${NC}"
        break
    fi
    if ! ps -p $FRONTEND_PID > /dev/null; then
        echo -e "${RED}⚠️  前端服务已停止${NC}"
        break
    fi
done
