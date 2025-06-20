#!/usr/bin/env python3
"""
React前端开发服务器启动脚本
自动检查依赖、启动开发服务器
"""

import os
import sys
import subprocess
import json
import time
from pathlib import Path

def print_banner():
    """打印启动横幅"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║        🚀 Gemini风格智能客服系统 - React前端启动器           ║
    ║                                                              ║
    ║        基于 React 18 + Ant Design X + TypeScript            ║
    ║        提供炫酷的Gemini风格聊天界面                          ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_node_version():
    """检查Node.js版本"""
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"✅ Node.js版本: {version}")
            
            # 检查版本是否满足要求 (>=16.0.0)
            version_num = version.replace('v', '').split('.')[0]
            if int(version_num) >= 16:
                return True
            else:
                print(f"❌ Node.js版本过低，需要 >= 16.0.0，当前版本: {version}")
                return False
        else:
            print("❌ Node.js未安装")
            return False
    except FileNotFoundError:
        print("❌ Node.js未安装")
        return False

def check_package_manager():
    """检查包管理器"""
    # 优先检查pnpm
    try:
        result = subprocess.run(['pnpm', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"✅ pnpm版本: {version}")
            return 'pnpm'
    except FileNotFoundError:
        pass
    
    # 检查npm
    try:
        result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"✅ npm版本: {version}")
            return 'npm'
    except FileNotFoundError:
        pass
    
    print("❌ 未找到包管理器 (pnpm/npm)")
    return None

def check_dependencies(package_manager):
    """检查依赖是否已安装"""
    if not os.path.exists('node_modules'):
        print("📦 node_modules不存在，需要安装依赖...")
        return False
    
    # 检查package.json的修改时间
    package_json_time = os.path.getmtime('package.json')
    node_modules_time = os.path.getmtime('node_modules')
    
    if package_json_time > node_modules_time:
        print("📦 package.json已更新，需要重新安装依赖...")
        return False
    
    print("✅ 依赖已安装")
    return True

def install_dependencies(package_manager):
    """安装依赖"""
    print(f"📦 使用 {package_manager} 安装依赖...")
    
    try:
        if package_manager == 'pnpm':
            result = subprocess.run(['pnpm', 'install'], check=True)
        else:
            result = subprocess.run(['npm', 'install'], check=True)
        
        print("✅ 依赖安装完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 依赖安装失败: {e}")
        return False

def check_backend_connection():
    """检查后端连接"""
    try:
        import requests
        response = requests.get('http://localhost:9999/health', timeout=5)
        if response.status_code == 200:
            print("✅ 后端服务连接正常")
            return True
        else:
            print(f"⚠️  后端服务响应异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"⚠️  后端服务连接失败: {e}")
        print("💡 请确保后端服务已启动 (python run.py)")
        return False

def start_dev_server(package_manager):
    """启动开发服务器"""
    print("🚀 启动React开发服务器...")
    
    try:
        if package_manager == 'pnpm':
            subprocess.run(['pnpm', 'dev'], check=True)
        else:
            subprocess.run(['npm', 'run', 'dev'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ 开发服务器启动失败: {e}")
        return False
    except KeyboardInterrupt:
        print("\n👋 开发服务器已停止")
        return True

def show_info():
    """显示项目信息"""
    info = """
    📋 项目信息:
    ├── 前端地址: http://localhost:5173
    ├── 后端地址: http://localhost:9999
    ├── API文档: http://localhost:9999/docs
    └── 聊天界面: http://localhost:5173/chat
    
    🎨 Gemini风格特性:
    ├── ✨ 炫酷的渐变背景和动画效果
    ├── 🎯 智能建议和快捷操作
    ├── 🖼️  多模态内容支持 (图片/视频/音频/文档)
    ├── 🤖 基于Ant Design X的RICH设计范式
    ├── 📱 完全响应式设计
    └── 🌙 明暗主题切换
    
    🔧 开发工具:
    ├── React 18 + TypeScript
    ├── Ant Design 5 + Ant Design X
    ├── Vite 5 (快速构建)
    ├── UnoCSS (原子化CSS)
    └── Zustand (状态管理)
    """
    print(info)

def main():
    """主函数"""
    print_banner()
    
    # 检查当前目录
    if not os.path.exists('package.json'):
        print("❌ 当前目录不是React项目根目录")
        print("💡 请在 web-react 目录下运行此脚本")
        sys.exit(1)
    
    # 检查Node.js
    if not check_node_version():
        print("💡 请安装Node.js 16+: https://nodejs.org/")
        sys.exit(1)
    
    # 检查包管理器
    package_manager = check_package_manager()
    if not package_manager:
        print("💡 请安装npm或pnpm")
        sys.exit(1)
    
    # 检查并安装依赖
    if not check_dependencies(package_manager):
        if not install_dependencies(package_manager):
            sys.exit(1)
    
    # 检查后端连接
    check_backend_connection()
    
    # 显示项目信息
    show_info()
    
    # 启动开发服务器
    print("⏳ 3秒后启动开发服务器...")
    time.sleep(3)
    
    start_dev_server(package_manager)

if __name__ == '__main__':
    main()
