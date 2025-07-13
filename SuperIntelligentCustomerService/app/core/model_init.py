"""
简单的模型初始化模块
"""
import asyncio
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# 添加models目录到路径
models_dir = Path(__file__).parent.parent.parent / "models"
sys.path.append(str(models_dir))


async def init_models():
    """异步初始化模型"""
    try:
        logger.info("🤖 开始初始化AI模型...")
        
        # 导入下载模块
        from .download_models import download_all_models, check_models_exist
        
        # 检查模型状态
        status = check_models_exist()
        logger.info(f"📊 模型状态检查: {status}")
        
        # 如果模型不存在，在后台下载
        if not status["all_exist"]:
            logger.info("⬇️ 检测到模型缺失，开始后台下载...")
            
            # 在线程池中运行下载任务，避免阻塞启动
            result = await asyncio.to_thread(download_all_models)
            
            if result:
                logger.info("🎉 模型下载完成！")
            else:
                logger.warning("⚠️ 模型下载部分失败，但应用将继续运行")
        else:
            logger.info("✅ 所有模型已存在，跳过下载")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 模型初始化失败: {e}")
        logger.info("📝 应用将继续运行，但AI功能可能受限")
        return False
