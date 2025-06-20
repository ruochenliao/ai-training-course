import React, { useState, useRef, useEffect } from 'react';
import { 
  Image, 
  Palette, 
  Download, 
  Share2, 
  Trash2, 
  Settings,
  Loader2,
  RefreshCw,
  Eye,
  Copy,
  Wand2
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Textarea } from '../ui/textarea';
import { Input } from '../ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { Slider } from '../ui/slider';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../ui/dialog';
import { useToast } from '../ui/use-toast';

const ImageGenerationInterface = ({ onImageGenerated }) => {
  const [prompt, setPrompt] = useState('');
  const [negativePrompt, setNegativePrompt] = useState('');
  const [selectedEngine, setSelectedEngine] = useState('dalle3');
  const [selectedStyle, setSelectedStyle] = useState('');
  const [selectedSize, setSelectedSize] = useState('1024x1024');
  const [quality, setQuality] = useState('standard');
  const [numImages, setNumImages] = useState([1]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationProgress, setGenerationProgress] = useState(0);
  const [generatedImages, setGeneratedImages] = useState([]);
  const [generationHistory, setGenerationHistory] = useState([]);
  const [availableEngines, setAvailableEngines] = useState([]);
  const [availableStyles, setAvailableStyles] = useState([]);
  const [activeTasks, setActiveTasks] = useState([]);
  const [selectedImage, setSelectedImage] = useState(null);
  const [showImageModal, setShowImageModal] = useState(false);

  const { toast } = useToast();

  // 初始化
  useEffect(() => {
    initializeImageGeneration();
    loadGenerationHistory();
    
    // 定期更新活动任务
    const interval = setInterval(loadActiveTasks, 5000);
    return () => clearInterval(interval);
  }, []);

  const initializeImageGeneration = async () => {
    try {
      // 获取可用引擎
      const enginesResponse = await fetch('/api/v1/image-generation/engines');
      const enginesData = await enginesResponse.json();
      
      if (enginesData.success) {
        setAvailableEngines(enginesData.engines);
        setSelectedEngine(enginesData.default_engine);
      }

      // 获取可用风格
      const stylesResponse = await fetch('/api/v1/image-generation/styles');
      const stylesData = await stylesResponse.json();
      
      if (stylesData.success) {
        setAvailableStyles(stylesData.styles);
      }
    } catch (error) {
      console.error('初始化图像生成失败:', error);
      toast({
        title: "初始化失败",
        description: "图像生成服务初始化失败",
        variant: "destructive"
      });
    }
  };

  const loadGenerationHistory = async () => {
    try {
      const response = await fetch('/api/v1/image-generation/history?limit=20');
      const data = await response.json();
      
      if (data.success) {
        setGenerationHistory(data.history);
      }
    } catch (error) {
      console.error('加载生成历史失败:', error);
    }
  };

  const loadActiveTasks = async () => {
    try {
      const response = await fetch('/api/v1/image-generation/tasks');
      const data = await response.json();
      
      if (data.success) {
        setActiveTasks(data.active_tasks.tasks || []);
      }
    } catch (error) {
      console.error('加载活动任务失败:', error);
    }
  };

  const generateImage = async () => {
    if (!prompt.trim()) {
      toast({
        title: "输入错误",
        description: "请输入图像描述",
        variant: "destructive"
      });
      return;
    }

    setIsGenerating(true);
    setGenerationProgress(0);
    setGeneratedImages([]);

    // 模拟进度更新
    const progressInterval = setInterval(() => {
      setGenerationProgress(prev => {
        if (prev >= 90) {
          clearInterval(progressInterval);
          return prev;
        }
        return prev + Math.random() * 10;
      });
    }, 500);

    try {
      const requestData = {
        prompt: prompt,
        negative_prompt: negativePrompt || undefined,
        size: selectedSize,
        style: selectedStyle || undefined,
        quality: quality,
        num_images: numImages[0],
        engine: selectedEngine
      };

      const response = await fetch('/api/v1/image-generation/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
      });

      const data = await response.json();
      
      if (data.success) {
        setGeneratedImages(data.images);
        setGenerationProgress(100);
        
        if (onImageGenerated) {
          onImageGenerated(data);
        }

        toast({
          title: "生成成功",
          description: `成功生成 ${data.images.length} 张图像`,
          variant: "success"
        });

        // 刷新历史记录
        loadGenerationHistory();
      } else {
        throw new Error(data.error || '图像生成失败');
      }
    } catch (error) {
      console.error('图像生成失败:', error);
      toast({
        title: "生成失败",
        description: error.message,
        variant: "destructive"
      });
    } finally {
      clearInterval(progressInterval);
      setIsGenerating(false);
      setGenerationProgress(0);
    }
  };

  const downloadImage = (imageData, index) => {
    try {
      const link = document.createElement('a');
      link.href = `data:image/png;base64,${imageData.data}`;
      link.download = `generated_image_${Date.now()}_${index + 1}.png`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (error) {
      console.error('下载图像失败:', error);
      toast({
        title: "下载失败",
        description: "图像下载失败",
        variant: "destructive"
      });
    }
  };

  const copyImageToClipboard = async (imageData) => {
    try {
      const response = await fetch(`data:image/png;base64,${imageData.data}`);
      const blob = await response.blob();
      
      await navigator.clipboard.write([
        new ClipboardItem({ 'image/png': blob })
      ]);
      
      toast({
        title: "复制成功",
        description: "图像已复制到剪贴板",
        variant: "success"
      });
    } catch (error) {
      console.error('复制图像失败:', error);
      toast({
        title: "复制失败",
        description: "图像复制失败",
        variant: "destructive"
      });
    }
  };

  const shareImage = async (imageData) => {
    try {
      if (navigator.share) {
        const response = await fetch(`data:image/png;base64,${imageData.data}`);
        const blob = await response.blob();
        const file = new File([blob], 'generated_image.png', { type: 'image/png' });
        
        await navigator.share({
          title: 'AI生成的图像',
          text: prompt,
          files: [file]
        });
      } else {
        // 降级到复制链接
        await copyImageToClipboard(imageData);
      }
    } catch (error) {
      console.error('分享图像失败:', error);
      toast({
        title: "分享失败",
        description: "图像分享失败",
        variant: "destructive"
      });
    }
  };

  const cancelTask = async (taskId) => {
    try {
      const response = await fetch(`/api/v1/image-generation/tasks/${taskId}`, {
        method: 'DELETE'
      });

      const data = await response.json();
      
      if (data.success) {
        toast({
          title: "任务已取消",
          description: "图像生成任务已取消",
          variant: "success"
        });
        loadActiveTasks();
      }
    } catch (error) {
      console.error('取消任务失败:', error);
      toast({
        title: "取消失败",
        description: "任务取消失败",
        variant: "destructive"
      });
    }
  };

  const usePromptTemplate = (template) => {
    setPrompt(template);
  };

  const promptTemplates = [
    "一只可爱的小猫咪，卡通风格，高质量",
    "未来科技城市，赛博朋克风格，霓虹灯",
    "美丽的山水风景，中国画风格，水墨画",
    "宇宙星空，梦幻色彩，高清壁纸",
    "现代建筑设计，简约风格，建筑摄影"
  ];

  return (
    <div className="space-y-6">
      <Tabs defaultValue="generate" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="generate">图像生成</TabsTrigger>
          <TabsTrigger value="history">生成历史</TabsTrigger>
          <TabsTrigger value="tasks">活动任务</TabsTrigger>
        </TabsList>

        <TabsContent value="generate" className="space-y-6">
          {/* 生成参数设置 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Wand2 className="w-5 h-5" />
                <span>图像生成</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* 提示词输入 */}
              <div className="space-y-2">
                <label className="text-sm font-medium">描述提示词</label>
                <Textarea
                  placeholder="描述你想要生成的图像..."
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  rows={3}
                />
                
                {/* 提示词模板 */}
                <div className="flex flex-wrap gap-2">
                  {promptTemplates.map((template, index) => (
                    <Button
                      key={index}
                      variant="outline"
                      size="sm"
                      onClick={() => usePromptTemplate(template)}
                    >
                      {template.substring(0, 20)}...
                    </Button>
                  ))}
                </div>
              </div>

              {/* 负面提示词 */}
              <div className="space-y-2">
                <label className="text-sm font-medium">负面提示词（可选）</label>
                <Textarea
                  placeholder="描述你不想要的元素..."
                  value={negativePrompt}
                  onChange={(e) => setNegativePrompt(e.target.value)}
                  rows={2}
                />
              </div>

              {/* 生成参数 */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">生成引擎</label>
                  <Select value={selectedEngine} onValueChange={setSelectedEngine}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {availableEngines.map((engine) => (
                        <SelectItem key={engine.name} value={engine.name}>
                          {engine.display_name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">图像尺寸</label>
                  <Select value={selectedSize} onValueChange={setSelectedSize}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="512x512">512×512</SelectItem>
                      <SelectItem value="768x768">768×768</SelectItem>
                      <SelectItem value="1024x1024">1024×1024</SelectItem>
                      <SelectItem value="1792x1024">1792×1024</SelectItem>
                      <SelectItem value="1024x1792">1024×1792</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">图像风格</label>
                  <Select value={selectedStyle} onValueChange={setSelectedStyle}>
                    <SelectTrigger>
                      <SelectValue placeholder="选择风格" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="">默认</SelectItem>
                      {availableStyles.map((style) => (
                        <SelectItem key={style.name} value={style.name}>
                          {style.display_name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">图像质量</label>
                  <Select value={quality} onValueChange={setQuality}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="standard">标准</SelectItem>
                      <SelectItem value="hd">高清</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* 生成数量 */}
              <div className="space-y-2">
                <label className="text-sm font-medium">
                  生成数量: {numImages[0]}
                </label>
                <Slider
                  value={numImages}
                  onValueChange={setNumImages}
                  min={1}
                  max={4}
                  step={1}
                  className="w-full"
                />
              </div>

              {/* 生成按钮 */}
              <div className="flex items-center space-x-4">
                <Button
                  onClick={generateImage}
                  disabled={isGenerating || !prompt.trim()}
                  size="lg"
                >
                  {isGenerating ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      生成中...
                    </>
                  ) : (
                    <>
                      <Image className="w-4 h-4 mr-2" />
                      生成图像
                    </>
                  )}
                </Button>

                {isGenerating && (
                  <div className="flex-1">
                    <Progress value={generationProgress} className="w-full" />
                    <div className="text-sm text-gray-600 mt-1">
                      生成进度: {Math.round(generationProgress)}%
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* 生成结果 */}
          {generatedImages.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>生成结果</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {generatedImages.map((image, index) => (
                    <div key={index} className="relative group">
                      <img
                        src={`data:image/png;base64,${image.data}`}
                        alt={`Generated ${index + 1}`}
                        className="w-full h-64 object-cover rounded-lg cursor-pointer"
                        onClick={() => {
                          setSelectedImage(image);
                          setShowImageModal(true);
                        }}
                      />
                      
                      {/* 操作按钮 */}
                      <div className="absolute inset-0 bg-black bg-opacity-50 opacity-0 group-hover:opacity-100 transition-opacity rounded-lg flex items-center justify-center space-x-2">
                        <Button
                          size="sm"
                          variant="secondary"
                          onClick={() => {
                            setSelectedImage(image);
                            setShowImageModal(true);
                          }}
                        >
                          <Eye className="w-4 h-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="secondary"
                          onClick={() => downloadImage(image, index)}
                        >
                          <Download className="w-4 h-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="secondary"
                          onClick={() => copyImageToClipboard(image)}
                        >
                          <Copy className="w-4 h-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="secondary"
                          onClick={() => shareImage(image)}
                        >
                          <Share2 className="w-4 h-4" />
                        </Button>
                      </div>

                      {/* 图像信息 */}
                      <div className="mt-2 text-sm text-gray-600">
                        <div>尺寸: {image.size?.[0]}×{image.size?.[1]}</div>
                        <div>大小: {(image.file_size / 1024).toFixed(1)} KB</div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="history">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>生成历史</span>
                <Button variant="outline" size="sm" onClick={loadGenerationHistory}>
                  <RefreshCw className="w-4 h-4 mr-2" />
                  刷新
                </Button>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {generationHistory.length > 0 ? (
                <div className="space-y-4">
                  {generationHistory.map((record, index) => (
                    <div key={index} className="border rounded-lg p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="font-medium">{record.prompt}</div>
                          <div className="text-sm text-gray-600 mt-1">
                            {new Date(record.timestamp).toLocaleString()}
                          </div>
                        </div>
                        <Badge variant={record.success ? "success" : "destructive"}>
                          {record.success ? "成功" : "失败"}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center text-gray-500 py-8">
                  暂无生成历史
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="tasks">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>活动任务</span>
                <Button variant="outline" size="sm" onClick={loadActiveTasks}>
                  <RefreshCw className="w-4 h-4 mr-2" />
                  刷新
                </Button>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {activeTasks.length > 0 ? (
                <div className="space-y-4">
                  {activeTasks.map((task, index) => (
                    <div key={index} className="border rounded-lg p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="font-medium">{task.prompt}</div>
                          <div className="text-sm text-gray-600">
                            状态: {task.status} | 开始时间: {new Date(task.start_time).toLocaleString()}
                          </div>
                        </div>
                        <Button
                          variant="destructive"
                          size="sm"
                          onClick={() => cancelTask(task.task_id)}
                        >
                          <Trash2 className="w-4 h-4 mr-2" />
                          取消
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center text-gray-500 py-8">
                  暂无活动任务
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* 图像预览模态框 */}
      <Dialog open={showImageModal} onOpenChange={setShowImageModal}>
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle>图像预览</DialogTitle>
          </DialogHeader>
          {selectedImage && (
            <div className="space-y-4">
              <img
                src={`data:image/png;base64,${selectedImage.data}`}
                alt="Preview"
                className="w-full max-h-96 object-contain rounded-lg"
              />
              <div className="flex items-center justify-between">
                <div className="text-sm text-gray-600">
                  尺寸: {selectedImage.size?.[0]}×{selectedImage.size?.[1]} | 
                  大小: {(selectedImage.file_size / 1024).toFixed(1)} KB
                </div>
                <div className="flex space-x-2">
                  <Button
                    variant="outline"
                    onClick={() => downloadImage(selectedImage, 0)}
                  >
                    <Download className="w-4 h-4 mr-2" />
                    下载
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => copyImageToClipboard(selectedImage)}
                  >
                    <Copy className="w-4 h-4 mr-2" />
                    复制
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => shareImage(selectedImage)}
                  >
                    <Share2 className="w-4 h-4 mr-2" />
                    分享
                  </Button>
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default ImageGenerationInterface;
