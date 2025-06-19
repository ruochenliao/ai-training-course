@echo off
setlocal enabledelayedexpansion

REM 企业级Agent+RAG知识库系统开发环境启动脚本 (Windows版本)

echo 🚀 企业级Agent+RAG知识库系统开发环境启动
echo ================================================

REM 检查Docker是否安装
echo [INFO] 检查Docker环境...
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker未安装，请先安装Docker Desktop
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Compose未安装，请先安装Docker Compose
    pause
    exit /b 1
)

echo [INFO] Docker环境检查通过

REM 创建必要的目录
echo [STEP] 创建必要的目录...
if not exist "logs" mkdir logs
if not exist "uploads" mkdir uploads
if not exist "temp" mkdir temp
if not exist "ssl" mkdir ssl
if not exist "monitoring\prometheus" mkdir monitoring\prometheus
if not exist "monitoring\grafana\provisioning" mkdir monitoring\grafana\provisioning
if not exist "monitoring\logstash\pipeline" mkdir monitoring\logstash\pipeline
if not exist "nginx\conf.d" mkdir nginx\conf.d
if not exist "scripts\mysql" mkdir scripts\mysql

echo [INFO] 目录创建完成

REM 创建后端环境变量文件
echo [STEP] 创建环境变量文件...
if not exist "backend\.env" (
    echo # 基础配置 > backend\.env
    echo DEBUG=true >> backend\.env
    echo ENVIRONMENT=development >> backend\.env
    echo. >> backend\.env
    echo # 数据库配置 >> backend\.env
    echo DATABASE_URL=mysql://root:password@mysql:3306/enterprise_rag >> backend\.env
    echo. >> backend\.env
    echo # Redis配置 >> backend\.env
    echo REDIS_URL=redis://redis:6379/0 >> backend\.env
    echo. >> backend\.env
    echo # Milvus配置 >> backend\.env
    echo MILVUS_HOST=milvus >> backend\.env
    echo MILVUS_PORT=19530 >> backend\.env
    echo. >> backend\.env
    echo # Neo4j配置 >> backend\.env
    echo NEO4J_URI=bolt://neo4j:7687 >> backend\.env
    echo NEO4J_USER=neo4j >> backend\.env
    echo NEO4J_PASSWORD=password >> backend\.env
    echo. >> backend\.env
    echo # MinIO配置 >> backend\.env
    echo MINIO_ENDPOINT=minio:9000 >> backend\.env
    echo MINIO_ACCESS_KEY=minioadmin >> backend\.env
    echo MINIO_SECRET_KEY=minioadmin >> backend\.env
    echo. >> backend\.env
    echo # Celery配置 >> backend\.env
    echo CELERY_BROKER_URL=redis://redis:6379/1 >> backend\.env
    echo CELERY_RESULT_BACKEND=redis://redis:6379/2 >> backend\.env
    echo. >> backend\.env
    echo # AI模型配置（请填入实际的API密钥） >> backend\.env
    echo LLM_API_KEY=your_deepseek_api_key_here >> backend\.env
    echo VLM_API_KEY=your_qwen_api_key_here >> backend\.env
    echo EMBEDDING_API_KEY=your_embedding_api_key_here >> backend\.env
    echo RERANKER_API_KEY=your_reranker_api_key_here >> backend\.env
    
    echo [INFO] 后端环境变量文件已创建: backend\.env
    echo [WARNING] 请编辑 backend\.env 文件，填入实际的API密钥
)

REM 创建MySQL初始化脚本
if not exist "scripts\mysql\init.sql" (
    echo -- 创建数据库 > scripts\mysql\init.sql
    echo CREATE DATABASE IF NOT EXISTS enterprise_rag CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci; >> scripts\mysql\init.sql
    echo. >> scripts\mysql\init.sql
    echo -- 创建用户 >> scripts\mysql\init.sql
    echo CREATE USER IF NOT EXISTS 'rag_user'@'%%' IDENTIFIED BY 'rag_password'; >> scripts\mysql\init.sql
    echo GRANT ALL PRIVILEGES ON enterprise_rag.* TO 'rag_user'@'%%'; >> scripts\mysql\init.sql
    echo. >> scripts\mysql\init.sql
    echo -- 刷新权限 >> scripts\mysql\init.sql
    echo FLUSH PRIVILEGES; >> scripts\mysql\init.sql
    echo. >> scripts\mysql\init.sql
    echo -- 使用数据库 >> scripts\mysql\init.sql
    echo USE enterprise_rag; >> scripts\mysql\init.sql
    
    echo [INFO] MySQL初始化脚本已创建
)

REM 创建Prometheus配置
if not exist "monitoring\prometheus.yml" (
    echo global: > monitoring\prometheus.yml
    echo   scrape_interval: 15s >> monitoring\prometheus.yml
    echo. >> monitoring\prometheus.yml
    echo scrape_configs: >> monitoring\prometheus.yml
    echo   - job_name: 'backend' >> monitoring\prometheus.yml
    echo     static_configs: >> monitoring\prometheus.yml
    echo       - targets: ['backend:8000'] >> monitoring\prometheus.yml
    echo     metrics_path: '/metrics' >> monitoring\prometheus.yml
    echo. >> monitoring\prometheus.yml
    echo   - job_name: 'prometheus' >> monitoring\prometheus.yml
    echo     static_configs: >> monitoring\prometheus.yml
    echo       - targets: ['localhost:9090'] >> monitoring\prometheus.yml
    
    echo [INFO] 监控配置已创建
)

REM 启动Docker服务
echo [STEP] 启动Docker服务...

echo [INFO] 拉取Docker镜像...
docker-compose pull

echo [INFO] 构建应用镜像...
docker-compose build

echo [INFO] 启动所有服务...
docker-compose up -d

echo [INFO] 服务启动完成

REM 等待服务就绪
echo [STEP] 等待服务就绪...
set /a attempt=1
set /a max_attempts=30

:wait_loop
curl -s http://localhost:8000/health >nul 2>&1
if !errorlevel! equ 0 (
    echo [INFO] 后端服务已就绪
    goto :services_ready
)

echo [INFO] 等待后端服务启动... (!attempt!/!max_attempts!)
timeout /t 5 /nobreak >nul
set /a attempt+=1

if !attempt! leq !max_attempts! goto :wait_loop

echo [ERROR] 后端服务启动超时
pause
exit /b 1

:services_ready

REM 显示服务信息
echo.
echo [STEP] 服务信息:
echo.
echo 🌐 用户端:        http://localhost:3000
echo 🔧 管理端:        http://localhost:3001
echo 📊 监控面板:      http://localhost:3002
echo 🔍 API文档:       http://localhost:8000/docs
echo 💾 数据库管理:    http://localhost:8080 (可选)
echo 📈 Prometheus:    http://localhost:9090
echo 📊 Grafana:       http://localhost:3002 (admin/admin)
echo 🔍 Kibana:        http://localhost:5601
echo 📁 MinIO:         http://localhost:9001 (minioadmin/minioadmin)
echo 🕸️  Neo4j:         http://localhost:7474 (neo4j/password)
echo.
echo 📋 查看日志: docker-compose logs -f [service_name]
echo 🛑 停止服务: docker-compose down
echo 🔄 重启服务: docker-compose restart [service_name]
echo.

echo [INFO] 开发环境启动完成! 🎉

pause
