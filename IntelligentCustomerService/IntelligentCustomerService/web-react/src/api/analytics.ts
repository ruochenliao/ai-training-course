import { request } from '../utils/request'

// 时间范围类型
export type TimeRange = '1h' | '6h' | '24h' | '7d' | '30d' | '90d' | 'custom'

// 图表数据点接口
export interface DataPoint {
  timestamp: string
  value: number
  label?: string
}

// 趋势数据接口
export interface TrendData {
  current: number
  previous: number
  change: number
  changePercent: number
  trend: 'up' | 'down' | 'stable'
}

// 统计概览接口
export interface OverviewStats {
  totalSessions: TrendData
  activeSessions: TrendData
  avgResponseTime: TrendData
  satisfactionRate: TrendData
  resolvedSessions: TrendData
  onlineAgents: TrendData
}

// 会话统计接口
export interface SessionAnalytics {
  overview: OverviewStats
  sessionsByHour: DataPoint[]
  sessionsByDay: DataPoint[]
  sessionsBySource: Array<{
    source: string
    count: number
    percentage: number
  }>
  sessionsByStatus: Array<{
    status: string
    count: number
    percentage: number
  }>
  avgWaitingTime: DataPoint[]
  avgResponseTime: DataPoint[]
  avgSessionDuration: DataPoint[]
}

// 客服统计接口
export interface AgentAnalytics {
  totalAgents: number
  onlineAgents: number
  busyAgents: number
  avgSessionsPerAgent: number
  topPerformers: Array<{
    agentId: string
    agentName: string
    avatar: string
    totalSessions: number
    resolvedSessions: number
    avgResponseTime: number
    satisfactionRate: number
    score: number
  }>
  agentWorkload: Array<{
    agentId: string
    agentName: string
    currentSessions: number
    maxSessions: number
    utilization: number
  }>
  responseTimeDistribution: Array<{
    range: string
    count: number
    percentage: number
  }>
}

// 用户统计接口
export interface UserAnalytics {
  totalUsers: TrendData
  newUsers: TrendData
  activeUsers: TrendData
  returningUsers: TrendData
  usersByVipLevel: Array<{
    level: number
    count: number
    percentage: number
  }>
  userActivity: DataPoint[]
  userRetention: Array<{
    period: string
    rate: number
  }>
  topUsers: Array<{
    userId: string
    username: string
    avatar: string
    totalSessions: number
    lastActiveAt: string
    vipLevel: number
  }>
}

// 满意度统计接口
export interface SatisfactionAnalytics {
  overallRating: TrendData
  ratingDistribution: Array<{
    rating: number
    count: number
    percentage: number
  }>
  satisfactionTrend: DataPoint[]
  feedbackKeywords: Array<{
    keyword: string
    count: number
    sentiment: 'positive' | 'negative' | 'neutral'
  }>
  departmentSatisfaction: Array<{
    department: string
    rating: number
    count: number
  }>
}

// 热门问题接口
export interface PopularQuestion {
  id: string
  question: string
  category: string
  count: number
  trend: 'up' | 'down' | 'stable'
  avgResponseTime: number
  satisfactionRate: number
  lastAsked: string
}

// 知识库统计接口
export interface KnowledgeAnalytics {
  totalArticles: TrendData
  totalViews: TrendData
  searchQueries: TrendData
  hitRate: TrendData
  popularArticles: Array<{
    id: string
    title: string
    category: string
    views: number
    likes: number
    helpfulRate: number
  }>
  searchKeywords: Array<{
    keyword: string
    count: number
    hitRate: number
  }>
  categoryStats: Array<{
    category: string
    articleCount: number
    viewCount: number
    avgRating: number
  }>
}

// 系统性能统计接口
export interface PerformanceAnalytics {
  responseTime: {
    avg: number
    p50: number
    p95: number
    p99: number
    trend: DataPoint[]
  }
  throughput: {
    requestsPerSecond: number
    trend: DataPoint[]
  }
  errorRate: {
    rate: number
    trend: DataPoint[]
  }
  systemLoad: {
    cpu: DataPoint[]
    memory: DataPoint[]
    disk: DataPoint[]
  }
  apiEndpoints: Array<{
    endpoint: string
    requests: number
    avgResponseTime: number
    errorRate: number
  }>
}

// 实时统计接口
export interface RealTimeStats {
  currentSessions: number
  waitingSessions: number
  onlineAgents: number
  avgWaitingTime: number
  recentSessions: Array<{
    id: string
    userId: string
    username: string
    status: string
    waitingTime: number
    agentName?: string
  }>
  systemAlerts: Array<{
    id: string
    type: 'warning' | 'error' | 'info'
    message: string
    timestamp: string
  }>
}

// 报告接口
export interface Report {
  id: string
  name: string
  type: 'session' | 'agent' | 'user' | 'satisfaction' | 'knowledge' | 'performance'
  description: string
  schedule: 'daily' | 'weekly' | 'monthly' | 'custom'
  recipients: string[]
  isEnabled: boolean
  lastGenerated?: string
  nextGeneration?: string
  createdAt: string
  updatedAt: string
}

// 查询参数接口
export interface AnalyticsQueryParams {
  timeRange?: TimeRange
  startDate?: string
  endDate?: string
  agentId?: string
  department?: string
  source?: string
  granularity?: 'hour' | 'day' | 'week' | 'month'
}

export const analyticsApi = {
  // 概览统计
  getOverviewStats: (params?: AnalyticsQueryParams): Promise<OverviewStats> => {
    return request.get('/api/analytics/overview', { params })
  },

  // 会话分析
  getSessionAnalytics: (params?: AnalyticsQueryParams): Promise<SessionAnalytics> => {
    return request.get('/api/analytics/sessions', { params })
  },

  // 客服分析
  getAgentAnalytics: (params?: AnalyticsQueryParams): Promise<AgentAnalytics> => {
    return request.get('/api/analytics/agents', { params })
  },

  // 用户分析
  getUserAnalytics: (params?: AnalyticsQueryParams): Promise<UserAnalytics> => {
    return request.get('/api/analytics/users', { params })
  },

  // 满意度分析
  getSatisfactionAnalytics: (params?: AnalyticsQueryParams): Promise<SatisfactionAnalytics> => {
    return request.get('/api/analytics/satisfaction', { params })
  },

  // 热门问题
  getPopularQuestions: (
    params?: AnalyticsQueryParams & {
      limit?: number
      category?: string
    },
  ): Promise<PopularQuestion[]> => {
    return request.get('/api/analytics/popular-questions', { params })
  },

  // 知识库分析
  getKnowledgeAnalytics: (params?: AnalyticsQueryParams): Promise<KnowledgeAnalytics> => {
    return request.get('/api/analytics/knowledge', { params })
  },

  // 系统性能分析
  getPerformanceAnalytics: (params?: AnalyticsQueryParams): Promise<PerformanceAnalytics> => {
    return request.get('/api/analytics/performance', { params })
  },

  // 实时统计
  getRealTimeStats: (): Promise<RealTimeStats> => {
    return request.get('/api/analytics/realtime')
  },

  // 自定义查询
  customQuery: (query: {
    metrics: string[]
    dimensions: string[]
    filters?: Record<string, any>
    timeRange?: AnalyticsQueryParams
    groupBy?: string[]
    orderBy?: string
    limit?: number
  }): Promise<{
    data: Record<string, any>[]
    total: number
    aggregations?: Record<string, number>
  }> => {
    return request.post('/api/analytics/custom', query)
  },

  // 导出数据
  exportAnalytics: (type: string, params?: AnalyticsQueryParams): Promise<Blob> => {
    return request.get(`/api/analytics/${type}/export`, {
      params,
      responseType: 'blob',
    })
  },

  // 报告管理
  getReports: (): Promise<Report[]> => {
    return request.get('/api/analytics/reports')
  },

  createReport: (data: Omit<Report, 'id' | 'createdAt' | 'updatedAt'>): Promise<Report> => {
    return request.post('/api/analytics/reports', data)
  },

  updateReport: (id: string, data: Partial<Report>): Promise<Report> => {
    return request.put(`/api/analytics/reports/${id}`, data)
  },

  deleteReport: (id: string): Promise<void> => {
    return request.delete(`/api/analytics/reports/${id}`)
  },

  generateReport: (
    id: string,
  ): Promise<{
    reportId: string
    downloadUrl: string
  }> => {
    return request.post(`/api/analytics/reports/${id}/generate`)
  },

  // 仪表板配置
  getDashboardConfig: (): Promise<{
    widgets: Array<{
      id: string
      type: string
      title: string
      config: Record<string, any>
      position: { x: number; y: number; w: number; h: number }
    }>
  }> => {
    return request.get('/api/analytics/dashboard/config')
  },

  updateDashboardConfig: (config: {
    widgets: Array<{
      id: string
      type: string
      title: string
      config: Record<string, any>
      position: { x: number; y: number; w: number; h: number }
    }>
  }): Promise<void> => {
    return request.put('/api/analytics/dashboard/config', config)
  },

  // 预警规则
  getAlertRules: (): Promise<
    Array<{
      id: string
      name: string
      metric: string
      condition: 'gt' | 'lt' | 'eq' | 'gte' | 'lte'
      threshold: number
      isEnabled: boolean
      recipients: string[]
      createdAt: string
    }>
  > => {
    return request.get('/api/analytics/alerts')
  },

  createAlertRule: (data: {
    name: string
    metric: string
    condition: 'gt' | 'lt' | 'eq' | 'gte' | 'lte'
    threshold: number
    recipients: string[]
  }): Promise<void> => {
    return request.post('/api/analytics/alerts', data)
  },

  updateAlertRule: (
    id: string,
    data: {
      name?: string
      threshold?: number
      isEnabled?: boolean
      recipients?: string[]
    },
  ): Promise<void> => {
    return request.put(`/api/analytics/alerts/${id}`, data)
  },

  deleteAlertRule: (id: string): Promise<void> => {
    return request.delete(`/api/analytics/alerts/${id}`)
  },

  // 数据对比
  compareData: (params: {
    metric: string
    currentPeriod: AnalyticsQueryParams
    previousPeriod: AnalyticsQueryParams
    dimensions?: string[]
  }): Promise<{
    current: DataPoint[]
    previous: DataPoint[]
    comparison: {
      change: number
      changePercent: number
      trend: 'up' | 'down' | 'stable'
    }
  }> => {
    return request.post('/api/analytics/compare', params)
  },

  // 预测分析
  getForecast: (params: {
    metric: string
    timeRange: AnalyticsQueryParams
    forecastDays: number
    confidence?: number
  }): Promise<{
    historical: DataPoint[]
    forecast: DataPoint[]
    confidence: {
      upper: DataPoint[]
      lower: DataPoint[]
    }
  }> => {
    return request.post('/api/analytics/forecast', params)
  },

  // 异常检测
  detectAnomalies: (params: {
    metric: string
    timeRange: AnalyticsQueryParams
    sensitivity?: 'low' | 'medium' | 'high'
  }): Promise<{
    data: DataPoint[]
    anomalies: Array<{
      timestamp: string
      value: number
      expected: number
      severity: 'low' | 'medium' | 'high'
    }>
  }> => {
    return request.post('/api/analytics/anomalies', params)
  },

  // 数据质量检查
  checkDataQuality: (params?: {
    startDate?: string
    endDate?: string
  }): Promise<{
    completeness: number
    accuracy: number
    consistency: number
    timeliness: number
    issues: Array<{
      type: string
      description: string
      severity: 'low' | 'medium' | 'high'
      count: number
    }>
  }> => {
    return request.get('/api/analytics/data-quality', { params })
  },
}
