import { Text2SQLResponse } from './types';

// 流式响应消息
export interface StreamResponseMessage {
  source: string;
  content: string;
  is_final?: boolean;
  region?: string;
  type?: string;
  is_feedback_response?: boolean; // 添加标记是否为用户反馈后的响应
}

export interface FinalSqlData {
  sql: string;
}

export interface FinalExplanationData {
  explanation: string;
}

export interface FinalDataResult {
  results: any[];
}

export interface FinalVisualizationData {
  type: string;
  config: any;
}

// API基础URL - 确保使用完整URL
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL + '/api/v1' || 'http://localhost:8000/api/v1';
console.log('使用API基础URL:', API_BASE_URL);

/**
 * WebSocket连接类，管理Text2SQL的WebSocket通信
 */
export class Text2SQLWebSocket {
  private socket: WebSocket | null = null;
  private isConnected: boolean = false;
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 5;
  private reconnectTimeout: number = 2000; // 开始重连时间(ms)
  private reconnectTimeoutId: NodeJS.Timeout | null = null;
  private url: string;
  
  // 回调函数
  private onMessageCallback: ((message: StreamResponseMessage) => void) | null = null;
  private onResultCallback: ((result: Text2SQLResponse) => void) | null = null;
  private onErrorCallback: ((error: Error) => void) | null = null;
  private onFinalSqlCallback: ((data: string) => void) | null = null;
  private onFinalExplanationCallback: ((data: string) => void) | null = null;
  private onFinalDataCallback: ((data: any[]) => void) | null = null;
  private onFinalVisualizationCallback: ((data: FinalVisualizationData) => void) | null = null;
  
  constructor() {
    // 计算WebSocket URL (将http/https替换为ws/wss)
    let wsBaseUrl = API_BASE_URL.replace(/^http/, 'ws');
    this.url = `${wsBaseUrl}/text2sql/websocket`;
    console.log('WebSocket URL:', this.url);
  }
  
  /**
   * 建立WebSocket连接
   */
  public connect(): void {
    if (this.socket && (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING)) {
      console.log('WebSocket已连接或正在连接中');
      return;
    }
    
    try {
      console.log('正在连接WebSocket:', this.url);
      this.socket = new WebSocket(this.url);
      
      console.log('WebSocket对象已创建，等待连接建立...');
      
      this.socket.onopen = this.handleOpen.bind(this);
      this.socket.onmessage = this.handleSocketMessage.bind(this);
      this.socket.onclose = this.handleClose.bind(this);
      this.socket.onerror = this.handleError.bind(this);
    } catch (error) {
      console.error('WebSocket连接创建错误:', error);
      this.notifyError(new Error(`WebSocket连接失败: ${error}`));
      this.attemptReconnect();
    }
  }
  
  /**
   * 关闭WebSocket连接
   */
  public disconnect(): void {
    if (this.socket) {
      console.log('关闭WebSocket连接');
      this.socket.close();
      this.socket = null;
    }
    
    this.isConnected = false;
    
    // 清除重连计时器
    if (this.reconnectTimeoutId) {
      clearTimeout(this.reconnectTimeoutId);
      this.reconnectTimeoutId = null;
    }
  }
  
  /**
   * 发送查询到WebSocket
   */
  public sendQuery(query: string): void {
    if (!this.isConnected) {
      console.log('WebSocket未连接，正在连接...');
      this.connect();
      
      // 连接后发送查询
      setTimeout(() => {
        if (this.isConnected) {
          this.sendQuery(query);
        } else {
          this.notifyError(new Error('无法连接到WebSocket服务器'));
        }
      }, 1000);
      return;
    }
    
    try {
      console.log('发送查询到WebSocket:', query);
      if (this.socket && this.socket.readyState === WebSocket.OPEN) {
        this.socket.send(JSON.stringify({
          query: query
        }));
      } else {
        this.notifyError(new Error('WebSocket未就绪，无法发送消息'));
      }
    } catch (error) {
      console.error('发送查询错误:', error);
      this.notifyError(new Error(`发送查询失败: ${error}`));
    }
  }
  
  /**
   * 设置消息回调
   */
  public setCallbacks(
      onMessage: (message: StreamResponseMessage) => void, onResult: (result: Text2SQLResponse) => void, onError: (error: Error) => void, onFinalSql?: (data: string) => void, onFinalExplanation?: (data: string) => void, onFinalData?: (data: any[]) => void, onFinalVisualization?: (data: FinalVisualizationData) => void, handleFinalAnalysis?: (analysis: string) => void  ): void {
    this.onMessageCallback = onMessage;
    this.onResultCallback = onResult;
    this.onErrorCallback = onError;
    this.onFinalSqlCallback = onFinalSql || null;
    this.onFinalExplanationCallback = onFinalExplanation || null;
    this.onFinalDataCallback = onFinalData || null;
    this.onFinalVisualizationCallback = onFinalVisualization || null;
  }
  
  /**
   * 处理WebSocket连接打开
   */
  private handleOpen(event: Event): void {
    console.log('WebSocket连接已打开:', event);
    this.isConnected = true;
    this.reconnectAttempts = 0;
  }
  
  /**
   * 处理WebSocket接收到的消息
   */
  private handleSocketMessage(event: MessageEvent): void {
    try {
      const data = JSON.parse(event.data);
      console.log('WebSocket接收到消息:', data);
      
      // 检查是否有错误
      if (data.error) {
        if (this.onErrorCallback) {
          this.onErrorCallback(new Error(data.error));
        }
        return;
      }
      
      // 处理不同类型的消息
      if (data.type === 'message') {
        const message: StreamResponseMessage = {
          source: data.source || '系统',
          content: data.content || '',
          is_final: data.is_final || false,
          region: data.region || null,
          type: data.message_type || 'text'
        };
        
        // 特殊处理：如果来源是查询分析智能体，但没有设置区域，则设置为analysis
        if (message.source === '查询分析智能体' && !message.region) {
          message.region = 'analysis';
          console.log('设置查询分析智能体消息区域为: analysis');
        }
        
        // 特殊处理：处理来自用户代理的反馈消息
        // 由于前端已添加分隔符，如果后端也添加了分隔符，可能会导致重复显示
        // 此处我们检查内容是否包含分隔符，如果包含则不做特殊处理
        if (message.source === 'user_proxy' && message.content) {
          // 确保消息内容不会导致分隔符重复
          if (message.content.includes("----------------------------")) {
            // 如果后端消息已经包含分隔符，我们可以检查前端是否已添加过分隔符
            // 但这需要维护一个状态，暂不实现
            console.log('消息已包含分隔符，不做特殊处理');
          }
        }
        
        if (this.onMessageCallback) {
          this.onMessageCallback(message);
        }
        
        // 特殊消息处理
        if (data.is_final && data.result) {
          this.handleFinalResult(data);
        }
      }
      else if (data.type === 'final_result') {
        // 处理最终结果
        if (this.onResultCallback && data.result) {
          this.onResultCallback(data.result);
        }
      }
    } catch (error) {
      console.error('处理WebSocket消息时出错:', error);
      if (this.onErrorCallback) {
        this.onErrorCallback(new Error('处理WebSocket消息时出错'));
      }
    }
  }
  
  /**
   * 处理最终结果
   */
  private handleFinalResult(data: any): void {
    // 检查是否有特定类型的最终结果
    if (data.result) {
      // SQL结果
      if (data.result.sql && this.onFinalSqlCallback) {
        this.onFinalSqlCallback(data.result.sql);
      }
      
      // 解释结果
      if (data.result.explanation && this.onFinalExplanationCallback) {
        this.onFinalExplanationCallback(data.result.explanation);
      }
      
      // 数据结果
      if (data.result.results && this.onFinalDataCallback) {
        this.onFinalDataCallback(data.result.results);
      }
      
      // 可视化结果
      if ((data.result.visualization_type || data.result.visualization_config) && 
          this.onFinalVisualizationCallback) {
        this.onFinalVisualizationCallback({
          type: data.result.visualization_type,
          config: data.result.visualization_config
        });
      }
    }
  }
  
  /**
   * 处理WebSocket关闭
   */
  private handleClose(event: CloseEvent): void {
    console.log('WebSocket连接已关闭:', event);
    this.isConnected = false;
    
    // 非正常关闭时尝试重连
    if (event.code !== 1000) {
      this.attemptReconnect();
    }
  }
  
  /**
   * 处理WebSocket错误
   */
  private handleError(event: Event): void {
    console.error('WebSocket错误:', event);
    const errorDetail = event.toString ? event.toString() : '未知错误';
    console.error('WebSocket详细错误信息:', errorDetail);
    this.notifyError(new Error(`WebSocket连接错误: ${errorDetail}`));
  }
  
  /**
   * 尝试重新连接
   */
  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log('达到最大重连次数，停止重连');
      this.notifyError(new Error('无法连接到服务器，请稍后再试'));
      return;
    }
    
    const delay = this.reconnectTimeout * Math.pow(1.5, this.reconnectAttempts);
    console.log(`${delay}ms后尝试重连(第${this.reconnectAttempts + 1}次)`);
    
    this.reconnectTimeoutId = setTimeout(() => {
      this.reconnectAttempts++;
      this.connect();
    }, delay);
  }
  
  /**
   * 通知错误
   */
  private notifyError(error: Error): void {
    if (this.onErrorCallback) {
      this.onErrorCallback(error);
    }
  }
  
  /**
   * 获取WebSocket实例
   */
  public getSocket(): WebSocket | null {
    return this.socket;
  }
  
  /**
   * 发送一般消息到WebSocket
   */
  public sendMessage(content: string): void {
    if (!this.isConnected) {
      console.log('WebSocket未连接，正在连接...');
      this.connect();
      
      // 连接后发送消息
      setTimeout(() => {
        if (this.isConnected) {
          this.sendMessage(content);
        } else {
          this.notifyError(new Error('无法连接到WebSocket服务器'));
        }
      }, 1000);
      return;
    }
    
    try {
      console.log('发送反馈消息到WebSocket:', content);
      if (this.socket && this.socket.readyState === WebSocket.OPEN) {
        // 修改为符合TextMessage模型结构的消息格式，并添加is_feedback标记
        this.socket.send(JSON.stringify({
          content: content,
          source: "user",
          type: "text",
          role: "user",
          is_feedback: true // 添加标记表示这是用户反馈
        }));
      } else {
        this.notifyError(new Error('WebSocket未就绪，无法发送消息'));
      }
    } catch (error) {
      console.error('发送消息错误:', error);
      this.notifyError(new Error(`发送消息失败: ${error}`));
    }
  }
}

// 创建全局WebSocket实例
let webSocketInstance: Text2SQLWebSocket | null = null;

/**
 * 获取WebSocket实例
 */
export const getWebSocketInstance = (): Text2SQLWebSocket => {
  if (!webSocketInstance) {
    webSocketInstance = new Text2SQLWebSocket();
  }
  return webSocketInstance;
};

/**
 * 使用WebSocket发送Text2SQL请求
 */
export const sendWebSocketText2SQLRequest = (
  query: string,
  onMessage: (message: StreamResponseMessage) => void,
  onResult: (result: Text2SQLResponse) => void,
  onError: (error: Error) => void,
  onFinalSql?: (data: string) => void,
  onFinalExplanation?: (data: string) => void,
  onFinalData?: (data: any[]) => void,
  onFinalVisualization?: (data: FinalVisualizationData) => void
): void => {
  try {
    const ws = getWebSocketInstance();
    ws.setCallbacks(
      onMessage,
      onResult,
      onError,
      onFinalSql,
      onFinalExplanation,
      onFinalData,
      onFinalVisualization
    );
    ws.connect();
    ws.sendQuery(query);
  } catch (error) {
    console.error('WebSocket请求错误:', error);
    onError(error instanceof Error ? error : new Error(String(error)));
  }
};

/**
 * 关闭WebSocket连接
 */
export const closeWebSocketConnection = (): void => {
  if (webSocketInstance) {
    webSocketInstance.disconnect();
  }
};

/**
 * 发送标准Text2SQL请求
 * 
 * @param query 自然语言查询
 * @returns 处理结果
 */
export const sendText2SQLRequest = async (query: string): Promise<Text2SQLResponse> => {
  try {
    const response = await fetch(`${API_BASE_URL}/text2sql/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || '请求处理失败');
    }

    return await response.json();
  } catch (error) {
    console.error('API请求失败:', error);
    throw error;
  }
};

// 为EventSource的错误事件添加自定义类型
interface ErrorEventSource extends Event {
  data?: string;
}

/**
 * 发送流式Text2SQL请求
 * 
 * @param query 自然语言查询
 * @param onMessage 处理每个消息的回调函数
 * @param onResult 处理最终结果的回调函数
 * @param onError 错误处理回调函数
 * @param onFinalSql 处理最终SQL结果的回调函数
 * @param onFinalExplanation 处理最终解释结果的回调函数
 * @param onFinalData 处理最终数据结果的回调函数
 * @param onFinalVisualization 处理最终可视化结果的回调函数
 */
export const sendStreamingText2SQLRequest = (
  query: string,
  onMessage: (message: StreamResponseMessage) => void,
  onResult: (result: Text2SQLResponse) => void,
  onError: (error: Error) => void,
  onFinalSql?: (data: string) => void,
  onFinalExplanation?: (data: string) => void,
  onFinalData?: (data: any[]) => void,
  onFinalVisualization?: (data: FinalVisualizationData) => void
): EventSource => {
  console.log('开始流式请求:', query);
  
  // 使用URL参数方式请求
  const apiUrl = `${API_BASE_URL}/text2sql/stream?query=${encodeURIComponent(query)}`;
  console.log('API URL:', apiUrl);
  
  try {
    const eventSource = new EventSource(apiUrl);
    
    // 连接打开
    eventSource.onopen = (event) => {
      console.log('EventSource连接已打开', event);
    };
    
    // 消息处理
    eventSource.addEventListener('message', (event: MessageEvent) => {
      try {
        console.log('收到消息:', event.data);
        const data = JSON.parse(event.data);
        onMessage(data);
      } catch (e) {
        console.error('解析消息失败:', e, '原始消息:', event.data);
        // 不要中断连接，继续处理其他消息
      }
    });
    
    // 最终结果处理
    eventSource.addEventListener('result', (event: MessageEvent) => {
      try {
        console.log('收到最终结果:', event.data);
        const data = JSON.parse(event.data);
        onResult(data);
        console.log('关闭EventSource连接(来自result事件)');
        eventSource.close();
      } catch (e) {
        console.error('解析结果失败:', e, '原始结果:', event.data);
        onError(new Error(`解析最终结果失败: ${e}`));
      }
    });
    
    // SQL结果处理
    eventSource.addEventListener('final_sql', (event: MessageEvent) => {
      try {
        console.log('收到SQL结果:', event.data);
        if (onFinalSql) {
          onFinalSql(JSON.parse(event.data));
        }
      } catch (e) {
        console.error('解析SQL结果失败:', e, '原始数据:', event.data);
      }
    });
    
    // 解释结果处理
    eventSource.addEventListener('final_explanation', (event: MessageEvent) => {
      try {
        console.log('收到解释结果:', event.data);
        if (onFinalExplanation) {
          onFinalExplanation(JSON.parse(event.data));
        }
      } catch (e) {
        console.error('解析解释结果失败:', e, '原始数据:', event.data);
      }
    });
    
    // 数据结果处理
    eventSource.addEventListener('final_data', (event: MessageEvent) => {
      try {
        console.log('收到数据结果:', event.data);
        if (onFinalData) {
          onFinalData(JSON.parse(event.data));
        }
      } catch (e) {
        console.error('解析数据结果失败:', e, '原始数据:', event.data);
      }
    });
    
    // 可视化结果处理
    eventSource.addEventListener('final_visualization', (event: MessageEvent) => {
      try {
        console.log('收到可视化结果:', event.data);
        if (onFinalVisualization) {
          onFinalVisualization(JSON.parse(event.data));
        }
      } catch (e) {
        console.error('解析可视化结果失败:', e, '原始数据:', event.data);
      }
    });
    
    // 错误处理
    eventSource.addEventListener('error', (event: Event) => {
      console.error('EventSource错误:', event);
      
      // 检查连接状态
      if ((eventSource as any).readyState === 2) { // CLOSED
        console.log('EventSource连接已关闭');
      } else if ((eventSource as any).readyState === 0) { // CONNECTING
        console.log('EventSource正在连接中');
      } else {
        console.log('EventSource连接状态:', (eventSource as any).readyState);
      }
      
      try {
        const errorEvent = event as ErrorEventSource;
        if (errorEvent.data) {
          console.log('错误事件数据:', errorEvent.data);
          try {
            const data = JSON.parse(errorEvent.data);
            onError(new Error(data.detail || '处理请求过程中发生错误'));
          } catch (parseError) {
            onError(new Error(`无法解析错误信息: ${errorEvent.data}`));
          }
        } else {
          onError(new Error('连接中断或请求处理失败'));
        }
      } catch (e) {
        console.error('处理错误事件时出错:', e);
        onError(new Error('连接中断或请求处理失败'));
      }
      
      console.log('关闭EventSource连接(来自error事件)');
      eventSource.close();
    });
    
    return eventSource;
  } catch (initError: any) {
    console.error('初始化EventSource失败:', initError);
    onError(new Error(`无法建立连接: ${initError.message}`));
    // 由于不能返回null，创建一个虚拟的EventSource并立即关闭它
    const dummyEventSource = new EventSource(`data:,`);
    dummyEventSource.close();
    return dummyEventSource;
  }
}; 