'use client'

import React, {useEffect, useRef, useState} from 'react'
import {Avatar, Button, Card, Input, Layout, message, Spin, Tag, Typography} from 'antd'
import {FileTextOutlined, RobotOutlined, SendOutlined, UserOutlined} from '@ant-design/icons'

const { Content } = Layout
const { TextArea } = Input
const { Text, Paragraph } = Typography

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  sources?: Array<{
    id: string
    content_preview: string
    score: number
    source_type: string
    metadata: any
  }>
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [conversationId, setConversationId] = useState<number | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const sendMessage = async () => {
    if (!inputValue.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInputValue('')
    setIsLoading(true)

    try {
      const response = await fetch('/api/v1/chat/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          message: inputValue,
          conversation_id: conversationId,
          knowledge_base_ids: [],
          stream: false
        })
      })

      if (!response.ok) {
        throw new Error('发送消息失败')
      }

      const data = await response.json()

      const assistantMessage: Message = {
        id: data.message_id.toString(),
        role: 'assistant',
        content: data.message,
        timestamp: new Date(),
        sources: data.sources
      }

      setMessages(prev => [...prev, assistantMessage])
      
      if (!conversationId) {
        setConversationId(data.conversation_id)
      }

    } catch (error) {
      console.error('发送消息失败:', error)
      message.error('发送消息失败，请稍后重试')
      
      const errorMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: '抱歉，发送消息时出现错误，请稍后重试。',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const formatTimestamp = (timestamp: Date) => {
    return timestamp.toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <Layout className="h-screen">
      <Content className="flex flex-col h-full">
        {/* 消息列表 */}
        <div className="flex-1 overflow-y-auto p-6 bg-gray-50">
          <div className="max-w-4xl mx-auto space-y-4">
            {messages.length === 0 && (
              <div className="text-center py-12">
                <RobotOutlined className="text-6xl text-gray-400 mb-4" />
                <Text className="text-lg text-gray-500">
                  您好！我是您的AI助手，有什么可以帮助您的吗？
                </Text>
              </div>
            )}

            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div className={`flex max-w-3xl ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                  <Avatar
                    icon={msg.role === 'user' ? <UserOutlined /> : <RobotOutlined />}
                    className={`${msg.role === 'user' ? 'ml-3' : 'mr-3'} flex-shrink-0`}
                    style={{
                      backgroundColor: msg.role === 'user' ? '#1890ff' : '#52c41a'
                    }}
                  />
                  
                  <Card
                    className={`${msg.role === 'user' ? 'bg-blue-50' : 'bg-white'} shadow-sm`}
                    bodyStyle={{ padding: '16px' }}
                  >
                    <Paragraph className="mb-2 whitespace-pre-wrap">
                      {msg.content}
                    </Paragraph>
                    
                    {/* 来源信息 */}
                    {msg.sources && msg.sources.length > 0 && (
                      <div className="mt-4 pt-4 border-t border-gray-200">
                        <Text strong className="text-gray-600 block mb-2">
                          参考来源：
                        </Text>
                        <div className="space-y-2">
                          {msg.sources.slice(0, 3).map((source, index) => (
                            <Card
                              key={source.id}
                              size="small"
                              className="bg-gray-50"
                              bodyStyle={{ padding: '12px' }}
                            >
                              <div className="flex items-center justify-between mb-2">
                                <div className="flex items-center space-x-2">
                                  <FileTextOutlined className="text-gray-500" />
                                  <Text strong>来源 {index + 1}</Text>
                                  <Tag color="blue">{source.source_type}</Tag>
                                </div>
                                <Tag color="green">
                                  相关度: {(source.score * 100).toFixed(1)}%
                                </Tag>
                              </div>
                              <Text className="text-gray-700 text-sm">
                                {source.content_preview}
                              </Text>
                            </Card>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    <div className="mt-2">
                      <Text type="secondary" className="text-xs">
                        {formatTimestamp(msg.timestamp)}
                      </Text>
                    </div>
                  </Card>
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="flex justify-start">
                <div className="flex">
                  <Avatar
                    icon={<RobotOutlined />}
                    className="mr-3 flex-shrink-0"
                    style={{ backgroundColor: '#52c41a' }}
                  />
                  <Card className="bg-white shadow-sm" bodyStyle={{ padding: '16px' }}>
                    <div className="flex items-center space-x-2">
                      <Spin size="small" />
                      <Text className="text-gray-500">正在思考...</Text>
                    </div>
                  </Card>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* 输入区域 */}
        <div className="border-t bg-white p-4">
          <div className="max-w-4xl mx-auto">
            <div className="flex space-x-3">
              <TextArea
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="输入您的问题..."
                autoSize={{ minRows: 1, maxRows: 4 }}
                disabled={isLoading}
                className="flex-1"
              />
              <Button
                type="primary"
                icon={<SendOutlined />}
                onClick={sendMessage}
                disabled={!inputValue.trim() || isLoading}
                loading={isLoading}
                size="large"
              >
                发送
              </Button>
            </div>
            
            <div className="mt-2 text-center">
              <Text type="secondary" className="text-xs">
                按 Enter 发送消息，Shift + Enter 换行
              </Text>
            </div>
          </div>
        </div>
      </Content>
    </Layout>
  )
}
