/**
 * Gemini风格聊天界面组件
 * 实现Google Gemini风格的智能对话界面
 */

'use client';

import React, {useEffect, useRef, useState} from 'react';
import {AnimatePresence, motion} from 'framer-motion';
import {
    ClearOutlined,
    DownloadOutlined,
    AudioOutlined,
    MoreOutlined,
    PaperClipOutlined,
    SendOutlined,
    StopOutlined
} from '@ant-design/icons';
import {Button, Dropdown, Input, message, Tooltip, Upload} from 'antd';
import {useTheme} from '@/contexts/ThemeContext';
import {MessageBubble} from './MessageBubble';
import {TypingIndicator} from './TypingIndicator';
import {ChatHeader} from './ChatHeader';
import {useChat} from '@/hooks/useChat';
import {useWebSocket} from '@/hooks/useWebSocket';

const { TextArea } = Input;

interface Message {
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

interface GeminiChatInterfaceProps {
  conversationId?: string;
  onNewConversation?: () => void;
  className?: string;
}

export function GeminiChatInterface({ 
  conversationId, 
  onNewConversation,
  className = ''
}: GeminiChatInterfaceProps) {
  const { theme, isDark } = useTheme();
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [uploadedImages, setUploadedImages] = useState<string[]>([]);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  
  const { sendMessage, isLoading } = useChat();
  const { isConnected, sendMessage: sendWebSocketMessage } = useWebSocket(
    conversationId ? `/api/v1/conversations/ws/${conversationId}` : null
  );

  // 自动滚动到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 处理发送消息
  const handleSendMessage = async () => {
    if (!inputValue.trim() && uploadedImages.length === 0) return;

    const newMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue.trim(),
      timestamp: new Date(),
      images: uploadedImages.length > 0 ? [...uploadedImages] : undefined
    };

    setMessages(prev => [...prev, newMessage]);
    setInputValue('');
    setUploadedImages([]);
    setIsTyping(true);

    try {
      // 使用WebSocket发送消息（如果连接可用）
      if (isConnected && conversationId) {
        sendWebSocketMessage({
          content: newMessage.content,
          images: newMessage.images,
          use_agents: true
        });
      } else {
        // 使用HTTP API发送消息
        const response = await sendMessage({
          conversationId: conversationId || 'new',
          content: newMessage.content,
          images: newMessage.images,
          useAgents: true
        });

        if (response.success) {
          const assistantMessage: Message = {
            id: (Date.now() + 1).toString(),
            role: 'assistant',
            content: response.response,
            timestamp: new Date(),
            metadata: {
              processingTime: response.processing_time_ms,
              agentUsed: response.agent_used,
              searchResults: response.metadata?.search_results
            }
          };
          setMessages(prev => [...prev, assistantMessage]);
        }
      }
    } catch (error) {
      console.error('发送消息失败:', error);
      message.error('发送消息失败，请重试');
    } finally {
      setIsTyping(false);
    }
  };

  // 处理键盘事件
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // 处理图片上传
  const handleImageUpload = (file: File) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const imageUrl = e.target?.result as string;
      setUploadedImages(prev => [...prev, imageUrl]);
    };
    reader.readAsDataURL(file);
    return false; // 阻止默认上传行为
  };

  // 清空对话
  const handleClearChat = () => {
    setMessages([]);
    message.success('对话已清空');
  };

  // 导出对话
  const handleExportChat = () => {
    const chatData = {
      conversationId,
      messages,
      exportTime: new Date().toISOString()
    };
    const blob = new Blob([JSON.stringify(chatData, null, 2)], { 
      type: 'application/json' 
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `chat-${conversationId || 'new'}-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
    message.success('对话已导出');
  };

  // 更多操作菜单
  const moreMenuItems = [
    {
      key: 'clear',
      label: '清空对话',
      icon: <ClearOutlined />,
      onClick: handleClearChat
    },
    {
      key: 'export',
      label: '导出对话',
      icon: <DownloadOutlined />,
      onClick: handleExportChat
    }
  ];

  return (
    <div 
      className={`flex flex-col h-full ${className}`}
      style={{ 
        backgroundColor: theme.colors.background,
        color: theme.colors.onBackground 
      }}
    >
      {/* 聊天头部 */}
      <ChatHeader 
        conversationId={conversationId}
        onNewConversation={onNewConversation}
        isConnected={isConnected}
      />

      {/* 消息列表 */}
      <div className="flex-1 overflow-y-auto px-4 py-2">
        <div className="max-w-4xl mx-auto space-y-4">
          <AnimatePresence>
            {messages.map((message) => (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3 }}
              >
                <MessageBubble message={message} />
              </motion.div>
            ))}
          </AnimatePresence>
          
          {/* 打字指示器 */}
          {isTyping && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
            >
              <TypingIndicator />
            </motion.div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* 输入区域 */}
      <div 
        className="border-t px-4 py-3"
        style={{ 
          borderColor: theme.colors.outline,
          backgroundColor: theme.colors.surface 
        }}
      >
        <div className="max-w-4xl mx-auto">
          {/* 上传的图片预览 */}
          {uploadedImages.length > 0 && (
            <div className="mb-3 flex flex-wrap gap-2">
              {uploadedImages.map((image, index) => (
                <div key={index} className="relative">
                  <img 
                    src={image} 
                    alt={`上传图片 ${index + 1}`}
                    className="w-16 h-16 object-cover rounded-lg"
                  />
                  <Button
                    size="small"
                    type="text"
                    className="absolute -top-1 -right-1 w-5 h-5 min-w-0 p-0"
                    onClick={() => setUploadedImages(prev => 
                      prev.filter((_, i) => i !== index)
                    )}
                  >
                    ×
                  </Button>
                </div>
              ))}
            </div>
          )}

          {/* 输入框和按钮 */}
          <div className="flex items-end gap-2">
            <div className="flex-1">
              <TextArea
                ref={inputRef}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="输入消息... (Shift+Enter 换行)"
                autoSize={{ minRows: 1, maxRows: 6 }}
                style={{
                  backgroundColor: theme.colors.background,
                  borderColor: theme.colors.outline,
                  color: theme.colors.onBackground
                }}
              />
            </div>
            
            {/* 工具按钮 */}
            <div className="flex items-center gap-1">
              <Upload
                beforeUpload={handleImageUpload}
                showUploadList={false}
                accept="image/*"
              >
                <Tooltip title="上传图片">
                  <Button 
                    type="text" 
                    icon={<PaperClipOutlined />}
                    style={{ color: theme.colors.onSurfaceVariant }}
                  />
                </Tooltip>
              </Upload>
              
              <Tooltip title={isRecording ? "停止录音" : "语音输入"}>
                <Button 
                  type="text" 
                  icon={isRecording ? <StopOutlined /> : <AudioOutlined />}
                  onClick={() => setIsRecording(!isRecording)}
                  style={{ 
                    color: isRecording ? theme.colors.error : theme.colors.onSurfaceVariant 
                  }}
                />
              </Tooltip>
              
              <Dropdown menu={{ items: moreMenuItems }} placement="topRight">
                <Button 
                  type="text" 
                  icon={<MoreOutlined />}
                  style={{ color: theme.colors.onSurfaceVariant }}
                />
              </Dropdown>
              
              <Button
                type="primary"
                icon={<SendOutlined />}
                onClick={handleSendMessage}
                loading={isLoading}
                disabled={!inputValue.trim() && uploadedImages.length === 0}
                style={{
                  backgroundColor: theme.colors.primary,
                  borderColor: theme.colors.primary
                }}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
