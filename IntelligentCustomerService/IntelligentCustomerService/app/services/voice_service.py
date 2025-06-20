"""
语音交互服务
提供语音输入识别、语音合成、实时语音处理等功能
"""

import asyncio
import logging
import io
import base64
import json
from typing import Any, Dict, List, Optional, AsyncGenerator, Union
from datetime import datetime
import tempfile
import os

import aiofiles
import httpx
from pydub import AudioSegment
from pydub.playback import play
import speech_recognition as sr
import pyttsx3
import numpy as np

from ..core.model_manager import model_manager, ModelType
from ..core.cache_manager import cache_manager

logger = logging.getLogger(__name__)


class VoiceConfig:
    """语音服务配置"""
    
    def __init__(self):
        # 语音识别配置
        self.speech_recognition_engine = "whisper"  # whisper, google, azure
        self.whisper_model = "base"
        self.language = "zh-CN"
        
        # 语音合成配置
        self.tts_engine = "edge-tts"  # edge-tts, azure, openai
        self.voice_name = "zh-CN-XiaoxiaoNeural"
        self.speech_rate = 1.0
        self.speech_volume = 0.8
        
        # 音频处理配置
        self.sample_rate = 16000
        self.chunk_size = 1024
        self.audio_format = "wav"
        self.max_audio_duration = 60  # 秒
        
        # 实时语音配置
        self.enable_vad = True  # 语音活动检测
        self.silence_threshold = 0.01
        self.silence_duration = 2.0  # 秒


class VoiceService:
    """语音交互服务"""
    
    def __init__(self, config: Optional[VoiceConfig] = None):
        self.config = config or VoiceConfig()
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.tts_engine = None
        self.is_listening = False
        self.is_speaking = False
        
        # 初始化TTS引擎
        self._init_tts_engine()
        
        # 语音缓存
        self.voice_cache = {}
        
        logger.info("语音服务初始化完成")
    
    def _init_tts_engine(self):
        """初始化TTS引擎"""
        try:
            if self.config.tts_engine == "pyttsx3":
                self.tts_engine = pyttsx3.init()
                self.tts_engine.setProperty('rate', int(self.config.speech_rate * 200))
                self.tts_engine.setProperty('volume', self.config.speech_volume)
                
                # 设置中文语音
                voices = self.tts_engine.getProperty('voices')
                for voice in voices:
                    if 'chinese' in voice.name.lower() or 'zh' in voice.id.lower():
                        self.tts_engine.setProperty('voice', voice.id)
                        break
                        
            logger.info(f"TTS引擎初始化成功: {self.config.tts_engine}")
            
        except Exception as e:
            logger.error(f"TTS引擎初始化失败: {str(e)}")
    
    async def speech_to_text(
        self,
        audio_data: Union[bytes, str],
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        语音转文字
        
        Args:
            audio_data: 音频数据（bytes）或base64编码字符串
            language: 语言代码
            
        Returns:
            识别结果字典
        """
        try:
            # 处理音频数据
            if isinstance(audio_data, str):
                audio_data = base64.b64decode(audio_data)
            
            # 创建临时文件
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            try:
                # 使用语音识别
                with sr.AudioFile(temp_file_path) as source:
                    audio = self.recognizer.record(source)
                
                # 选择识别引擎
                if self.config.speech_recognition_engine == "google":
                    text = self.recognizer.recognize_google(
                        audio, 
                        language=language or self.config.language
                    )
                elif self.config.speech_recognition_engine == "whisper":
                    text = await self._whisper_recognize(audio_data)
                else:
                    text = self.recognizer.recognize_sphinx(audio)
                
                result = {
                    "success": True,
                    "text": text,
                    "confidence": 0.9,  # 默认置信度
                    "language": language or self.config.language,
                    "duration": self._get_audio_duration(audio_data),
                    "timestamp": datetime.now().isoformat()
                }
                
                logger.info(f"语音识别成功: {text[:50]}...")
                return result
                
            finally:
                # 清理临时文件
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except Exception as e:
            logger.error(f"语音识别失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "text": "",
                "timestamp": datetime.now().isoformat()
            }
    
    async def _whisper_recognize(self, audio_data: bytes) -> str:
        """使用Whisper进行语音识别"""
        try:
            # 这里可以集成OpenAI Whisper API或本地Whisper模型
            # 暂时使用模拟实现
            await asyncio.sleep(0.1)  # 模拟处理时间
            return "这是Whisper识别的结果"
            
        except Exception as e:
            logger.error(f"Whisper识别失败: {str(e)}")
            raise
    
    async def text_to_speech(
        self,
        text: str,
        voice_name: Optional[str] = None,
        speed: Optional[float] = None,
        output_format: str = "wav"
    ) -> Dict[str, Any]:
        """
        文字转语音
        
        Args:
            text: 要合成的文本
            voice_name: 语音名称
            speed: 语速
            output_format: 输出格式
            
        Returns:
            合成结果字典
        """
        try:
            # 检查缓存
            cache_key = f"tts_{hash(text)}_{voice_name}_{speed}"
            cached_result = await cache_manager.get(cache_key)
            if cached_result:
                return cached_result
            
            # 使用不同的TTS引擎
            if self.config.tts_engine == "edge-tts":
                audio_data = await self._edge_tts_synthesize(text, voice_name, speed)
            elif self.config.tts_engine == "openai":
                audio_data = await self._openai_tts_synthesize(text, voice_name, speed)
            else:
                audio_data = await self._pyttsx3_synthesize(text, speed)
            
            result = {
                "success": True,
                "audio_data": base64.b64encode(audio_data).decode(),
                "format": output_format,
                "duration": self._get_audio_duration(audio_data),
                "text": text,
                "voice": voice_name or self.config.voice_name,
                "timestamp": datetime.now().isoformat()
            }
            
            # 缓存结果
            await cache_manager.set(cache_key, result, expire=3600)
            
            logger.info(f"语音合成成功: {text[:50]}...")
            return result
            
        except Exception as e:
            logger.error(f"语音合成失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "audio_data": "",
                "timestamp": datetime.now().isoformat()
            }
    
    async def _edge_tts_synthesize(
        self, 
        text: str, 
        voice_name: Optional[str], 
        speed: Optional[float]
    ) -> bytes:
        """使用Edge TTS进行语音合成"""
        try:
            import edge_tts
            
            voice = voice_name or self.config.voice_name
            rate = f"{int((speed or self.config.speech_rate) * 100)}%"
            
            communicate = edge_tts.Communicate(text, voice, rate=rate)
            
            # 生成音频数据
            audio_data = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data += chunk["data"]
            
            return audio_data
            
        except ImportError:
            logger.warning("edge-tts未安装，使用备用TTS引擎")
            return await self._pyttsx3_synthesize(text, speed)
        except Exception as e:
            logger.error(f"Edge TTS合成失败: {str(e)}")
            raise
    
    async def _openai_tts_synthesize(
        self, 
        text: str, 
        voice_name: Optional[str], 
        speed: Optional[float]
    ) -> bytes:
        """使用OpenAI TTS进行语音合成"""
        try:
            # 这里可以集成OpenAI TTS API
            # 暂时使用模拟实现
            await asyncio.sleep(0.5)  # 模拟API调用时间
            return b"mock_audio_data"
            
        except Exception as e:
            logger.error(f"OpenAI TTS合成失败: {str(e)}")
            raise
    
    async def _pyttsx3_synthesize(self, text: str, speed: Optional[float]) -> bytes:
        """使用pyttsx3进行语音合成"""
        try:
            if not self.tts_engine:
                raise ValueError("TTS引擎未初始化")
            
            # 设置语速
            if speed:
                self.tts_engine.setProperty('rate', int(speed * 200))
            
            # 创建临时文件
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file_path = temp_file.name
            
            try:
                # 保存到文件
                self.tts_engine.save_to_file(text, temp_file_path)
                self.tts_engine.runAndWait()
                
                # 读取音频数据
                async with aiofiles.open(temp_file_path, 'rb') as f:
                    audio_data = await f.read()
                
                return audio_data
                
            finally:
                # 清理临时文件
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except Exception as e:
            logger.error(f"pyttsx3合成失败: {str(e)}")
            raise
    
    def _get_audio_duration(self, audio_data: bytes) -> float:
        """获取音频时长"""
        try:
            # 创建临时文件
            with tempfile.NamedTemporaryFile(suffix='.wav') as temp_file:
                temp_file.write(audio_data)
                temp_file.flush()
                
                # 使用pydub获取时长
                audio = AudioSegment.from_wav(temp_file.name)
                return len(audio) / 1000.0  # 转换为秒
                
        except Exception as e:
            logger.warning(f"获取音频时长失败: {str(e)}")
            return 0.0
    
    async def start_real_time_recognition(
        self,
        callback: callable,
        language: Optional[str] = None
    ):
        """
        开始实时语音识别
        
        Args:
            callback: 识别结果回调函数
            language: 语言代码
        """
        try:
            self.is_listening = True
            
            # 调整麦克风
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source)
            
            logger.info("开始实时语音识别")
            
            while self.is_listening:
                try:
                    # 监听音频
                    with self.microphone as source:
                        audio = self.recognizer.listen(
                            source, 
                            timeout=1, 
                            phrase_time_limit=5
                        )
                    
                    # 识别文本
                    text = self.recognizer.recognize_google(
                        audio, 
                        language=language or self.config.language
                    )
                    
                    # 调用回调函数
                    await callback({
                        "text": text,
                        "confidence": 0.9,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                except sr.WaitTimeoutError:
                    # 超时，继续监听
                    continue
                except sr.UnknownValueError:
                    # 无法识别，继续监听
                    continue
                except Exception as e:
                    logger.error(f"实时识别错误: {str(e)}")
                    await asyncio.sleep(1)
                    
        except Exception as e:
            logger.error(f"实时语音识别失败: {str(e)}")
        finally:
            self.is_listening = False
            logger.info("实时语音识别已停止")
    
    def stop_real_time_recognition(self):
        """停止实时语音识别"""
        self.is_listening = False
        logger.info("停止实时语音识别")
    
    async def play_audio(self, audio_data: Union[bytes, str]):
        """播放音频"""
        try:
            if isinstance(audio_data, str):
                audio_data = base64.b64decode(audio_data)
            
            # 创建临时文件
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            try:
                # 播放音频
                audio = AudioSegment.from_wav(temp_file_path)
                play(audio)
                
            finally:
                # 清理临时文件
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except Exception as e:
            logger.error(f"音频播放失败: {str(e)}")
    
    async def get_voice_status(self) -> Dict[str, Any]:
        """获取语音服务状态"""
        return {
            "is_listening": self.is_listening,
            "is_speaking": self.is_speaking,
            "tts_engine": self.config.tts_engine,
            "speech_recognition_engine": self.config.speech_recognition_engine,
            "language": self.config.language,
            "voice_name": self.config.voice_name,
            "available_voices": await self._get_available_voices()
        }
    
    async def _get_available_voices(self) -> List[Dict[str, str]]:
        """获取可用语音列表"""
        try:
            if self.config.tts_engine == "edge-tts":
                import edge_tts
                voices = await edge_tts.list_voices()
                return [
                    {
                        "name": voice["Name"],
                        "display_name": voice["DisplayName"],
                        "language": voice["Locale"],
                        "gender": voice["Gender"]
                    }
                    for voice in voices
                    if voice["Locale"].startswith("zh")
                ]
            else:
                return [
                    {
                        "name": self.config.voice_name,
                        "display_name": "默认语音",
                        "language": self.config.language,
                        "gender": "Female"
                    }
                ]
                
        except Exception as e:
            logger.error(f"获取语音列表失败: {str(e)}")
            return []


# 全局语音服务实例
voice_service = VoiceService()
