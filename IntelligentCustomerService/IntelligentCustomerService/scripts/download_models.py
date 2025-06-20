#!/usr/bin/env python3
"""
模型下载脚本
自动从ModelScope下载嵌入模型和重排模型
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional
import argparse

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from modelscope import snapshot_download
import torch

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ModelDownloader:
    """模型下载器"""
    
    def __init__(self, cache_dir: str = "./models", force_download: bool = False):
        """
        初始化模型下载器
        
        Args:
            cache_dir: 模型缓存目录
            force_download: 是否强制重新下载
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.force_download = force_download
        
        # 模型配置
        self.models_config = {
            "embedding": {
                "model_id": "Qwen/Qwen3-0.6B",
                "description": "通义千问3-0.6B嵌入模型",
                "required_files": [
                    "config.json",
                    "pytorch_model.bin",
                    "tokenizer.json",
                    "tokenizer_config.json",
                    "vocab.txt"
                ]
            },
            "rerank": {
                "model_id": "Qwen/Qwen3-Reranker-0.6B", 
                "description": "通义千问3-Reranker-0.6B重排模型",
                "required_files": [
                    "config.json",
                    "pytorch_model.bin",
                    "tokenizer.json",
                    "tokenizer_config.json"
                ]
            }
        }
    
    def check_model_exists(self, model_type: str) -> bool:
        """检查模型是否已存在"""
        try:
            model_config = self.models_config.get(model_type)
            if not model_config:
                return False
            
            model_id = model_config["model_id"]
            model_path = self.cache_dir / model_id.replace("/", "--")
            
            if not model_path.exists():
                return False
            
            # 检查必需文件是否存在
            required_files = model_config.get("required_files", [])
            for file_name in required_files:
                if not (model_path / file_name).exists():
                    logger.warning(f"模型 {model_type} 缺少文件: {file_name}")
                    return False
            
            logger.info(f"模型 {model_type} 已存在: {model_path}")
            return True
            
        except Exception as e:
            logger.error(f"检查模型 {model_type} 时出错: {str(e)}")
            return False
    
    def download_model(self, model_type: str) -> Optional[str]:
        """
        下载指定模型
        
        Args:
            model_type: 模型类型 (embedding, rerank)
            
        Returns:
            模型本地路径
        """
        try:
            model_config = self.models_config.get(model_type)
            if not model_config:
                logger.error(f"未知的模型类型: {model_type}")
                return None
            
            model_id = model_config["model_id"]
            description = model_config["description"]
            
            logger.info(f"开始下载 {description} ({model_id})")
            
            # 检查是否需要下载
            if not self.force_download and self.check_model_exists(model_type):
                logger.info(f"模型 {model_type} 已存在，跳过下载")
                return str(self.cache_dir / model_id.replace("/", "--"))
            
            # 下载模型
            model_path = snapshot_download(
                model_id=model_id,
                cache_dir=str(self.cache_dir),
                revision="master"
            )
            
            logger.info(f"模型 {description} 下载完成: {model_path}")
            
            # 验证下载的文件
            if self.verify_model(model_type, model_path):
                logger.info(f"模型 {model_type} 验证成功")
                return model_path
            else:
                logger.error(f"模型 {model_type} 验证失败")
                return None
                
        except Exception as e:
            logger.error(f"下载模型 {model_type} 失败: {str(e)}")
            return None
    
    def verify_model(self, model_type: str, model_path: str) -> bool:
        """验证模型文件完整性"""
        try:
            model_config = self.models_config.get(model_type)
            if not model_config:
                return False
            
            model_path = Path(model_path)
            required_files = model_config.get("required_files", [])
            
            # 检查必需文件
            for file_name in required_files:
                file_path = model_path / file_name
                if not file_path.exists():
                    logger.error(f"缺少必需文件: {file_path}")
                    return False
                
                # 检查文件大小
                if file_path.stat().st_size == 0:
                    logger.error(f"文件为空: {file_path}")
                    return False
            
            # 尝试加载模型配置
            config_path = model_path / "config.json"
            if config_path.exists():
                import json
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    logger.info(f"模型配置: {config.get('model_type', 'unknown')}")
            
            return True
            
        except Exception as e:
            logger.error(f"验证模型失败: {str(e)}")
            return False
    
    def download_all_models(self) -> Dict[str, Optional[str]]:
        """下载所有模型"""
        results = {}
        
        for model_type in self.models_config.keys():
            logger.info(f"\n{'='*50}")
            logger.info(f"处理模型: {model_type}")
            logger.info(f"{'='*50}")
            
            model_path = self.download_model(model_type)
            results[model_type] = model_path
            
            if model_path:
                logger.info(f"✅ {model_type} 模型下载成功")
            else:
                logger.error(f"❌ {model_type} 模型下载失败")
        
        return results
    
    def get_model_info(self) -> Dict[str, Dict]:
        """获取模型信息"""
        info = {}
        
        for model_type, config in self.models_config.items():
            model_id = config["model_id"]
            model_path = self.cache_dir / model_id.replace("/", "--")
            
            info[model_type] = {
                "model_id": model_id,
                "description": config["description"],
                "local_path": str(model_path),
                "exists": self.check_model_exists(model_type),
                "size_mb": self._get_directory_size(model_path) if model_path.exists() else 0
            }
        
        return info
    
    def _get_directory_size(self, path: Path) -> float:
        """获取目录大小（MB）"""
        try:
            total_size = 0
            for file_path in path.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
            return total_size / (1024 * 1024)  # 转换为MB
        except Exception:
            return 0
    
    def cleanup_incomplete_downloads(self):
        """清理不完整的下载"""
        try:
            for model_type in self.models_config.keys():
                if not self.check_model_exists(model_type):
                    model_id = self.models_config[model_type]["model_id"]
                    model_path = self.cache_dir / model_id.replace("/", "--")
                    
                    if model_path.exists():
                        logger.info(f"清理不完整的模型: {model_path}")
                        import shutil
                        shutil.rmtree(model_path)
                        
        except Exception as e:
            logger.error(f"清理不完整下载失败: {str(e)}")


def check_system_requirements():
    """检查系统要求"""
    logger.info("检查系统要求...")
    
    # 检查Python版本
    python_version = sys.version_info
    if python_version < (3, 8):
        logger.error(f"Python版本过低: {python_version}, 需要3.8+")
        return False
    
    # 检查可用磁盘空间
    import shutil
    free_space = shutil.disk_usage(".").free / (1024**3)  # GB
    if free_space < 5:
        logger.warning(f"磁盘空间不足: {free_space:.1f}GB, 建议至少5GB")
    
    # 检查PyTorch
    try:
        import torch
        logger.info(f"PyTorch版本: {torch.__version__}")
        logger.info(f"CUDA可用: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            logger.info(f"CUDA版本: {torch.version.cuda}")
            logger.info(f"GPU数量: {torch.cuda.device_count()}")
    except ImportError:
        logger.warning("PyTorch未安装，某些功能可能不可用")
    
    # 检查ModelScope
    try:
        import modelscope
        logger.info(f"ModelScope版本: {modelscope.__version__}")
    except ImportError:
        logger.error("ModelScope未安装，无法下载模型")
        return False
    
    return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="下载智能客服系统所需的AI模型")
    parser.add_argument(
        "--cache-dir", 
        default="./models",
        help="模型缓存目录 (默认: ./models)"
    )
    parser.add_argument(
        "--force", 
        action="store_true",
        help="强制重新下载已存在的模型"
    )
    parser.add_argument(
        "--model-type",
        choices=["embedding", "rerank", "all"],
        default="all",
        help="要下载的模型类型 (默认: all)"
    )
    parser.add_argument(
        "--info",
        action="store_true",
        help="仅显示模型信息，不下载"
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="清理不完整的下载"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="验证已下载的模型"
    )
    
    args = parser.parse_args()
    
    # 检查系统要求
    if not check_system_requirements():
        logger.error("系统要求检查失败")
        sys.exit(1)
    
    # 创建下载器
    downloader = ModelDownloader(
        cache_dir=args.cache_dir,
        force_download=args.force
    )
    
    try:
        if args.cleanup:
            logger.info("清理不完整的下载...")
            downloader.cleanup_incomplete_downloads()
            return
        
        if args.info:
            logger.info("获取模型信息...")
            model_info = downloader.get_model_info()
            
            print("\n" + "="*60)
            print("模型信息")
            print("="*60)
            
            for model_type, info in model_info.items():
                print(f"\n{model_type.upper()} 模型:")
                print(f"  ID: {info['model_id']}")
                print(f"  描述: {info['description']}")
                print(f"  本地路径: {info['local_path']}")
                print(f"  已下载: {'✅' if info['exists'] else '❌'}")
                if info['exists']:
                    print(f"  大小: {info['size_mb']:.1f} MB")
            
            return
        
        if args.verify:
            logger.info("验证已下载的模型...")
            for model_type in downloader.models_config.keys():
                if downloader.check_model_exists(model_type):
                    logger.info(f"✅ {model_type} 模型验证通过")
                else:
                    logger.error(f"❌ {model_type} 模型验证失败")
            return
        
        # 下载模型
        if args.model_type == "all":
            logger.info("开始下载所有模型...")
            results = downloader.download_all_models()
        else:
            logger.info(f"开始下载 {args.model_type} 模型...")
            model_path = downloader.download_model(args.model_type)
            results = {args.model_type: model_path}
        
        # 输出结果摘要
        print("\n" + "="*60)
        print("下载结果摘要")
        print("="*60)
        
        success_count = 0
        for model_type, model_path in results.items():
            if model_path:
                print(f"✅ {model_type}: {model_path}")
                success_count += 1
            else:
                print(f"❌ {model_type}: 下载失败")
        
        print(f"\n成功下载: {success_count}/{len(results)} 个模型")
        
        if success_count == len(results):
            print("\n🎉 所有模型下载完成！")
            print("现在可以启动智能客服系统了。")
        else:
            print("\n⚠️  部分模型下载失败，请检查网络连接和日志信息。")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("用户中断下载")
        sys.exit(1)
    except Exception as e:
        logger.error(f"下载过程中发生错误: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
