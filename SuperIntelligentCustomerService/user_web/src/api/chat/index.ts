import type {ChatMessageVo, ChatSendRequest, GetChatListParams} from './types';
import {get, post} from '@/utils/request';
import {useUserStore} from '@/stores';

// 发送消息（仅支持流式）

// 发送消息（流式）- 更新为匹配后端接口
export const sendStream = async (data: ChatSendRequest): Promise<ReadableStream> => {
  const userStore = useUserStore();

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  if (userStore.token) {
    headers['token'] = userStore.token;
  }

  // 构建符合后端期望的请求体
  const requestBody = {
    message: data.message,
    session_id: data.sessionId ? parseInt(data.sessionId) : undefined,
    files: data.files || []
  };

  const response = await fetch('/api/v1/chat/send', {
    method: 'POST',
    headers,
    body: JSON.stringify(requestBody),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`发送消息失败: ${response.status} ${errorText}`);
  }

  if (!response.body) {
    throw new Error('响应体为空');
  }

  return response.body;
};

// 解析流式响应 - 适配后端SSE格式
export const parseStreamResponse = async function* (
  stream: ReadableStream
): AsyncGenerator<string, void, unknown> {
  const reader = stream.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();

      if (done) {
        break;
      }

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');

      // 保留最后一行（可能不完整）
      buffer = lines.pop() || '';

      for (const line of lines) {
        const trimmedLine = line.trim();

        if (trimmedLine === '') {
          continue;
        }

        if (trimmedLine === 'data: [DONE]') {
          return;
        }

        if (trimmedLine.startsWith('data: ')) {
          try {
            const content = trimmedLine.slice(6); // 移除 'data: ' 前缀

            // 后端直接返回文本内容，不是JSON格式
            if (content && content !== '[DONE]') {
              yield content;
            }
          } catch (parseError) {
            console.warn('解析流式数据失败:', parseError, '原始数据:', trimmedLine);
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
};

// 新增对应会话聊天记录
export function addChat(data: ChatMessageVo) {
  return post('/api/v1/system/message', data);
}

// 获取当前会话的聊天记录
export function getChatList(params: GetChatListParams) {
  return get<ChatMessageVo[]>('/api/v1/system/message/list', {
    session_id: params.sessionId ? parseInt(params.sessionId) : undefined,
    page: params.pageNum || 1,
    page_size: params.pageSize || 20,
    content: params.content,
    role: params.role
  });
}

// 获取聊天服务健康状态
export function getHealthStatus() {
  return get('/api/v1/chat/health');
}

// 获取聊天服务统计信息（管理员功能）
export function getServiceStats() {
  return get('/api/v1/chat/stats');
}

// 获取可用模型列表
export function getAvailableModels(params?: { page?: number; page_size?: number; model_type?: string }) {
  return get('/api/v1/chat/models/list', params);
}
