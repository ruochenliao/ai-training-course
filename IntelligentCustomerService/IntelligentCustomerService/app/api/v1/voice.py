"""
语音交互API
提供语音识别、语音合成、实时语音处理等接口
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import json

from ...services.voice_service import voice_service, VoiceConfig
from ...services.analytics_service import analytics_service, EventType
from ...core.dependency import DependPermission

logger = logging.getLogger(__name__)

voice_router = APIRouter()


class SpeechToTextRequest(BaseModel):
    """语音转文字请求"""
    audio_data: str = Field(..., description="音频数据（base64编码）")
    language: Optional[str] = Field(None, description="语言代码")
    user_id: Optional[str] = Field(None, description="用户ID")
    session_id: Optional[str] = Field(None, description="会话ID")


class TextToSpeechRequest(BaseModel):
    """文字转语音请求"""
    text: str = Field(..., description="要合成的文本")
    voice_name: Optional[str] = Field(None, description="语音名称")
    speed: Optional[float] = Field(None, description="语速")
    output_format: str = Field("wav", description="输出格式")
    user_id: Optional[str] = Field(None, description="用户ID")


class VoiceConfigRequest(BaseModel):
    """语音配置请求"""
    speech_recognition_engine: Optional[str] = Field(None, description="语音识别引擎")
    tts_engine: Optional[str] = Field(None, description="语音合成引擎")
    language: Optional[str] = Field(None, description="语言代码")
    voice_name: Optional[str] = Field(None, description="语音名称")
    speech_rate: Optional[float] = Field(None, description="语速")
    speech_volume: Optional[float] = Field(None, description="音量")


@voice_router.post("/speech-to-text", summary="语音转文字")
async def speech_to_text(request: SpeechToTextRequest):
    """
    语音转文字
    
    将音频数据转换为文本
    """
    try:
        # 跟踪事件
        await analytics_service.track_event(
            event_type=EventType.VOICE_USED,
            user_id=request.user_id,
            session_id=request.session_id,
            properties={
                "action": "speech_to_text",
                "language": request.language
            }
        )
        
        # 执行语音识别
        result = await voice_service.speech_to_text(
            audio_data=request.audio_data,
            language=request.language
        )
        
        if result["success"]:
            return {
                "success": True,
                "text": result["text"],
                "confidence": result["confidence"],
                "language": result["language"],
                "duration": result["duration"],
                "timestamp": result["timestamp"]
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"语音识别失败: {result['error']}"
            )
            
    except Exception as e:
        logger.error(f"语音转文字失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@voice_router.post("/text-to-speech", summary="文字转语音")
async def text_to_speech(request: TextToSpeechRequest):
    """
    文字转语音
    
    将文本转换为语音音频
    """
    try:
        # 跟踪事件
        await analytics_service.track_event(
            event_type=EventType.VOICE_USED,
            user_id=request.user_id,
            properties={
                "action": "text_to_speech",
                "text_length": len(request.text),
                "voice_name": request.voice_name,
                "speed": request.speed
            }
        )
        
        # 执行语音合成
        result = await voice_service.text_to_speech(
            text=request.text,
            voice_name=request.voice_name,
            speed=request.speed,
            output_format=request.output_format
        )
        
        if result["success"]:
            return {
                "success": True,
                "audio_data": result["audio_data"],
                "format": result["format"],
                "duration": result["duration"],
                "voice": result["voice"],
                "timestamp": result["timestamp"]
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"语音合成失败: {result['error']}"
            )
            
    except Exception as e:
        logger.error(f"文字转语音失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@voice_router.post("/upload-audio", summary="上传音频文件")
async def upload_audio(
    file: UploadFile = File(...),
    user_id: Optional[str] = Form(None),
    session_id: Optional[str] = Form(None),
    language: Optional[str] = Form(None)
):
    """
    上传音频文件进行语音识别
    
    支持多种音频格式
    """
    try:
        # 检查文件类型
        if not file.content_type.startswith('audio/'):
            raise HTTPException(
                status_code=400,
                detail="只支持音频文件"
            )
        
        # 读取文件内容
        audio_data = await file.read()
        
        # 跟踪事件
        await analytics_service.track_event(
            event_type=EventType.VOICE_USED,
            user_id=user_id,
            session_id=session_id,
            properties={
                "action": "upload_audio",
                "filename": file.filename,
                "content_type": file.content_type,
                "file_size": len(audio_data)
            }
        )
        
        # 执行语音识别
        result = await voice_service.speech_to_text(
            audio_data=audio_data,
            language=language
        )
        
        if result["success"]:
            return {
                "success": True,
                "filename": file.filename,
                "text": result["text"],
                "confidence": result["confidence"],
                "language": result["language"],
                "duration": result["duration"],
                "timestamp": result["timestamp"]
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"语音识别失败: {result['error']}"
            )
            
    except Exception as e:
        logger.error(f"上传音频失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@voice_router.get("/voices", summary="获取可用语音列表")
async def get_available_voices():
    """
    获取可用语音列表
    
    返回系统支持的所有语音选项
    """
    try:
        status = await voice_service.get_voice_status()
        return {
            "success": True,
            "voices": status["available_voices"],
            "current_voice": status["voice_name"],
            "tts_engine": status["tts_engine"]
        }
        
    except Exception as e:
        logger.error(f"获取语音列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@voice_router.get("/status", summary="获取语音服务状态")
async def get_voice_status():
    """
    获取语音服务状态
    
    返回当前语音服务的配置和状态信息
    """
    try:
        status = await voice_service.get_voice_status()
        return {
            "success": True,
            "status": status
        }
        
    except Exception as e:
        logger.error(f"获取语音状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@voice_router.post("/config", summary="更新语音配置")
async def update_voice_config(
    request: VoiceConfigRequest,
    _: str = DependPermission
):
    """
    更新语音配置
    
    需要管理员权限
    """
    try:
        # 更新配置
        config_updates = {}
        if request.speech_recognition_engine:
            config_updates["speech_recognition_engine"] = request.speech_recognition_engine
        if request.tts_engine:
            config_updates["tts_engine"] = request.tts_engine
        if request.language:
            config_updates["language"] = request.language
        if request.voice_name:
            config_updates["voice_name"] = request.voice_name
        if request.speech_rate:
            config_updates["speech_rate"] = request.speech_rate
        if request.speech_volume:
            config_updates["speech_volume"] = request.speech_volume
        
        # 应用配置更新
        for key, value in config_updates.items():
            setattr(voice_service.config, key, value)
        
        # 重新初始化TTS引擎
        voice_service._init_tts_engine()
        
        return {
            "success": True,
            "message": "语音配置已更新",
            "updated_config": config_updates
        }
        
    except Exception as e:
        logger.error(f"更新语音配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@voice_router.websocket("/real-time")
async def real_time_voice_websocket(websocket: WebSocket):
    """
    实时语音交互WebSocket
    
    支持实时语音识别和语音合成
    """
    await websocket.accept()
    
    try:
        logger.info("实时语音WebSocket连接建立")
        
        # 实时识别回调函数
        async def recognition_callback(result: Dict[str, Any]):
            try:
                await websocket.send_text(json.dumps({
                    "type": "recognition_result",
                    "data": result
                }))
            except Exception as e:
                logger.error(f"发送识别结果失败: {str(e)}")
        
        # 启动实时识别
        recognition_task = None
        
        while True:
            try:
                # 接收客户端消息
                data = await websocket.receive_text()
                message = json.loads(data)
                
                message_type = message.get("type")
                
                if message_type == "start_recognition":
                    # 开始实时识别
                    if not voice_service.is_listening:
                        language = message.get("language")
                        recognition_task = asyncio.create_task(
                            voice_service.start_real_time_recognition(
                                callback=recognition_callback,
                                language=language
                            )
                        )
                        
                        await websocket.send_text(json.dumps({
                            "type": "recognition_started",
                            "message": "实时语音识别已启动"
                        }))
                
                elif message_type == "stop_recognition":
                    # 停止实时识别
                    voice_service.stop_real_time_recognition()
                    if recognition_task:
                        recognition_task.cancel()
                        recognition_task = None
                    
                    await websocket.send_text(json.dumps({
                        "type": "recognition_stopped",
                        "message": "实时语音识别已停止"
                    }))
                
                elif message_type == "synthesize":
                    # 语音合成
                    text = message.get("text", "")
                    voice_name = message.get("voice_name")
                    speed = message.get("speed")
                    
                    if text:
                        result = await voice_service.text_to_speech(
                            text=text,
                            voice_name=voice_name,
                            speed=speed
                        )
                        
                        await websocket.send_text(json.dumps({
                            "type": "synthesis_result",
                            "data": result
                        }))
                
                elif message_type == "ping":
                    # 心跳
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    }))
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"处理WebSocket消息失败: {str(e)}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": str(e)
                }))
    
    except WebSocketDisconnect:
        logger.info("实时语音WebSocket连接断开")
    except Exception as e:
        logger.error(f"实时语音WebSocket错误: {str(e)}")
    finally:
        # 清理资源
        voice_service.stop_real_time_recognition()
        if 'recognition_task' in locals() and recognition_task:
            recognition_task.cancel()


@voice_router.post("/test", summary="测试语音功能")
async def test_voice_functionality():
    """
    测试语音功能
    
    执行基础的语音识别和合成测试
    """
    try:
        test_results = {
            "speech_recognition": False,
            "text_to_speech": False,
            "available_voices": [],
            "errors": []
        }
        
        # 测试语音合成
        try:
            tts_result = await voice_service.text_to_speech(
                text="这是一个语音合成测试",
                output_format="wav"
            )
            test_results["text_to_speech"] = tts_result["success"]
            if not tts_result["success"]:
                test_results["errors"].append(f"TTS测试失败: {tts_result.get('error', '未知错误')}")
        except Exception as e:
            test_results["errors"].append(f"TTS测试异常: {str(e)}")
        
        # 获取可用语音
        try:
            status = await voice_service.get_voice_status()
            test_results["available_voices"] = status["available_voices"]
        except Exception as e:
            test_results["errors"].append(f"获取语音列表失败: {str(e)}")
        
        # 总体测试结果
        test_results["overall_success"] = (
            test_results["text_to_speech"] and
            len(test_results["available_voices"]) > 0
        )
        
        return {
            "success": True,
            "test_results": test_results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"语音功能测试失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
