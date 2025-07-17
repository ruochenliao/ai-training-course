@echo off
echo 开始构建静态文件...

:: 运行构建命令
call npm run export

echo.
echo 构建完成！静态文件已生成在 out 目录中
echo.
echo 部署步骤：
echo 1. 将 out 目录中的所有文件复制到您的 Nginx 服务器网站根目录
echo.
echo Nginx配置参考：
echo server {
echo     listen 80;
echo     server_name your_domain.com;
echo     root /path/to/your/website;
echo.
echo     location / {
echo         try_files $uri $uri/ /index.html;
echo     }
echo }
echo.
echo 按任意键退出...
pause > nul 