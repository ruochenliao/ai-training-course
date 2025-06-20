import React, { useState, useEffect } from 'react';
import { 
  BarChart3, 
  TrendingUp, 
  Users, 
  Activity, 
  AlertTriangle,
  Eye,
  Download,
  RefreshCw,
  Calendar,
  Filter
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { DatePickerWithRange } from '../ui/date-range-picker';
import { useToast } from '../ui/use-toast';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

const AnalyticsDashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [userSegments, setUserSegments] = useState(null);
  const [trendsData, setTrendsData] = useState(null);
  const [churnPrediction, setChurnPrediction] = useState([]);
  const [selectedMetric, setSelectedMetric] = useState('events');
  const [selectedPeriod, setSelectedPeriod] = useState(7);
  const [isLoading, setIsLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);

  const { toast } = useToast();

  // 初始化
  useEffect(() => {
    loadDashboardData();
    loadTrendsData();
    loadChurnPrediction();
    
    // 定期刷新数据
    const interval = setInterval(() => {
      loadDashboardData();
    }, 300000); // 5分钟刷新一次
    
    return () => clearInterval(interval);
  }, [selectedPeriod]);

  const loadDashboardData = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/v1/analytics/dashboard');
      const data = await response.json();
      
      if (data.success) {
        setDashboardData(data.dashboard);
        setUserSegments(data.dashboard.user_segments);
        setLastUpdated(new Date());
      }
    } catch (error) {
      console.error('加载仪表板数据失败:', error);
      toast({
        title: "加载失败",
        description: "无法加载分析数据",
        variant: "destructive"
      });
    } finally {
      setIsLoading(false);
    }
  };

  const loadTrendsData = async () => {
    try {
      const response = await fetch(`/api/v1/analytics/trends?metric=${selectedMetric}&days=${selectedPeriod}`);
      const data = await response.json();
      
      if (data.success) {
        setTrendsData(data.trends);
      }
    } catch (error) {
      console.error('加载趋势数据失败:', error);
    }
  };

  const loadChurnPrediction = async () => {
    try {
      const response = await fetch('/api/v1/analytics/churn-prediction?days_threshold=7');
      const data = await response.json();
      
      if (data.success) {
        setChurnPrediction(data.at_risk_users.slice(0, 10)); // 只显示前10个
      }
    } catch (error) {
      console.error('加载流失预测失败:', error);
    }
  };

  const exportReport = async () => {
    try {
      const response = await fetch('/api/v1/analytics/reports/user-engagement?days=30');
      const data = await response.json();
      
      if (data.success) {
        // 创建并下载报告
        const reportContent = JSON.stringify(data.report, null, 2);
        const blob = new Blob([reportContent], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `analytics_report_${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        toast({
          title: "导出成功",
          description: "分析报告已下载",
          variant: "success"
        });
      }
    } catch (error) {
      console.error('导出报告失败:', error);
      toast({
        title: "导出失败",
        description: "无法导出分析报告",
        variant: "destructive"
      });
    }
  };

  const formatNumber = (num) => {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
  };

  const getTrendColor = (direction) => {
    switch (direction) {
      case 'up': return 'text-green-600';
      case 'down': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getTrendIcon = (direction) => {
    switch (direction) {
      case 'up': return <TrendingUp className="w-4 h-4" />;
      case 'down': return <TrendingUp className="w-4 h-4 rotate-180" />;
      default: return <Activity className="w-4 h-4" />;
    }
  };

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

  if (!dashboardData) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-4" />
          <p>加载分析数据中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 头部控制 */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">数据分析仪表板</h2>
          {lastUpdated && (
            <p className="text-sm text-gray-600">
              最后更新: {lastUpdated.toLocaleString()}
            </p>
          )}
        </div>
        
        <div className="flex items-center space-x-2">
          <Select value={selectedPeriod.toString()} onValueChange={(value) => setSelectedPeriod(parseInt(value))}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7">最近7天</SelectItem>
              <SelectItem value="30">最近30天</SelectItem>
              <SelectItem value="90">最近90天</SelectItem>
            </SelectContent>
          </Select>
          
          <Button variant="outline" onClick={loadDashboardData} disabled={isLoading}>
            <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            刷新
          </Button>
          
          <Button variant="outline" onClick={exportReport}>
            <Download className="w-4 h-4 mr-2" />
            导出报告
          </Button>
        </div>
      </div>

      {/* 概览卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">总事件数</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatNumber(dashboardData.overview.total_events)}
            </div>
            <p className="text-xs text-muted-foreground">
              日均 {formatNumber(dashboardData.overview.avg_daily_events)} 个事件
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">活跃用户</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatNumber(dashboardData.overview.unique_users)}
            </div>
            <p className="text-xs text-muted-foreground">
              日均 {formatNumber(dashboardData.overview.avg_daily_users)} 个用户
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">用户分群</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {userSegments?.total_users || 0}
            </div>
            <p className="text-xs text-muted-foreground">
              {Object.keys(userSegments?.segments || {}).length} 个分群
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">流失风险</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {dashboardData.at_risk_users.high_risk}
            </div>
            <p className="text-xs text-muted-foreground">
              高风险用户数量
            </p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">概览</TabsTrigger>
          <TabsTrigger value="trends">趋势分析</TabsTrigger>
          <TabsTrigger value="segments">用户分群</TabsTrigger>
          <TabsTrigger value="churn">流失预测</TabsTrigger>
          <TabsTrigger value="features">功能使用</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          {/* 日活跃度趋势 */}
          <Card>
            <CardHeader>
              <CardTitle>日活跃度趋势</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={Object.entries(dashboardData.daily_metrics).map(([date, metrics]) => ({
                  date,
                  events: metrics.events,
                  users: metrics.unique_users
                }))}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Area type="monotone" dataKey="events" stackId="1" stroke="#8884d8" fill="#8884d8" name="事件数" />
                  <Area type="monotone" dataKey="users" stackId="2" stroke="#82ca9d" fill="#82ca9d" name="用户数" />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* 性能指标 */}
          {dashboardData.performance && Object.keys(dashboardData.performance).length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>系统性能</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold">
                      {(dashboardData.performance.avg_response_time * 1000).toFixed(0)}ms
                    </div>
                    <div className="text-sm text-gray-600">平均响应时间</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold">
                      {(dashboardData.performance.avg_error_rate * 100).toFixed(2)}%
                    </div>
                    <div className="text-sm text-gray-600">错误率</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold">
                      {(dashboardData.performance.avg_cpu_usage * 100).toFixed(1)}%
                    </div>
                    <div className="text-sm text-gray-600">CPU使用率</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold">
                      {(dashboardData.performance.avg_memory_usage * 100).toFixed(1)}%
                    </div>
                    <div className="text-sm text-gray-600">内存使用率</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="trends" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>趋势分析</span>
                <Select value={selectedMetric} onValueChange={setSelectedMetric}>
                  <SelectTrigger className="w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="events">事件数</SelectItem>
                    <SelectItem value="users">用户数</SelectItem>
                    <SelectItem value="sessions">会话数</SelectItem>
                    <SelectItem value="errors">错误数</SelectItem>
                  </SelectContent>
                </Select>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {trendsData && (
                <>
                  <div className="mb-4 p-4 bg-gray-50 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-sm text-gray-600">趋势方向</div>
                        <div className={`flex items-center space-x-1 ${getTrendColor(trendsData.summary.trend_direction)}`}>
                          {getTrendIcon(trendsData.summary.trend_direction)}
                          <span className="font-medium">
                            {trendsData.summary.trend_direction === 'up' ? '上升' : 
                             trendsData.summary.trend_direction === 'down' ? '下降' : '稳定'}
                          </span>
                        </div>
                      </div>
                      <div>
                        <div className="text-sm text-gray-600">变化幅度</div>
                        <div className={`font-medium ${getTrendColor(trendsData.summary.trend_direction)}`}>
                          {trendsData.summary.trend_percentage > 0 ? '+' : ''}
                          {trendsData.summary.trend_percentage.toFixed(1)}%
                        </div>
                      </div>
                      <div>
                        <div className="text-sm text-gray-600">平均值</div>
                        <div className="font-medium">
                          {formatNumber(trendsData.summary.avg_value)}
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={trendsData.data}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis />
                      <Tooltip />
                      <Line type="monotone" dataKey="value" stroke="#8884d8" strokeWidth={2} />
                    </LineChart>
                  </ResponsiveContainer>
                </>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="segments" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* 用户分群饼图 */}
            <Card>
              <CardHeader>
                <CardTitle>用户分群分布</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={Object.entries(userSegments?.segments || {}).map(([segment, data]) => ({
                        name: segment,
                        value: data.count,
                        percentage: data.percentage
                      }))}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percentage }) => `${name} ${percentage}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {Object.entries(userSegments?.segments || {}).map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* 分群详情 */}
            <Card>
              <CardHeader>
                <CardTitle>分群详情</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {Object.entries(userSegments?.segments || {}).map(([segment, data], index) => (
                    <div key={segment} className="flex items-center justify-between p-3 border rounded-lg">
                      <div className="flex items-center space-x-3">
                        <div 
                          className="w-4 h-4 rounded-full"
                          style={{ backgroundColor: COLORS[index % COLORS.length] }}
                        />
                        <div>
                          <div className="font-medium">{segment}</div>
                          <div className="text-sm text-gray-600">{data.count} 用户</div>
                        </div>
                      </div>
                      <Badge variant="secondary">{data.percentage}%</Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="churn" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>流失风险用户</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {churnPrediction.map((user, index) => (
                  <div key={user.user_id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex-1">
                      <div className="font-medium">用户 {user.user_id}</div>
                      <div className="text-sm text-gray-600">
                        最后活跃: {new Date(user.last_activity).toLocaleDateString()} 
                        ({user.days_inactive} 天前)
                      </div>
                      <div className="text-sm">
                        用户分群: <Badge variant="outline">{user.user_segment}</Badge>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm text-gray-600">风险评分</div>
                      <div className="flex items-center space-x-2">
                        <Progress value={user.risk_score * 100} className="w-20" />
                        <span className={`font-medium ${
                          user.risk_score > 0.7 ? 'text-red-600' : 
                          user.risk_score > 0.3 ? 'text-yellow-600' : 'text-green-600'
                        }`}>
                          {(user.risk_score * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="features" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>功能使用统计</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={Object.entries(dashboardData.feature_usage).map(([feature, count]) => ({
                  feature,
                  count
                }))}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="feature" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" fill="#8884d8" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AnalyticsDashboard;
