#!/bin/bash

# 企业RAG系统部署脚本
# 用于生产环境的一键部署

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "$1 命令未找到，请先安装"
        exit 1
    fi
}

# 检查环境变量
check_env_vars() {
    local required_vars=(
        "QWEN_API_KEY"
        "SECRET_KEY"
        "DOMAIN_NAME"
    )
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            log_error "环境变量 $var 未设置"
            exit 1
        fi
    done
}

# 创建必要的目录
create_directories() {
    log_info "创建必要的目录..."
    
    local dirs=(
        "data/uploads"
        "logs"
        "logs/nginx"
        "ssl"
        "monitoring/prometheus"
        "monitoring/grafana/dashboards"
        "monitoring/grafana/datasources"
        "monitoring/logstash/pipeline"
        "database"
    )
    
    for dir in "${dirs[@]}"; do
        mkdir -p "$dir"
        log_info "创建目录: $dir"
    done
}

# 生成SSL证书（自签名，生产环境应使用真实证书）
generate_ssl_certificates() {
    log_info "生成SSL证书..."
    
    if [ ! -f "ssl/${DOMAIN_NAME}.crt" ]; then
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout "ssl/${DOMAIN_NAME}.key" \
            -out "ssl/${DOMAIN_NAME}.crt" \
            -subj "/C=CN/ST=Beijing/L=Beijing/O=Company/CN=${DOMAIN_NAME}"
        
        # 为子域名创建证书
        cp "ssl/${DOMAIN_NAME}.crt" "ssl/admin.${DOMAIN_NAME}.crt"
        cp "ssl/${DOMAIN_NAME}.key" "ssl/admin.${DOMAIN_NAME}.key"
        cp "ssl/${DOMAIN_NAME}.crt" "ssl/api.${DOMAIN_NAME}.crt"
        cp "ssl/${DOMAIN_NAME}.key" "ssl/api.${DOMAIN_NAME}.key"
        cp "ssl/${DOMAIN_NAME}.crt" "ssl/monitor.${DOMAIN_NAME}.crt"
        cp "ssl/${DOMAIN_NAME}.key" "ssl/monitor.${DOMAIN_NAME}.key"
        
        log_success "SSL证书生成完成"
    else
        log_info "SSL证书已存在，跳过生成"
    fi
}

# 创建Nginx基本认证文件
create_nginx_auth() {
    log_info "创建Nginx基本认证文件..."
    
    if [ ! -f "nginx/.htpasswd" ]; then
        # 创建监控访问的用户名密码
        echo "admin:\$apr1\$salt\$hash" > nginx/.htpasswd
        log_warning "请修改 nginx/.htpasswd 文件中的密码"
    fi
}

# 创建环境配置文件
create_env_file() {
    log_info "创建环境配置文件..."
    
    cat > .env.prod << EOF
# 生产环境配置
ENV=production
DEBUG=false

# 数据库配置
DATABASE_URL=postgresql://rag_user:rag_password@postgres:5432/rag_db
REDIS_URL=redis://redis:6379/0

# 向量数据库配置
MILVUS_HOST=milvus-standalone
MILVUS_PORT=19530

# 图数据库配置
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=neo4j_password

# API密钥
QWEN_API_KEY=${QWEN_API_KEY}
SECRET_KEY=${SECRET_KEY}

# 域名配置
DOMAIN_NAME=${DOMAIN_NAME}
CORS_ORIGINS=https://${DOMAIN_NAME},https://admin.${DOMAIN_NAME}

# 监控配置
PROMETHEUS_RETENTION=30d
GRAFANA_ADMIN_PASSWORD=admin_password
EOF

    log_success "环境配置文件创建完成"
}

# 创建监控配置
create_monitoring_config() {
    log_info "创建监控配置..."
    
    # Prometheus配置
    cat > monitoring/prometheus/prometheus.yml << EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  # - "first_rules.yml"
  # - "second_rules.yml"

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'

  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx:80']

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']

  - job_name: 'milvus'
    static_configs:
      - targets: ['milvus-standalone:9091']
EOF

    # Grafana数据源配置
    cat > monitoring/grafana/datasources/prometheus.yml << EOF
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
EOF

    log_success "监控配置创建完成"
}

# 创建数据库初始化脚本
create_database_init() {
    log_info "创建数据库初始化脚本..."
    
    cat > database/init.sql << EOF
-- 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- 创建用户表
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建知识库表
CREATE TABLE IF NOT EXISTS knowledge_bases (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    embedding_model VARCHAR(100) DEFAULT 'text-embedding-ada-002',
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建文档表
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    content TEXT,
    file_path VARCHAR(500),
    file_type VARCHAR(50),
    file_size INTEGER,
    knowledge_base_id INTEGER REFERENCES knowledge_bases(id),
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建对话表
CREATE TABLE IF NOT EXISTS conversations (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    title VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建消息表
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER REFERENCES conversations(id),
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建默认管理员用户
INSERT INTO users (username, email, full_name, hashed_password, role) 
VALUES ('admin', 'admin@company.com', '系统管理员', 
        '\$2b\$12\$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6ukx/L/jdy', 'admin')
ON CONFLICT (username) DO NOTHING;
EOF

    log_success "数据库初始化脚本创建完成"
}

# 构建和启动服务
deploy_services() {
    log_info "构建和启动服务..."
    
    # 停止现有服务
    docker-compose -f docker-compose.prod.yml down
    
    # 构建镜像
    log_info "构建Docker镜像..."
    docker-compose -f docker-compose.prod.yml build --no-cache
    
    # 启动服务
    log_info "启动服务..."
    docker-compose -f docker-compose.prod.yml up -d
    
    # 等待服务启动
    log_info "等待服务启动..."
    sleep 30
    
    # 检查服务状态
    log_info "检查服务状态..."
    docker-compose -f docker-compose.prod.yml ps
}

# 运行健康检查
health_check() {
    log_info "运行健康检查..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost:8000/api/v1/health > /dev/null 2>&1; then
            log_success "后端服务健康检查通过"
            break
        else
            log_warning "健康检查失败，重试中... ($attempt/$max_attempts)"
            sleep 10
            ((attempt++))
        fi
    done
    
    if [ $attempt -gt $max_attempts ]; then
        log_error "健康检查失败，请检查服务状态"
        exit 1
    fi
}

# 运行集成测试
run_integration_tests() {
    log_info "运行集成测试..."
    
    if [ -f "scripts/integration_test.py" ]; then
        python3 scripts/integration_test.py --url http://localhost:8000
        if [ $? -eq 0 ]; then
            log_success "集成测试通过"
        else
            log_warning "集成测试失败，请检查日志"
        fi
    else
        log_warning "集成测试脚本不存在，跳过测试"
    fi
}

# 显示部署信息
show_deployment_info() {
    log_success "部署完成！"
    echo ""
    echo "服务访问地址："
    echo "  用户前端: https://${DOMAIN_NAME}"
    echo "  管理后台: https://admin.${DOMAIN_NAME}"
    echo "  API接口: https://api.${DOMAIN_NAME}"
    echo "  监控面板: https://monitor.${DOMAIN_NAME}"
    echo ""
    echo "默认管理员账号："
    echo "  用户名: admin"
    echo "  密码: admin123"
    echo ""
    echo "监控服务："
    echo "  Grafana: http://localhost:3002"
    echo "  Prometheus: http://localhost:9090"
    echo "  Kibana: http://localhost:5601"
    echo ""
    echo "数据库连接："
    echo "  PostgreSQL: localhost:5432"
    echo "  Redis: localhost:6379"
    echo "  Milvus: localhost:19530"
    echo "  Neo4j: localhost:7474"
    echo ""
    log_warning "请确保防火墙已正确配置，并更新DNS记录指向服务器IP"
}

# 主函数
main() {
    log_info "开始部署企业RAG系统..."
    
    # 检查必要的命令
    check_command "docker"
    check_command "docker-compose"
    check_command "openssl"
    check_command "curl"
    
    # 检查环境变量
    check_env_vars
    
    # 创建目录和配置文件
    create_directories
    generate_ssl_certificates
    create_nginx_auth
    create_env_file
    create_monitoring_config
    create_database_init
    
    # 部署服务
    deploy_services
    
    # 健康检查
    health_check
    
    # 运行测试
    run_integration_tests
    
    # 显示部署信息
    show_deployment_info
}

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
