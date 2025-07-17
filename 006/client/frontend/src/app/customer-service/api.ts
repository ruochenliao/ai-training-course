import type { ChatRequestBody, SessionResponse, ImageContent } from './types'

export const AVAILABLE_MODELS = [
  { id: 'gpt-4', name: 'GPT-4' },
  { id: 'gpt-3.5-turbo', name: 'GPT-3.5' },
  { id: 'qwen-vl-max', name: 'Qwen VL Max' }
]

const API_BASE_URL = (process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000') + '/api/v1';

export const sendStreamingChatRequest = async (
  request: ChatRequestBody,
  onChunk: (chunk: string) => void,
  onComplete: () => void,
  onError: (error: Error) => void
) => {
  try {
    const response = await fetch(API_BASE_URL + `/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('Response body is null');
    }

    const decoder = new TextDecoder();
    let buffer = '';

    const processText = (text: string) => {
      const lines = text.split('\n');

      lines.forEach(line => {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));
            if (data.content) {
              onChunk(data.content);
            }
          } catch (e) {
            console.error('Failed to parse SSE data:', e);
          }
        }
      });
    };

    while (true) {
      const { done, value } = await reader.read();

      if (done) {
        if (buffer) {
          processText(buffer);
        }
        onComplete();
        break;
      }

      const chunk = decoder.decode(value, { stream: true });
      buffer += chunk;

      const lines = buffer.split('\n\n');
      buffer = lines.pop() || '';

      lines.forEach(line => processText(line));
    }
  } catch (error) {
    onError(error as Error);
  }
};

// 创建新会话
export const createSession = async (userId: string): Promise<SessionResponse> => {
  const response = await fetch(`${API_BASE_URL}/chat/session/create`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ user_id: userId }),
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return await response.json();
};

// 获取会话信息
export const getSession = async (sessionId: string): Promise<SessionResponse> => {
  const response = await fetch(`${API_BASE_URL}/chat/session/${sessionId}`);

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error('Session not found');
    }
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return await response.json();
};

// 获取用户的所有会话
export const getUserSessions = async (userId: string): Promise<SessionResponse[]> => {
  const response = await fetch(`${API_BASE_URL}/chat/sessions/${userId}`);

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return await response.json();
};

// 上传图片
export const uploadImage = async (
  file: File,
  sessionId?: string,
  userId: string = "1"
): Promise<ImageContent> => {
  const formData = new FormData();
  formData.append('file', file);

  if (sessionId) {
    formData.append('session_id', sessionId);
  }

  formData.append('user_id', userId);

  const response = await fetch(`${API_BASE_URL}/chat/upload-image`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return await response.json();
};