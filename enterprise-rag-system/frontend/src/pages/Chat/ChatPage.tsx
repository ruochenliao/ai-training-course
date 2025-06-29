import React, { useState } from 'react'
import { Avatar, Button, Card, Divider, Input, Space, Typography } from 'antd'
import { RobotOutlined, SendOutlined, UserOutlined } from '@ant-design/icons'

const { Title, Text } = Typography
const { TextArea } = Input

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

const ChatPage: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: '您好！我是您的AI助手，基于企业知识库为您提供智能问答服务。请问有什么可以帮助您的吗？',
      timestamp: new Date(),
    },
  ])
  const [inputValue, setInputValue] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSendMessage = async () => {
    if (!inputValue.trim() || loading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue.trim(),
      timestamp: new Date(),
    }

    setMessages(prev => [...prev, userMessage])
    setInputValue('')
    setLoading(true)

    // 模拟AI回复
    setTimeout(() => {
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `感谢您的问题："${userMessage.content}"。这是一个模拟回复，实际项目中这里会调用真实的AI接口来生成回答。`,
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, assistantMessage])
      setLoading(false)
    }, 1000)
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  return (
    <div style={{ padding: 24, height: 'calc(100vh - 64px)', display: 'flex', flexDirection: 'column' }}>
      {/* 页面标题 */}
      <div style={{ marginBottom: 24 }}>
        <Title level={2} style={{ margin: 0, color: '#1e293b' }}>
          智能对话
        </Title>
        <Text style={{ color: '#64748b' }}>基于企业知识库的智能问答系统</Text>
      </div>

      {/* 聊天区域 */}
      <Card
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
        }}
        bodyStyle={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          padding: 0,
        }}
      >
        {/* 消息列表 */}
        <div
          style={{
            flex: 1,
            padding: 24,
            overflowY: 'auto',
            background: '#fafafa',
          }}
        >
          <Space direction='vertical' size='large' style={{ width: '100%' }}>
            {messages.map(message => (
              <div
                key={message.id}
                style={{
                  display: 'flex',
                  justifyContent: message.role === 'user' ? 'flex-end' : 'flex-start',
                  width: '100%',
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    flexDirection: message.role === 'user' ? 'row-reverse' : 'row',
                    alignItems: 'flex-start',
                    maxWidth: '70%',
                    gap: 12,
                  }}
                >
                  <Avatar
                    size='default'
                    icon={message.role === 'user' ? <UserOutlined /> : <RobotOutlined />}
                    style={{
                      background:
                        message.role === 'user'
                          ? 'linear-gradient(135deg, #0ea5e9, #8b5cf6)'
                          : 'linear-gradient(135deg, #10b981, #059669)',
                      flexShrink: 0,
                    }}
                  />
                  <div
                    style={{
                      background: message.role === 'user' ? '#0ea5e9' : '#ffffff',
                      color: message.role === 'user' ? '#ffffff' : '#1e293b',
                      padding: '12px 16px',
                      borderRadius: 12,
                      boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
                      border: message.role === 'assistant' ? '1px solid #e2e8f0' : 'none',
                    }}
                  >
                    <div style={{ marginBottom: 4 }}>{message.content}</div>
                    <div
                      style={{
                        fontSize: 12,
                        opacity: 0.7,
                        textAlign: 'right',
                      }}
                    >
                      {formatTime(message.timestamp)}
                    </div>
                  </div>
                </div>
              </div>
            ))}

            {loading && (
              <div style={{ display: 'flex', justifyContent: 'flex-start', width: '100%' }}>
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
                  <Avatar
                    size='default'
                    icon={<RobotOutlined />}
                    style={{
                      background: 'linear-gradient(135deg, #10b981, #059669)',
                    }}
                  />
                  <div
                    style={{
                      background: '#ffffff',
                      padding: '12px 16px',
                      borderRadius: 12,
                      boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
                      border: '1px solid #e2e8f0',
                    }}
                  >
                    <div style={{ display: 'flex', gap: 4 }}>
                      <div
                        style={{
                          width: 8,
                          height: 8,
                          borderRadius: '50%',
                          background: '#94a3b8',
                          animation: 'pulse 1.5s ease-in-out infinite',
                        }}
                      />
                      <div
                        style={{
                          width: 8,
                          height: 8,
                          borderRadius: '50%',
                          background: '#94a3b8',
                          animation: 'pulse 1.5s ease-in-out infinite 0.2s',
                        }}
                      />
                      <div
                        style={{
                          width: 8,
                          height: 8,
                          borderRadius: '50%',
                          background: '#94a3b8',
                          animation: 'pulse 1.5s ease-in-out infinite 0.4s',
                        }}
                      />
                    </div>
                  </div>
                </div>
              </div>
            )}
          </Space>
        </div>

        <Divider style={{ margin: 0 }} />

        {/* 输入区域 */}
        <div style={{ padding: 24 }}>
          <Space.Compact style={{ width: '100%' }}>
            <TextArea
              value={inputValue}
              onChange={e => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder='请输入您的问题...'
              autoSize={{ minRows: 1, maxRows: 4 }}
              disabled={loading}
              style={{
                resize: 'none',
                borderRadius: '8px 0 0 8px',
              }}
            />
            <Button
              type='primary'
              icon={<SendOutlined />}
              onClick={handleSendMessage}
              loading={loading}
              disabled={!inputValue.trim()}
              style={{
                height: 'auto',
                minHeight: 40,
                background: 'linear-gradient(135deg, #0ea5e9, #8b5cf6)',
                border: 'none',
                borderRadius: '0 8px 8px 0',
              }}
            >
              发送
            </Button>
          </Space.Compact>

          <div style={{ marginTop: 8, textAlign: 'center' }}>
            <Text type='secondary' style={{ fontSize: 12 }}>
              AI助手可能会出错，请核实重要信息
            </Text>
          </div>
        </div>
      </Card>

      <style>
        {`
          @keyframes pulse {
            0%, 80%, 100% {
              opacity: 0.3;
              transform: scale(0.8);
            }
            40% {
              opacity: 1;
              transform: scale(1);
            }
          }
        `}
      </style>
    </div>
  )
}

export default ChatPage
