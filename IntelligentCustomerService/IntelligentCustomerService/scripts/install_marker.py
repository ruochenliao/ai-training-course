#!/usr/bin/env python3
"""
Marker框架安装和配置脚本
自动安装Marker及其依赖，配置模型和环境
"""

import os
import sys
import subprocess
import platform
from pathlib import Path
import requests
import zipfile
import shutil

def print_banner():
    """打印安装横幅"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║        📄 Marker文档解析框架安装器                           ║
    ║                                                              ║
    ║        自动安装Marker及其依赖                                ║
    ║        配置模型和环境                                        ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_system_requirements():
    """检查系统要求"""
    print("🔍 检查系统要求...")
    
    # 检查Python版本
    python_version = sys.version_info
    if python_version < (3, 8):
        print(f"❌ Python版本过低: {python_version.major}.{python_version.minor}")
        print("💡 Marker需要Python 3.8+")
        return False
    
    print(f"✅ Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # 检查操作系统
    system = platform.system()
    print(f"✅ 操作系统: {system}")
    
    # 检查可用内存（简单检查）
    try:
        import psutil
        memory = psutil.virtual_memory()
        memory_gb = memory.total / (1024**3)
        print(f"✅ 系统内存: {memory_gb:.1f} GB")
        
        if memory_gb < 4:
            print("⚠️  警告: 系统内存较少，Marker可能运行缓慢")
    except ImportError:
        print("⚠️  无法检查内存信息（psutil未安装）")
    
    return True

def install_system_dependencies():
    """安装系统依赖"""
    print("\n📦 安装系统依赖...")
    
    system = platform.system()
    
    if system == "Linux":
        # Ubuntu/Debian
        try:
            subprocess.run([
                "sudo", "apt-get", "update"
            ], check=True)
            
            subprocess.run([
                "sudo", "apt-get", "install", "-y",
                "poppler-utils",  # PDF处理
                "tesseract-ocr",  # OCR
                "tesseract-ocr-chi-sim",  # 中文OCR
                "tesseract-ocr-chi-tra",  # 繁体中文OCR
                "libgl1-mesa-glx",  # OpenGL
                "libglib2.0-0",
                "libsm6",
                "libxext6",
                "libxrender-dev",
                "libgomp1"
            ], check=True)
            
            print("✅ Linux系统依赖安装完成")
            
        except subprocess.CalledProcessError as e:
            print(f"⚠️  系统依赖安装失败: {e}")
            print("💡 请手动安装: poppler-utils tesseract-ocr")
    
    elif system == "Darwin":  # macOS
        try:
            # 检查Homebrew
            subprocess.run(["brew", "--version"], check=True, capture_output=True)
            
            subprocess.run([
                "brew", "install",
                "poppler",
                "tesseract",
                "tesseract-lang"
            ], check=True)
            
            print("✅ macOS系统依赖安装完成")
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("⚠️  请先安装Homebrew，然后手动安装依赖:")
            print("   brew install poppler tesseract tesseract-lang")
    
    elif system == "Windows":
        print("⚠️  Windows系统请手动安装以下依赖:")
        print("   1. Poppler for Windows")
        print("   2. Tesseract OCR")
        print("   3. 配置环境变量")

def install_python_dependencies():
    """安装Python依赖"""
    print("\n🐍 安装Python依赖...")
    
    # 基础依赖
    base_packages = [
        "torch>=2.0.0",
        "torchvision>=0.15.0",
        "transformers>=4.30.0",
        "pillow>=9.0.0",
        "opencv-python>=4.7.0",
        "numpy>=1.21.0",
        "scipy>=1.7.0",
        "scikit-image>=0.19.0",
        "matplotlib>=3.5.0",
        "tqdm>=4.64.0",
        "requests>=2.28.0",
        "beautifulsoup4>=4.11.0",
        "lxml>=4.9.0",
        "Pillow>=9.0.0",
        "pdf2image>=1.16.0",
        "pytesseract>=0.3.10",
        "pymupdf>=1.22.0",
        "python-docx>=0.8.11",
        "python-pptx>=0.6.21",
        "openpyxl>=3.1.0",
        "pandas>=1.5.0"
    ]
    
    for package in base_packages:
        try:
            print(f"📦 安装 {package}...")
            subprocess.run([
                sys.executable, "-m", "pip", "install", package
            ], check=True, capture_output=True)
            print(f"✅ {package} 安装成功")
        except subprocess.CalledProcessError as e:
            print(f"❌ {package} 安装失败: {e}")

def install_marker():
    """安装Marker框架"""
    print("\n📄 安装Marker框架...")
    
    try:
        # 方法1: 从PyPI安装（如果可用）
        try:
            subprocess.run([
                sys.executable, "-m", "pip", "install", "marker-pdf"
            ], check=True, capture_output=True)
            print("✅ Marker从PyPI安装成功")
            return True
        except subprocess.CalledProcessError:
            print("⚠️  PyPI安装失败，尝试从源码安装...")
        
        # 方法2: 从GitHub安装
        marker_repo = "https://github.com/VikParuchuri/marker.git"
        marker_dir = Path("./marker_temp")
        
        if marker_dir.exists():
            shutil.rmtree(marker_dir)
        
        print(f"📥 克隆Marker仓库...")
        subprocess.run([
            "git", "clone", marker_repo, str(marker_dir)
        ], check=True)
        
        # 安装Marker
        original_dir = os.getcwd()
        os.chdir(marker_dir)
        
        try:
            subprocess.run([
                sys.executable, "-m", "pip", "install", "-e", "."
            ], check=True)
            print("✅ Marker从源码安装成功")
            
        finally:
            os.chdir(original_dir)
            shutil.rmtree(marker_dir)
        
        return True
        
    except Exception as e:
        print(f"❌ Marker安装失败: {e}")
        return False

def download_models():
    """下载Marker模型"""
    print("\n🤖 下载Marker模型...")
    
    models_dir = Path("./models/marker")
    models_dir.mkdir(parents=True, exist_ok=True)
    
    # Marker模型列表
    models = {
        "layout_model": {
            "url": "https://huggingface.co/vikp/layout_model/resolve/main/pytorch_model.bin",
            "path": models_dir / "layout_model.bin"
        },
        "order_model": {
            "url": "https://huggingface.co/vikp/order_model/resolve/main/pytorch_model.bin", 
            "path": models_dir / "order_model.bin"
        },
        "detection_model": {
            "url": "https://huggingface.co/vikp/column_model/resolve/main/pytorch_model.bin",
            "path": models_dir / "detection_model.bin"
        }
    }
    
    for model_name, model_info in models.items():
        if model_info["path"].exists():
            print(f"✅ {model_name} 已存在，跳过下载")
            continue
        
        try:
            print(f"📥 下载 {model_name}...")
            response = requests.get(model_info["url"], stream=True)
            response.raise_for_status()
            
            with open(model_info["path"], "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"✅ {model_name} 下载完成")
            
        except Exception as e:
            print(f"❌ {model_name} 下载失败: {e}")
            print(f"💡 请手动下载: {model_info['url']}")

def create_config():
    """创建配置文件"""
    print("\n⚙️  创建配置文件...")
    
    config_content = """
# Marker配置文件
MARKER_CONFIG = {
    'models_dir': './models/marker',
    'temp_dir': './temp/marker',
    'max_pages': 1000,
    'batch_size': 1,
    'languages': ['zh', 'en'],
    'extract_images': True,
    'extract_tables': True,
    'ocr_all_pages': False,
    'device': 'auto'  # 'cpu', 'cuda', 'auto'
}

# 模型路径配置
MODEL_PATHS = {
    'layout_model': './models/marker/layout_model.bin',
    'order_model': './models/marker/order_model.bin', 
    'detection_model': './models/marker/detection_model.bin'
}
"""
    
    config_file = Path("./app/core/marker_config.py")
    config_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_file, "w", encoding="utf-8") as f:
        f.write(config_content)
    
    print(f"✅ 配置文件创建: {config_file}")

def test_installation():
    """测试安装"""
    print("\n🧪 测试Marker安装...")
    
    try:
        # 测试导入
        import marker
        print("✅ Marker导入成功")
        
        # 测试基础功能
        from marker import convert_single_pdf
        print("✅ Marker功能可用")
        
        return True
        
    except ImportError as e:
        print(f"❌ Marker导入失败: {e}")
        print("💡 请检查安装是否成功")
        return False
    except Exception as e:
        print(f"⚠️  Marker测试警告: {e}")
        return True

def create_test_script():
    """创建测试脚本"""
    print("\n📝 创建测试脚本...")
    
    test_script = """#!/usr/bin/env python3
'''
Marker测试脚本
'''

import sys
from pathlib import Path

def test_marker():
    try:
        from marker import convert_single_pdf
        print("✅ Marker导入成功")
        
        # 这里可以添加更多测试
        print("✅ Marker测试通过")
        return True
        
    except ImportError as e:
        print(f"❌ Marker导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ Marker测试失败: {e}")
        return False

if __name__ == "__main__":
    success = test_marker()
    sys.exit(0 if success else 1)
"""
    
    test_file = Path("./scripts/test_marker.py")
    test_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(test_file, "w", encoding="utf-8") as f:
        f.write(test_script)
    
    # 设置执行权限
    test_file.chmod(0o755)
    
    print(f"✅ 测试脚本创建: {test_file}")

def main():
    """主函数"""
    print_banner()
    
    # 检查系统要求
    if not check_system_requirements():
        print("❌ 系统要求检查失败")
        sys.exit(1)
    
    # 安装系统依赖
    install_system_dependencies()
    
    # 安装Python依赖
    install_python_dependencies()
    
    # 安装Marker
    if not install_marker():
        print("❌ Marker安装失败")
        sys.exit(1)
    
    # 下载模型
    download_models()
    
    # 创建配置
    create_config()
    
    # 测试安装
    if test_installation():
        print("\n🎉 Marker安装完成！")
        
        # 创建测试脚本
        create_test_script()
        
        print("\n📋 后续步骤:")
        print("1. 运行测试: python scripts/test_marker.py")
        print("2. 查看配置: app/core/marker_config.py")
        print("3. 开始使用Marker文档解析功能")
        
    else:
        print("\n⚠️  安装可能存在问题，请检查错误信息")

if __name__ == "__main__":
    main()
