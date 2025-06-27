"""
Qwen-VL-Max多模态服务 - 企业级RAG系统
严格按照技术栈要求：qwen-vl-max (DashScope API，图像理解)
"""
import asyncio
import base64
import io
import time
from typing import List, Dict, Any, Optional

import dashscope
from PIL import Image
from app.core.config import settings
from dashscope import MultiModalConversation
from loguru import logger


class QwenMultimodalService:
    """Qwen-VL-Max多模态服务"""
    
    def __init__(self):
        self.api_key = settings.DASHSCOPE_API_KEY
        self.model_name = "qwen-vl-max"
        self.max_image_size = 10 * 1024 * 1024  # 10MB
        self.supported_formats = {"jpg", "jpeg", "png", "bmp", "gif", "webp"}
        self.max_images_per_request = 10
        
        # 设置DashScope API密钥
        dashscope.api_key = self.api_key
        
        # 请求统计
        self.request_count = 0
        self.total_latency = 0.0
        self.error_count = 0
        self.processed_images = 0
    
    def _validate_image(self, image_data: bytes, filename: str = None) -> tuple[bool, str]:
        """验证图像文件"""
        try:
            # 检查文件大小
            if len(image_data) > self.max_image_size:
                return False, f"图像文件过大，最大支持{self.max_image_size // 1024 // 1024}MB"
            
            # 检查图像格式
            try:
                image = Image.open(io.BytesIO(image_data))
                format_lower = image.format.lower() if image.format else ""
                
                if format_lower not in self.supported_formats:
                    return False, f"不支持的图像格式: {image.format}，支持格式: {', '.join(self.supported_formats)}"
                
                # 检查图像尺寸
                width, height = image.size
                if width * height > 4096 * 4096:  # 限制像素总数
                    return False, "图像分辨率过高，请使用较小的图像"
                
                return True, "图像验证通过"
                
            except Exception as e:
                return False, f"无效的图像文件: {str(e)}"
                
        except Exception as e:
            return False, f"图像验证失败: {str(e)}"
    
    def _encode_image_to_base64(self, image_data: bytes) -> str:
        """将图像编码为base64"""
        return base64.b64encode(image_data).decode('utf-8')
    
    async def analyze_image(
        self,
        image_data: bytes,
        prompt: str = "请描述这张图片的内容",
        filename: str = None
    ) -> Dict[str, Any]:
        """分析单张图像"""
        try:
            start_time = time.time()
            
            # 验证图像
            is_valid, error_msg = self._validate_image(image_data, filename)
            if not is_valid:
                return {
                    "success": False,
                    "error": error_msg,
                    "latency_ms": 0
                }
            
            # 编码图像
            image_base64 = self._encode_image_to_base64(image_data)
            
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
            
            # 调用DashScope API
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                self._call_multimodal_api,
                messages
            )
            
            end_time = time.time()
            latency = (end_time - start_time) * 1000
            
            # 更新统计
            self.request_count += 1
            self.total_latency += latency
            self.processed_images += 1
            
            if response.status_code == 200:
                result = {
                    "success": True,
                    "content": response.output.choices[0].message.content,
                    "model": self.model_name,
                    "usage": {
                        "input_tokens": response.usage.input_tokens,
                        "output_tokens": response.usage.output_tokens,
                        "total_tokens": response.usage.total_tokens
                    },
                    "latency_ms": latency,
                    "filename": filename
                }
                
                logger.info(f"图像分析成功: {filename}, 耗时: {latency:.2f}ms")
                return result
            else:
                self.error_count += 1
                error_msg = f"API调用失败: {response.code} - {response.message}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "latency_ms": latency
                }
                
        except Exception as e:
            self.error_count += 1
            logger.error(f"图像分析失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "latency_ms": 0
            }
    
    def _call_multimodal_api(self, messages: List[Dict[str, Any]]) -> Any:
        """同步调用多模态API"""
        return MultiModalConversation.call(
            model=self.model_name,
            messages=messages
        )
    
    async def analyze_multiple_images(
        self,
        images: List[Dict[str, Any]],  # [{"data": bytes, "filename": str, "prompt": str}]
        global_prompt: str = None
    ) -> List[Dict[str, Any]]:
        """批量分析多张图像"""
        try:
            if len(images) > self.max_images_per_request:
                return [{
                    "success": False,
                    "error": f"批量处理最多支持{self.max_images_per_request}张图像"
                }]
            
            # 并行处理图像
            tasks = []
            for image_info in images:
                image_data = image_info["data"]
                filename = image_info.get("filename", "unknown")
                prompt = image_info.get("prompt", global_prompt or "请描述这张图片的内容")
                
                task = self.analyze_image(image_data, prompt, filename)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理结果
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    processed_results.append({
                        "success": False,
                        "error": str(result),
                        "filename": images[i].get("filename", "unknown")
                    })
                else:
                    processed_results.append(result)
            
            logger.info(f"批量图像分析完成，处理{len(images)}张图像")
            return processed_results
            
        except Exception as e:
            logger.error(f"批量图像分析失败: {e}")
            return [{
                "success": False,
                "error": str(e)
            }]
    
    async def image_qa(
        self,
        image_data: bytes,
        question: str,
        context: Optional[str] = None,
        filename: str = None
    ) -> Dict[str, Any]:
        """图像问答"""
        try:
            # 构建提示词
            if context:
                prompt = f"上下文信息：{context}\n\n问题：{question}"
            else:
                prompt = question
            
            return await self.analyze_image(image_data, prompt, filename)
            
        except Exception as e:
            logger.error(f"图像问答失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def extract_text_from_image(
        self,
        image_data: bytes,
        filename: str = None
    ) -> Dict[str, Any]:
        """从图像中提取文本（OCR）"""
        try:
            prompt = "请提取这张图片中的所有文本内容，保持原有的格式和结构。如果没有文本，请说明图片内容。"
            
            result = await self.analyze_image(image_data, prompt, filename)
            
            if result["success"]:
                # 添加OCR特定的元数据
                result["extraction_type"] = "ocr"
                result["has_text"] = len(result["content"].strip()) > 0
            
            return result
            
        except Exception as e:
            logger.error(f"图像文本提取失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def describe_image_for_search(
        self,
        image_data: bytes,
        filename: str = None
    ) -> Dict[str, Any]:
        """为搜索生成图像描述"""
        try:
            prompt = """请详细描述这张图片的内容，包括：
1. 主要对象和场景
2. 颜色、形状、位置等视觉特征
3. 可能的用途或含义
4. 任何可见的文字或标识
请用简洁明了的语言描述，便于后续搜索和检索。"""
            
            result = await self.analyze_image(image_data, prompt, filename)
            
            if result["success"]:
                result["description_type"] = "search_optimized"
            
            return result
            
        except Exception as e:
            logger.error(f"图像搜索描述生成失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def compare_images(
        self,
        image1_data: bytes,
        image2_data: bytes,
        comparison_prompt: str = "请比较这两张图片的异同点",
        filename1: str = None,
        filename2: str = None
    ) -> Dict[str, Any]:
        """比较两张图像"""
        try:
            start_time = time.time()
            
            # 验证两张图像
            is_valid1, error1 = self._validate_image(image1_data, filename1)
            is_valid2, error2 = self._validate_image(image2_data, filename2)
            
            if not is_valid1:
                return {"success": False, "error": f"图像1验证失败: {error1}"}
            if not is_valid2:
                return {"success": False, "error": f"图像2验证失败: {error2}"}
            
            # 编码图像
            image1_base64 = self._encode_image_to_base64(image1_data)
            image2_base64 = self._encode_image_to_base64(image2_data)
            
            # 构建消息
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"image": f"data:image/jpeg;base64,{image1_base64}"},
                        {"image": f"data:image/jpeg;base64,{image2_base64}"},
                        {"text": comparison_prompt}
                    ]
                }
            ]
            
            # 调用API
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                self._call_multimodal_api,
                messages
            )
            
            end_time = time.time()
            latency = (end_time - start_time) * 1000
            
            # 更新统计
            self.request_count += 1
            self.total_latency += latency
            self.processed_images += 2
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "content": response.output.choices[0].message.content,
                    "model": self.model_name,
                    "comparison_type": "image_comparison",
                    "filenames": [filename1, filename2],
                    "usage": {
                        "input_tokens": response.usage.input_tokens,
                        "output_tokens": response.usage.output_tokens,
                        "total_tokens": response.usage.total_tokens
                    },
                    "latency_ms": latency
                }
            else:
                self.error_count += 1
                return {
                    "success": False,
                    "error": f"API调用失败: {response.code} - {response.message}",
                    "latency_ms": latency
                }
                
        except Exception as e:
            self.error_count += 1
            logger.error(f"图像比较失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_service_info(self) -> Dict[str, Any]:
        """获取服务信息"""
        return {
            "model_name": self.model_name,
            "max_image_size_mb": self.max_image_size // 1024 // 1024,
            "supported_formats": list(self.supported_formats),
            "max_images_per_request": self.max_images_per_request,
            "api_provider": "DashScope"
        }
    
    async def get_usage_stats(self) -> Dict[str, Any]:
        """获取使用统计"""
        avg_latency = self.total_latency / self.request_count if self.request_count > 0 else 0
        avg_images = self.processed_images / self.request_count if self.request_count > 0 else 0
        error_rate = self.error_count / self.request_count if self.request_count > 0 else 0
        
        return {
            "total_requests": self.request_count,
            "processed_images": self.processed_images,
            "total_latency_ms": self.total_latency,
            "avg_latency_ms": avg_latency,
            "avg_images_per_request": avg_images,
            "error_count": self.error_count,
            "error_rate": error_rate,
            "model": self.model_name
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            # 创建一个简单的测试图像
            test_image = Image.new('RGB', (100, 100), color='red')
            img_buffer = io.BytesIO()
            test_image.save(img_buffer, format='JPEG')
            test_image_data = img_buffer.getvalue()
            
            # 测试API调用
            start_time = time.time()
            result = await self.analyze_image(
                test_image_data,
                "这是什么颜色？",
                "test_image.jpg"
            )
            end_time = time.time()
            
            if result["success"]:
                return {
                    "status": "healthy",
                    "model": self.model_name,
                    "api_accessible": True,
                    "test_latency_ms": (end_time - start_time) * 1000,
                    "usage_stats": await self.get_usage_stats()
                }
            else:
                return {
                    "status": "unhealthy",
                    "model": self.model_name,
                    "api_accessible": False,
                    "error": result.get("error")
                }
                
        except Exception as e:
            return {
                "status": "error",
                "model": self.model_name,
                "api_accessible": False,
                "error": str(e)
            }


# 全局Qwen多模态服务实例
qwen_multimodal_service = QwenMultimodalService()


# 便捷函数
async def analyze_image_content(
    image_data: bytes,
    prompt: str = "请描述这张图片的内容",
    filename: str = None
) -> Dict[str, Any]:
    """分析图像内容的便捷函数"""
    return await qwen_multimodal_service.analyze_image(image_data, prompt, filename)


async def extract_image_text(
    image_data: bytes,
    filename: str = None
) -> Dict[str, Any]:
    """提取图像文本的便捷函数"""
    return await qwen_multimodal_service.extract_text_from_image(image_data, filename)


async def answer_image_question(
    image_data: bytes,
    question: str,
    context: Optional[str] = None,
    filename: str = None
) -> Dict[str, Any]:
    """图像问答的便捷函数"""
    return await qwen_multimodal_service.image_qa(image_data, question, context, filename)
