"""
模型下载工具
从魔塔社区(ModelScope)下载Qwen3-8B嵌入模型和Qwen3-Reranker-8B重排模型
"""
import asyncio
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional, Dict, Any

try:
    from modelscope import snapshot_download
    from modelscope.hub.api import HubApi
    MODELSCOPE_AVAILABLE = True
except ImportError:
    MODELSCOPE_AVAILABLE = False
    snapshot_download = None
    HubApi = None

logger = logging.getLogger(__name__)


class ModelDownloader:
    """模型下载器 - 从魔塔社区下载模型"""
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        初始化模型下载器

        Args:
            cache_dir: 模型缓存目录，默认为项目根目录下的models文件夹
        """

        # 设置缓存目录
        if cache_dir is None:
            project_root = Path(__file__).parent.parent.parent
            cache_dir = project_root / "models"

        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # 设置ModelScope环境变量，强制使用项目目录
        import os
        os.environ['MODELSCOPE_CACHE'] = str(self.cache_dir)
        os.environ['HF_HOME'] = str(self.cache_dir)  # 也设置HuggingFace缓存目录
        logger.info(f"设置ModelScope缓存目录: {self.cache_dir}")
        
        # 模型配置 - 使用魔塔社区的Qwen模型
        self.models_config = {
            "embedding": {
                "model_id": "Qwen/Qwen3-0.6B",  # 魔塔社区Qwen3-0.6B模型
                "model_name": "Qwen3-0.6B",
                "description": "Qwen3-0.6B嵌入模型",
                "cache_subdir": "embedding"
            },
            "reranker": {
                "model_id": "Qwen/Qwen3-Reranker-0.6B",  # 魔塔社区Qwen3-Reranker-0.6B模型
                "model_name": "Qwen3-Reranker-0.6B",
                "description": "Qwen3-Reranker-0.6B重排模型",
                "cache_subdir": "reranker"
            }
        }
        
        logger.info(f"模型下载器初始化完成，缓存目录: {self.cache_dir}")
    
    def get_model_cache_path(self, model_type: str) -> Path:
        """获取模型缓存路径"""
        if model_type not in self.models_config:
            raise ValueError(f"不支持的模型类型: {model_type}")
        
        config = self.models_config[model_type]
        return self.cache_dir / config["cache_subdir"] / config["model_name"]
    
    def is_model_cached(self, model_type: str) -> bool:
        """检查模型是否已缓存"""
        model_path = self.get_model_cache_path(model_type)
        return model_path.exists() and any(model_path.iterdir())
    
    async def download_model_async(self, model_type: str, force_download: bool = False) -> str:
        """异步下载模型"""
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            return await loop.run_in_executor(
                executor, 
                self.download_model, 
                model_type, 
                force_download
            )
    
    def download_model(self, model_type: str, force_download: bool = False) -> str:
        """
        下载指定类型的模型
        
        Args:
            model_type: 模型类型 ('embedding' 或 'reranker')
            force_download: 是否强制重新下载
            
        Returns:
            模型本地路径
        """
        if model_type not in self.models_config:
            raise ValueError(f"不支持的模型类型: {model_type}，支持的类型: {list(self.models_config.keys())}")
        
        config = self.models_config[model_type]
        model_path = self.get_model_cache_path(model_type)
        
        # 检查是否已缓存
        if not force_download and self.is_model_cached(model_type):
            logger.info(f"✅ {config['description']}已缓存: {model_path}")
            return str(model_path)
        
        logger.info(f"🚀 开始下载{config['description']}...")
        logger.info(f"📍 模型ID: {config['model_id']}")
        logger.info(f"📁 缓存路径: {model_path}")
        
        try:
            # 创建缓存目录
            model_path.mkdir(parents=True, exist_ok=True)

            # 从魔塔社区下载模型到指定目录
            # 环境变量已在__init__中设置，这里直接使用local_dir参数
            downloaded_path = snapshot_download(
                model_id=config['model_id'],
                local_dir=str(model_path),      # 指定本地存储目录
                revision='master'
            )

            logger.info(f"✅ {config['description']}下载完成: {downloaded_path}")
            return downloaded_path

        except Exception as e:
            logger.error(f"❌ {config['description']}下载失败: {e}")
            raise
    
    def download_all_models(self, force_download: bool = False) -> Dict[str, str]:
        """
        下载所有模型
        
        Args:
            force_download: 是否强制重新下载
            
        Returns:
            模型类型到路径的映射
        """
        results = {}
        
        for model_type in self.models_config.keys():
            try:
                model_path = self.download_model(model_type, force_download)
                results[model_type] = model_path
            except Exception as e:
                logger.error(f"下载{model_type}模型失败: {e}")
                results[model_type] = None
        
        return results
    
    async def download_all_models_async(self, force_download: bool = False) -> Dict[str, str]:
        """异步下载所有模型"""
        tasks = []
        for model_type in self.models_config.keys():
            task = self.download_model_async(model_type, force_download)
            tasks.append((model_type, task))
        
        results = {}
        for model_type, task in tasks:
            try:
                model_path = await task
                results[model_type] = model_path
            except Exception as e:
                logger.error(f"异步下载{model_type}模型失败: {e}")
                results[model_type] = None
        
        return results
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        info = {
            "cache_dir": str(self.cache_dir),
            "models": {},
            "total_cache_size": 0,
            "modelscope_config": {
                "cache_env": os.environ.get('MODELSCOPE_CACHE', 'Not Set'),
                "hf_home_env": os.environ.get('HF_HOME', 'Not Set')
            }
        }

        total_size = 0
        for model_type, config in self.models_config.items():
            model_path = self.get_model_cache_path(model_type)
            is_cached = self.is_model_cached(model_type)
            cache_size = self._get_directory_size(model_path) if is_cached else 0
            total_size += cache_size

            info["models"][model_type] = {
                "model_id": config["model_id"],
                "model_name": config["model_name"],
                "description": config["description"],
                "cache_path": str(model_path),
                "is_cached": is_cached,
                "cache_size": cache_size,
                "cache_size_mb": round(cache_size / (1024 * 1024), 2),
                "last_modified": self._get_last_modified(model_path) if is_cached else None
            }

        info["total_cache_size"] = total_size
        info["total_cache_size_mb"] = round(total_size / (1024 * 1024), 2)

        return info
    
    def _get_directory_size(self, path: Path) -> int:
        """获取目录大小（字节）"""
        if not path.exists():
            return 0

        total_size = 0
        try:
            for file_path in path.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
        except Exception as e:
            logger.warning(f"计算目录大小失败: {e}")

        return total_size

    def _get_last_modified(self, path: Path) -> str:
        """获取目录最后修改时间"""
        if not path.exists():
            return None

        try:
            # 获取目录中最新文件的修改时间
            latest_time = 0
            for file_path in path.rglob('*'):
                if file_path.is_file():
                    file_time = file_path.stat().st_mtime
                    if file_time > latest_time:
                        latest_time = file_time

            if latest_time > 0:
                from datetime import datetime
                return datetime.fromtimestamp(latest_time).isoformat()
        except Exception as e:
            logger.warning(f"获取最后修改时间失败: {e}")

        return None

    def get_download_progress(self, model_type: str) -> Dict[str, Any]:
        """获取模型下载进度（简化版本）"""
        if model_type not in self.models_config:
            return {"status": "unknown", "progress": 0}

        model_path = self.get_model_cache_path(model_type)
        if self.is_model_cached(model_type):
            return {"status": "completed", "progress": 100}
        elif model_path.exists():
            return {"status": "downloading", "progress": 50}  # 简化的进度估算
        else:
            return {"status": "not_started", "progress": 0}

    def validate_model_integrity(self, model_type: str) -> bool:
        """验证模型完整性"""
        if not self.is_model_cached(model_type):
            return False

        model_path = self.get_model_cache_path(model_type)
        try:
            # 检查关键文件是否存在
            required_files = ['config.json', 'pytorch_model.bin']  # 或其他必需文件
            for file_name in required_files:
                file_path = model_path / file_name
                if not file_path.exists():
                    # 尝试查找其他可能的模型文件
                    model_files = list(model_path.glob('*.bin')) + list(model_path.glob('*.safetensors'))
                    if not model_files:
                        logger.warning(f"模型文件不完整: {model_path}")
                        return False

            return True
        except Exception as e:
            logger.error(f"验证模型完整性失败: {e}")
            return False
    
    def clear_cache(self, model_type: Optional[str] = None):
        """
        清理模型缓存
        
        Args:
            model_type: 要清理的模型类型，None表示清理所有
        """
        if model_type is None:
            # 清理所有模型缓存
            for mt in self.models_config.keys():
                self._clear_model_cache(mt)
        else:
            self._clear_model_cache(model_type)
    
    def _clear_model_cache(self, model_type: str):
        """清理指定模型的缓存"""
        if model_type not in self.models_config:
            logger.warning(f"未知的模型类型: {model_type}")
            return
        
        model_path = self.get_model_cache_path(model_type)
        if model_path.exists():
            import shutil
            try:
                shutil.rmtree(model_path)
                logger.info(f"🧹 已清理{self.models_config[model_type]['description']}缓存")
            except Exception as e:
                logger.error(f"清理缓存失败: {e}")


# 全局模型下载器实例
_model_downloader = None

def get_model_downloader(cache_dir: Optional[str] = None) -> ModelDownloader:
    """获取全局模型下载器实例"""
    global _model_downloader
    if _model_downloader is None:
        _model_downloader = ModelDownloader(cache_dir)
    return _model_downloader
