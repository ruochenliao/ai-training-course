"""
AI绘画API
提供文本到图像生成、图像编辑、风格转换等接口
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import json

from ...services.image_generation_service import image_generation_service, ImageGenerationConfig
from ...services.analytics_service import analytics_service, EventType
from ...core.dependency import DependPermission

logger = logging.getLogger(__name__)

image_generation_router = APIRouter()


class ImageGenerationRequest(BaseModel):
    """图像生成请求"""
    prompt: str = Field(..., description="生成提示词")
    negative_prompt: Optional[str] = Field(None, description="负面提示词")
    size: Optional[str] = Field("1024x1024", description="图像尺寸")
    style: Optional[str] = Field(None, description="风格")
    quality: Optional[str] = Field("standard", description="质量")
    num_images: int = Field(1, description="生成数量", ge=1, le=4)
    engine: Optional[str] = Field(None, description="生成引擎")
    user_id: Optional[str] = Field(None, description="用户ID")


class ImageEditRequest(BaseModel):
    """图像编辑请求"""
    image_data: str = Field(..., description="原始图像数据（base64）")
    prompt: str = Field(..., description="编辑提示词")
    mask_data: Optional[str] = Field(None, description="遮罩数据（base64）")
    user_id: Optional[str] = Field(None, description="用户ID")


class ImageGenerationConfigRequest(BaseModel):
    """图像生成配置请求"""
    primary_engine: Optional[str] = Field(None, description="主要生成引擎")
    fallback_engine: Optional[str] = Field(None, description="备用生成引擎")
    default_size: Optional[str] = Field(None, description="默认尺寸")
    max_batch_size: Optional[int] = Field(None, description="最大批量大小")
    timeout: Optional[int] = Field(None, description="超时时间")
    enable_content_filter: Optional[bool] = Field(None, description="启用内容过滤")


@image_generation_router.post("/generate", summary="生成图像")
async def generate_image(request: ImageGenerationRequest, background_tasks: BackgroundTasks):
    """
    生成图像
    
    根据文本提示词生成图像
    """
    try:
        # 跟踪事件
        await analytics_service.track_event(
            event_type=EventType.IMAGE_GENERATED,
            user_id=request.user_id,
            properties={
                "prompt": request.prompt[:100],  # 只记录前100个字符
                "size": request.size,
                "style": request.style,
                "quality": request.quality,
                "num_images": request.num_images,
                "engine": request.engine
            }
        )
        
        # 执行图像生成
        result = await image_generation_service.generate_image(
            prompt=request.prompt,
            negative_prompt=request.negative_prompt,
            size=request.size,
            style=request.style,
            quality=request.quality,
            num_images=request.num_images,
            user_id=request.user_id,
            engine=request.engine
        )
        
        if result["success"]:
            return {
                "success": True,
                "task_id": result["task_id"],
                "images": result["images"],
                "prompt": result["prompt"],
                "engine": result["engine"],
                "parameters": result["parameters"],
                "generation_time": result["generation_time"],
                "timestamp": result["timestamp"]
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"图像生成失败: {result['error']}"
            )
            
    except Exception as e:
        logger.error(f"图像生成失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@image_generation_router.post("/edit", summary="编辑图像")
async def edit_image(request: ImageEditRequest):
    """
    编辑图像
    
    基于提示词编辑现有图像
    """
    try:
        # 跟踪事件
        await analytics_service.track_event(
            event_type=EventType.IMAGE_GENERATED,
            user_id=request.user_id,
            properties={
                "action": "edit_image",
                "prompt": request.prompt[:100],
                "has_mask": request.mask_data is not None
            }
        )
        
        # 执行图像编辑
        result = await image_generation_service.edit_image(
            image_data=request.image_data,
            prompt=request.prompt,
            mask_data=request.mask_data,
            user_id=request.user_id
        )
        
        if result["success"]:
            return {
                "success": True,
                "edited_image": result["edited_image"],
                "prompt": result["prompt"],
                "timestamp": result["timestamp"]
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"图像编辑失败: {result['error']}"
            )
            
    except Exception as e:
        logger.error(f"图像编辑失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@image_generation_router.get("/history", summary="获取生成历史")
async def get_generation_history(
    user_id: Optional[str] = None,
    limit: int = 20
):
    """
    获取图像生成历史
    
    返回用户的图像生成记录
    """
    try:
        history = await image_generation_service.get_generation_history(
            user_id=user_id,
            limit=limit
        )
        
        return {
            "success": True,
            "history": history,
            "count": len(history)
        }
        
    except Exception as e:
        logger.error(f"获取生成历史失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@image_generation_router.get("/tasks", summary="获取活动任务")
async def get_active_tasks():
    """
    获取当前活动的生成任务
    
    返回正在进行的图像生成任务状态
    """
    try:
        tasks = await image_generation_service.get_active_tasks()
        
        return {
            "success": True,
            "active_tasks": tasks
        }
        
    except Exception as e:
        logger.error(f"获取活动任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@image_generation_router.delete("/tasks/{task_id}", summary="取消任务")
async def cancel_task(task_id: str):
    """
    取消图像生成任务
    
    取消指定的生成任务
    """
    try:
        success = await image_generation_service.cancel_task(task_id)
        
        if success:
            return {
                "success": True,
                "message": f"任务 {task_id} 已取消"
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=f"任务 {task_id} 不存在或无法取消"
            )
            
    except Exception as e:
        logger.error(f"取消任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@image_generation_router.get("/engines", summary="获取可用引擎")
async def get_available_engines():
    """
    获取可用的图像生成引擎
    
    返回系统支持的所有生成引擎
    """
    try:
        engines = [
            {
                "name": "dalle3",
                "display_name": "DALL-E 3",
                "description": "OpenAI的最新图像生成模型",
                "supported_sizes": ["1024x1024", "1792x1024", "1024x1792"],
                "supported_styles": ["vivid", "natural"],
                "max_batch_size": 1
            },
            {
                "name": "stable_diffusion",
                "display_name": "Stable Diffusion",
                "description": "开源的图像生成模型",
                "supported_sizes": ["512x512", "768x768", "1024x1024"],
                "supported_styles": ["realistic", "artistic", "anime"],
                "max_batch_size": 4
            },
            {
                "name": "midjourney",
                "display_name": "Midjourney",
                "description": "高质量艺术风格图像生成",
                "supported_sizes": ["1024x1024", "1792x1024"],
                "supported_styles": ["artistic", "photographic", "abstract"],
                "max_batch_size": 4,
                "status": "开发中"
            }
        ]
        
        return {
            "success": True,
            "engines": engines,
            "default_engine": image_generation_service.config.primary_engine
        }
        
    except Exception as e:
        logger.error(f"获取可用引擎失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@image_generation_router.get("/styles", summary="获取可用风格")
async def get_available_styles():
    """
    获取可用的图像风格
    
    返回系统支持的所有图像风格
    """
    try:
        styles = [
            {
                "name": "realistic",
                "display_name": "写实风格",
                "description": "真实感强的照片风格"
            },
            {
                "name": "artistic",
                "display_name": "艺术风格",
                "description": "艺术化的绘画风格"
            },
            {
                "name": "anime",
                "display_name": "动漫风格",
                "description": "日式动漫插画风格"
            },
            {
                "name": "abstract",
                "display_name": "抽象风格",
                "description": "抽象艺术风格"
            },
            {
                "name": "vintage",
                "display_name": "复古风格",
                "description": "复古怀旧风格"
            },
            {
                "name": "cyberpunk",
                "display_name": "赛博朋克",
                "description": "未来科技风格"
            }
        ]
        
        return {
            "success": True,
            "styles": styles
        }
        
    except Exception as e:
        logger.error(f"获取可用风格失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@image_generation_router.get("/config", summary="获取生成配置")
async def get_generation_config():
    """
    获取当前的图像生成配置
    
    返回系统的生成配置信息
    """
    try:
        config = image_generation_service.config
        
        return {
            "success": True,
            "config": {
                "primary_engine": config.primary_engine,
                "fallback_engine": config.fallback_engine,
                "default_size": config.default_size,
                "max_batch_size": config.max_batch_size,
                "timeout": config.timeout,
                "enable_content_filter": config.enable_content_filter,
                "supported_formats": config.supported_formats,
                "output_format": config.output_format
            }
        }
        
    except Exception as e:
        logger.error(f"获取生成配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@image_generation_router.post("/config", summary="更新生成配置")
async def update_generation_config(
    request: ImageGenerationConfigRequest,
    _: str = DependPermission
):
    """
    更新图像生成配置
    
    需要管理员权限
    """
    try:
        # 更新配置
        config_updates = {}
        if request.primary_engine:
            config_updates["primary_engine"] = request.primary_engine
        if request.fallback_engine:
            config_updates["fallback_engine"] = request.fallback_engine
        if request.default_size:
            config_updates["default_size"] = request.default_size
        if request.max_batch_size:
            config_updates["max_batch_size"] = request.max_batch_size
        if request.timeout:
            config_updates["timeout"] = request.timeout
        if request.enable_content_filter is not None:
            config_updates["enable_content_filter"] = request.enable_content_filter
        
        # 应用配置更新
        for key, value in config_updates.items():
            setattr(image_generation_service.config, key, value)
        
        return {
            "success": True,
            "message": "图像生成配置已更新",
            "updated_config": config_updates
        }
        
    except Exception as e:
        logger.error(f"更新生成配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@image_generation_router.post("/test", summary="测试图像生成")
async def test_image_generation():
    """
    测试图像生成功能
    
    执行基础的图像生成测试
    """
    try:
        test_prompt = "一只可爱的小猫咪，卡通风格"
        
        # 执行测试生成
        result = await image_generation_service.generate_image(
            prompt=test_prompt,
            size="512x512",
            num_images=1,
            user_id="test_user"
        )
        
        test_results = {
            "generation_test": result["success"],
            "test_prompt": test_prompt,
            "generation_time": result.get("generation_time", 0),
            "engine_used": result.get("engine", "unknown"),
            "errors": []
        }
        
        if not result["success"]:
            test_results["errors"].append(result.get("error", "未知错误"))
        
        return {
            "success": True,
            "test_results": test_results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"图像生成测试失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@image_generation_router.get("/stats", summary="获取生成统计")
async def get_generation_stats():
    """
    获取图像生成统计信息
    
    返回系统的生成统计数据
    """
    try:
        # 获取历史记录
        history = await image_generation_service.get_generation_history(limit=1000)
        
        # 计算统计信息
        total_generations = len(history)
        successful_generations = len([h for h in history if h.get("success", False)])
        
        # 按日期统计
        daily_stats = {}
        for record in history:
            date = record.get("timestamp", "")[:10]  # 取日期部分
            if date:
                daily_stats[date] = daily_stats.get(date, 0) + 1
        
        # 获取活动任务
        active_tasks = await image_generation_service.get_active_tasks()
        
        return {
            "success": True,
            "stats": {
                "total_generations": total_generations,
                "successful_generations": successful_generations,
                "success_rate": successful_generations / max(total_generations, 1),
                "active_tasks": active_tasks["active_count"],
                "daily_stats": daily_stats
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取生成统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
