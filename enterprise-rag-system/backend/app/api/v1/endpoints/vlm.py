"""
VLM多模态服务API端点
"""

import base64
from typing import List

from app.core.security import get_current_user
from app.models.user import User
from app.services.vlm_service import vlm_service
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field

from app.core.exceptions import ExternalServiceException

router = APIRouter()


class ImageAnalysisRequest(BaseModel):
    """图片分析请求"""
    image_base64: str = Field(..., description="Base64编码的图片数据")
    prompt: str = Field("请详细描述这张图片的内容", description="分析提示词")
    max_tokens: int = Field(1000, ge=100, le=2000, description="最大生成token数")


class ImageAnalysisResponse(BaseModel):
    """图片分析响应"""
    description: str
    model: str
    usage: dict = {}
    success: bool


class BatchImageAnalysisRequest(BaseModel):
    """批量图片分析请求"""
    images_base64: List[str] = Field(..., description="Base64编码的图片数据列表")
    prompt: str = Field("请分别描述这些图片的内容", description="分析提示词")
    max_tokens: int = Field(2000, ge=100, le=4000, description="最大生成token数")


class BatchImageAnalysisResponse(BaseModel):
    """批量图片分析响应"""
    results: List[dict]
    total: int
    success_count: int
    failed_count: int


class OCRRequest(BaseModel):
    """OCR请求"""
    image_base64: str = Field(..., description="Base64编码的图片数据")
    language: str = Field("auto", description="语言设置")


class OCRResponse(BaseModel):
    """OCR响应"""
    text: str
    language: str
    model: str
    confidence: float
    success: bool


class ChartAnalysisRequest(BaseModel):
    """图表分析请求"""
    image_base64: str = Field(..., description="Base64编码的图片数据")
    chart_type: str = Field("auto", description="图表类型提示")


class ChartAnalysisResponse(BaseModel):
    """图表分析响应"""
    analysis: str
    chart_type: str
    model: str
    success: bool


class ImageCaptionRequest(BaseModel):
    """图片标题生成请求"""
    image_base64: str = Field(..., description="Base64编码的图片数据")
    style: str = Field("detailed", description="描述风格")


class ImageCaptionResponse(BaseModel):
    """图片标题生成响应"""
    caption: str
    style: str
    model: str
    success: bool


@router.post("/analyze-image", response_model=ImageAnalysisResponse)
async def analyze_image(
    request: ImageAnalysisRequest,
    current_user: User = Depends(get_current_user)
):
    """
    分析单张图片
    """
    try:
        result = await vlm_service.analyze_image(
            image_data=request.image_base64,
            prompt=request.prompt,
            max_tokens=request.max_tokens
        )
        
        return ImageAnalysisResponse(**result)
        
    except ExternalServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"图片分析失败: {str(e)}")


@router.post("/analyze-image/upload", response_model=ImageAnalysisResponse)
async def analyze_uploaded_image(
    file: UploadFile = File(..., description="上传的图片文件"),
    prompt: str = Form("请详细描述这张图片的内容", description="分析提示词"),
    max_tokens: int = Form(1000, description="最大生成token数"),
    current_user: User = Depends(get_current_user)
):
    """
    分析上传的图片文件
    """
    try:
        # 验证文件类型
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="文件必须是图片格式")
        
        # 读取文件内容
        image_data = await file.read()
        
        # 转换为base64
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        result = await vlm_service.analyze_image(
            image_data=image_base64,
            prompt=prompt,
            max_tokens=max_tokens
        )
        
        return ImageAnalysisResponse(**result)
        
    except ExternalServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"图片分析失败: {str(e)}")


@router.post("/analyze-images/batch", response_model=BatchImageAnalysisResponse)
async def analyze_images_batch(
    request: BatchImageAnalysisRequest,
    current_user: User = Depends(get_current_user)
):
    """
    批量分析图片
    """
    try:
        if len(request.images_base64) > 10:
            raise HTTPException(status_code=400, detail="批量分析最多支持10张图片")
        
        results = await vlm_service.analyze_images_batch(
            images=request.images_base64,
            prompt=request.prompt,
            max_tokens=request.max_tokens
        )
        
        success_count = sum(1 for result in results if result.get("success", False))
        failed_count = len(results) - success_count
        
        return BatchImageAnalysisResponse(
            results=results,
            total=len(results),
            success_count=success_count,
            failed_count=failed_count
        )
        
    except ExternalServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量图片分析失败: {str(e)}")


@router.post("/extract-text", response_model=OCRResponse)
async def extract_text_from_image(
    request: OCRRequest,
    current_user: User = Depends(get_current_user)
):
    """
    从图片中提取文字（OCR）
    """
    try:
        result = await vlm_service.extract_text_from_image(
            image_data=request.image_base64,
            language=request.language
        )
        
        return OCRResponse(**result)
        
    except ExternalServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文字提取失败: {str(e)}")


@router.post("/extract-text/upload", response_model=OCRResponse)
async def extract_text_from_uploaded_image(
    file: UploadFile = File(..., description="上传的图片文件"),
    language: str = Form("auto", description="语言设置"),
    current_user: User = Depends(get_current_user)
):
    """
    从上传的图片中提取文字
    """
    try:
        # 验证文件类型
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="文件必须是图片格式")
        
        # 读取文件内容
        image_data = await file.read()
        
        # 转换为base64
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        result = await vlm_service.extract_text_from_image(
            image_data=image_base64,
            language=language
        )
        
        return OCRResponse(**result)
        
    except ExternalServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文字提取失败: {str(e)}")


@router.post("/analyze-chart", response_model=ChartAnalysisResponse)
async def analyze_chart_or_diagram(
    request: ChartAnalysisRequest,
    current_user: User = Depends(get_current_user)
):
    """
    分析图表或图形
    """
    try:
        result = await vlm_service.analyze_chart_or_diagram(
            image_data=request.image_base64,
            chart_type=request.chart_type
        )
        
        return ChartAnalysisResponse(**result)
        
    except ExternalServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"图表分析失败: {str(e)}")


@router.post("/generate-caption", response_model=ImageCaptionResponse)
async def generate_image_caption(
    request: ImageCaptionRequest,
    current_user: User = Depends(get_current_user)
):
    """
    生成图片标题/描述
    """
    try:
        result = await vlm_service.generate_image_caption(
            image_data=request.image_base64,
            style=request.style
        )
        
        return ImageCaptionResponse(**result)
        
    except ExternalServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"图片标题生成失败: {str(e)}")


@router.get("/supported-formats")
async def get_supported_formats():
    """
    获取支持的图片格式
    """
    return {
        "supported_formats": [
            {
                "extension": ".jpg",
                "mime_type": "image/jpeg",
                "description": "JPEG图片格式"
            },
            {
                "extension": ".jpeg",
                "mime_type": "image/jpeg",
                "description": "JPEG图片格式"
            },
            {
                "extension": ".png",
                "mime_type": "image/png",
                "description": "PNG图片格式"
            },
            {
                "extension": ".bmp",
                "mime_type": "image/bmp",
                "description": "BMP图片格式"
            },
            {
                "extension": ".gif",
                "mime_type": "image/gif",
                "description": "GIF图片格式"
            },
            {
                "extension": ".webp",
                "mime_type": "image/webp",
                "description": "WebP图片格式"
            }
        ],
        "max_file_size": "10MB",
        "max_batch_size": 10
    }


@router.get("/caption-styles")
async def get_caption_styles():
    """
    获取支持的标题风格
    """
    return {
        "styles": [
            {
                "value": "detailed",
                "name": "详细描述",
                "description": "生成详细的图片描述，包括主要内容、场景、人物、物体等"
            },
            {
                "value": "brief",
                "name": "简洁标题",
                "description": "生成简洁的图片标题"
            },
            {
                "value": "creative",
                "name": "创意描述",
                "description": "生成富有创意和想象力的标题和描述"
            }
        ]
    }


@router.get("/languages")
async def get_supported_languages():
    """
    获取OCR支持的语言
    """
    return {
        "languages": [
            {
                "code": "auto",
                "name": "自动检测",
                "description": "自动检测图片中的语言"
            },
            {
                "code": "zh",
                "name": "中文",
                "description": "中文文字识别"
            },
            {
                "code": "en",
                "name": "英文",
                "description": "英文文字识别"
            },
            {
                "code": "ja",
                "name": "日文",
                "description": "日文文字识别"
            },
            {
                "code": "ko",
                "name": "韩文",
                "description": "韩文文字识别"
            }
        ]
    }
