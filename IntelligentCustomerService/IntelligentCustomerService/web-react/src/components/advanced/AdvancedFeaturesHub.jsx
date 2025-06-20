import React, { useState, useEffect } from 'react';
import { 
  Mic, 
  Image, 
  Users, 
  BarChart3, 
  Settings,
  Sparkles,
  Zap,
  Brain,
  Palette
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../ui/dialog';
import { useToast } from '../ui/use-toast';

// 导入各个功能组件
import VoiceInterface from '../voice/VoiceInterface';
import ImageGenerationInterface from '../image/ImageGenerationInterface';
import CollaborationInterface from '../collaboration/CollaborationInterface';
import AnalyticsDashboard from '../analytics/AnalyticsDashboard';

const AdvancedFeaturesHub = ({ currentUser }) => {
  const [activeFeature, setActiveFeature] = useState('voice');
  const [featureStats, setFeatureStats] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

  const { toast } = useToast();

  // 功能配置
  const features = [
    {
      id: 'voice',
      name: '语音交互',
      description: '智能语音识别与合成',
      icon: Mic,
      color: 'bg-blue-500',
      component: VoiceInterface,
      enabled: true
    },
    {
      id: 'image',
      name: 'AI绘画',
      description: '文本到图像生成',
      icon: Palette,
      color: 'bg-purple-500',
      component: ImageGenerationInterface,
      enabled: true
    },
    {
      id: 'collaboration',
      name: '实时协作',
      description: '多用户实时聊天协作',
      icon: Users,
      color: 'bg-green-500',
      component: CollaborationInterface,
      enabled: true
    },
    {
      id: 'analytics',
      name: '高级分析',
      description: '用户行为与数据洞察',
      icon: BarChart3,
      color: 'bg-orange-500',
      component: AnalyticsDashboard,
      enabled: true
    }
  ];

  // 初始化
  useEffect(() => {
    loadFeatureStats();
    
    // 定期更新统计信息
    const interval = setInterval(loadFeatureStats, 60000); // 每分钟更新
    return () => clearInterval(interval);
  }, []);

  const loadFeatureStats = async () => {
    try {
      const stats = {};
      
      // 获取语音功能统计
      try {
        const voiceResponse = await fetch('/api/v1/voice/status');
        const voiceData = await voiceResponse.json();
        stats.voice = {
          status: voiceData.success ? 'active' : 'inactive',
          isListening: voiceData.status?.is_listening || false,
          isSpeaking: voiceData.status?.is_speaking || false
        };
      } catch (error) {
        stats.voice = { status: 'error' };
      }

      // 获取图像生成统计
      try {
        const imageResponse = await fetch('/api/v1/image-generation/stats');
        const imageData = await imageResponse.json();
        stats.image = {
          status: imageData.success ? 'active' : 'inactive',
          totalGenerations: imageData.stats?.total_generations || 0,
          successRate: imageData.stats?.success_rate || 0,
          activeTasks: imageData.stats?.active_tasks || 0
        };
      } catch (error) {
        stats.image = { status: 'error' };
      }

      // 获取协作功能统计
      try {
        const collabResponse = await fetch('/api/v1/collaboration/stats');
        const collabData = await collabResponse.json();
        stats.collaboration = {
          status: collabData.success ? 'active' : 'inactive',
          totalRooms: collabData.stats?.total_rooms || 0,
          activeRooms: collabData.stats?.active_rooms || 0,
          totalUsers: collabData.stats?.total_users || 0
        };
      } catch (error) {
        stats.collaboration = { status: 'error' };
      }

      // 获取分析功能统计
      try {
        const analyticsResponse = await fetch('/api/v1/analytics/dashboard');
        const analyticsData = await analyticsResponse.json();
        stats.analytics = {
          status: analyticsData.success ? 'active' : 'inactive',
          totalEvents: analyticsData.dashboard?.overview?.total_events || 0,
          uniqueUsers: analyticsData.dashboard?.overview?.unique_users || 0,
          atRiskUsers: analyticsData.dashboard?.at_risk_users?.high_risk || 0
        };
      } catch (error) {
        stats.analytics = { status: 'error' };
      }

      setFeatureStats(stats);
    } catch (error) {
      console.error('加载功能统计失败:', error);
    }
  };

  const testAllFeatures = async () => {
    setIsLoading(true);
    const results = {};

    try {
      // 测试语音功能
      try {
        const voiceResponse = await fetch('/api/v1/voice/test', { method: 'POST' });
        const voiceData = await voiceResponse.json();
        results.voice = voiceData.success;
      } catch (error) {
        results.voice = false;
      }

      // 测试图像生成功能
      try {
        const imageResponse = await fetch('/api/v1/image-generation/test', { method: 'POST' });
        const imageData = await imageResponse.json();
        results.image = imageData.success;
      } catch (error) {
        results.image = false;
      }

      // 测试协作功能
      try {
        const collabResponse = await fetch('/api/v1/collaboration/test', { method: 'POST' });
        const collabData = await collabResponse.json();
        results.collaboration = collabData.success;
      } catch (error) {
        results.collaboration = false;
      }

      // 测试分析功能
      try {
        const analyticsResponse = await fetch('/api/v1/analytics/test', { method: 'POST' });
        const analyticsData = await analyticsResponse.json();
        results.analytics = analyticsData.success;
      } catch (error) {
        results.analytics = false;
      }

      // 显示测试结果
      const successCount = Object.values(results).filter(Boolean).length;
      const totalCount = Object.keys(results).length;

      toast({
        title: "功能测试完成",
        description: `${successCount}/${totalCount} 个功能测试通过`,
        variant: successCount === totalCount ? "success" : "warning"
      });

      // 刷新统计信息
      loadFeatureStats();
    } catch (error) {
      console.error('功能测试失败:', error);
      toast({
        title: "测试失败",
        description: "功能测试过程中发生错误",
        variant: "destructive"
      });
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'active':
        return <Badge variant="success">正常</Badge>;
      case 'inactive':
        return <Badge variant="secondary">未激活</Badge>;
      case 'error':
        return <Badge variant="destructive">错误</Badge>;
      default:
        return <Badge variant="outline">未知</Badge>;
    }
  };

  const getFeatureIcon = (feature) => {
    const IconComponent = feature.icon;
    return <IconComponent className="w-6 h-6" />;
  };

  const renderActiveFeature = () => {
    const feature = features.find(f => f.id === activeFeature);
    if (!feature || !feature.enabled) return null;

    const Component = feature.component;
    const props = {
      currentUser,
      onTextGenerated: (text) => {
        // 处理语音识别结果
        console.log('语音识别结果:', text);
      },
      onVoiceGenerated: (data) => {
        // 处理语音合成结果
        console.log('语音合成结果:', data);
      },
      onImageGenerated: (data) => {
        // 处理图像生成结果
        console.log('图像生成结果:', data);
      },
      onRoomChange: (room) => {
        // 处理房间变更
        console.log('房间变更:', room);
      }
    };

    return <Component {...props} />;
  };

  return (
    <div className="space-y-6">
      {/* 头部 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center space-x-2">
            <Sparkles className="w-8 h-8 text-purple-600" />
            <span>高级功能中心</span>
          </h1>
          <p className="text-gray-600 mt-2">
            体验最新的AI驱动功能：语音交互、AI绘画、实时协作和智能分析
          </p>
        </div>
        
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            onClick={testAllFeatures}
            disabled={isLoading}
          >
            <Zap className="w-4 h-4 mr-2" />
            {isLoading ? '测试中...' : '测试所有功能'}
          </Button>
          
          <Dialog open={showSettings} onOpenChange={setShowSettings}>
            <DialogTrigger asChild>
              <Button variant="outline">
                <Settings className="w-4 h-4 mr-2" />
                设置
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>功能设置</DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                <p className="text-sm text-gray-600">
                  在这里可以配置各个高级功能的参数和选项。
                </p>
                {/* 这里可以添加具体的设置选项 */}
                <div className="text-center text-gray-500">
                  功能设置面板开发中...
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* 功能概览卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {features.map((feature) => (
          <Card 
            key={feature.id}
            className={`cursor-pointer transition-all hover:shadow-lg ${
              activeFeature === feature.id ? 'ring-2 ring-blue-500' : ''
            }`}
            onClick={() => setActiveFeature(feature.id)}
          >
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div className={`p-2 rounded-lg ${feature.color} text-white`}>
                  {getFeatureIcon(feature)}
                </div>
                {getStatusBadge(featureStats[feature.id]?.status)}
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <h3 className="font-semibold">{feature.name}</h3>
                <p className="text-sm text-gray-600">{feature.description}</p>
                
                {/* 功能特定的统计信息 */}
                {feature.id === 'voice' && featureStats.voice && (
                  <div className="text-xs space-y-1">
                    {featureStats.voice.isListening && (
                      <div className="text-blue-600">🎤 正在监听</div>
                    )}
                    {featureStats.voice.isSpeaking && (
                      <div className="text-green-600">🔊 正在播放</div>
                    )}
                  </div>
                )}
                
                {feature.id === 'image' && featureStats.image && (
                  <div className="text-xs space-y-1">
                    <div>生成: {featureStats.image.totalGenerations}</div>
                    <div>成功率: {(featureStats.image.successRate * 100).toFixed(1)}%</div>
                    {featureStats.image.activeTasks > 0 && (
                      <div className="text-blue-600">活动任务: {featureStats.image.activeTasks}</div>
                    )}
                  </div>
                )}
                
                {feature.id === 'collaboration' && featureStats.collaboration && (
                  <div className="text-xs space-y-1">
                    <div>房间: {featureStats.collaboration.totalRooms}</div>
                    <div>活跃: {featureStats.collaboration.activeRooms}</div>
                    <div>在线: {featureStats.collaboration.totalUsers}</div>
                  </div>
                )}
                
                {feature.id === 'analytics' && featureStats.analytics && (
                  <div className="text-xs space-y-1">
                    <div>事件: {featureStats.analytics.totalEvents}</div>
                    <div>用户: {featureStats.analytics.uniqueUsers}</div>
                    {featureStats.analytics.atRiskUsers > 0 && (
                      <div className="text-red-600">风险: {featureStats.analytics.atRiskUsers}</div>
                    )}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* 功能内容区域 */}
      <Card className="min-h-[600px]">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            {getFeatureIcon(features.find(f => f.id === activeFeature))}
            <span>{features.find(f => f.id === activeFeature)?.name}</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {renderActiveFeature()}
        </CardContent>
      </Card>

      {/* 快速操作面板 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Brain className="w-5 h-5" />
            <span>智能助手</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Button variant="outline" className="h-20 flex flex-col space-y-2">
              <Mic className="w-6 h-6" />
              <span className="text-sm">语音助手</span>
            </Button>
            
            <Button variant="outline" className="h-20 flex flex-col space-y-2">
              <Palette className="w-6 h-6" />
              <span className="text-sm">创意绘画</span>
            </Button>
            
            <Button variant="outline" className="h-20 flex flex-col space-y-2">
              <Users className="w-6 h-6" />
              <span className="text-sm">团队协作</span>
            </Button>
            
            <Button variant="outline" className="h-20 flex flex-col space-y-2">
              <BarChart3 className="w-6 h-6" />
              <span className="text-sm">数据洞察</span>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default AdvancedFeaturesHub;
