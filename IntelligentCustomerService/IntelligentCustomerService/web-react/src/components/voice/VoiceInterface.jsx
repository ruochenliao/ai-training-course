import React, { useState, useRef, useEffect } from 'react';
import { 
  Mic, 
  MicOff, 
  Volume2, 
  VolumeX, 
  Play, 
  Pause, 
  Settings,
  Upload,
  Download
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Slider } from '../ui/slider';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { Textarea } from '../ui/textarea';
import { useToast } from '../ui/use-toast';

const VoiceInterface = ({ onTextGenerated, onVoiceGenerated }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [audioLevel, setAudioLevel] = useState(0);
  const [recognizedText, setRecognizedText] = useState('');
  const [synthesizedAudio, setSynthesizedAudio] = useState(null);
  const [availableVoices, setAvailableVoices] = useState([]);
  const [selectedVoice, setSelectedVoice] = useState('');
  const [speechRate, setSpeechRate] = useState([1.0]);
  const [volume, setVolume] = useState([0.8]);
  const [language, setLanguage] = useState('zh-CN');
  const [textToSynthesize, setTextToSynthesize] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const websocketRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const recordingTimerRef = useRef(null);
  const audioElementRef = useRef(null);

  const { toast } = useToast();

  // 初始化语音服务
  useEffect(() => {
    initializeVoiceService();
    return () => {
      cleanup();
    };
  }, []);

  const initializeVoiceService = async () => {
    try {
      // 获取可用语音列表
      const response = await fetch('/api/v1/voice/voices');
      const data = await response.json();
      
      if (data.success) {
        setAvailableVoices(data.voices);
        if (data.voices.length > 0) {
          setSelectedVoice(data.voices[0].name);
        }
      }

      // 建立WebSocket连接
      connectWebSocket();
    } catch (error) {
      console.error('初始化语音服务失败:', error);
      toast({
        title: "初始化失败",
        description: "语音服务初始化失败，请检查网络连接",
        variant: "destructive"
      });
    }
  };

  const connectWebSocket = () => {
    try {
      const wsUrl = `ws://localhost:8000/api/v1/voice/real-time`;
      websocketRef.current = new WebSocket(wsUrl);

      websocketRef.current.onopen = () => {
        setIsConnected(true);
        toast({
          title: "连接成功",
          description: "实时语音服务已连接",
          variant: "success"
        });
      };

      websocketRef.current.onmessage = (event) => {
        const message = JSON.parse(event.data);
        handleWebSocketMessage(message);
      };

      websocketRef.current.onclose = () => {
        setIsConnected(false);
        setIsRecording(false);
      };

      websocketRef.current.onerror = (error) => {
        console.error('WebSocket错误:', error);
        setIsConnected(false);
      };
    } catch (error) {
      console.error('WebSocket连接失败:', error);
    }
  };

  const handleWebSocketMessage = (message) => {
    switch (message.type) {
      case 'recognition_result':
        setRecognizedText(message.data.text);
        if (onTextGenerated) {
          onTextGenerated(message.data.text);
        }
        break;
      case 'synthesis_result':
        if (message.data.success) {
          setSynthesizedAudio(message.data.audio_data);
          if (onVoiceGenerated) {
            onVoiceGenerated(message.data);
          }
        }
        break;
      case 'recognition_started':
        setIsRecording(true);
        startRecordingTimer();
        break;
      case 'recognition_stopped':
        setIsRecording(false);
        stopRecordingTimer();
        break;
      case 'error':
        toast({
          title: "语音服务错误",
          description: message.message,
          variant: "destructive"
        });
        break;
    }
  };

  const startRecording = async () => {
    try {
      if (!isConnected) {
        toast({
          title: "连接错误",
          description: "请先连接到语音服务",
          variant: "destructive"
        });
        return;
      }

      // 获取麦克风权限
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      // 设置音频分析
      setupAudioAnalysis(stream);

      // 发送开始识别命令
      websocketRef.current.send(JSON.stringify({
        type: 'start_recognition',
        language: language
      }));

      setRecognizedText('');
    } catch (error) {
      console.error('开始录音失败:', error);
      toast({
        title: "录音失败",
        description: "无法访问麦克风，请检查权限设置",
        variant: "destructive"
      });
    }
  };

  const stopRecording = () => {
    if (websocketRef.current && isConnected) {
      websocketRef.current.send(JSON.stringify({
        type: 'stop_recognition'
      }));
    }

    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
  };

  const setupAudioAnalysis = (stream) => {
    audioContextRef.current = new AudioContext();
    analyserRef.current = audioContextRef.current.createAnalyser();
    const source = audioContextRef.current.createMediaStreamSource(stream);
    
    source.connect(analyserRef.current);
    analyserRef.current.fftSize = 256;
    
    const bufferLength = analyserRef.current.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    
    const updateAudioLevel = () => {
      if (analyserRef.current && isRecording) {
        analyserRef.current.getByteFrequencyData(dataArray);
        const average = dataArray.reduce((a, b) => a + b) / bufferLength;
        setAudioLevel(average);
        requestAnimationFrame(updateAudioLevel);
      }
    };
    
    updateAudioLevel();
  };

  const startRecordingTimer = () => {
    setRecordingTime(0);
    recordingTimerRef.current = setInterval(() => {
      setRecordingTime(prev => prev + 1);
    }, 1000);
  };

  const stopRecordingTimer = () => {
    if (recordingTimerRef.current) {
      clearInterval(recordingTimerRef.current);
      recordingTimerRef.current = null;
    }
  };

  const synthesizeSpeech = async () => {
    if (!textToSynthesize.trim()) {
      toast({
        title: "输入错误",
        description: "请输入要合成的文本",
        variant: "destructive"
      });
      return;
    }

    setIsLoading(true);

    try {
      if (isConnected && websocketRef.current) {
        // 通过WebSocket发送合成请求
        websocketRef.current.send(JSON.stringify({
          type: 'synthesize',
          text: textToSynthesize,
          voice_name: selectedVoice,
          speed: speechRate[0]
        }));
      } else {
        // 通过HTTP API发送合成请求
        const response = await fetch('/api/v1/voice/text-to-speech', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            text: textToSynthesize,
            voice_name: selectedVoice,
            speed: speechRate[0],
            output_format: 'wav'
          })
        });

        const data = await response.json();
        
        if (data.success) {
          setSynthesizedAudio(data.audio_data);
          if (onVoiceGenerated) {
            onVoiceGenerated(data);
          }
        } else {
          throw new Error(data.error || '语音合成失败');
        }
      }
    } catch (error) {
      console.error('语音合成失败:', error);
      toast({
        title: "合成失败",
        description: error.message,
        variant: "destructive"
      });
    } finally {
      setIsLoading(false);
    }
  };

  const playAudio = () => {
    if (!synthesizedAudio) return;

    try {
      const audioBlob = new Blob([
        Uint8Array.from(atob(synthesizedAudio), c => c.charCodeAt(0))
      ], { type: 'audio/wav' });
      
      const audioUrl = URL.createObjectURL(audioBlob);
      
      if (audioElementRef.current) {
        audioElementRef.current.src = audioUrl;
        audioElementRef.current.volume = volume[0];
        audioElementRef.current.play();
        setIsPlaying(true);
      }
    } catch (error) {
      console.error('播放音频失败:', error);
      toast({
        title: "播放失败",
        description: "音频播放失败",
        variant: "destructive"
      });
    }
  };

  const pauseAudio = () => {
    if (audioElementRef.current) {
      audioElementRef.current.pause();
      setIsPlaying(false);
    }
  };

  const downloadAudio = () => {
    if (!synthesizedAudio) return;

    try {
      const audioBlob = new Blob([
        Uint8Array.from(atob(synthesizedAudio), c => c.charCodeAt(0))
      ], { type: 'audio/wav' });
      
      const url = URL.createObjectURL(audioBlob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `synthesized_speech_${Date.now()}.wav`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('下载音频失败:', error);
      toast({
        title: "下载失败",
        description: "音频下载失败",
        variant: "destructive"
      });
    }
  };

  const uploadAudioFile = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    if (!file.type.startsWith('audio/')) {
      toast({
        title: "文件错误",
        description: "请选择音频文件",
        variant: "destructive"
      });
      return;
    }

    setIsLoading(true);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('language', language);

      const response = await fetch('/api/v1/voice/upload-audio', {
        method: 'POST',
        body: formData
      });

      const data = await response.json();
      
      if (data.success) {
        setRecognizedText(data.text);
        if (onTextGenerated) {
          onTextGenerated(data.text);
        }
        toast({
          title: "识别成功",
          description: `音频文件识别完成，置信度: ${(data.confidence * 100).toFixed(1)}%`,
          variant: "success"
        });
      } else {
        throw new Error(data.error || '音频识别失败');
      }
    } catch (error) {
      console.error('音频上传失败:', error);
      toast({
        title: "上传失败",
        description: error.message,
        variant: "destructive"
      });
    } finally {
      setIsLoading(false);
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const cleanup = () => {
    if (websocketRef.current) {
      websocketRef.current.close();
    }
    if (audioContextRef.current) {
      audioContextRef.current.close();
    }
    if (recordingTimerRef.current) {
      clearInterval(recordingTimerRef.current);
    }
  };

  return (
    <div className="space-y-6">
      {/* 连接状态 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Badge variant={isConnected ? "success" : "destructive"}>
            {isConnected ? "已连接" : "未连接"}
          </Badge>
          {isRecording && (
            <Badge variant="warning" className="animate-pulse">
              录音中 {formatTime(recordingTime)}
            </Badge>
          )}
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={connectWebSocket}
          disabled={isConnected}
        >
          重新连接
        </Button>
      </div>

      {/* 语音识别区域 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Mic className="w-5 h-5" />
            <span>语音识别</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center space-x-4">
            <Button
              onClick={isRecording ? stopRecording : startRecording}
              disabled={!isConnected}
              variant={isRecording ? "destructive" : "default"}
              size="lg"
            >
              {isRecording ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
              {isRecording ? "停止录音" : "开始录音"}
            </Button>
            
            <div className="flex-1">
              <label htmlFor="audio-upload" className="cursor-pointer">
                <Button variant="outline" asChild>
                  <span>
                    <Upload className="w-4 h-4 mr-2" />
                    上传音频
                  </span>
                </Button>
              </label>
              <input
                id="audio-upload"
                type="file"
                accept="audio/*"
                onChange={uploadAudioFile}
                className="hidden"
              />
            </div>

            <Select value={language} onValueChange={setLanguage}>
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="zh-CN">中文</SelectItem>
                <SelectItem value="en-US">英语</SelectItem>
                <SelectItem value="ja-JP">日语</SelectItem>
                <SelectItem value="ko-KR">韩语</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* 音频电平指示器 */}
          {isRecording && (
            <div className="space-y-2">
              <div className="text-sm text-gray-600">音频电平</div>
              <Progress value={audioLevel} className="w-full" />
            </div>
          )}

          {/* 识别结果 */}
          {recognizedText && (
            <div className="space-y-2">
              <div className="text-sm font-medium">识别结果:</div>
              <div className="p-3 bg-gray-50 rounded-lg border">
                {recognizedText}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* 语音合成区域 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Volume2 className="w-5 h-5" />
            <span>语音合成</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Textarea
            placeholder="输入要合成的文本..."
            value={textToSynthesize}
            onChange={(e) => setTextToSynthesize(e.target.value)}
            rows={3}
          />

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">语音选择</label>
              <Select value={selectedVoice} onValueChange={setSelectedVoice}>
                <SelectTrigger>
                  <SelectValue placeholder="选择语音" />
                </SelectTrigger>
                <SelectContent>
                  {availableVoices.map((voice) => (
                    <SelectItem key={voice.name} value={voice.name}>
                      {voice.display_name} ({voice.language})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">语速: {speechRate[0]}</label>
              <Slider
                value={speechRate}
                onValueChange={setSpeechRate}
                min={0.5}
                max={2.0}
                step={0.1}
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">音量: {Math.round(volume[0] * 100)}%</label>
              <Slider
                value={volume}
                onValueChange={setVolume}
                min={0}
                max={1}
                step={0.1}
              />
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <Button
              onClick={synthesizeSpeech}
              disabled={isLoading || !textToSynthesize.trim()}
            >
              {isLoading ? "合成中..." : "生成语音"}
            </Button>

            {synthesizedAudio && (
              <>
                <Button
                  variant="outline"
                  onClick={isPlaying ? pauseAudio : playAudio}
                >
                  {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                  {isPlaying ? "暂停" : "播放"}
                </Button>

                <Button
                  variant="outline"
                  onClick={downloadAudio}
                >
                  <Download className="w-4 h-4 mr-2" />
                  下载
                </Button>
              </>
            )}
          </div>
        </CardContent>
      </Card>

      {/* 隐藏的音频元素 */}
      <audio
        ref={audioElementRef}
        onEnded={() => setIsPlaying(false)}
        onPause={() => setIsPlaying(false)}
        onPlay={() => setIsPlaying(true)}
      />
    </div>
  );
};

export default VoiceInterface;
