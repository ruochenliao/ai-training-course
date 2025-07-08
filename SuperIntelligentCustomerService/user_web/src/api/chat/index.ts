import type { ChatMessageVo, GetChatListParams, SendDTO } from './types';
import { get, post, request } from '@/utils/request';
import { useUserStore } from '@/stores';

// 发送消息（仅支持流式）

// 发送消息（流式）
export const sendStream = async (data: SendDTO): Promise<ReadableStream> => {
  const userStore = useUserStore();

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  if (userStore.token) {
    headers['token'] = userStore.token;
  }

  const response = await fetch('/api/v1/chat/send', {
    method: 'POST',
    headers,
    body: JSON.stringify({
      ...data,
      stream: true, // 启用流式响应
    }),
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

// 解析流式响应
export const parseStreamResponse = async function* (
  stream: ReadableStream
): AsyncGenerator<any, void, unknown> {
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
            const jsonStr = trimmedLine.slice(6); // 移除 'data: ' 前缀
            const data = JSON.parse(jsonStr);

            if (data.error) {
              throw new Error(data.error.message || '流式响应错误');
            }

            yield data;
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
  return post('/system/message', data);
}

// 获取当前会话的聊天记录
export function getChatList(params: GetChatListParams) {
  return get<ChatMessageVo[]>('/system/message/list', params);
}
