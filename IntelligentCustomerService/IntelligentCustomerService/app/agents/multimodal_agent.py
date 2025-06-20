"""
多模态智能体
负责处理包含图像、视频、音频等多媒体内容的用户请求
"""

import asyncio
import base64
import logging
from typing import Any, Dict, List, Optional, Union, Tuple
from datetime import datetime
import mimetypes
import os
from pathlib import Path

from autogen_core import CancellationToken
from PIL import Image
import io

from .base_agent import BaseAgent
from ..core.model_manager import model_manager, ModelType

logger = logging.getLogger(__name__)


class MediaProcessor:
    """媒体处理器"""
    
    @staticmethod
    def is_image(file_path_or_data: Union[str, bytes]) -> bool:
        """检查是否为图像文件"""
        if isinstance(file_path_or_data, str):
            mime_type, _ = mimetypes.guess_type(file_path_or_data)
            return mime_type and mime_type.startswith('image/')
        elif isinstance(file_path_or_data, bytes):
            try:
                Image.open(io.BytesIO(file_path_or_data))
                return True
            except Exception:
                return False
        return False
    
    @staticmethod
    def is_video(file_path: str) -> bool:
        """检查是否为视频文件"""
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type and mime_type.startswith('video/')
    
    @staticmethod
    def is_audio(file_path: str) -> bool:
        """检查是否为音频文件"""
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type and mime_type.startswith('audio/')
    
    @staticmethod
    async def process_image(image_data: Union[str, bytes], max_size: Tuple[int, int] = (1024, 1024)) -> bytes:
        """处理图像数据"""
        try:
            if isinstance(image_data, str):
                # 文件路径
                with open(image_data, 'rb') as f:
                    image_bytes = f.read()
            else:
                # 字节数据
                image_bytes = image_data
            
            # 使用PIL处理图像
            image = Image.open(io.BytesIO(image_bytes))
            
            # 转换为RGB模式
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # 调整大小
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # 转换为字节
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=85)
            
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"图像处理失败: {str(e)}")
            raise
    
    @staticmethod
    def encode_image_to_base64(image_data: bytes) -> str:
        """将图像编码为base64"""
        return base64.b64encode(image_data).decode('utf-8')
    
    @staticmethod
    def create_data_url(image_data: bytes, mime_type: str = "image/jpeg") -> str:
        """创建data URL"""
        base64_data = MediaProcessor.encode_image_to_base64(image_data)
        return f"data:{mime_type};base64,{base64_data}"


class MultimodalAgent(BaseAgent):
    """
    多模态智能体
    
    主要职责：
    - 处理包含图像的用户请求
    - 分析图像内容并提供描述
    - 回答关于图像的问题
    - 处理视频和音频内容（未来扩展）
    - 多模态内容的理解和生成
    """
    
    def __init__(
        self,
        name: str = "MultimodalAgent",
        system_message: str = None,
        model_config: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """
        初始化多模态智能体
        
        Args:
            name: 智能体名称
            system_message: 系统提示词
            model_config: 模型配置
            **kwargs: 其他配置参数
        """
        if system_message is None:
            system_message = self._get_default_system_message()
        
        super().__init__(
            name=name,
            system_message=system_message,
            model_config=model_config,
            **kwargs
        )
        
        # 多模态配置
        self.max_image_size = model_config.get('max_image_size', (1024, 1024)) if model_config else (1024, 1024)
        self.supported_formats = model_config.get('supported_formats', ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']) if model_config else ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']
        self.max_file_size = model_config.get('max_file_size', 10 * 1024 * 1024) if model_config else 10 * 1024 * 1024  # 10MB
        
        # 媒体处理器
        self.media_processor = MediaProcessor()
        
        # 多模态模型服务
        self.multimodal_service = None
        
        # 处理统计
        self.image_processed = 0
        self.video_processed = 0
        self.audio_processed = 0
        
        logger.info(f"多模态智能体 {self.name} 初始化完成")
    
    def _get_default_system_message(self) -> str:
        """获取默认系统提示词"""
        return """你是一个专业的多模态AI助手。你的主要职责是：

1. 分析和理解用户上传的图像、视频、音频等多媒体内容
2. 提供准确、详细的内容描述和分析
3. 回答用户关于多媒体内容的问题
4. 识别图像中的对象、文字、场景等信息
5. 提供有用的建议和见解

你具备以下能力：
- 图像识别和分析
- 文字识别（OCR）
- 场景理解
- 对象检测
- 情感分析
- 内容总结

请始终提供准确、有用的分析结果，如果无法确定某些信息，请诚实说明。"""
    
    async def initialize_services(self):
        """初始化服务依赖"""
        try:
            # 获取多模态模型服务
            self.multimodal_service = model_manager.get_default_model(ModelType.MULTIMODAL)
            if not self.multimodal_service:
                logger.warning("多模态模型服务不可用，将影响图像分析功能")
            
            logger.info(f"多模态智能体 {self.name} 服务初始化完成")
            
        except Exception as e:
            logger.error(f"多模态智能体服务初始化失败: {str(e)}")
            raise
    
    async def _handle_message(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        cancellation_token: Optional[CancellationToken] = None
    ) -> str:
        """
        处理多模态请求的核心逻辑
        
        Args:
            message: 用户消息
            context: 上下文信息（包含多媒体文件）
            cancellation_token: 取消令牌
            
        Returns:
            多模态分析结果
        """
        try:
            # 确保服务已初始化
            if not self.multimodal_service:
                await self.initialize_services()
            
            # 检查是否包含多媒体内容
            media_content = await self._extract_media_content(context)
            
            if not media_content:
                return "我没有检测到任何图像、视频或音频内容。请上传多媒体文件，我将为您分析。"
            
            # 处理不同类型的媒体内容
            analysis_results = []
            
            for media_item in media_content:
                media_type = media_item['type']
                
                if media_type == 'image':
                    result = await self._analyze_image(media_item, message, context)
                    analysis_results.append(result)
                elif media_type == 'video':
                    result = await self._analyze_video(media_item, message, context)
                    analysis_results.append(result)
                elif media_type == 'audio':
                    result = await self._analyze_audio(media_item, message, context)
                    analysis_results.append(result)
            
            # 生成综合回答
            response = await self._generate_multimodal_response(
                message, analysis_results, context
            )
            
            return response
            
        except Exception as e:
            logger.error(f"多模态处理失败: {str(e)}")
            return f"抱歉，在处理多媒体内容时遇到了问题：{str(e)}"
    
    async def _extract_media_content(self, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """提取多媒体内容"""
        media_content = []
        
        if not context:
            return media_content
        
        # 从上下文中提取图像
        images = context.get('images', [])
        for image in images:
            media_content.append({
                'type': 'image',
                'data': image.get('data'),
                'filename': image.get('filename', ''),
                'mime_type': image.get('mime_type', 'image/jpeg')
            })
        
        # 从上下文中提取文件
        files = context.get('files', [])
        for file_info in files:
            file_path = file_info.get('path', '')
            filename = file_info.get('filename', '')
            
            if self.media_processor.is_image(file_path):
                media_content.append({
                    'type': 'image',
                    'path': file_path,
                    'filename': filename,
                    'mime_type': file_info.get('mime_type', 'image/jpeg')
                })
            elif self.media_processor.is_video(file_path):
                media_content.append({
                    'type': 'video',
                    'path': file_path,
                    'filename': filename,
                    'mime_type': file_info.get('mime_type', 'video/mp4')
                })
            elif self.media_processor.is_audio(file_path):
                media_content.append({
                    'type': 'audio',
                    'path': file_path,
                    'filename': filename,
                    'mime_type': file_info.get('mime_type', 'audio/mpeg')
                })
        
        return media_content
    
    async def _analyze_image(
        self,
        image_item: Dict[str, Any],
        user_message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """分析图像内容"""
        try:
            self.image_processed += 1
            
            # 获取图像数据
            if 'data' in image_item:
                image_data = image_item['data']
            elif 'path' in image_item:
                with open(image_item['path'], 'rb') as f:
                    image_data = f.read()
            else:
                raise ValueError("图像数据不可用")
            
            # 检查文件大小
            if len(image_data) > self.max_file_size:
                raise ValueError(f"图像文件过大，最大支持 {self.max_file_size / 1024 / 1024:.1f}MB")
            
            # 处理图像
            processed_image = await self.media_processor.process_image(
                image_data, self.max_image_size
            )
            
            # 使用多模态模型分析
            if self.multimodal_service:
                # 构建分析提示词
                analysis_prompt = self._build_image_analysis_prompt(user_message)
                
                # 调用多模态模型
                analysis_result = await self.multimodal_service.analyze_image(
                    image_data=processed_image,
                    prompt=analysis_prompt
                )
                
                return {
                    'type': 'image',
                    'filename': image_item.get('filename', '未知图像'),
                    'analysis': analysis_result,
                    'success': True,
                    'processed_at': datetime.now().isoformat()
                }
            else:
                # 降级处理：基础图像信息
                return await self._basic_image_analysis(processed_image, image_item)
                
        except Exception as e:
            logger.error(f"图像分析失败: {str(e)}")
            return {
                'type': 'image',
                'filename': image_item.get('filename', '未知图像'),
                'analysis': f"图像分析失败: {str(e)}",
                'success': False,
                'error': str(e)
            }
    
    def _build_image_analysis_prompt(self, user_message: str) -> str:
        """构建图像分析提示词"""
        base_prompt = "请详细分析这张图像，包括："
        
        # 根据用户消息调整分析重点
        if any(word in user_message.lower() for word in ['文字', '文本', 'text', 'ocr']):
            base_prompt += "\n- 识别图像中的所有文字内容"
        
        if any(word in user_message.lower() for word in ['对象', '物体', 'object', '识别']):
            base_prompt += "\n- 识别图像中的主要对象和物体"
        
        if any(word in user_message.lower() for word in ['场景', 'scene', '环境']):
            base_prompt += "\n- 描述图像的场景和环境"
        
        if any(word in user_message.lower() for word in ['颜色', 'color', '色彩']):
            base_prompt += "\n- 分析图像的色彩构成"
        
        if any(word in user_message.lower() for word in ['情感', 'emotion', '感觉']):
            base_prompt += "\n- 分析图像传达的情感或氛围"
        
        # 默认分析内容
        base_prompt += """
- 图像的主要内容和主题
- 图像中的重要细节
- 图像的整体质量和特点
- 任何值得注意的特殊元素

请用中文回答，内容要详细且准确。"""
        
        if user_message and user_message.strip():
            base_prompt += f"\n\n用户特别询问: {user_message}"
        
        return base_prompt
    
    async def _basic_image_analysis(self, image_data: bytes, image_item: Dict[str, Any]) -> Dict[str, Any]:
        """基础图像分析（当多模态模型不可用时）"""
        try:
            # 使用PIL获取基础信息
            image = Image.open(io.BytesIO(image_data))
            
            analysis = f"""图像基础信息：
- 尺寸: {image.size[0]} x {image.size[1]} 像素
- 模式: {image.mode}
- 格式: {image.format or '未知'}
- 文件大小: {len(image_data) / 1024:.1f} KB

注意：由于多模态模型服务不可用，无法提供详细的内容分析。请确保多模态模型服务正常运行以获得完整的图像分析功能。"""
            
            return {
                'type': 'image',
                'filename': image_item.get('filename', '未知图像'),
                'analysis': analysis,
                'success': True,
                'basic_info': {
                    'width': image.size[0],
                    'height': image.size[1],
                    'mode': image.mode,
                    'format': image.format,
                    'size_kb': len(image_data) / 1024
                }
            }
            
        except Exception as e:
            logger.error(f"基础图像分析失败: {str(e)}")
            return {
                'type': 'image',
                'filename': image_item.get('filename', '未知图像'),
                'analysis': f"无法分析图像: {str(e)}",
                'success': False,
                'error': str(e)
            }
    
    async def _analyze_video(
        self,
        video_item: Dict[str, Any],
        user_message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """分析视频内容（未来实现）"""
        self.video_processed += 1
        
        return {
            'type': 'video',
            'filename': video_item.get('filename', '未知视频'),
            'analysis': '视频分析功能正在开发中，敬请期待。',
            'success': False,
            'note': '视频分析功能将在后续版本中提供'
        }
    
    async def _analyze_audio(
        self,
        audio_item: Dict[str, Any],
        user_message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """分析音频内容（未来实现）"""
        self.audio_processed += 1
        
        return {
            'type': 'audio',
            'filename': audio_item.get('filename', '未知音频'),
            'analysis': '音频分析功能正在开发中，敬请期待。',
            'success': False,
            'note': '音频分析功能将在后续版本中提供'
        }
    
    async def _generate_multimodal_response(
        self,
        user_message: str,
        analysis_results: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """生成多模态分析的综合回答"""
        try:
            if not analysis_results:
                return "没有成功分析任何多媒体内容。"
            
            # 统计分析结果
            successful_analyses = [r for r in analysis_results if r.get('success', False)]
            failed_analyses = [r for r in analysis_results if not r.get('success', False)]
            
            response_parts = []
            
            # 添加成功分析的结果
            if successful_analyses:
                response_parts.append("📸 多媒体内容分析结果：\n")
                
                for i, result in enumerate(successful_analyses, 1):
                    filename = result.get('filename', f'文件{i}')
                    analysis = result.get('analysis', '无分析结果')
                    media_type = result.get('type', '未知类型')
                    
                    response_parts.append(f"**{i}. {filename} ({media_type})**")
                    response_parts.append(analysis)
                    response_parts.append("")  # 空行分隔
            
            # 添加失败分析的信息
            if failed_analyses:
                response_parts.append("❌ 以下文件分析失败：")
                for result in failed_analyses:
                    filename = result.get('filename', '未知文件')
                    error = result.get('error', result.get('analysis', '未知错误'))
                    response_parts.append(f"- {filename}: {error}")
                response_parts.append("")
            
            # 添加总结
            if successful_analyses:
                total_files = len(analysis_results)
                successful_count = len(successful_analyses)
                response_parts.append(f"📊 分析完成：成功处理 {successful_count}/{total_files} 个文件")
                
                if user_message and user_message.strip():
                    response_parts.append(f"\n针对您的问题「{user_message}」，以上是我对上传内容的详细分析。如需更多信息，请告诉我您想了解的具体方面。")
            
            return "\n".join(response_parts)
            
        except Exception as e:
            logger.error(f"生成多模态回答失败: {str(e)}")
            return "分析完成，但生成回答时遇到问题。请查看上述分析结果。"
    
    async def analyze_image_direct(
        self,
        image_data: Union[str, bytes],
        prompt: str = "请描述这张图片"
    ) -> str:
        """
        直接图像分析接口（供其他组件调用）
        
        Args:
            image_data: 图像数据（文件路径或字节数据）
            prompt: 分析提示词
            
        Returns:
            分析结果
        """
        try:
            if not self.multimodal_service:
                await self.initialize_services()
            
            if isinstance(image_data, str):
                with open(image_data, 'rb') as f:
                    image_bytes = f.read()
            else:
                image_bytes = image_data
            
            # 处理图像
            processed_image = await self.media_processor.process_image(
                image_bytes, self.max_image_size
            )
            
            # 分析图像
            if self.multimodal_service:
                result = await self.multimodal_service.analyze_image(
                    image_data=processed_image,
                    prompt=prompt
                )
                return result
            else:
                return "多模态模型服务不可用"
                
        except Exception as e:
            logger.error(f"直接图像分析失败: {str(e)}")
            return f"图像分析失败: {str(e)}"
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """获取处理统计信息"""
        return {
            'agent_name': self.name,
            'images_processed': self.image_processed,
            'videos_processed': self.video_processed,
            'audios_processed': self.audio_processed,
            'total_processed': self.image_processed + self.video_processed + self.audio_processed,
            'supported_formats': self.supported_formats,
            'max_file_size_mb': self.max_file_size / 1024 / 1024,
            'max_image_size': self.max_image_size
        }
