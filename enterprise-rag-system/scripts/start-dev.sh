#!/bin/bash

# 企业级Agent+RAG知识库系统开发环境启动脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_message() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 检查Docker是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker未安装，请先安装Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi
    
    print_message "Docker环境检查通过"
}

# 检查端口是否被占用
check_ports() {
    local ports=(3000 3001 3002 8000 3306 6379 19530 7474 7687 9000 9001)
    local occupied_ports=()
    
    for port in "${ports[@]}"; do
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            occupied_ports+=($port)
        fi
    done
    
    if [ ${#occupied_ports[@]} -gt 0 ]; then
        print_warning "以下端口被占用: ${occupied_ports[*]}"
        print_warning "请确保这些端口可用，或修改docker-compose.yml中的端口配置"
        read -p "是否继续启动? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# 创建必要的目录
create_directories() {
    print_step "创建必要的目录..."
    
    mkdir -p logs
    mkdir -p uploads
    mkdir -p temp
    mkdir -p ssl
    mkdir -p monitoring/prometheus
    mkdir -p monitoring/grafana/provisioning
    mkdir -p monitoring/logstash/pipeline
    mkdir -p nginx/conf.d
    mkdir -p scripts/mysql
    
    print_message "目录创建完成"
}

# 创建环境变量文件
create_env_files() {
    print_step "创建环境变量文件..."
    
    # 后端环境变量
    if [ ! -f backend/.env ]; then
        cat > backend/.env << EOF
# 基础配置
DEBUG=true
ENVIRONMENT=development

# 数据库配置
DATABASE_URL=mysql://root:password@mysql:3306/enterprise_rag

# Redis配置
REDIS_URL=redis://redis:6379/0

# Milvus配置
MILVUS_HOST=milvus
MILVUS_PORT=19530

# Neo4j配置
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# MinIO配置
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

# Celery配置
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

# AI模型配置（请填入实际的API密钥）
LLM_API_KEY=your_deepseek_api_key_here
VLM_API_KEY=your_qwen_api_key_here
EMBEDDING_API_KEY=your_embedding_api_key_here
RERANKER_API_KEY=your_reranker_api_key_here
EOF
        print_message "后端环境变量文件已创建: backend/.env"
        print_warning "请编辑 backend/.env 文件，填入实际的API密钥"
    fi
    
    # 前端环境变量
    if [ ! -f frontend/user-app/.env.local ]; then
        cat > frontend/user-app/.env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
EOF
        print_message "用户端环境变量文件已创建: frontend/user-app/.env.local"
    fi
    
    if [ ! -f frontend/admin-app/.env ]; then
        cat > frontend/admin-app/.env << EOF
NUXT_PUBLIC_API_URL=http://localhost:8000
NUXT_PUBLIC_WS_URL=ws://localhost:8000
EOF
        print_message "管理端环境变量文件已创建: frontend/admin-app/.env"
    fi
}

# 创建MySQL初始化脚本
create_mysql_init() {
    print_step "创建MySQL初始化脚本..."
    
    cat > scripts/mysql/init.sql << EOF
-- 创建数据库
CREATE DATABASE IF NOT EXISTS enterprise_rag CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建用户
CREATE USER IF NOT EXISTS 'rag_user'@'%' IDENTIFIED BY 'rag_password';
GRANT ALL PRIVILEGES ON enterprise_rag.* TO 'rag_user'@'%';

-- 刷新权限
FLUSH PRIVILEGES;

-- 使用数据库
USE enterprise_rag;

-- 这里可以添加初始化数据
EOF
    
    print_message "MySQL初始化脚本已创建"
}

# 创建Nginx配置
create_nginx_config() {
    print_step "创建Nginx配置..."
    
    cat > nginx/nginx.conf << EOF
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }
    
    upstream frontend_user {
        server frontend-user:3000;
    }
    
    upstream frontend_admin {
        server frontend-admin:3000;
    }
    
    server {
        listen 80;
        server_name localhost;
        
        # 用户端
        location / {
            proxy_pass http://frontend_user;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }
        
        # 管理端
        location /admin {
            proxy_pass http://frontend_admin;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }
        
        # API
        location /api {
            proxy_pass http://backend;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }
        
        # WebSocket
        location /ws {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade \$http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }
    }
}
EOF
    
    print_message "Nginx配置已创建"
}

# 创建监控配置
create_monitoring_config() {
    print_step "创建监控配置..."
    
    # Prometheus配置
    cat > monitoring/prometheus.yml << EOF
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
    
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
EOF
    
    print_message "监控配置已创建"
}

# 启动服务
start_services() {
    print_step "启动Docker服务..."
    
    # 拉取镜像
    print_message "拉取Docker镜像..."
    docker-compose pull
    
    # 构建自定义镜像
    print_message "构建应用镜像..."
    docker-compose build
    
    # 启动服务
    print_message "启动所有服务..."
    docker-compose up -d
    
    print_message "服务启动完成"
}

# 等待服务就绪
wait_for_services() {
    print_step "等待服务就绪..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            print_message "后端服务已就绪"
            break
        fi
        
        print_message "等待后端服务启动... ($attempt/$max_attempts)"
        sleep 5
        ((attempt++))
    done
    
    if [ $attempt -gt $max_attempts ]; then
        print_error "后端服务启动超时"
        exit 1
    fi
}

# 显示服务信息
show_service_info() {
    print_step "服务信息:"
    echo
    echo "🌐 用户端:        http://localhost:3000"
    echo "🔧 管理端:        http://localhost:3001"
    echo "📊 监控面板:      http://localhost:3002"
    echo "🔍 API文档:       http://localhost:8000/docs"
    echo "💾 数据库管理:    http://localhost:8080 (可选)"
    echo "📈 Prometheus:    http://localhost:9090"
    echo "📊 Grafana:       http://localhost:3002 (admin/admin)"
    echo "🔍 Kibana:        http://localhost:5601"
    echo "📁 MinIO:         http://localhost:9001 (minioadmin/minioadmin)"
    echo "🕸️  Neo4j:         http://localhost:7474 (neo4j/password)"
    echo
    echo "📋 查看日志: docker-compose logs -f [service_name]"
    echo "🛑 停止服务: docker-compose down"
    echo "🔄 重启服务: docker-compose restart [service_name]"
    echo
}

# 主函数
main() {
    echo "🚀 企业级Agent+RAG知识库系统开发环境启动"
    echo "================================================"
    
    check_docker
    check_ports
    create_directories
    create_env_files
    create_mysql_init
    create_nginx_config
    create_monitoring_config
    start_services
    wait_for_services
    show_service_info
    
    print_message "开发环境启动完成! 🎉"
}

# 运行主函数
main "$@"
