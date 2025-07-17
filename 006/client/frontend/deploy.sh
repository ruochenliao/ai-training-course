#!/bin/bash

# 创建部署目录
DEPLOY_DIR="deploy"
mkdir -p $DEPLOY_DIR

# 复制必要文件
cp -r .next $DEPLOY_DIR/
cp -r public $DEPLOY_DIR/ 2>/dev/null || :
cp package.json $DEPLOY_DIR/
cp next.config.js $DEPLOY_DIR/ 2>/dev/null || :

# 创建生产环境的 package.json
cat > $DEPLOY_DIR/package.json << EOF
{
  "name": "danwen-agent-system",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "start": "next start"
  },
  "dependencies": {
    "next": "^14.0.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  }
}
EOF

echo "部署文件已准备完成，位于 $DEPLOY_DIR 目录"
echo "请将此目录下的所有文件复制到您的 Nginx 服务器上"
echo ""
echo "在服务器上需要执行的命令："
echo "1. cd 到部署目录"
echo "2. npm install --production"
echo "3. npm start (或使用 pm2 等进程管理工具启动)"
echo ""
echo "Nginx 配置示例："
echo "server {"
echo "    listen 80;"
echo "    server_name your_domain.com;"
echo ""
echo "    location / {"
echo "        proxy_pass http://localhost:3000;"
echo "        proxy_http_version 1.1;"
echo "        proxy_set_header Upgrade \$http_upgrade;"
echo "        proxy_set_header Connection 'upgrade';"
echo "        proxy_set_header Host \$host;"
echo "        proxy_cache_bypass \$http_upgrade;"
echo "    }"
echo "}" 