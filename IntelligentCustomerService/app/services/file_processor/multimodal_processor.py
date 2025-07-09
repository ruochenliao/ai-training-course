"""
多模态处理器
使用多模态LLM生成图片描述
"""
import asyncio
import base64
import logging
import time
from typing import Dict, List, Any, Optional
from pathlib import Path

try:
    # 阿里云DashScope多模态API
    from dashscope import MultiModalConversation
    DASHSCOPE_AVAILABLE = True
except ImportError:
    DASHSCOPE_AVAILABLE = False
    MultiModalConversation = None

from .processor_config import ProcessorConfig

logger = logging.getLogger(__name__)


class MultimodalProcessor:
    """
    多模态处理器
    使用VLLM API生成图片描述
    """
    
    def __init__(self, config: ProcessorConfig):
        """
        初始化多模态处理器
        
        Args:
            config: 处理器配置
        """
        self.config = config
        self.multimodal_config = config.multimodal_config
        self.initialized = False
        
        # 统计信息
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_processing_time": 0.0,
            "average_processing_time": 0.0,
            "api_errors": {}
        }
        
        logger.info("多模态处理器初始化完成")
    
    async def initialize(self) -> None:
        """初始化处理器"""
        try:
            if not DASHSCOPE_AVAILABLE:
                logger.warning("DashScope库不可用，多模态功能将受限")
            
            # 检查API密钥
            api_key = self.multimodal_config.get("api_key")
            if not api_key:
                logger.warning("未配置DashScope API密钥")
            
            self.initialized = True
            logger.info("多模态处理器初始化成功")
            
        except Exception as e:
            logger.error(f"多模态处理器初始化失败: {e}")
            raise
    
    async def analyze_image(
        self,
        image_data: bytes,
        filename: str = None,
        metadata: Dict[str, Any] = None,
        custom_prompt: str = None
    ) -> Dict[str, Any]:
        """
        分析单张图片
        
        Args:
            image_data: 图片数据
            filename: 文件名
            metadata: 元数据
            custom_prompt: 自定义提示词
            
        Returns:
            分析结果
        """
        start_time = time.time()
        
        try:
            if not self.initialized:
                raise RuntimeError("多模态处理器未初始化")
            
            self.stats["total_requests"] += 1
            
            # 验证图片
            if not self._validate_image(image_data, filename):
                raise ValueError("无效的图片数据")
            
            # 编码图片为Base64
            image_base64 = self._encode_image_to_base64(image_data)
            
            # 构建提示词
            prompt = custom_prompt or self._build_analysis_prompt(filename, metadata)
            
            # 调用多模态API
            if DASHSCOPE_AVAILABLE and self.multimodal_config.get("api_key"):
                result = await self._call_dashscope_api(image_base64, prompt)
            else:
                # 降级到简单描述
                result = await self._fallback_description(filename, len(image_data))
            
            # 更新统计信息
            processing_time = time.time() - start_time
            self._update_stats(processing_time, True)
            
            result["processing_time"] = processing_time
            result["filename"] = filename
            
            logger.info(f"图片分析完成: {filename}, 耗时: {processing_time:.2f}秒")
            
            return result
            
        except Exception as e:
            # 更新错误统计
            processing_time = time.time() - start_time
            self._update_stats(processing_time, False)
            
            logger.error(f"图片分析失败: {filename}, 错误: {e}")
            
            return {
                "success": False,
                "error": str(e),
                "description": "",
                "metadata": {},
                "processing_time": processing_time,
                "filename": filename
            }
    
    async def analyze_batch(
        self,
        images: List[Dict[str, Any]],
        batch_prompt: str = None
    ) -> List[Dict[str, Any]]:
        """
        批量分析图片
        
        Args:
            images: 图片列表，每个元素包含 {"data": bytes, "filename": str, "metadata": dict}
            batch_prompt: 批处理提示词
            
        Returns:
            分析结果列表
        """
        try:
            if not images:
                return []
            
            # 限制批处理大小
            batch_size = self.multimodal_config.get("batch_size", 5)
            if len(images) > batch_size:
                logger.warning(f"批处理大小超限，将处理前{batch_size}张图片")
                images = images[:batch_size]
            
            # 并行处理图片
            tasks = []
            for image_info in images:
                task = self.analyze_image(
                    image_data=image_info["data"],
                    filename=image_info.get("filename", "unknown"),
                    metadata=image_info.get("metadata", {}),
                    custom_prompt=batch_prompt
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理异常结果
            final_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    final_results.append({
                        "success": False,
                        "error": str(result),
                        "description": "",
                        "filename": images[i].get("filename", "unknown")
                    })
                else:
                    final_results.append(result)
            
            logger.info(f"批量图片分析完成: {len(final_results)}张图片")
            
            return final_results
            
        except Exception as e:
            logger.error(f"批量图片分析失败: {e}")
            return [{"success": False, "error": str(e)} for _ in images]
    
    def _validate_image(self, image_data: bytes, filename: str = None) -> bool:
        """
        验证图片数据
        
        Args:
            image_data: 图片数据
            filename: 文件名
            
        Returns:
            是否有效
        """
        try:
            # 检查数据大小
            if len(image_data) == 0:
                return False
            
            if len(image_data) > self.config.max_image_size:
                logger.warning(f"图片过大: {len(image_data)} bytes")
                return False
            
            # 检查文件头（简单验证）
            if image_data.startswith(b'\xff\xd8\xff'):  # JPEG
                return True
            elif image_data.startswith(b'\x89PNG\r\n\x1a\n'):  # PNG
                return True
            elif image_data.startswith(b'GIF87a') or image_data.startswith(b'GIF89a'):  # GIF
                return True
            elif image_data.startswith(b'BM'):  # BMP
                return True
            elif image_data.startswith(b'RIFF') and b'WEBP' in image_data[:12]:  # WebP
                return True
            else:
                # 如果有文件名，根据扩展名判断
                if filename:
                    ext = Path(filename).suffix.lower()
                    if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff']:
                        return True
                
                logger.warning(f"未识别的图片格式: {filename}")
                return False
            
        except Exception as e:
            logger.error(f"图片验证失败: {e}")
            return False
    
    def _encode_image_to_base64(self, image_data: bytes) -> str:
        """
        将图片编码为Base64
        
        Args:
            image_data: 图片数据
            
        Returns:
            Base64编码字符串
        """
        return base64.b64encode(image_data).decode('utf-8')
    
    def _build_analysis_prompt(self, filename: str = None, metadata: Dict[str, Any] = None) -> str:
        """
        构建分析提示词
        
        Args:
            filename: 文件名
            metadata: 元数据
            
        Returns:
            提示词
        """
        base_prompt = self.multimodal_config.get("default_prompt", "请详细描述这张图片的内容。")
        
        # 根据文件名或元数据调整提示词
        if filename:
            if any(keyword in filename.lower() for keyword in ['chart', 'graph', '图表', '图形']):
                return "请详细描述这张图表的内容，包括图表类型、数据趋势、标题和标签等信息。"
            elif any(keyword in filename.lower() for keyword in ['document', 'doc', '文档', '文件']):
                return "请详细描述这张文档图片的内容，包括文字信息、布局结构、标题等。"
            elif any(keyword in filename.lower() for keyword in ['screenshot', '截图', '屏幕']):
                return "请详细描述这张截图的内容，包括界面元素、文字信息、操作步骤等。"
        
        # 根据元数据调整
        if metadata:
            context = metadata.get("context", "")
            if context:
                return f"在{context}的背景下，{base_prompt}"
        
        return base_prompt
    
    async def _call_dashscope_api(self, image_base64: str, prompt: str) -> Dict[str, Any]:
        """
        调用DashScope多模态API
        
        Args:
            image_base64: Base64编码的图片
            prompt: 提示词
            
        Returns:
            API响应结果
        """
        try:
            # 构建消息
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"image": f"data:image/jpeg;base64,{image_base64}"},
                        {"text": prompt}
                    ]
                }
            ]
            
            # 在线程池中调用API
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                self._call_dashscope_sync,
                messages
            )
            
            if response.status_code == 200:
                content = response.output.choices[0].message.content
                return {
                    "success": True,
                    "description": content,
                    "metadata": {
                        "model": self.multimodal_config["model_name"],
                        "api_provider": "dashscope",
                        "prompt": prompt
                    }
                }
            else:
                error_msg = f"API调用失败: {response.status_code}, {response.message}"
                self._record_api_error(error_msg)
                raise Exception(error_msg)
            
        except Exception as e:
            logger.error(f"DashScope API调用失败: {e}")
            raise
    
    def _call_dashscope_sync(self, messages: List[Dict[str, Any]]) -> Any:
        """
        同步调用DashScope API
        
        Args:
            messages: 消息列表
            
        Returns:
            API响应
        """
        return MultiModalConversation.call(
            model=self.multimodal_config["model_name"],
            messages=messages,
            max_tokens=self.multimodal_config.get("max_tokens", 2000),
            temperature=self.multimodal_config.get("temperature", 0.1)
        )
    
    async def _fallback_description(self, filename: str, file_size: int) -> Dict[str, Any]:
        """
        降级描述（当API不可用时）
        
        Args:
            filename: 文件名
            file_size: 文件大小
            
        Returns:
            简单描述结果
        """
        description = f"这是一张名为 {filename or '未知'} 的图片文件，大小为 {file_size} 字节。"
        
        # 根据文件名推测内容类型
        if filename:
            if any(keyword in filename.lower() for keyword in ['chart', 'graph', '图表']):
                description += "根据文件名判断，这可能是一张图表或图形。"
            elif any(keyword in filename.lower() for keyword in ['photo', '照片', 'pic']):
                description += "根据文件名判断，这可能是一张照片。"
            elif any(keyword in filename.lower() for keyword in ['screenshot', '截图']):
                description += "根据文件名判断，这可能是一张截图。"
        
        return {
            "success": True,
            "description": description,
            "metadata": {
                "fallback": True,
                "reason": "API不可用或未配置"
            }
        }

    def _record_api_error(self, error_msg: str) -> None:
        """
        记录API错误

        Args:
            error_msg: 错误消息
        """
        error_type = "unknown"
        if "status_code" in error_msg:
            error_type = "http_error"
        elif "timeout" in error_msg.lower():
            error_type = "timeout"
        elif "auth" in error_msg.lower():
            error_type = "authentication"

        self.stats["api_errors"][error_type] = self.stats["api_errors"].get(error_type, 0) + 1

    def _update_stats(self, processing_time: float, success: bool) -> None:
        """
        更新统计信息

        Args:
            processing_time: 处理时间
            success: 是否成功
        """
        if success:
            self.stats["successful_requests"] += 1
        else:
            self.stats["failed_requests"] += 1

        self.stats["total_processing_time"] += processing_time

        # 更新平均处理时间
        if self.stats["total_requests"] > 0:
            self.stats["average_processing_time"] = (
                self.stats["total_processing_time"] / self.stats["total_requests"]
            )

    def get_stats(self) -> Dict[str, Any]:
        """
        获取处理器统计信息

        Returns:
            统计信息
        """
        success_rate = 0.0
        if self.stats["total_requests"] > 0:
            success_rate = self.stats["successful_requests"] / self.stats["total_requests"]

        return {
            **self.stats,
            "success_rate": success_rate,
            "config": {
                "model_name": self.multimodal_config.get("model_name"),
                "max_tokens": self.multimodal_config.get("max_tokens"),
                "batch_size": self.multimodal_config.get("batch_size"),
                "api_available": DASHSCOPE_AVAILABLE and bool(self.multimodal_config.get("api_key"))
            }
        }

    async def close(self) -> None:
        """关闭处理器，释放资源"""
        try:
            self.initialized = False
            logger.info("多模态处理器已关闭")
        except Exception as e:
            logger.error(f"关闭多模态处理器失败: {e}")
