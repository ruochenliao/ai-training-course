import React, { useState, useEffect, useRef, useCallback } from 'react'
import ReactDOM from 'react-dom'
import { Link } from 'react-router-dom'
import '../../styles/Text2SQL.css'
import '../../styles/Text2SQLTabs.css'
import '../../styles/ChatStyle.css'
import '../../styles/HybridExamples.css'
import '../../styles/EnterpriseChatStyle.css'
import '../../styles/TimelineChatStyle.css'
import {
  StreamResponseMessage,
  FinalVisualizationData,
  closeWebSocketConnection,
  getWebSocketInstance,
  WebSocketConnectionState,
  globalWebSocketState,
  globalWebSocketError,
  getConnections
} from './api'
import { Text2SQLResponse } from './types'

// 导入组件
import TabPanel from './components/TabPanel'
import Tabs from './components/Tabs'
import AnalysisTab from './components/AnalysisTab'
import SQLTab from './components/SQLTab'
import VisualizationTab from './components/VisualizationTab'
import ControlPanel from './components/ControlPanel'
import UserFeedback from './components/UserFeedback'
import ErrorMessage from './components/ErrorMessage'
import ConnectionSelector from './components/ConnectionSelector'
import HybridExamplesPanel from './components/HybridExamplesPanel'
import ChatHistorySidebar from './components/ChatHistorySidebar'
import TimelineChat from './components/TimelineChat'
import RegionPanel from './components/RegionPanel'
// 导入工具函数
import { convertToCSV as csvConverter, FormattedOutput as OutputFormatter } from './utils'

// 导入混合检索相关
import { hybridQAService, enhancedText2SQLService } from '../../services/hybridQA'
import type { SimilarQAPair } from '../../types/hybridQA'
import { Switch, Tooltip } from 'antd'
import { BulbOutlined, SendOutlined } from '@ant-design/icons'
// 导入聊天历史服务
import { chatHistoryService } from '../../services/chatHistoryService'
import type { SaveChatHistoryRequest } from '../../services/chatHistoryService'
// 导入共享类型
import type { ChatHistory, TimelineMessage, Connection } from '../../types/chat'




// 内联定义图标组件
const Brain = (props: React.SVGProps<SVGSVGElement>) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="24"
    height="24"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    {...props}
  >
    <path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96.44 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 1.98-3A2.5 2.5 0 0 1 9.5 2Z" />
    <path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96.44 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-1.98-3A2.5 2.5 0 0 0 14.5 2Z" />
  </svg>
)

const Database = (props: React.SVGProps<SVGSVGElement>) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="24"
    height="24"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    {...props}
  >
    <ellipse cx="12" cy="5" rx="9" ry="3"></ellipse>
    <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"></path>
    <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"></path>
  </svg>
)

const Search = (props: React.SVGProps<SVGSVGElement>) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="24"
    height="24"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    {...props}
  >
    <circle cx="11" cy="11" r="8"></circle>
    <path d="m21 21-4.3-4.3"></path>
  </svg>
)

const BarChart = (props: React.SVGProps<SVGSVGElement>) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="24"
    height="24"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    {...props}
  >
    <line x1="12" y1="20" x2="12" y2="10"></line>
    <line x1="18" y1="20" x2="18" y2="4"></line>
    <line x1="6" y1="20" x2="6" y2="16"></line>
  </svg>
)

const FileText = (props: React.SVGProps<SVGSVGElement>) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="24"
    height="24"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    {...props}
  >
    <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"></path>
    <polyline points="14 2 14 8 20 8"></polyline>
    <line x1="16" y1="13" x2="8" y2="13"></line>
    <line x1="16" y1="17" x2="8" y2="17"></line>
    <line x1="10" y1="9" x2="8" y2="9"></line>
  </svg>
)

const Code = (props: React.SVGProps<SVGSVGElement>) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="24"
    height="24"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    {...props}
  >
    <polyline points="16 18 22 12 16 6"></polyline>
    <polyline points="8 6 2 12 8 18"></polyline>
  </svg>
)

const CodeIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="24"
    height="24"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    {...props}
  >
    <path d="m18 16 4-4-4-4"></path>
    <path d="m6 8-4 4 4 4"></path>
    <path d="m14.5 4-5 16"></path>
  </svg>
)

// 导入错误图标
const AlertCircle = (props: React.SVGProps<SVGSVGElement>) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="24"
    height="24"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    {...props}
  >
    <circle cx="12" cy="12" r="10"></circle>
    <line x1="12" y1="8" x2="12" y2="12"></line>
    <line x1="12" y1="16" x2="12" y2="16"></line>
  </svg>
)

// 添加连接状态图标
const WifiIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="24"
    height="24"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    {...props}
  >
    <path d="M5 12.55a11 11 0 0 1 14.08 0"></path>
    <path d="M1.42 9a16 16 0 0 1 21.16 0"></path>
    <path d="M8.53 16.11a6 6 0 0 1 6.95 0"></path>
    <line x1="12" y1="20" x2="12.01" y2="20"></line>
  </svg>
)

// WebSocket连接状态指示器组件
const WebSocketStatusIndicator = () => {
  const [status, setStatus] = useState(globalWebSocketState);

  useEffect(() => {
    // 创建一个定时器，定期检查WebSocket状态
    const intervalId = setInterval(() => {
      setStatus(globalWebSocketState);
    }, 500); // 每500ms检查一次

    return () => clearInterval(intervalId);
  }, []);

  // 根据状态返回不同的样式类和文本
  const getStatusInfo = () => {
    switch (status) {
      case WebSocketConnectionState.CONNECTED:
        return { statusClass: 'websocket-status-connected', text: '已连接' };
      case WebSocketConnectionState.CONNECTING:
        return { statusClass: 'websocket-status-connecting', text: '连接中' };
      case WebSocketConnectionState.RECONNECTING:
        return { statusClass: 'websocket-status-reconnecting', text: '重连中' };
      case WebSocketConnectionState.ERROR:
        return { statusClass: 'websocket-status-error', text: '连接错误' };
      case WebSocketConnectionState.DISCONNECTED:
        return { statusClass: 'websocket-status-disconnected', text: '未连接' };
      default:
        return { statusClass: 'websocket-status-disconnected', text: '未知状态' };
    }
  };

  const statusInfo = getStatusInfo();

  return (
    <div className={`websocket-status ${statusInfo.statusClass}`}>
      <div className="websocket-status-dot"></div>
      <span>{statusInfo.text}</span>
    </div>
  );
}

// 定义处理步骤类型
type ProcessingStep = {
  id: number;
  message: string;
  timestamp: Date;
  source: string;
};

// 定义用户反馈状态类型
type UserFeedbackState = {
  visible: boolean;
  message: string;
  promptMessage: string;
};

// 修改RegionOutput类型
type RegionOutputs = {
  analysis: {
    merged: string;
    messages: StreamResponseMessage[];
    hasContent: boolean;
    streaming: boolean;
  };
  sql: {
    merged: string;
    messages: StreamResponseMessage[];
    hasContent: boolean;
    streaming: boolean;
  };
  explanation: {
    merged: string;
    messages: StreamResponseMessage[];
    hasContent: boolean;
    streaming: boolean;
  };
  data: {
    merged: string;
    messages: StreamResponseMessage[];
    hasContent: boolean;
    streaming: boolean;
  };
  visualization: {
    merged: string;
    messages: StreamResponseMessage[];
    hasContent: boolean;
    streaming: boolean;
  };
  process: {
    merged: string;
    messages: StreamResponseMessage[];
    hasContent: boolean;
    streaming: boolean;
  };
};



export default function Text2SQL() {
  const [query, setQuery] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [processingSteps, setProcessingSteps] = useState<ProcessingStep[]>([]);



  // 数据库连接状态
  const [connections, setConnections] = useState<Connection[]>([]);
  const [selectedConnectionId, setSelectedConnectionId] = useState<number | null>(null);
  const [loadingConnections, setLoadingConnections] = useState<boolean>(false);

  // 用户反馈启用状态
  const [userFeedbackEnabled, setUserFeedbackEnabled] = useState<boolean>(false);

  // 添加分页状态
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)

  // 按区域分类的流式输出
  const [regionOutputs, setRegionOutputs] = useState<RegionOutputs>({
    analysis: {
      merged: '',
      messages: [],
      hasContent: false,
      streaming: false
    },
    sql: {
      merged: '',
      messages: [],
      hasContent: false,
      streaming: false
    },
    explanation: {
      merged: '',
      messages: [],
      hasContent: false,
      streaming: false
    },
    data: {
      merged: '',
      messages: [],
      hasContent: false,
      streaming: false
    },
    visualization: {
      merged: '',
      messages: [],
      hasContent: false,
      streaming: false
    },
    process: {
      merged: '',
      messages: [],
      hasContent: false,
      streaming: false
    }
  })

  // 最终结果的状态
  const [sqlResult, setSqlResult] = useState<string | null>(null)
  const [explanationResult, setExplanationResult] = useState<string | null>(null)
  const [analysisResult, setAnalysisResult] = useState<string | null>(null) // 添加分析结果状态
  const [dataResult, setDataResult] = useState<any[] | null>(null)
  const [visualizationResult, setVisualizationResult] = useState<{
    type: string;
    config: any;
  } | null>(null)

  // 解释区域的独立状态管理
  const [explanationState, setExplanationState] = useState({
    hasContent: false,
    streaming: false
  })

  // 区域折叠状态
  const [collapsedSections, setCollapsedSections] = useState({
    analysis: false,
    sql: false,
    explanation: false,
    data: false,
    visualization: false,
    process: true // 默认折叠处理过程
  })

  // 添加用户反馈状态
  const [userFeedback, setUserFeedback] = useState<UserFeedbackState>({
    visible: false,
    message: '',
    promptMessage: ''
  });

  // 混合检索相关状态
  const [hybridExamplesVisible, setHybridExamplesVisible] = useState(false);
  const [similarExamples, setSimilarExamples] = useState<SimilarQAPair[]>([]);
  const [hybridRetrievalEnabled, setHybridRetrievalEnabled] = useState(true);
  const [schemaContext, setSchemaContext] = useState<any>(null);

  // 聊天历史和时间轴状态
  const [chatHistories, setChatHistories] = useState<ChatHistory[]>([]);
  const [selectedHistoryId, setSelectedHistoryId] = useState<string | null>(null);
  const [timelineMessages, setTimelineMessages] = useState<TimelineMessage[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string>('');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [savedSessionIds, setSavedSessionIds] = useState<Set<string>>(new Set()); // 已保存的会话ID

  // 图表引用
  const chartRef = useRef<HTMLCanvasElement>(null)
  // 存储EventSource实例以便在需要时关闭
  const eventSourceRef = useRef<EventSource | null>(null)

  // 在组件顶部添加计数器引用
  const processingStepIdRef = useRef(1)

  // 生成唯一ID的函数
  const generateId = () => `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

  // 创建新的聊天会话
  const createNewChatSession = () => {
    const sessionId = generateId();
    setCurrentSessionId(sessionId);
    setSelectedHistoryId(null);
    setTimelineMessages([]);
    resetProcessingState();
    // 清除保存状态，允许新会话保存
    setSavedSessionIds(prev => {
      const newSet = new Set(prev);
      newSet.delete(sessionId); // 确保新会话ID不在已保存列表中
      return newSet;
    });
    console.log('🆕 创建新聊天会话:', sessionId);
    return sessionId;
  };

  // 添加时间轴消息
  const addTimelineMessage = (
    type: 'user' | 'assistant' | 'system',
    content: string,
    metadata?: any
  ) => {
    const message: TimelineMessage = {
      id: generateId(),
      type,
      content,
      timestamp: new Date(),
      status: type === 'user' ? 'sent' : 'streaming',
      metadata
    };

    setTimelineMessages(prev => [...prev, message]);
    return message.id;
  };

  // 更新时间轴消息状态
  const updateTimelineMessage = (
    messageId: string,
    updates: Partial<TimelineMessage>
  ) => {
    setTimelineMessages(prev =>
      prev.map(msg =>
        msg.id === messageId ? { ...msg, ...updates } : msg
      )
    );
  };

  // 保存聊天历史
  const saveChatHistory = async (query: string) => {
    if (!currentSessionId || !query.trim()) return;

    const history: ChatHistory = {
      id: currentSessionId,
      title: query.length > 50 ? query.substring(0, 50) + '...' : query,
      timestamp: new Date(),
      query,
      response: {
        analysis: analysisResult || regionOutputs.analysis.merged,
        sql: sqlResult || '',
        explanation: explanationResult || '',
        data: dataResult || [],
        visualization: visualizationResult
      },
      connectionId: selectedConnectionId
    };

    // 更新本地状态
    setChatHistories(prev => {
      const existing = prev.find(h => h.id === currentSessionId);
      if (existing) {
        return prev.map(h => h.id === currentSessionId ? history : h);
      }
      return [history, ...prev];
    });

    // 保存到数据库
    try {
      const saveRequest: SaveChatHistoryRequest = {
        session_id: currentSessionId,
        title: history.title,
        query: history.query,
        response: history.response,
        connection_id: history.connectionId ?? undefined
      };

      await chatHistoryService.saveChatHistoryViaSSE(saveRequest);
      console.log('聊天历史保存成功:', currentSessionId);
    } catch (error) {
      console.error('保存聊天历史失败:', error);
      // 不影响用户体验，只记录错误
    }
  };

  // 加载聊天历史列表
  const loadChatHistories = async () => {
    try {
      console.log('🔄 开始加载聊天历史，连接ID:', selectedConnectionId);
      const response = await chatHistoryService.getChatHistories(
        0,
        50,
        selectedConnectionId || undefined
      );
      console.log('📥 后端响应:', response);

      const histories: ChatHistory[] = response.sessions.map(session => ({
        id: session.id,
        title: session.title,
        timestamp: new Date(session.timestamp),
        query: session.query,
        response: session.response,
        connectionId: session.connection_id || null
      }));

      setChatHistories(histories);
      console.log('✅ 聊天历史加载成功，数量:', histories.length);
      console.log('📋 历史记录详情:', histories);
    } catch (error) {
      console.error('❌ 加载聊天历史失败:', error);
    }
  };

  // 选择历史记录
  const handleSelectHistory = async (historyId: string) => {
    try {
      console.log('🔍 选择历史记录:', historyId);

      // 首先尝试从本地状态获取
      let history = chatHistories.find(h => h.id === historyId);
      console.log('📋 本地历史记录:', history ? '找到' : '未找到');

      // 如果本地没有，从数据库获取
      if (!history) {
        console.log('🌐 从数据库获取历史记录...');
        const response = await chatHistoryService.getChatHistory(historyId);
        history = {
          id: response.session_id,
          title: response.title,
          timestamp: new Date(response.created_at),
          query: response.query,
          response: response.response,
          connectionId: response.connection_id || null
        };
        console.log('📥 数据库历史记录:', history);
      }

      if (!history) {
        console.error('❌ 未找到历史记录:', historyId);
        return;
      }

      console.log('✅ 开始恢复历史记录:', {
        id: history.id,
        title: history.title,
        hasAnalysis: !!history.response.analysis,
        hasSql: !!history.response.sql,
        hasExplanation: !!history.response.explanation,
        hasData: !!(history.response.data && history.response.data.length > 0),
        hasVisualization: !!history.response.visualization
      });

      setSelectedHistoryId(historyId);
      setCurrentSessionId(historyId);

      // 恢复历史数据
      setSqlResult(history.response.sql);
      setExplanationResult(history.response.explanation);
      setAnalysisResult(history.response.analysis); // 恢复分析结果
      setDataResult(history.response.data);
      setVisualizationResult(history.response.visualization);

      // 重要：恢复解释区域的独立状态
      setExplanationState({
        hasContent: !!history.response.explanation,
        streaming: false
      });

      // 重要：更新regionOutputs状态，确保右侧内容区域显示
      setRegionOutputs({
        analysis: {
          merged: history.response.analysis || '',
          messages: [],
          hasContent: !!history.response.analysis,
          streaming: false
        },
        sql: {
          merged: history.response.sql || '',
          messages: [],
          hasContent: !!history.response.sql,
          streaming: false
        },
        explanation: {
          merged: history.response.explanation || '',
          messages: [],
          hasContent: !!history.response.explanation,
          streaming: false
        },
        data: {
          merged: history.response.data && history.response.data.length > 0 ?
                  `查询返回了 ${history.response.data.length} 条数据记录` : '',
          messages: [],
          hasContent: !!(history.response.data && history.response.data.length > 0),
          streaming: false
        },
        visualization: {
          merged: history.response.visualization ?
                  `生成了 ${history.response.visualization.type || '图表'} 类型的可视化` : '',
          messages: [],
          hasContent: !!history.response.visualization,
          streaming: false
        },
        process: {
          merged: '',
          messages: [],
          hasContent: false,
          streaming: false
        }
      });

      console.log('🔄 regionOutputs状态已更新，右侧内容应该显示');

      // 重建时间轴消息
      const messages: TimelineMessage[] = [
        {
        id: generateId(),
        type: 'user',
        content: history.query,
        timestamp: history.timestamp,
        status: 'sent'
      }
    ];

    if (history.response.analysis) {
      messages.push({
        id: generateId(),
        type: 'assistant',
        content: history.response.analysis,
        timestamp: new Date(history.timestamp.getTime() + 1000),
        status: 'completed',
        metadata: { region: 'analysis', source: '查询分析智能体' }
      });
    }

    if (history.response.sql) {
      messages.push({
        id: generateId(),
        type: 'assistant',
        content: history.response.sql,
        timestamp: new Date(history.timestamp.getTime() + 2000),
        status: 'completed',
        metadata: { region: 'sql', source: 'SQL生成智能体', isSQL: true }
      });
    }

    if (history.response.explanation) {
      messages.push({
        id: generateId(),
        type: 'assistant',
        content: history.response.explanation,
        timestamp: new Date(history.timestamp.getTime() + 3000),
        status: 'completed',
        metadata: { region: 'explanation', source: 'SQL解释智能体' }
      });
    }

    if (history.response.data && history.response.data.length > 0) {
      messages.push({
        id: generateId(),
        type: 'assistant',
        content: `查询返回了 ${history.response.data.length} 条数据记录`,
        timestamp: new Date(history.timestamp.getTime() + 4000),
        status: 'completed',
        metadata: { region: 'data', source: '数据查询智能体' }
      });
    }

    if (history.response.visualization) {
      messages.push({
        id: generateId(),
        type: 'assistant',
        content: `生成了 ${history.response.visualization.type} 类型的可视化图表`,
        timestamp: new Date(history.timestamp.getTime() + 5000),
        status: 'completed',
        metadata: { region: 'visualization', source: '可视化推荐智能体', isVisualization: true }
      });
    }

    setTimelineMessages(messages);
    console.log('✅ 历史记录恢复完成，时间轴消息数量:', messages.length);
    } catch (error) {
      console.error('❌ 选择历史记录失败:', error);
    }
  };

  // 删除聊天历史
  const handleDeleteHistory = async (historyId: string) => {
    try {
      console.log('🗑️ 删除聊天历史:', historyId);

      // 显示确认对话框
      const confirmed = window.confirm('确定要删除这条聊天记录吗？此操作无法撤销。');
      if (!confirmed) {
        return;
      }

      // 调用删除API
      await chatHistoryService.deleteChatHistory(historyId);

      // 从本地状态中移除
      setChatHistories(prev => prev.filter(h => h.id !== historyId));

      // 如果删除的是当前选中的历史记录，则创建新会话
      if (selectedHistoryId === historyId) {
        createNewChatSession();
      }

      console.log('✅ 聊天历史删除成功');
    } catch (error) {
      console.error('❌ 删除聊天历史失败:', error);
      alert('删除失败，请稍后重试');
    }
  };

  // 获取数据库连接列表
  useEffect(() => {
    const fetchConnections = async () => {
      try {
        setLoadingConnections(true);
        const response = await getConnections();
        setConnections(response.data);

        // 如果有连接，默认选择第一个
        if (response.data.length > 0) {
          setSelectedConnectionId(response.data[0].id);
        }
      } catch (error) {
        console.error('获取数据库连接失败:', error);
        setError('获取数据库连接失败，请检查网络连接或联系管理员');
      } finally {
        setLoadingConnections(false);
      }
    };

    fetchConnections();

    // 初始化一个新的聊天会话
    createNewChatSession();

    // 加载聊天历史
    loadChatHistories();
  }, []); // 仅在组件挂载时执行一次

  // 当选择的连接改变时，重新加载聊天历史
  useEffect(() => {
    if (selectedConnectionId) {
      loadChatHistories();
    }
  }, [selectedConnectionId]);

  // 监听查询完成状态，自动保存聊天历史
  useEffect(() => {
    const shouldSave =
      !loading && // 不在加载中
      currentSessionId && // 有会话ID
      !savedSessionIds.has(currentSessionId) && // 该会话还未保存
      sqlResult && // 有SQL结果
      dataResult && // 有数据结果
      timelineMessages.length > 0; // 有时间轴消息

    if (shouldSave) {
      const userMessage = timelineMessages.find(msg => msg.type === 'user');
      if (userMessage) {
        console.log('🔄 检测到查询完成，自动保存聊天历史');

        // 延迟保存，确保所有状态都已更新
        const saveTimeout = setTimeout(async () => {
          try {
            await saveChatHistory(userMessage.content);
            await loadChatHistories();
            // 标记该会话已保存
            setSavedSessionIds(prev => new Set(prev).add(currentSessionId));
            console.log('✅ 聊天历史自动保存成功');
          } catch (error) {
            console.error('❌ 聊天历史自动保存失败:', error);
          }
        }, 2000); // 2秒延迟

        return () => clearTimeout(saveTimeout);
      }
    }
  }, [loading, currentSessionId, sqlResult, dataResult, timelineMessages, savedSessionIds]);

  // 切换折叠状态
  const toggleCollapse = (section: string) => {
    setCollapsedSections(prev => ({
      ...prev,
      [section]: !prev[section as keyof typeof prev]
    }));
  }

  // 处理最终SQL结果
  const handleFinalSql = (sql: string) => {
    console.log('收到最终SQL结果，关闭流式状态', sql);
    // 标记SQL区域流式输出结束
    setRegionOutputs(prev => ({
      ...prev,
      sql: {
        ...prev.sql,
        streaming: false,
        finalResult: sql,
        hasContent: true
      }
    }));
    setSqlResult(sql);
  };

  // 处理最终解释结果
  const handleFinalExplanation = (explanation: string) => {
    console.log('收到最终解释结果，关闭流式状态', {
      explanationLength: explanation ? explanation.length : 0,
      currentExplanationResult: explanationResult ? `当前内容长度 ${explanationResult.length}` : '无当前内容'
    });

    // 标记解释区域流式输出结束
    setRegionOutputs(prev => {
      return {
        ...prev,
        explanation: {
          ...prev.explanation,
          streaming: false,
          hasContent: true  // 确保区域被标记为有内容
        }
      };
    });

    // 解释内容已生成完成
    console.log('SQL解释内容已生成完成');
  };

  // 处理最终数据结果
  const handleFinalData = (data: any[]) => {
    console.log('收到最终数据结果，关闭流式状态');
    // 标记数据区域流式输出结束
    setRegionOutputs(prev => ({
      ...prev,
      data: {
        ...prev.data,
        streaming: false,
        hasContent: true  // 确保区域被标记为有内容
      }
    }));
    setDataResult(data);
  }

  // 处理最终可视化结果
  const handleFinalVisualization = async (visualization: FinalVisualizationData) => {
    console.log('🎨 handleFinalVisualization被调用，可视化结果:', visualization);
    console.log('📊 当前数据结果:', dataResult);
    console.log('收到最终可视化结果，关闭流式状态');

    // 标记可视化区域流式输出结束
    setRegionOutputs(prev => ({
      ...prev,
      visualization: {
        ...prev.visualization,
        streaming: false,
        hasContent: true  // 确保区域被标记为有内容
      }
    }));

    // 设置可视化结果
    setVisualizationResult(visualization);
    console.log('✅ 可视化结果已设置:', visualization);

    // 在收到可视化结果后直接设置 loading 状态为 false，使分析按钮可用
    // 只有当region='visualization'的消息且is_final=true时，才设置分析按钮为可用状态
    setLoading(false);
    console.log('可视化数据已准备就绪，分析按钮恢复可用');

    // 可视化数据已准备就绪，触发保存聊天历史
    console.log('🔄 可视化数据已准备就绪，准备保存聊天历史');

    // 延迟保存，确保所有数据都已设置完成
    setTimeout(async () => {
      if (currentSessionId) {
        // 获取当前用户查询（从时间轴消息中获取）
        const userMessage = timelineMessages.find(msg => msg.type === 'user');
        if (userMessage) {
          try {
            await saveChatHistory(userMessage.content);
            // 保存后立即刷新历史列表
            await loadChatHistories();
            console.log('聊天历史已保存并刷新列表（从可视化完成触发）');
          } catch (error) {
            console.error('保存聊天历史失败:', error);
          }
        }
      }
    }, 500);
  }

  // 处理最终分析结果
  const handleFinalAnalysis = (analysis: string) => {
    console.log('收到最终分析结果，关闭流式状态');
    // 标记分析区域流式输出结束
    setRegionOutputs(prev => ({
      ...prev,
      analysis: {
        ...prev.analysis,
        streaming: false,
        hasContent: true
      }
    }));
  }

  // 处理最终结果
  const handleResult = (finalResult: Text2SQLResponse) => {
    console.log('🎯 handleResult被调用，最终结果:', finalResult);
    setError(null); // 清除错误

    // 检查所有区域的流式输出是否都已结束
    const allRegionsCompleted = Object.values(regionOutputs).every(region => !region.streaming);

    // 检查并处理解释结果
    const validExplanation = finalResult.explanation &&
                            typeof finalResult.explanation === 'string' &&
                            finalResult.explanation.trim() ?
                            finalResult.explanation : null;

    // 保存聊天历史（在处理完成后）
    setTimeout(async () => {
      if (currentSessionId) {
        // 获取当前用户查询（从时间轴消息中获取）
        const userMessage = timelineMessages.find(msg => msg.type === 'user');
        if (userMessage) {
          await saveChatHistory(userMessage.content);
          // 保存后立即刷新历史列表
          await loadChatHistories();
          console.log('聊天历史已保存并刷新列表');
        }
      }
    }, 1000);

    // 标记所有区域流式输出结束并设置hasContent
    setRegionOutputs(prev => {
      const updated = { ...prev };
      Object.keys(updated).forEach(key => {
        const region = updated[key as keyof typeof updated];
        region.streaming = false;

        // 根据最终结果设置hasContent
        if (key === 'sql' && finalResult.sql) {
          region.hasContent = true;
        }
        if (key === 'explanation' && validExplanation) {
          region.hasContent = true;
          region.merged = validExplanation; // 确保merged字段有正确的内容
          console.log('设置explanation区域merged字段:', validExplanation.substring(0, 50) + '...');
        }
        if (key === 'data' && finalResult.results && finalResult.results.length > 0) {
          region.hasContent = true;
        }
        if (key === 'visualization' && (finalResult.visualization_type || finalResult.visualization_config)) {
          region.hasContent = true;
        }
      });
      return updated;
    });

    // 设置最终结果的所有部分
    setSqlResult(finalResult.sql);

    // 不在这里设置解释内容，而是依赖流式消息的累加逻辑
    console.log('保留现有解释内容，当前长度:', explanationResult ? explanationResult.length : 0);

    setDataResult(finalResult.results);
    setVisualizationResult({
      type: finalResult.visualization_type,
      config: finalResult.visualization_config
    });

    // 打印日志，帮助调试
    console.log('设置最终结果:', {
      sql: finalResult.sql ? finalResult.sql.substring(0, 50) + '...' : null,
      explanation: validExplanation ? validExplanation.substring(0, 50) + '...' : null,
      results: finalResult.results ? `${finalResult.results.length} 条结果` : null,
      visualization: finalResult.visualization_type
    });

    // 如果有解释内容，记录日志
    if (validExplanation) {
      console.log('有解释内容，内容长度:', validExplanation.length);
    }

    // 只有当收到region='visualization'的消息且is_final=true时，才将分析按钮设置为可用状态
    // 不要根据regionOutputs.visualization的状态来判断，因为它可能被错误地标记为完成
    // 这里不再设置分析按钮状态，而是依赖handleMessage中对region='visualization'的消息处理
  }

  // 处理错误
  const handleError = (error: Error) => {
    console.error('处理出错:', error);

    // 使用更友好的错误消息
    let errorMessage = error.message || '请求处理过程中发生错误';

    // 检查是否是WebSocket连接错误
    if (errorMessage.includes('WebSocket') ||
        errorMessage.includes('连接') ||
        errorMessage.includes('服务器')) {
      // 使用全局WebSocket错误信息（如果有）
      if (globalWebSocketError) {
        errorMessage = globalWebSocketError;
      } else {
        errorMessage = '无法连接到服务器，请稍后再试';
      }
    }

    setError(errorMessage);
    setLoading(false); // 发生错误时一定要停止加载状态

    // 重置所有区域的流式状态
    setRegionOutputs(prev => {
      const updated = { ...prev };
      Object.keys(updated).forEach(key => {
        const region = updated[key as keyof typeof updated];
        region.streaming = false;
      });
      return updated;
    });
  }

  // 添加页面切换函数
  const handlePageChange = (pageNumber: number) => {
    setCurrentPage(pageNumber);
  };

  // 添加计算总页数的函数
  const getTotalPages = () => {
    if (!dataResult) return 1;
    return Math.ceil(dataResult.length / pageSize);
  };

  // 获取当前页的数据
  const getCurrentPageData = () => {
    if (!dataResult) return [];
    const startIndex = (currentPage - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    return dataResult.slice(startIndex, endIndex);
  };

  // 重置处理状态
  const resetProcessingState = () => {
    setError(null);
    setLoading(false);
    setProcessingSteps([]);
    setCurrentPage(1); // 重置分页状态


    // 完全重置所有状态
    console.log('重置处理状态：完全重置所有区域');

    // 重置所有区域的状态
    setRegionOutputs({
      analysis: {
        merged: '',
        messages: [],
        hasContent: false,
        streaming: false
      },
      sql: {
        merged: '',
        messages: [],
        hasContent: false,
        streaming: false
      },
      explanation: {
        merged: '',
        messages: [],
        hasContent: false,
        streaming: false
      },
      data: {
        merged: '',
        messages: [],
        hasContent: false,
        streaming: false
      },
      visualization: {
        merged: '',
        messages: [],
        hasContent: false,
        streaming: false
      },
      process: {
        merged: '',
        messages: [],
        hasContent: false,
        streaming: false
      }
    });

    // 重置所有结果
    setSqlResult(null);
    setExplanationResult(null);
    setAnalysisResult(null); // 重置分析结果
    setDataResult(null);
    setVisualizationResult(null);

    // 重置解释区域的独立状态
    setExplanationState({
      hasContent: false,
      streaming: false
    });

    // 关闭之前的EventSource连接
    if (eventSourceRef.current) {
      try {
        eventSourceRef.current.close();
        console.log('已关闭之前的EventSource连接');
      } catch (err) {
        console.error('关闭EventSource连接时出错:', err);
      }
      eventSourceRef.current = null;
    }
  }

  // 监听WebSocket连接状态变化
  useEffect(() => {
    // 创建一个定时器，定期检查WebSocket状态
    const intervalId = setInterval(() => {
      // 如果有WebSocket错误且当前没有显示错误，则显示错误
      if (globalWebSocketError && !error && !loading) {
        setError(globalWebSocketError);
      }

      // 如果WebSocket恢复正常且当前显示的是WebSocket错误，则清除错误
      if (globalWebSocketState === WebSocketConnectionState.CONNECTED &&
          error && (error === globalWebSocketError || error.includes('连接') || error.includes('服务器'))) {
        setError(null);
      }
    }, 1000); // 每秒检查一次

    return () => clearInterval(intervalId);
  }, [error, loading]);

  // 流式查询处理
  const handleStreamSearch = async () => {
    if (loading) return;

    // 检查SSE状态
    if (globalWebSocketState === WebSocketConnectionState.ERROR ||
        globalWebSocketState === WebSocketConnectionState.DISCONNECTED) {
      // 尝试重新连接
      try {
        const sse = getWebSocketInstance();
        const connected = await sse.connect();
        if (!connected) {
          setError(globalWebSocketError || '无法连接到服务器，请稍后再试');
          return;
        }
      } catch (error) {
        setError(globalWebSocketError || '无法连接到服务器，请稍后再试');
        return;
      }
    }

    setError(null);
    setLoading(true);

    // 保存当前查询内容以便发送
    const currentQuery = query.trim();

    // 清空输入框
    setQuery('');

    // 重置所有状态，包括解释内容
    setProcessingSteps([]);
    setCurrentPage(1);
    setSqlResult(null);
    setExplanationResult(null);
    setAnalysisResult(null); // 重置分析结果
    setDataResult(null);
    setVisualizationResult(null);

    // 重置解释区域的独立状态
    setExplanationState({
      hasContent: false,
      streaming: false
    });

    if (!currentQuery) {
      setError('请输入有效的查询');
      setLoading(false);
      return;
    }

    // 检查是否选择了数据库连接
    if (!selectedConnectionId) {
      setError('请选择一个数据库连接');
      setLoading(false);
      return;
    }

    // 创建新的聊天会话（如果需要）
    let sessionId = currentSessionId;
    if (!sessionId || selectedHistoryId) {
      sessionId = createNewChatSession();
    }

    // 添加用户消息到时间轴
    const userMessageId = addTimelineMessage('user', currentQuery);

    // 初始化UI状态，确保分析区域可见
    console.log('初始化分析区域');

    // 清理消息缓存，防止重复消息检测影响新查询
    messageCache.current.clear();

    // 一次性重置所有区域的状态，避免重复设置
    setRegionOutputs({
      analysis: {
        merged: '',
        messages: [],
        hasContent: false,
        streaming: false
      },
      sql: {
        merged: '',
        messages: [],
        hasContent: false,
        streaming: false
      },
      explanation: {
        merged: '',
        messages: [],
        hasContent: false,
        streaming: false
      },
      data: {
        merged: '',
        messages: [],
        hasContent: false,
        streaming: false
      },
      visualization: {
        merged: '',
        messages: [],
        hasContent: false,
        streaming: false
      },
      process: {
        merged: '',
        messages: [],
        hasContent: false,
        streaming: false
      }
    });

    // 强制设置分析区域为展开状态
    setCollapsedSections(prev => ({
      ...prev,
      analysis: false
    }));

    // 直接在DOM上更新样式以确保分析区域可见
    setTimeout(() => {
      const analysisContainer = document.querySelector('.analysis-output-container');
      if (analysisContainer) {
        // 确保容器可见
        (analysisContainer as HTMLElement).style.display = 'block';
        (analysisContainer as HTMLElement).style.minHeight = '200px';

        // 滚动到分析区域
        analysisContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
        console.log('滚动到analysis-output-container');
      } else {
        console.warn('找不到分析区域容器');
      }

      // 确保内容区域可见
      const contentArea = document.querySelector('.analysis-content');
      if (contentArea) {
        (contentArea as HTMLElement).style.minHeight = '100px';
        (contentArea as HTMLElement).style.display = 'block';
        console.log('设置analysis-content样式');
      } else {
        console.warn('找不到分析内容区域');
      }
    }, 100);

    try {
      // 使用SSE进行流式通信
      console.log('正在使用SSE发送查询...');

      // 导入SSE发送函数
      const { sendSSEText2SQLRequest } = await import('./api');

      // 发送SSE请求
      sendSSEText2SQLRequest(
        currentQuery,
        handleMessage,
        handleResult,
        handleError,
        handleFinalSql,
        handleFinalExplanation,
        handleFinalData,
        handleFinalVisualization,
        selectedConnectionId,
        userFeedbackEnabled
      );

      console.log('SSE查询已发送');
    } catch (error) {
      console.error('SSE请求失败:', error);
      setError(`SSE请求失败: ${error instanceof Error ? error.message : '未知错误'}`);
      setLoading(false);
    }
  };

  // 组件卸载时关闭连接
  useEffect(() => {
    return () => {
      // 关闭EventSource连接
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }

      // 关闭WebSocket连接
      closeWebSocketConnection();
    };
  }, []);

  // 修改图表相关逻辑，减少页面抖动
  useEffect(() => {
    if (visualizationResult && dataResult && dataResult.length > 0 && chartRef.current) {
      // 添加一个标记，避免重复渲染
      if (chartRef.current.dataset.rendered === 'true') {
        return;
      }

      // 如果可视化类型是表格，跳过图表渲染
      if (visualizationResult.type === 'table') {
        console.log('表格类型可视化，跳过图表渲染');
        // 标记为已渲染，避免重复处理
        chartRef.current.dataset.rendered = 'true';

        // 表格类型可视化已完成，但我们不在这里设置分析按钮状态
        console.log('表格类型可视化完成');
        return;
      }

      // 使用动态导入引入Chart.js
      import('chart.js/auto').then((ChartModule) => {
        const Chart = ChartModule.default;

        // 获取画布上下文
        const canvas = chartRef.current;
        if (!canvas) return;

        // 销毁现有图表
        try {
          const chartInstance = Chart.getChart(canvas);
          if (chartInstance) {
            chartInstance.destroy();
          }
        } catch (e) {
          console.log('No existing chart to destroy');
        }

        // 准备图表数据
        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        try {
          // 标记为已渲染，避免重复渲染
          canvas.dataset.rendered = 'true';

          const chartType = visualizationResult.type as 'bar' | 'line' | 'pie' | 'scatter';
          const config = prepareChartConfig(chartType, visualizationResult.config, dataResult);
          new Chart(ctx, config);

          // 图表渲染完成，但我们不在这里设置分析按钮状态
          console.log('图表渲染完成');
        } catch (error) {
          console.error('图表渲染错误:', error);
          // 图表渲染出错，但我们不在这里设置分析按钮状态
          console.log('图表渲染出错');
        }
      });
    }

    // 清理函数
    return () => {
      if (chartRef.current) {
        // 重置已渲染标记
        chartRef.current.dataset.rendered = 'false';

        // 动态导入Chart.js并清理图表
        import('chart.js/auto').then((ChartModule) => {
          const Chart = ChartModule.default;
          try {
            const chartInstance = Chart.getChart(chartRef.current!);
            if (chartInstance) {
              chartInstance.destroy();
            }
          } catch (e) {
            console.log('Error cleaning up chart:', e);
          }
        }).catch(err => {
          console.error('清理图表时出错:', err);
        });
      }
    };
  }, [visualizationResult, dataResult]);

  // 添加图表配置准备函数
  const prepareChartConfig = (
    type: 'bar' | 'line' | 'pie' | 'scatter',
    config: any,
    data: any[]
  ) => {
    // 提取数据点
    const labels = data.map(item => {
      // 尝试获取X轴字段值
      const xField = config.xAxis || Object.keys(item)[0];
      return item[xField];
    });

    // 提取数据系列
    const yField = config.yAxis || Object.keys(data[0])[1];
    const dataPoints = data.map(item => item[yField]);

    // 生成配置
    return {
      type, // 使用正确的类型
      data: {
        labels: labels,
        datasets: [{
          label: config.title || '数据系列',
          data: dataPoints,
          backgroundColor: type === 'pie' ?
            ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40'] :
            'rgba(54, 162, 235, 0.5)',
          borderColor: 'rgba(54, 162, 235, 1)',
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          title: {
            display: !!config.title,
            text: config.title || ''
          },
          tooltip: {
            enabled: true
          },
          legend: {
            display: type === 'pie'
          }
        }
      }
    };
  };

  // 优化的区域输出更新函数 - 专门为流式markdown优化
  const updateRegionOutputs = useCallback((region: string, content: string, isFinal?: boolean) => {
    setRegionOutputs(prev => {
      const updatedRegions = { ...prev };
      const regionData = updatedRegions[region as keyof typeof updatedRegions];

      if (!regionData) {
        console.error(`未知区域: ${region}`);
        return prev;
      }

      // 对于分析区域和解释区域，使用专门的流式markdown重复检测策略
      if (region === 'analysis' || region === 'explanation') {
        // 对于分析和解释区域，几乎不进行重复检测，因为markdown流式内容可能包含重复的符号
        // 只检测完全相同且较长的内容块（超过100字符）
        if (content && content.length > 100 && regionData.merged === content) {
          console.log(`跳过完全重复的${region}内容: ${region} - ${content.substring(0, 30)}...`);
          regionData.streaming = isFinal !== true;
          return updatedRegions;
        }
      } else {
        // 其他区域保持原有的重复检测逻辑
        if (content && regionData.merged.includes(content)) {
          console.log(`跳过重复内容: ${region} - ${content.substring(0, 50)}...`);
          regionData.streaming = isFinal !== true;
          return updatedRegions;
        }
      }

      // 标记该区域已有内容
      regionData.hasContent = true;

      // 判断streaming状态
      regionData.streaming = isFinal !== true;

      // 连续输出逻辑 - 对于分析和解释区域，不在这里累积内容，避免双重累积
      if (region === 'analysis' || region === 'explanation') {
        // 分析和解释区域的内容由各自的状态管理，这里只更新流式状态
        // 不累积内容，避免与 analysisResult/explanationResult 状态重复
        console.log(`${region}区域内容由专门状态管理，跳过regionOutputs累积`);
      } else {
        // 其他区域正常累积内容
        if (regionData.merged === '' || regionData.merged.includes('正在分析您的问题')) {
          // 如果是初始状态或占位符，直接替换
          regionData.merged = content;
        } else {
          // 直接追加新内容，保持连续性
          regionData.merged += content;
        }
      }

      // 添加详细的调试信息，特别关注分析区域和解释区域
      if (region === 'analysis') {
        console.log(`🔄 [分析区域] 更新内容:`, {
          region,
          newContentLength: content.length,
          totalLength: regionData.merged.length,
          newContentPreview: content.substring(0, 50),
          totalContentPreview: regionData.merged.substring(regionData.merged.length - 50),
          newContentHasNewlines: content.includes('\n'),
          newContentHasSpaces: content.includes(' '),
          rawNewContent: JSON.stringify(content.substring(0, 50))
        });
      } else if (region === 'explanation') {
        console.log(`🔄 [解释区域] 更新内容:`, {
          region,
          newContentLength: content.length,
          totalLength: regionData.merged.length,
          newContentPreview: content.substring(0, 50),
          totalContentPreview: regionData.merged.substring(Math.max(0, regionData.merged.length - 50)),
          isAppending: regionData.merged.length > 0
        });
      } else {
        console.log(`更新区域内容: ${region} - 新增${content.length}字符，总长度${regionData.merged.length}`);
      }

      return updatedRegions;
    });
  }, []);

  // 简化的消息后处理函数
  const handlePostMessageTasks = useCallback((region: string, message: StreamResponseMessage, source: string, content: string) => {
    // 更新处理步骤
    if (content && region === 'process') {
      const step: ProcessingStep = {
        id: processingStepIdRef.current++,
        message: content,
        timestamp: new Date(),
        source: source
      };
      setProcessingSteps(prev => [...prev, step]);
    }

    // 检查是否是反馈请求消息
    if ((message.source === 'user_proxy' && message.content) ||
        (message.type === 'feedback_request' && message.content) ||
        (message.region === 'user_proxy' && message.content)) {
      setUserFeedback({
        visible: true,
        message: '',
        promptMessage: message.content
      });
    }
  }, []);

  // 消息去重缓存
  const messageCache = useRef(new Set<string>());

  // 优化的消息处理函数 - 专门为流式markdown优化
  const handleMessage = useCallback((message: StreamResponseMessage) => {
    // 清除错误状态
    setError(null);

    // 确定消息区域
    let region = message.region || 'process';
    const source = message.source || '系统';
    let content = message.content || '';

    // 对于分析区域和解释区域，不过滤包含空格和换行的内容，因为这些对markdown格式很重要
    if (region === 'analysis' || region === 'explanation') {
      // 只过滤完全空的内容
      if (!content) {
        return;
      }
    } else {
      // 其他区域过滤空消息
      if (!content.trim()) {
        return;
      }
    }

    // 优化消息去重逻辑 - 对分析区域和解释区域使用更精确的标识
    let messageId: string;
    if (region === 'analysis') {
      // 对于分析区域，使用时间戳和内容长度来生成更精确的标识
      messageId = `${region}-${source}-${Date.now()}-${content.length}-${content.substring(0, 20)}`;
    } else if (region === 'explanation') {
      // 对于解释区域，使用时间戳和内容哈希来生成更精确的标识，避免重复
      const contentHash = content.length + content.substring(0, 30) + content.substring(content.length - 30);
      messageId = `${region}-${source}-${Date.now()}-${contentHash}`;
    } else {
      // 其他区域保持原有逻辑
      messageId = `${region}-${source}-${content.substring(0, 100)}`;
    }

    if (messageCache.current.has(messageId)) {
      console.log(`跳过重复消息: ${region} - ${content.substring(0, 30)}...`);
      return;
    }
    messageCache.current.add(messageId);

    // 清理过期的缓存（保留最近1000条）
    if (messageCache.current.size > 1000) {
      const entries = Array.from(messageCache.current);
      messageCache.current.clear();
      entries.slice(-500).forEach(entry => messageCache.current.add(entry));
    }

    // 添加详细的调试信息，特别关注分析区域和解释区域的内容格式
    if (region === 'analysis') {
      console.log(`📋 [分析区域] 收到消息:`, {
        region,
        source,
        contentLength: content.length,
        contentPreview: content.substring(0, 100),
        hasNewlines: content.includes('\n'),
        hasSpaces: content.includes(' '),
        rawContent: JSON.stringify(content.substring(0, 100))
      });
    } else if (region === 'explanation') {
      console.log(`📋 [解释区域] 收到消息:`, {
        region,
        source,
        contentLength: content.length,
        contentPreview: content.substring(0, 100),
        hasNewlines: content.includes('\n'),
        hasSpaces: content.includes(' ')
      });
    } else {
      console.log(`📋 收到消息: ${region} - ${source} - ${content.substring(0, 50)}...`);
    }

    // 更新区域输出状态（主要显示逻辑）
    // 解释区域完全跳过 regionOutputs 处理，只使用 explanationResult 状态
    if (region !== 'explanation') {
      updateRegionOutputs(region, content, message.is_final);
    }

    // 异步更新其他状态，避免阻塞渲染
    setTimeout(() => {
      // 处理特殊区域的消息
      if (region === 'analysis') {
        // 更新分析结果 - 保持原始格式，直接累加
        setAnalysisResult(prev => {
          const prevContent = prev || '';
          // 对于分析区域，直接累加内容，保持markdown格式
          return prevContent + content;
        });
      } else if (region === 'explanation') {
        // 更新解释结果 - 与分析区域保持完全一致的处理逻辑
        setExplanationResult(prev => {
          const prevContent = prev || '';
          // 对于解释区域，直接累加内容，保持markdown格式（与分析区域完全一致）
          return prevContent + content;
        });

        // 同时更新解释区域的独立状态
        setExplanationState({
          hasContent: true,
          streaming: message.is_final !== true
        });
      }

      // 如果是可视化区域的最终消息，停止加载状态
      if (message.is_final === true && region === 'visualization') {
        setLoading(false);
        console.log('收到可视化区域的最终消息，分析按钮恢复可用');
      }

      // 处理其他消息后的任务
      handlePostMessageTasks(region, message, source, content);
    }, 0);
  }, [updateRegionOutputs, handlePostMessageTasks]);







  // 在组件内添加useEffect来监控SQL区域的显示条件
  useEffect(() => {

  }, [sqlResult, regionOutputs.sql.hasContent, regionOutputs.analysis.streaming, regionOutputs.analysis.hasContent]);

  // 添加MutationObserver来监控分析区域内容变化
  useEffect(() => {
    // 如果分析区域没有内容或已折叠，则不需要监控
    if (!regionOutputs.analysis.hasContent || collapsedSections.analysis) {
      return;
    }

    // 创建MutationObserver来监控内容变化
    const observer = new MutationObserver((mutations) => {
      // 检查是否正在流式输出，只有流式输出时才自动滚动到底部
      if (regionOutputs.analysis.streaming) {
        scrollAnalysisAreaToBottom();
      }
    });

    // 延迟一下再开始监控，确保元素已经渲染
    setTimeout(() => {
      // 查找分析区域容器
      const analysisContainer = document.querySelector('.analysis-content-container');
      if (analysisContainer) {
        // 配置监视选项，监视子树变化和子节点变化
        observer.observe(analysisContainer, {
          childList: true,
          subtree: true,
          characterData: true
        });

        // 初始化时滚动到底部，但只在流式输出时
        if (regionOutputs.analysis.streaming) {
          scrollAnalysisAreaToBottom();
        }
      }
    }, 100);

    // 清理函数
    return () => {
      observer.disconnect();
    };
  }, [regionOutputs.analysis.hasContent, regionOutputs.analysis.merged, regionOutputs.analysis.streaming, collapsedSections.analysis]);

  // 在 Text2SQL 组件内添加一个处理回车键的函数
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !loading && query.trim() !== '') {
      e.preventDefault();
      handleStreamSearch();
    }
  };

  // 混合检索相关函数
  const handleShowExamples = async () => {
    if (!query.trim() || !selectedConnectionId) {
      return;
    }

    setHybridExamplesVisible(true);
  };

  const handleExampleSelect = (example: SimilarQAPair) => {
    // 将选中的示例应用到查询中
    setQuery(example.qa_pair.question);
    setHybridExamplesVisible(false);

    // 可以选择自动执行查询
    // handleStreamSearch();
  };

  const handleCloseExamples = () => {
    setHybridExamplesVisible(false);
  };

  // 处理用户反馈提交
  const handleFeedbackSubmit = async () => {
    if (!userFeedback.message.trim()) return;

    try {
      console.log('发送用户反馈:', userFeedback.message);

      // 获取当前反馈消息
      const currentFeedback = userFeedback.message;

      // 在前端添加分隔符
      setRegionOutputs(prev => {
        const updatedRegions = { ...prev };
        const analysisRegion = updatedRegions.analysis;

        // 构建分隔符标记
        const separator = "\n\n----------------------------\n### 用户反馈：" + currentFeedback + "\n----------------------------\n\n";

        // 检查是否已经存在相同的反馈内容
        if (!analysisRegion.merged.includes(`用户反馈：${currentFeedback}`)) {
          analysisRegion.merged += separator;
        } else {
          console.log('该反馈已存在，不重复添加');
        }

        return updatedRegions;
      });

      // 使用SSE发送反馈
      const { sendUserFeedback } = await import('./api');
      const sseInstance = getWebSocketInstance();
      const sessionId = sseInstance.getCurrentSessionId();

      if (sessionId) {
        await sendUserFeedback(sessionId, currentFeedback, (error) => {
          console.error('发送反馈失败:', error);
          setError(`发送反馈失败: ${error.message}`);
        });
      } else {
        console.error('没有活动的SSE会话');
        setError('没有活动的会话，无法发送反馈');
      }

      // 清空并隐藏反馈区
      setUserFeedback({
        visible: false,
        message: '',
        promptMessage: ''
      });

      // 确保内容滚动到底部
      setTimeout(() => {
        scrollAnalysisAreaToBottom();
      }, 200);
    } catch (err) {
      console.error('发送用户反馈出错:', err);
      setError(`发送反馈失败: ${err}`);
    }
  };

  // 处理用户反馈取消
  const handleFeedbackCancel = () => {
    try {
      console.log('用户取消反馈');
      const ws = getWebSocketInstance();
      ws.sendMessage('取消操作');

      // 清空并隐藏反馈区
      setUserFeedback({
        visible: false,
        message: '',
        promptMessage: ''
      });
    } catch (err) {
      console.error('取消用户反馈出错:', err);
      setError(`取消反馈失败: ${err}`);
    }
  };

  // 处理用户同意操作
  const handleFeedbackApprove = async () => {
    try {
      console.log('发送用户同意反馈: APPROVE');

      // 在前端添加分隔符 - 确保只添加一次
      setRegionOutputs(prev => {
        const updatedRegions = { ...prev };
        const analysisRegion = updatedRegions.analysis;

        // 只有在当前内容中不包含分隔符时才添加
        if (!analysisRegion.merged.includes("用户已同意操作") &&
            !analysisRegion.merged.includes("----------------------------")) {
          const separator = "\n\n----------------------------\n### 用户已同意操作\n----------------------------\n\n";
          analysisRegion.merged += separator;
        }

        return updatedRegions;
      });

      // 使用SSE发送同意反馈
      const { sendUserApproval } = await import('./api');
      const sseInstance = getWebSocketInstance();
      const sessionId = sseInstance.getCurrentSessionId();

      if (sessionId) {
        await sendUserApproval(sessionId, (error) => {
          console.error('发送同意反馈失败:', error);
          setError(`发送同意反馈失败: ${error.message}`);
        });
      } else {
        console.error('没有活动的SSE会话');
        setError('没有活动的会话，无法发送同意反馈');
      }

      // 清空并隐藏反馈区
      setUserFeedback({
        visible: false,
        message: '',
        promptMessage: ''
      });

      // 确保内容滚动到底部
      setTimeout(() => {
        scrollAnalysisAreaToBottom();
      }, 200);
    } catch (err) {
      console.error('发送同意反馈出错:', err);
      setError(`发送同意反馈失败: ${err}`);
    }
  };



  // 滚动分析区域到底部的函数 - 优化版
  const scrollAnalysisAreaToBottom = () => {
    // 检查是否正在流式输出，只有流式输出时才自动滚动
    if (!regionOutputs.analysis.streaming) {
      return; // 如果不是流式输出，不进行自动滚动
    }

    // 首先尝试滚动分析区域容器
    const analysisContainer = document.querySelector('.analysis-content-container');
    if (analysisContainer && analysisContainer instanceof HTMLElement) {
      // 检查用户是否手动滚动了内容
      // 如果用户已经向上滚动了超过100像素，则不强制滚动到底部
      const scrollPosition = analysisContainer.scrollTop;
      const scrollHeight = analysisContainer.scrollHeight;
      const clientHeight = analysisContainer.clientHeight;

      // 如果用户已经向上滚动了超过200像素，则不强制滚动
      if (scrollHeight - scrollPosition - clientHeight > 200) {
        console.log('用户已手动滚动，不强制滚动到底部');
        return;
      }

      // 滚动到底部
      analysisContainer.scrollTop = analysisContainer.scrollHeight;

      // 尝试常见的内容容器选择器
      const analysisContent = document.querySelector('.analysis-content');
      if (analysisContent && analysisContent instanceof HTMLElement) {
        // 确保内容区域可见并可滚动
        analysisContent.style.display = 'block';
        analysisContent.style.overflow = 'auto';
        analysisContent.style.minHeight = '100px';

        // 延迟滚动以确保内容已经渲染
        setTimeout(() => {
          // 再次检查是否正在流式输出
          if (regionOutputs.analysis.streaming) {
            analysisContent.scrollTop = analysisContent.scrollHeight;
          }
        }, 100);
      }
    }
  };



  // 处理内容复制
  const handleCopyContent = useCallback((content: string, regionId: string) => {
    // 这里可以添加复制成功的提示
    console.log(`${regionId} 内容已复制到剪贴板`);
  }, []);





  return (
    <div className={`gemini-chat-layout ${sidebarCollapsed ? 'sidebar-collapsed' : ''}`}>
      {/* 左侧边栏 - 固定宽度，按照Gemini标准 */}
      <div className="gemini-sidebar">
        <ChatHistorySidebar
          histories={chatHistories}
          selectedHistoryId={selectedHistoryId}
          onSelectHistory={handleSelectHistory}
          onDeleteHistory={handleDeleteHistory}
          onNewChat={createNewChatSession}
          collapsed={sidebarCollapsed}
          onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
        />
      </div>

      {/* 右侧主区域 - 按照Gemini标准分为上下两部分 */}
      <div className="gemini-main-area">
        {/* 上部分：聊天内容区域 - 可滚动 */}
        <div className="gemini-chat-content">
          {/* 数据库连接选择器 - 左上角位置，与NewText2SQLPage一致 */}
          {connections.length > 0 && (
            <div style={{
              position: 'absolute',
              top: '16px',
              left: '24px',
              zIndex: 10
            }}>
              <ConnectionSelector
                connections={connections}
                selectedConnectionId={selectedConnectionId}
                setSelectedConnectionId={setSelectedConnectionId}
                loadingConnections={loadingConnections}
                userFeedbackEnabled={userFeedbackEnabled}
                setUserFeedbackEnabled={setUserFeedbackEnabled}
              />
            </div>
          )}

          {/* 内容显示区域 - 与NewText2SQLPage一致 */}
          <div style={{
            flex: 1,
            overflow: 'auto',
            minHeight: 0,
            padding: '24px',
            paddingTop: '80px' // 为数据库选择器留出空间
          }}>
            {/* 错误消息 */}
            <ErrorMessage error={error} />

            {/* 使用折叠面板显示5个区域 */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {/* 查询分析区域 */}
              {(regionOutputs.analysis.hasContent || regionOutputs.analysis.streaming) && (
                <RegionPanel
                  title="查询分析"
                  content={analysisResult || regionOutputs.analysis.merged}
                  isStreaming={regionOutputs.analysis.streaming}
                  hasContent={regionOutputs.analysis.hasContent}
                  region="analysis"
                  onCopyContent={handleCopyContent}
                />
              )}

              {/* SQL语句区域 */}
              {(regionOutputs.sql.hasContent || regionOutputs.sql.streaming) && (
                <RegionPanel
                  title="SQL语句"
                  content={sqlResult || regionOutputs.sql.merged}
                  isStreaming={regionOutputs.sql.streaming}
                  hasContent={regionOutputs.sql.hasContent}
                  region="sql"
                  onCopyContent={handleCopyContent}
                />
              )}

              {/* 语句解释区域 */}
              {(explanationState.hasContent || explanationState.streaming) && (
                <RegionPanel
                  title="语句解释"
                  content={explanationResult || ''}
                  isStreaming={explanationState.streaming}
                  hasContent={explanationState.hasContent}
                  region="explanation"
                  onCopyContent={handleCopyContent}
                />
              )}

              {/* 查询结果区域 */}
              {(regionOutputs.data.hasContent || regionOutputs.data.streaming) && (
                <RegionPanel
                  title="查询结果"
                  content={dataResult ? JSON.stringify(dataResult, null, 2) : regionOutputs.data.merged}
                  isStreaming={regionOutputs.data.streaming}
                  hasContent={regionOutputs.data.hasContent}
                  region="data"
                  onCopyContent={handleCopyContent}
                  dataResult={dataResult}
                  currentPage={currentPage}
                  pageSize={pageSize}
                  handlePageChange={handlePageChange}
                  getTotalPages={getTotalPages}
                  getCurrentPageData={getCurrentPageData}
                  convertToCSV={csvConverter}
                />
              )}

              {/* 数据可视化区域 */}
              {(regionOutputs.visualization.hasContent || regionOutputs.visualization.streaming) && (
                <RegionPanel
                  title="数据可视化"
                  content={visualizationResult ? JSON.stringify(visualizationResult, null, 2) : regionOutputs.visualization.merged}
                  isStreaming={regionOutputs.visualization.streaming}
                  hasContent={regionOutputs.visualization.hasContent}
                  region="visualization"
                  onCopyContent={handleCopyContent}
                  visualizationResult={visualizationResult}
                  dataResult={dataResult}
                />
              )}
            </div>

            {/* 用户反馈区域 */}
            <UserFeedback
              visible={userFeedback.visible}
              message={userFeedback.message}
              promptMessage={userFeedback.promptMessage}
              setMessage={(message) => setUserFeedback(prev => ({ ...prev, message }))}
              handleSubmit={handleFeedbackSubmit}
              handleApprove={handleFeedbackApprove}
              handleCancel={handleFeedbackCancel}
            />
          </div>
        </div>

        {/* 下部分：固定输入区域 - 按照Gemini标准 */}
        <div className="gemini-input-area">
          <div className="gemini-input-container">
            <div className="gemini-input-box">
              {/* 左侧控制按钮组 - 智能推荐 */}
              <div className="left-controls">
                <Tooltip title={hybridRetrievalEnabled ? "智能推荐已启用" : "智能推荐已禁用"}>
                  <button
                    className={`control-button ${hybridRetrievalEnabled ? 'active' : ''}`}
                    onClick={() => setHybridRetrievalEnabled(!hybridRetrievalEnabled)}
                    disabled={loading}
                  >
                    <BulbOutlined />
                  </button>
                </Tooltip>
              </div>

              {/* 输入框 */}
              <div className="input-wrapper">
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="向但问智能提问"
                  className="gemini-input"
                  disabled={loading}
                />
              </div>

              {/* 右侧按钮组 */}
              <div className="right-controls">
                {/* 智能示例按钮 */}
                {hybridRetrievalEnabled && (
                  <Tooltip title="查看智能推荐示例">
                    <button
                      onClick={handleShowExamples}
                      disabled={loading || query.trim() === '' || !selectedConnectionId}
                      className="control-button"
                    >
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M9 11H5a2 2 0 0 0-2 2v3a2 2 0 0 0 2 2h4"/>
                        <path d="M15 11h4a2 2 0 0 1 2 2v3a2 2 0 0 1-2 2h-4"/>
                        <path d="M12 2v20"/>
                        <circle cx="12" cy="8" r="2"/>
                      </svg>
                    </button>
                  </Tooltip>
                )}

                {/* 发送按钮 */}
                <Tooltip title="发送查询">
                  <button
                    onClick={handleStreamSearch}
                    disabled={loading || query.trim() === '' || !selectedConnectionId}
                    className="send-button"
                  >
                    {loading ? (
                      <svg className="animate-spin" width="20" height="20" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                    ) : (
                      <SendOutlined />
                    )}
                  </button>
                </Tooltip>
              </div>
            </div>

            {error && (
              <div style={{
                marginTop: '8px',
                color: '#ff4d4f',
                fontSize: '12px',
                textAlign: 'center'
              }}>
                {error}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 混合检索示例面板 */}
      <HybridExamplesPanel
        query={query}
        connectionId={selectedConnectionId}
        schemaContext={schemaContext}
        visible={hybridExamplesVisible}
        onExampleSelect={handleExampleSelect}
        onClose={handleCloseExamples}
      />
    </div>
  );
}