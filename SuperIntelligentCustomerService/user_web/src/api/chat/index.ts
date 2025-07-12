import type {ChatMessageVo, ChatSendRequest, GetChatListParams} from './types';
import {get, post} from '@/utils/request';
import {useUserStore} from '@/stores';

// 发送消息（仅支持流式）

// 发送消息（流式）- 更新为匹配后端接口
export const sendStream = async (data: ChatSendRequest): Promise<ReadableStream> => {
  const userStore = useUserStore();

  // 检查是否有文件需要上传
  const hasFiles = data.files && data.files.length > 0;

  let headers: Record<string, string> = {};
  let body: string | FormData;

  if (userStore.token) {
    headers['token'] = userStore.token;
  }

  if (hasFiles) {
    // 有文件时使用 FormData 格式
    const formData = new FormData();
    formData.append('message', data.message);

    if (data.sessionId) {
      formData.append('session_id', data.sessionId);
    }

    if (data.model_name) {
      formData.append('model_name', data.model_name);
    }

    // 添加文件
    data.files.forEach((file) => {
      formData.append('files', file);
    });

    body = formData;
    // 不设置 Content-Type，让浏览器自动设置 multipart/form-data 边界
  } else {
    // 无文件时使用 JSON 格式
    headers['Content-Type'] = 'application/json';
    body = JSON.stringify({
      message: data.message,
      session_id: data.sessionId ? parseInt(data.sessionId) : undefined,
      model_name: data.model_name,
      files: []
    });
  }

  const response = await fetch('/api/v1/chat/send', {
    method: 'POST',
    headers,
    body,
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
