"""
AI绘画集成服务
提供文本到图像生成、图像编辑、风格转换等功能
"""

import asyncio
import logging
import io
import base64
import json
import hashlib
from typing import Any, Dict, List, Optional, Union, Tuple
from datetime import datetime
import tempfile
import os
from pathlib import Path

import aiofiles
import httpx
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np

from ..core.model_manager import model_manager, ModelType
from ..core.cache_manager import cache_manager
from ..settings.config import settings

logger = logging.getLogger(__name__)


class ImageGenerationConfig:
    """AI绘画配置"""
    
    def __init__(self):
        # 主要生成引擎
        self.primary_engine = "dalle3"  # dalle3, midjourney, stable_diffusion
        self.fallback_engine = "stable_diffusion"
        
        # DALL-E 3 配置
        self.dalle3_model = "dall-e-3"
        self.dalle3_quality = "standard"  # standard, hd
        self.dalle3_style = "vivid"  # vivid, natural
        
        # Stable Diffusion 配置
        self.sd_model = "stable-diffusion-xl-base-1.0"
        self.sd_steps = 20
        self.sd_guidance_scale = 7.5
        self.sd_scheduler = "DPMSolverMultistepScheduler"
        
        # 通用配置
        self.default_size = "1024x1024"
        self.max_batch_size = 4
        self.timeout = 120  # 秒
        
        # 图像处理配置
        self.supported_formats = ["png", "jpg", "jpeg", "webp"]
        self.max_image_size = 10 * 1024 * 1024  # 10MB
        self.output_format = "png"
        
        # 内容安全配置
        self.enable_content_filter = True
        self.nsfw_threshold = 0.8


class ImageGenerationService:
    """AI绘画服务"""
    
    def __init__(self, config: Optional[ImageGenerationConfig] = None):
        self.config = config or ImageGenerationConfig()
        self.generation_history = []
        self.active_tasks = {}
        
        # 初始化HTTP客户端
        self.http_client = httpx.AsyncClient(timeout=self.config.timeout)
        
        logger.info("AI绘画服务初始化完成")
    
    async def generate_image(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        size: Optional[str] = None,
        style: Optional[str] = None,
        quality: Optional[str] = None,
        num_images: int = 1,
        user_id: Optional[str] = None,
        engine: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        生成图像
        
        Args:
            prompt: 生成提示词
            negative_prompt: 负面提示词
            size: 图像尺寸
            style: 风格
            quality: 质量
            num_images: 生成数量
            user_id: 用户ID
            engine: 指定引擎
            
        Returns:
            生成结果字典
        """
        try:
            # 参数验证
            if not prompt or len(prompt.strip()) == 0:
                raise ValueError("提示词不能为空")
            
            if num_images > self.config.max_batch_size:
                raise ValueError(f"批量生成数量不能超过{self.config.max_batch_size}")
            
            # 内容安全检查
            if self.config.enable_content_filter:
                safety_result = await self._check_content_safety(prompt)
                if not safety_result["safe"]:
                    return {
                        "success": False,
                        "error": "内容不符合安全规范",
                        "safety_result": safety_result,
                        "timestamp": datetime.now().isoformat()
                    }
            
            # 生成任务ID
            task_id = self._generate_task_id(prompt, user_id)
            
            # 检查缓存
            cache_key = f"image_gen_{hashlib.md5(prompt.encode()).hexdigest()}_{size}_{style}"
            cached_result = await cache_manager.get(cache_key)
            if cached_result:
                logger.info(f"使用缓存结果: {task_id}")
                return cached_result
            
            # 选择生成引擎
            selected_engine = engine or self.config.primary_engine
            
            # 记录任务开始
            self.active_tasks[task_id] = {
                "prompt": prompt,
                "status": "generating",
                "start_time": datetime.now(),
                "user_id": user_id
            }
            
            try:
                # 根据引擎生成图像
                if selected_engine == "dalle3":
                    result = await self._generate_with_dalle3(
                        prompt, size, style, quality, num_images
                    )
                elif selected_engine == "stable_diffusion":
                    result = await self._generate_with_stable_diffusion(
                        prompt, negative_prompt, size, num_images
                    )
                elif selected_engine == "midjourney":
                    result = await self._generate_with_midjourney(
                        prompt, size, style, num_images
                    )
                else:
                    raise ValueError(f"不支持的生成引擎: {selected_engine}")
                
                # 处理生成结果
                if result["success"]:
                    # 后处理图像
                    processed_images = []
                    for image_data in result["images"]:
                        processed_image = await self._post_process_image(image_data)
                        processed_images.append(processed_image)
                    
                    final_result = {
                        "success": True,
                        "task_id": task_id,
                        "images": processed_images,
                        "prompt": prompt,
                        "engine": selected_engine,
                        "parameters": {
                            "size": size or self.config.default_size,
                            "style": style,
                            "quality": quality,
                            "num_images": num_images
                        },
                        "generation_time": (datetime.now() - self.active_tasks[task_id]["start_time"]).total_seconds(),
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    # 缓存结果
                    await cache_manager.set(cache_key, final_result, expire=3600)
                    
                    # 记录历史
                    self.generation_history.append({
                        "task_id": task_id,
                        "prompt": prompt,
                        "user_id": user_id,
                        "success": True,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    logger.info(f"图像生成成功: {task_id}")
                    return final_result
                else:
                    raise Exception(result.get("error", "生成失败"))
                    
            finally:
                # 清理任务记录
                if task_id in self.active_tasks:
                    del self.active_tasks[task_id]
                    
        except Exception as e:
            logger.error(f"图像生成失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _generate_with_dalle3(
        self,
        prompt: str,
        size: Optional[str],
        style: Optional[str],
        quality: Optional[str],
        num_images: int
    ) -> Dict[str, Any]:
        """使用DALL-E 3生成图像"""
        try:
            # 构建API请求
            api_key = settings.OPENAI_API_KEY
            if not api_key:
                raise ValueError("OpenAI API密钥未配置")
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.config.dalle3_model,
                "prompt": prompt,
                "n": min(num_images, 1),  # DALL-E 3只支持单张
                "size": size or self.config.default_size,
                "quality": quality or self.config.dalle3_quality,
                "style": style or self.config.dalle3_style
            }
            
            # 发送请求
            response = await self.http_client.post(
                "https://api.openai.com/v1/images/generations",
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                images = []
                
                for image_info in result["data"]:
                    # 下载图像
                    image_response = await self.http_client.get(image_info["url"])
                    if image_response.status_code == 200:
                        image_data = base64.b64encode(image_response.content).decode()
                        images.append({
                            "data": image_data,
                            "format": "png",
                            "url": image_info["url"],
                            "revised_prompt": image_info.get("revised_prompt", prompt)
                        })
                
                return {
                    "success": True,
                    "images": images,
                    "engine": "dalle3"
                }
            else:
                error_info = response.json()
                raise Exception(f"DALL-E 3 API错误: {error_info.get('error', {}).get('message', '未知错误')}")
                
        except Exception as e:
            logger.error(f"DALL-E 3生成失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _generate_with_stable_diffusion(
        self,
        prompt: str,
        negative_prompt: Optional[str],
        size: Optional[str],
        num_images: int
    ) -> Dict[str, Any]:
        """使用Stable Diffusion生成图像"""
        try:
            # 这里可以集成Stability AI API或本地Stable Diffusion
            # 暂时使用模拟实现
            await asyncio.sleep(2)  # 模拟生成时间
            
            # 创建模拟图像
            images = []
            for i in range(num_images):
                # 创建一个简单的彩色图像作为示例
                img = Image.new('RGB', (1024, 1024), color=(100 + i * 30, 150, 200))
                
                # 转换为base64
                buffer = io.BytesIO()
                img.save(buffer, format='PNG')
                image_data = base64.b64encode(buffer.getvalue()).decode()
                
                images.append({
                    "data": image_data,
                    "format": "png",
                    "seed": 12345 + i,
                    "steps": self.config.sd_steps
                })
            
            return {
                "success": True,
                "images": images,
                "engine": "stable_diffusion"
            }
            
        except Exception as e:
            logger.error(f"Stable Diffusion生成失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _generate_with_midjourney(
        self,
        prompt: str,
        size: Optional[str],
        style: Optional[str],
        num_images: int
    ) -> Dict[str, Any]:
        """使用Midjourney生成图像"""
        try:
            # 这里可以集成Midjourney API
            # 暂时使用模拟实现
            await asyncio.sleep(3)  # 模拟生成时间
            
            return {
                "success": False,
                "error": "Midjourney集成正在开发中"
            }
            
        except Exception as e:
            logger.error(f"Midjourney生成失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _check_content_safety(self, prompt: str) -> Dict[str, Any]:
        """检查内容安全性"""
        try:
            # 简单的关键词过滤
            unsafe_keywords = [
                "暴力", "血腥", "恐怖", "色情", "裸体", "政治", "敏感"
            ]
            
            prompt_lower = prompt.lower()
            for keyword in unsafe_keywords:
                if keyword in prompt_lower:
                    return {
                        "safe": False,
                        "reason": f"包含不当内容: {keyword}",
                        "confidence": 0.9
                    }
            
            return {
                "safe": True,
                "confidence": 0.95
            }
            
        except Exception as e:
            logger.error(f"内容安全检查失败: {str(e)}")
            return {
                "safe": True,  # 默认通过
                "confidence": 0.5
            }
    
    async def _post_process_image(self, image_data: Dict[str, Any]) -> Dict[str, Any]:
        """后处理图像"""
        try:
            # 解码图像
            image_bytes = base64.b64decode(image_data["data"])
            image = Image.open(io.BytesIO(image_bytes))
            
            # 图像优化
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # 压缩优化
            if image.size[0] > 2048 or image.size[1] > 2048:
                image.thumbnail((2048, 2048), Image.Resampling.LANCZOS)
            
            # 保存优化后的图像
            buffer = io.BytesIO()
            image.save(buffer, format=self.config.output_format.upper(), quality=90, optimize=True)
            optimized_data = base64.b64encode(buffer.getvalue()).decode()
            
            # 生成缩略图
            thumbnail = image.copy()
            thumbnail.thumbnail((256, 256), Image.Resampling.LANCZOS)
            thumb_buffer = io.BytesIO()
            thumbnail.save(thumb_buffer, format='JPEG', quality=80)
            thumbnail_data = base64.b64encode(thumb_buffer.getvalue()).decode()
            
            return {
                **image_data,
                "data": optimized_data,
                "thumbnail": thumbnail_data,
                "size": image.size,
                "file_size": len(buffer.getvalue()),
                "optimized": True
            }
            
        except Exception as e:
            logger.error(f"图像后处理失败: {str(e)}")
            return image_data
    
    def _generate_task_id(self, prompt: str, user_id: Optional[str]) -> str:
        """生成任务ID"""
        content = f"{prompt}_{user_id}_{datetime.now().isoformat()}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    async def edit_image(
        self,
        image_data: str,
        prompt: str,
        mask_data: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        编辑图像
        
        Args:
            image_data: 原始图像数据（base64）
            prompt: 编辑提示词
            mask_data: 遮罩数据（base64）
            user_id: 用户ID
            
        Returns:
            编辑结果字典
        """
        try:
            # 这里可以集成图像编辑API
            # 暂时使用模拟实现
            await asyncio.sleep(1)
            
            return {
                "success": True,
                "edited_image": image_data,  # 返回原图作为示例
                "prompt": prompt,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"图像编辑失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_generation_history(
        self,
        user_id: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """获取生成历史"""
        try:
            history = self.generation_history
            
            if user_id:
                history = [h for h in history if h.get("user_id") == user_id]
            
            return history[-limit:]
            
        except Exception as e:
            logger.error(f"获取生成历史失败: {str(e)}")
            return []
    
    async def get_active_tasks(self) -> Dict[str, Any]:
        """获取活动任务"""
        return {
            "active_count": len(self.active_tasks),
            "tasks": list(self.active_tasks.values())
        }
    
    async def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        try:
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
                logger.info(f"任务已取消: {task_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"取消任务失败: {str(e)}")
            return False
    
    async def cleanup(self):
        """清理资源"""
        try:
            await self.http_client.aclose()
            logger.info("AI绘画服务资源清理完成")
        except Exception as e:
            logger.error(f"资源清理失败: {str(e)}")


# 全局图像生成服务实例
image_generation_service = ImageGenerationService()
