"""
集成启动脚本
同时启动智能客服系统和电商系统
"""
import os
import subprocess
import sys
import threading
import time
from pathlib import Path


def start_customer_service():
    """启动智能客服系统"""
    print("🚀 启动智能客服系统...")
    os.chdir(str(Path.cwd()))
    try:
        subprocess.run([sys.executable, "run.py"], check=True)
    except KeyboardInterrupt:
        print("智能客服系统已停止")
    except Exception as e:
        print(f"智能客服系统启动失败: {e}")


def start_shop_system():
    """启动电商系统"""
    print("🛍️ 启动电商系统...")
    os.chdir(str(Path.cwd() / "shop"))
    try:
        subprocess.run([sys.executable, "run.py"], check=True)
    except KeyboardInterrupt:
        print("电商系统已停止")
    except Exception as e:
        print(f"电商系统启动失败: {e}")


def main():
    """主函数"""
    print("=" * 60)
    print("🎯 智能客服 + 电商系统 集成启动器")
    print("=" * 60)
    
    # 检查目录结构
    current_dir = Path.cwd()
    customer_service_dir = current_dir
    shop_dir = current_dir / "shop"
    
    if not customer_service_dir.exists():
        print("❌ 未找到 IntelligentCustomerService1 目录")
        return
    
    if not shop_dir.exists():
        print("❌ 未找到 shop 目录")
        return
    
    print("📁 目录检查通过")
    print(f"   - 智能客服系统: {customer_service_dir}")
    print(f"   - 电商系统: {shop_dir}")
    print()
    
    # 选择启动模式
    print("请选择启动模式:")
    print("1. 仅启动智能客服系统 (端口: 9999)")
    print("2. 仅启动电商系统 (端口: 8001)")
    print("3. 同时启动两个系统")
    print("4. 退出")
    
    choice = input("\n请输入选择 (1-4): ").strip()
    
    if choice == "1":
        print("\n🚀 启动智能客服系统...")
        print("📍 访问地址: http://localhost:9999")
        print("📖 API文档: http://localhost:9999/docs")
        print("按 Ctrl+C 停止服务\n")
        start_customer_service()
        
    elif choice == "2":
        print("\n🛍️ 启动电商系统...")
        print("📍 访问地址: http://localhost:8001")
        print("📖 API文档: http://localhost:8001/shop/docs")
        print("按 Ctrl+C 停止服务\n")
        start_shop_system()
        
    elif choice == "3":
        print("\n🚀 同时启动两个系统...")
        print("📍 智能客服系统: http://localhost:9999")
        print("📍 电商系统: http://localhost:8001")
        print("📖 智能客服API文档: http://localhost:9999/docs")
        print("📖 电商系统API文档: http://localhost:8001/shop/docs")
        print("按 Ctrl+C 停止所有服务\n")
        
        # 使用线程同时启动两个系统
        customer_service_thread = threading.Thread(target=start_customer_service)
        shop_thread = threading.Thread(target=start_shop_system)
        
        try:
            customer_service_thread.start()
            time.sleep(2)  # 等待2秒再启动第二个系统
            shop_thread.start()
            
            # 等待线程结束
            customer_service_thread.join()
            shop_thread.join()
            
        except KeyboardInterrupt:
            print("\n🛑 正在停止所有服务...")
            
    elif choice == "4":
        print("👋 再见！")
        return
        
    else:
        print("❌ 无效选择，请重新运行程序")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 程序已停止")
    except Exception as e:
        print(f"\n❌ 程序运行出错: {e}")
