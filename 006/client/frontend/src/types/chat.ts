export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  status?: 'pending' | 'complete' | 'error';
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  status?: 'pending' | 'complete' | 'error';
}
