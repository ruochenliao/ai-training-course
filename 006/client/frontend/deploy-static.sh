#!/bin/bash

# 运行构建
npm run export

echo "静态文件已生成，位于 out 目录"
echo "请将 out 目录下的所有文件复制到您的 Nginx 服务器的网站根目录"
echo ""
echo "Nginx 配置示例："
echo "server {"
echo "    listen 80;"
echo "    server_name your_domain.com;"
echo "    root /var/www/html;  # 改为您的网站根目录"
echo ""
echo "    location / {"
echo "        try_files \$uri \$uri/ /index.html;"
echo "    }"
echo "}" 