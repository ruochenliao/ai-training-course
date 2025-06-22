"""
VLM (Vision Language Model) 多模态服务
"""

import asyncio
import base64
import io
from pathlib import Path
from typing import Dict, Any, List, Union

import httpx
from PIL import Image
from app.core.config import settings
from loguru import logger

from app.core.exceptions import ExternalServiceException


class VLMService:
    """VLM多模态服务类"""
    
    def __init__(self):
        """初始化VLM服务"""
        self.api_key = settings.VLM_API_KEY
        self.base_url = settings.VLM_API_BASE or "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
        self.model = settings.VLM_MODEL_NAME or "qwen-vl-max"
        self.max_retries = 3
        self.timeout = 60
        
        # 支持的图片格式
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp'}
        
        logger.info(f"VLM服务初始化完成，模型: {self.model}")
    
    async def analyze_image(
        self,
        image_data: Union[bytes, str, Path],
        prompt: str = "请详细描述这张图片的内容",
        max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """
        分析单张图片
        
        Args:
            image_data: 图片数据（bytes、base64字符串或文件路径）
            prompt: 分析提示词
            max_tokens: 最大生成token数
            
        Returns:
            分析结果字典
        """
        try:
            # 处理图片数据
            image_base64 = await self._process_image_data(image_data)
            
            # 构建请求
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                    ]
                }
            ]
            
            # 调用API
            result = await self._call_vlm_api(messages, max_tokens)
            
            return {
                "description": result.get("content", ""),
                "model": self.model,
                "usage": result.get("usage", {}),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"图片分析失败: {e}")
            return {
                "description": "",
                "model": self.model,
                "error": str(e),
                "success": False
            }
    
    async def analyze_images_batch(
        self,
        images: List[Union[bytes, str, Path]],
        prompt: str = "请分别描述这些图片的内容",
        max_tokens: int = 2000
    ) -> List[Dict[str, Any]]:
        """
        批量分析多张图片
        
        Args:
            images: 图片数据列表
            prompt: 分析提示词
            max_tokens: 最大生成token数
            
        Returns:
            分析结果列表
        """
        try:
            # 处理所有图片
            image_contents = []
            for i, image_data in enumerate(images):
                image_base64 = await self._process_image_data(image_data)
                image_contents.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}
                })
            
            # 构建请求
            content = [{"type": "text", "text": prompt}] + image_contents
            messages = [{"role": "user", "content": content}]
            
            # 调用API
            result = await self._call_vlm_api(messages, max_tokens)
            
            # 解析结果（假设返回的是对每张图片的描述）
            descriptions = result.get("content", "").split("\n\n")
            
            results = []
            for i, desc in enumerate(descriptions):
                if i < len(images):
                    results.append({
                        "index": i,
                        "description": desc.strip(),
                        "model": self.model,
                        "success": True
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"批量图片分析失败: {e}")
            return [{"index": i, "description": "", "error": str(e), "success": False} 
                   for i in range(len(images))]
    
    async def extract_text_from_image(
        self,
        image_data: Union[bytes, str, Path],
        language: str = "auto"
    ) -> Dict[str, Any]:
        """
        从图片中提取文字（OCR）
        
        Args:
            image_data: 图片数据
            language: 语言设置
            
        Returns:
            提取结果
        """
        try:
            image_base64 = await self._process_image_data(image_data)
            
            prompt = "请提取图片中的所有文字内容，保持原有的格式和结构。"
            if language == "zh":
                prompt = "请提取图片中的所有中文文字内容，保持原有的格式和结构。"
            elif language == "en":
                prompt = "Please extract all English text content from the image, maintaining the original format and structure."
            
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                    ]
                }
            ]
            
            result = await self._call_vlm_api(messages, 1500)
            
            return {
                "text": result.get("content", ""),
                "language": language,
                "model": self.model,
                "confidence": 0.9,  # VLM通常不提供置信度，使用默认值
                "success": True
            }
            
        except Exception as e:
            logger.error(f"图片文字提取失败: {e}")
            return {
                "text": "",
                "language": language,
                "error": str(e),
                "success": False
            }
    
    async def analyze_chart_or_diagram(
        self,
        image_data: Union[bytes, str, Path],
        chart_type: str = "auto"
    ) -> Dict[str, Any]:
        """
        分析图表或图形
        
        Args:
            image_data: 图片数据
            chart_type: 图表类型提示
            
        Returns:
            分析结果
        """
        try:
            image_base64 = await self._process_image_data(image_data)
            
            if chart_type == "auto":
                prompt = "请分析这张图片中的图表、图形或数据可视化内容，包括：1. 图表类型 2. 主要数据和趋势 3. 关键信息和结论"
            else:
                prompt = f"这是一张{chart_type}图表，请分析其中的数据和趋势，提取关键信息和结论。"
            
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                    ]
                }
            ]
            
            result = await self._call_vlm_api(messages, 1500)
            
            return {
                "analysis": result.get("content", ""),
                "chart_type": chart_type,
                "model": self.model,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"图表分析失败: {e}")
            return {
                "analysis": "",
                "chart_type": chart_type,
                "error": str(e),
                "success": False
            }
    
    async def generate_image_caption(
        self,
        image_data: Union[bytes, str, Path],
        style: str = "detailed"
    ) -> Dict[str, Any]:
        """
        生成图片标题/描述
        
        Args:
            image_data: 图片数据
            style: 描述风格（detailed/brief/creative）
            
        Returns:
            生成结果
        """
        try:
            image_base64 = await self._process_image_data(image_data)
            
            prompts = {
                "detailed": "请为这张图片生成一个详细的标题和描述，包括主要内容、场景、人物、物体等。",
                "brief": "请为这张图片生成一个简洁的标题。",
                "creative": "请为这张图片生成一个富有创意和想象力的标题和描述。"
            }
            
            prompt = prompts.get(style, prompts["detailed"])
            
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                    ]
                }
            ]
            
            result = await self._call_vlm_api(messages, 500)
            
            return {
                "caption": result.get("content", ""),
                "style": style,
                "model": self.model,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"图片标题生成失败: {e}")
            return {
                "caption": "",
                "style": style,
                "error": str(e),
                "success": False
            }
    
    async def _process_image_data(self, image_data: Union[bytes, str, Path]) -> str:
        """处理图片数据，转换为base64格式"""
        try:
            if isinstance(image_data, (str, Path)):
                # 文件路径
                path = Path(image_data)
                if not path.exists():
                    raise ValueError(f"图片文件不存在: {path}")
                
                if path.suffix.lower() not in self.supported_formats:
                    raise ValueError(f"不支持的图片格式: {path.suffix}")
                
                with open(path, 'rb') as f:
                    image_bytes = f.read()
            
            elif isinstance(image_data, str) and image_data.startswith('data:'):
                # base64数据URL
                return image_data.split(',')[1]
            
            elif isinstance(image_data, str):
                # base64字符串
                return image_data
            
            else:
                # bytes数据
                image_bytes = image_data
            
            # 验证图片并转换为JPEG格式
            try:
                image = Image.open(io.BytesIO(image_bytes))
                
                # 转换为RGB（如果需要）
                if image.mode in ('RGBA', 'LA', 'P'):
                    image = image.convert('RGB')
                
                # 压缩图片（如果太大）
                max_size = (1024, 1024)
                if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                    image.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # 转换为JPEG格式的bytes
                output = io.BytesIO()
                image.save(output, format='JPEG', quality=85)
                image_bytes = output.getvalue()
                
            except Exception as e:
                logger.warning(f"图片处理失败，使用原始数据: {e}")
            
            # 转换为base64
            return base64.b64encode(image_bytes).decode('utf-8')
            
        except Exception as e:
            logger.error(f"图片数据处理失败: {e}")
            raise ExternalServiceException(f"图片数据处理失败: {e}")
    
    async def _call_vlm_api(self, messages: List[Dict], max_tokens: int = 1000) -> Dict[str, Any]:
        """调用VLM API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "input": {
                "messages": messages
            },
            "parameters": {
                "max_tokens": max_tokens,
                "temperature": 0.1
            }
        }
        
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        self.base_url,
                        headers=headers,
                        json=data
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result.get("output"):
                            return {
                                "content": result["output"]["text"],
                                "usage": result.get("usage", {})
                            }
                        else:
                            raise ExternalServiceException(f"API返回格式错误: {result}")
                    else:
                        raise ExternalServiceException(f"API调用失败: {response.status_code} - {response.text}")
                        
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise ExternalServiceException(f"VLM API调用失败: {e}")
                
                logger.warning(f"VLM API调用失败，重试 {attempt + 1}/{self.max_retries}: {e}")
                await asyncio.sleep(2 ** attempt)  # 指数退避
        
        raise ExternalServiceException("VLM API调用超过最大重试次数")


# 全局VLM服务实例
vlm_service = VLMService()
