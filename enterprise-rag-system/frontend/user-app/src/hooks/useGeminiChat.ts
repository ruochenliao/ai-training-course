/**
 * Gemini风格聊天Hook
 * 支持多模态对话、流式响应、WebSocket连接
 */

import {useCallback, useRef, useState} from 'react';
import {message} from 'antd';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  images?: string[];
  metadata?: {
    searchResults?: any[];
    processingTime?: number;
    agentUsed?: boolean;
  };
}

interface SendMessageRequest {
  conversationId: string;
  content: string;
  images?: string[];
  useAgents?: boolean;
}

interface SendMessageResponse {
  success: boolean;
  response: string;
  processing_time_ms: number;
  agent_used: boolean;
  metadata?: {
    search_results?: any[];
  };
}

interface StreamMessageRequest {
  conversationId: string;
  content: string;
  images?: string[];
  useAgents?: boolean;
}

export function useGeminiChat() {
  const [isLoading, setIsLoading] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  const abortControllerRef = useRef<AbortController | null>(null);

  // 获取认证token
  const getAuthToken = () => {
    return localStorage.getItem('token') || localStorage.getItem('auth-token') || '';
  };

  // 发送普通消息
  const sendMessage = useCallback(async (request: SendMessageRequest): Promise<SendMessageResponse> => {
    setIsLoading(true);
    
    try {
      const response = await fetch('/api/v1/conversations/send', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${getAuthToken()}`,
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('发送消息失败:', error);
      message.error('发送消息失败');
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // 发送流式消息
  const sendStreamMessage = useCallback(async (
    request: StreamMessageRequest,
    onChunk?: (chunk: string) => void,
    onComplete?: (fullResponse: string) => void,
    onError?: (error: Error) => void
  ) => {
    setIsStreaming(true);
    setStreamingContent('');
    let fullResponse = '';

    // 取消之前的请求
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    try {
      const response = await fetch('/api/v1/conversations/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${getAuthToken()}`,
        },
        body: JSON.stringify(request),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('无法获取响应流');
      }

      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') {
              onComplete?.(fullResponse);
              return;
            }

            try {
              const parsed = JSON.parse(data);
              if (parsed.content) {
                fullResponse += parsed.content;
                setStreamingContent(fullResponse);
                onChunk?.(parsed.content);
              }
            } catch (e) {
              // 忽略解析错误
            }
          }
        }
      }

      onComplete?.(fullResponse);
    } catch (error) {
      if ((error as Error).name !== 'AbortError') {
        console.error('流式消息发送失败:', error);
        onError?.(error as Error);
      }
    } finally {
      setIsStreaming(false);
      setStreamingContent('');
    }
  }, []);

  // 上传图片
  const uploadImage = useCallback(async (file: File): Promise<string> => {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('/api/v1/conversations/upload-image', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${getAuthToken()}`,
        },
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data.url;
    } catch (error) {
      console.error('图片上传失败:', error);
      message.error('图片上传失败');
      throw error;
    }
  }, []);

  // 创建新对话
  const createConversation = useCallback(async (title?: string): Promise<string> => {
    try {
      const response = await fetch('/api/v1/conversations', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${getAuthToken()}`,
        },
        body: JSON.stringify({ title: title || '新对话' }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data.id;
    } catch (error) {
      console.error('创建对话失败:', error);
      message.error('创建对话失败');
      throw error;
    }
  }, []);

  // 获取对话历史
  const getConversationHistory = useCallback(async (conversationId: string): Promise<ChatMessage[]> => {
    try {
      const response = await fetch(`/api/v1/conversations/${conversationId}/messages`, {
        headers: {
          'Authorization': `Bearer ${getAuthToken()}`,
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data.messages || [];
    } catch (error) {
      console.error('获取对话历史失败:', error);
      return [];
    }
  }, []);

  // 删除对话
  const deleteConversation = useCallback(async (conversationId: string): Promise<void> => {
    try {
      const response = await fetch(`/api/v1/conversations/${conversationId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${getAuthToken()}`,
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      message.success('对话已删除');
    } catch (error) {
      console.error('删除对话失败:', error);
      message.error('删除对话失败');
      throw error;
    }
  }, []);

  // 停止生成
  const stopGeneration = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setIsStreaming(false);
      setStreamingContent('');
    }
  }, []);

  // 添加消息
  const addMessage = useCallback((message: ChatMessage) => {
    setMessages(prev => [...prev, message]);
  }, []);

  // 更新最后一条消息
  const updateLastMessage = useCallback((content: string) => {
    setMessages(prev => {
      const newMessages = [...prev];
      if (newMessages.length > 0) {
        newMessages[newMessages.length - 1] = {
          ...newMessages[newMessages.length - 1],
          content
        };
      }
      return newMessages;
    });
  }, []);

  // 清空消息
  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  // 重新生成最后一条回复
  const regenerateLastResponse = useCallback(() => {
    const lastUserMessage = messages.filter(msg => msg.role === 'user').pop();
    if (lastUserMessage) {
      // 移除最后一条助手消息
      setMessages(prev => {
        const lastIndex = prev.length - 1;
        if (lastIndex >= 0 && prev[lastIndex].role === 'assistant') {
          return prev.slice(0, lastIndex);
        }
        return prev;
      });
      
      // 重新发送用户消息
      sendMessage({
        conversationId: 'current',
        content: lastUserMessage.content,
        images: lastUserMessage.images,
        useAgents: true
      });
    }
  }, [messages, sendMessage]);

  return {
    // 状态
    isLoading,
    isStreaming,
    messages,
    streamingContent,
    
    // 方法
    sendMessage,
    sendStreamMessage,
    uploadImage,
    createConversation,
    getConversationHistory,
    deleteConversation,
    stopGeneration,
    addMessage,
    updateLastMessage,
    clearMessages,
    regenerateLastResponse,
  };
}
