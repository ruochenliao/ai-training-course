#!/usr/bin/env python3
"""
简单的模型下载器 - 从魔塔社区下载Qwen模型
"""
import os
import logging
from pathlib import Path

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 模型配置 - 使用项目根目录下的models文件夹
MODELS_DIR = Path(__file__).parent.parent.parent / "models"
EMBEDDING_MODEL_DIR = MODELS_DIR / "embedding" / "Qwen3-8B"
RERANKER_MODEL_DIR = MODELS_DIR / "reranker" / "Qwen3-Reranker-8B"


def download_embedding_model():
    """下载嵌入模型"""
    try:
        from modelscope import snapshot_download
        
        logger.info("🔄 开始下载嵌入模型 Qwen3-8B...")
        
        # 确保目录存在
        EMBEDDING_MODEL_DIR.parent.mkdir(parents=True, exist_ok=True)
        
        # 下载模型
        model_path = snapshot_download(
            'Qwen/Qwen3-8B',
            local_dir=str(EMBEDDING_MODEL_DIR),
            revision='master'
        )
        
        logger.info(f"✅ 嵌入模型下载完成: {model_path}")
        return True
        
    except ImportError:
        logger.error("❌ ModelScope未安装，请运行: pip install modelscope")
        return False
    except Exception as e:
        logger.error(f"❌ 嵌入模型下载失败: {e}")
        return False


def download_reranker_model():
    """下载重排模型"""
    try:
        from modelscope import snapshot_download
        
        logger.info("🔄 开始下载重排模型 Qwen3-Reranker-8B...")
        
        # 确保目录存在
        RERANKER_MODEL_DIR.parent.mkdir(parents=True, exist_ok=True)
        
        # 下载模型
        model_path = snapshot_download(
            'Qwen/Qwen3-Reranker-8B',
            local_dir=str(RERANKER_MODEL_DIR),
            revision='master'
        )
        
        logger.info(f"✅ 重排模型下载完成: {model_path}")
        return True
        
    except ImportError:
        logger.error("❌ ModelScope未安装，请运行: pip install modelscope")
        return False
    except Exception as e:
        logger.error(f"❌ 重排模型下载失败: {e}")
        return False


def check_models_exist():
    """检查模型是否存在"""
    embedding_exists = EMBEDDING_MODEL_DIR.exists() and any(EMBEDDING_MODEL_DIR.iterdir())
    reranker_exists = RERANKER_MODEL_DIR.exists() and any(RERANKER_MODEL_DIR.iterdir())
    
    return {
        "embedding_exists": embedding_exists,
        "reranker_exists": reranker_exists,
        "all_exist": embedding_exists and reranker_exists
    }


def download_all_models():
    """下载所有模型"""
    logger.info("🚀 开始下载所有模型...")
    
    # 检查模型是否已存在
    status = check_models_exist()
    logger.info(f"📊 模型状态: {status}")
    
    success_count = 0
    total_count = 2
    
    # 下载嵌入模型
    if not status["embedding_exists"]:
        if download_embedding_model():
            success_count += 1
    else:
        logger.info("✅ 嵌入模型已存在，跳过下载")
        success_count += 1
    
    # 下载重排模型
    if not status["reranker_exists"]:
        if download_reranker_model():
            success_count += 1
    else:
        logger.info("✅ 重排模型已存在，跳过下载")
        success_count += 1
    
    if success_count == total_count:
        logger.info("🎉 所有模型准备完成！")
        return True
    else:
        logger.warning(f"⚠️ 部分模型下载失败 ({success_count}/{total_count})")
        return False


if __name__ == "__main__":
    success = download_all_models()
    exit(0 if success else 1)
