import {useCallback, useEffect, useRef, useState} from 'react';
import {message} from 'antd';

export interface WebSocketOptions {
  url?: string;
  protocols?: string | string[];
  onOpen?: (event: Event) => void;
  onMessage?: (data: any) => void;
  onError?: (event: Event) => void;
  onClose?: (event: CloseEvent) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  reconnectLimit?: number;
  reconnectInterval?: number;
  heartbeatInterval?: number;
  heartbeatMessage?: string;
}

export interface WebSocketResult {
  ws: WebSocket | null;
  readyState: number;
  sendMessage: (data: any) => void;
  connect: () => void;
  disconnect: () => void;
  reconnect: () => void;
}

/**
 * WebSocket Hook
 * @param url WebSocket连接地址
 * @param options 配置选项
 * @returns WebSocket实例和相关方法
 */
function useWebSocket(url: string, options: WebSocketOptions = {}): WebSocketResult {
  const {
    protocols,
    onOpen,
    onMessage,
    onError,
    onClose,
    onConnect,
    onDisconnect,
    reconnectLimit = 3,
    reconnectInterval = 3000,
    heartbeatInterval = 30000,
    heartbeatMessage = 'ping'
  } = options;

  const [readyState, setReadyState] = useState<number>(WebSocket.CONNECTING);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<NodeJS.Timeout | null>(null);
  const heartbeatTimerRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectCountRef = useRef<number>(0);
  const urlRef = useRef<string>(url);

  // 清理定时器
  const clearTimers = useCallback(() => {
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
    if (heartbeatTimerRef.current) {
      clearInterval(heartbeatTimerRef.current);
      heartbeatTimerRef.current = null;
    }
  }, []);

  // 启动心跳
  const startHeartbeat = useCallback(() => {
    if (heartbeatInterval > 0) {
      heartbeatTimerRef.current = setInterval(() => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
          wsRef.current.send(heartbeatMessage);
        }
      }, heartbeatInterval);
    }
  }, [heartbeatInterval, heartbeatMessage]);

  // 停止心跳
  const stopHeartbeat = useCallback(() => {
    if (heartbeatTimerRef.current) {
      clearInterval(heartbeatTimerRef.current);
      heartbeatTimerRef.current = null;
    }
  }, []);

  // 连接WebSocket
  const connect = useCallback(() => {
    try {
      // 关闭现有连接
      if (wsRef.current) {
        wsRef.current.close();
      }

      // 创建新连接
      wsRef.current = new WebSocket(urlRef.current, protocols);
      setReadyState(WebSocket.CONNECTING);

      // 连接打开
      wsRef.current.onopen = (event) => {
        setReadyState(WebSocket.OPEN);
        reconnectCountRef.current = 0;
        startHeartbeat();
        onOpen?.(event);
        onConnect?.();
      };

      // 接收消息
      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          onMessage?.(data);
        } catch (error) {
          // 如果不是JSON格式，直接传递原始数据
          onMessage?.(event.data);
        }
      };

      // 连接错误
      wsRef.current.onerror = (event) => {
        setReadyState(WebSocket.CLOSED);
        stopHeartbeat();
        onError?.(event);
        message.error('WebSocket连接错误');
      };

      // 连接关闭
      wsRef.current.onclose = (event) => {
        setReadyState(WebSocket.CLOSED);
        stopHeartbeat();
        onClose?.(event);
        onDisconnect?.();

        // 自动重连
        if (reconnectCountRef.current < reconnectLimit && !event.wasClean) {
          reconnectCountRef.current++;
          reconnectTimerRef.current = setTimeout(() => {
            connect();
          }, reconnectInterval);
        }
      };
    } catch (error) {
      console.error('WebSocket连接失败:', error);
      message.error('WebSocket连接失败');
    }
  }, [protocols, onOpen, onMessage, onError, onClose, onConnect, onDisconnect, reconnectLimit, reconnectInterval, startHeartbeat, stopHeartbeat]);

  // 断开连接
  const disconnect = useCallback(() => {
    clearTimers();
    reconnectCountRef.current = reconnectLimit; // 阻止自动重连
    if (wsRef.current) {
      wsRef.current.close(1000, 'Manual disconnect');
      wsRef.current = null;
    }
    setReadyState(WebSocket.CLOSED);
  }, [clearTimers, reconnectLimit]);

  // 重新连接
  const reconnect = useCallback(() => {
    disconnect();
    setTimeout(() => {
      reconnectCountRef.current = 0;
      connect();
    }, 100);
  }, [connect, disconnect]);

  // 发送消息
  const sendMessage = useCallback((data: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      try {
        const message = typeof data === 'string' ? data : JSON.stringify(data);
        wsRef.current.send(message);
      } catch (error) {
        console.error('发送消息失败:', error);
        message.error('发送消息失败');
      }
    } else {
      console.warn('WebSocket未连接，无法发送消息');
      message.warning('连接已断开，请稍后重试');
    }
  }, []);

  // 更新URL
  useEffect(() => {
    urlRef.current = url;
  }, [url]);

  // 组件卸载时清理
  useEffect(() => {
    return () => {
      clearTimers();
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [clearTimers]);

  return {
    ws: wsRef.current,
    readyState,
    sendMessage,
    connect,
    disconnect,
    reconnect
  };
}

export default useWebSocket;
export { useWebSocket };