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

    // 构建消息对象
    const messages = [{
      role: 'user',
      content: data.message
    }];

    formData.append('messages', JSON.stringify(messages));

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
      messages: [{
        role: 'user',
        content: data.message
      }],
      session_id: data.sessionId || null,
      model_name: data.model_name
    });
  }

  const response = await fetch('/api/v1/customer/chat/stream', {
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

// 流式事件类型定义
export interface StreamEvent {
  id: string;
  type: 'start' | 'processing' | 'content' | 'complete' | 'error' | 'done' | 'user_message_saved' | 'ai_message_saved';
  timestamp: string;
  session_id?: string;
  user_id?: number;
  model_name?: string;
  data?: any;
  chunk_index?: number;
  total_length?: number;
  is_markdown?: boolean;
}

// 优化的流式响应解析器，支持完整的事件处理和错误恢复
export const parseStreamResponse = async function* (
  stream: ReadableStream
): AsyncGenerator<StreamEvent, void, unknown> {
  const reader = stream.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let eventCount = 0;

  try {
    while (true) {
      const { done, value } = await reader.read();

      if (done) {
        // 处理剩余的缓冲内容
        if (buffer.trim()) {
          console.warn('流结束时仍有未处理的缓冲内容:', buffer);
        }
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

        if (trimmedLine.startsWith('data: ')) {
          try {
            const jsonStr = trimmedLine.slice(6); // 移除 'data: ' 前缀

            // 跳过结束标记
            if (jsonStr === '[DONE]') {
              console.log('收到流结束标记');
              continue;
            }

            // 尝试解析JSON格式的事件数据
            if (jsonStr) {
              try {
                const event: StreamEvent = JSON.parse(jsonStr);
                eventCount++;

                // 验证事件格式
                if (event.type && event.timestamp) {
                  yield event;
                } else if (event.content) {
                  // 兼容旧格式：直接包含 content 字段
                  yield {
                    id: `compat_${Date.now()}_${eventCount}`,
                    type: 'content',
                    timestamp: new Date().toISOString(),
                    data: { content: event.content },
                    is_markdown: true
                  };
                } else {
                  console.warn('收到格式不完整的事件:', event);
                }
              } catch (jsonError) {
                // 如果不是JSON格式，可能是旧版本的纯文本格式，兼容处理
                console.warn('收到非JSON格式的流式数据，使用兼容模式:', jsonStr.substring(0, 100));
                yield {
                  id: `compat_${Date.now()}_${eventCount}`,
                  type: 'content',
                  timestamp: new Date().toISOString(),
                  data: jsonStr,
                  is_markdown: true
                };
                eventCount++;
              }
            }
          } catch (parseError) {
            console.error('解析流式数据失败:', parseError, '原始数据:', trimmedLine.substring(0, 100));
            // 继续处理下一行，不中断整个流
          }
        } else {
          // 处理非标准格式的数据
          console.debug('收到非标准格式数据:', trimmedLine.substring(0, 50));
        }
      }
    }

    console.log(`流式解析完成，共处理 ${eventCount} 个事件`);
  } catch (error) {
    console.error('流式解析过程中发生错误:', error);
    // 发送错误事件
    yield {
      id: `error_${Date.now()}`,
      type: 'error',
      timestamp: new Date().toISOString(),
      data: { message: `流式解析错误: ${error.message}` }
    };
  } finally {
    reader.releaseLock();
  }
};

// 新增对应会话聊天记录
export function addChat(data: ChatMessageVo) {
  return post('/api/v1/system/message', data);
}

// 获取当前会话的聊天记录 - 改为使用会话详情接口
export function getChatList(params: GetChatListParams) {
  if (!params.sessionId) {
    return Promise.resolve({ data: [] });
  }

  // 使用会话详情接口获取消息历史
  return get<any>(`/api/v1/customer/sessions/${params.sessionId}`).then(response => {
    // 从会话数据中提取消息列表
    const messages = response.data?.messages || [];

    // 转换消息格式以匹配前端期望的格式
    const formattedMessages = messages.map((msg: any, index: number) => ({
      id: index + 1, // 临时ID，因为文件系统存储的消息没有独立ID
      content: msg.content,
      role: msg.role,
      sessionId: params.sessionId,
      userId: response.data?.user_id,
      modelName: msg.model_name || 'DeepSeek VL Chat',
      totalTokens: msg.total_tokens || 0,
      deductCost: msg.deduct_cost || 0,
      remark: msg.remark || '',
      created_at: msg.created_at || response.data?.created_at,
      updated_at: msg.updated_at || response.data?.last_active
    }));

    return { data: formattedMessages };
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

// 上传图片到聊天会话
export async function uploadImage(file: File, sessionId?: string): Promise<any> {
  const userStore = useUserStore();
  const formData = new FormData();
  formData.append('file', file);

  if (sessionId) {
    formData.append('session_id', sessionId);
  }

  const headers: Record<string, string> = {};
  if (userStore.token) {
    headers['token'] = userStore.token;
  }

  const response = await fetch('/api/v1/customer/chat/upload-image', {
    method: 'POST',
    headers,
    body: formData,
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`上传图片失败: ${response.status} ${errorText}`);
  }

  return await response.json();
}
