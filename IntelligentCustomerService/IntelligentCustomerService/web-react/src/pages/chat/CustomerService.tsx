import React, { useEffect, useRef, useState } from 'react'
import { Avatar, Button, Card, Drawer, Empty, Input, Layout, List, message, Modal, Popconfirm, Spin, Tooltip, Typography } from 'antd'
import {
  ArrowLeftOutlined,
  ClockCircleOutlined,
  DeleteOutlined,
  EditOutlined,
  MenuOutlined,
  MessageOutlined,
  PlusOutlined,
  RobotOutlined,
  SendOutlined,
  UserOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../../store/auth'
import { useTheme } from '../../contexts/ThemeContext'
import { chatApi, type ChatConversation, type ChatMessage } from '../../api/chat'
import '../../styles/chat.css'

const { TextArea } = Input
const { Text, Title } = Typography
const { Header, Content } = Layout

/**
 * 智能客服前台页面
 * 参考ollama-webui-lite的简洁设计风格
 */
const CustomerService: React.FC = () => {
  const navigate = useNavigate()

  const { user } = useAuthStore()
  const { isDark } = useTheme()

  // 消息相关状态
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  // 对话相关状态
  const [conversations, setConversations] = useState<ChatConversation[]>([])
  const [currentConversationId, setCurrentConversationId] = useState<string>('')
  const [isInitialized, setIsInitialized] = useState(false)
  const [conversationsLoading, setConversationsLoading] = useState(false)

  // UI状态
  const [sidebarVisible, setSidebarVisible] = useState(false)
  const [editingConversationId, setEditingConversationId] = useState<string>('')
  const [editingTitle, setEditingTitle] = useState('')
  const [isEditModalVisible, setIsEditModalVisible] = useState(false)

  const messagesEndRef = useRef<HTMLDivElement>(null)

  // 自动滚动到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // 初始化：加载对话列表
  useEffect(() => {
    const initializeApp = async () => {
      try {
        await loadConversations()
        setIsInitialized(true)
      } catch (error) {
        console.error('初始化失败:', error)
        message.error('初始化失败，请刷新页面重试')
      }
    }

    if (!isInitialized) {
      initializeApp()
    }
  }, [isInitialized])

  // 加载对话列表
  const loadConversations = async () => {
    setConversationsLoading(true)
    try {
      const response = await chatApi.getConversations(1, 50)
      setConversations(response.data || [])

      // 如果有对话，选择第一个；否则创建新对话
      if (response.data && response.data.length > 0) {
        const firstConversation = response.data[0]
        setCurrentConversationId(firstConversation.conversation_id)
        await loadConversationMessages(firstConversation.conversation_id)
      } else {
        await createNewConversation()
      }
    } catch (error) {
      console.error('加载对话列表失败:', error)
      message.error('加载对话列表失败')
    } finally {
      setConversationsLoading(false)
    }
  }

  // 创建新对话
  const createNewConversation = async () => {
    try {
      const conversation = await chatApi.createConversation('新对话')
      const newConversation: ChatConversation = {
        id: conversation.id,
        conversation_id: conversation.conversation_id,
        user_id: conversation.user_id,
        title: conversation.title,
        is_active: conversation.is_active,
        last_message_at: conversation.last_message_at,
        created_at: conversation.created_at,
        updated_at: conversation.updated_at,
      }

      setConversations((prev) => [newConversation, ...prev])
      setCurrentConversationId(conversation.conversation_id)

      // 添加欢迎消息
      setMessages([
        {
          id: 'welcome',
          content: '您好！我是智能客服助手，有什么可以帮助您的吗？',
          sender: 'assistant',
          timestamp: new Date(),
        },
      ])

      message.success('新对话创建成功')
      setSidebarVisible(false)
    } catch (error) {
      console.error('创建对话失败:', error)
      message.error('创建对话失败')
    }
  }

  // 切换对话
  const switchConversation = async (conversationId: string) => {
    if (conversationId === currentConversationId) return

    setCurrentConversationId(conversationId)
    await loadConversationMessages(conversationId)
    setSidebarVisible(false)
  }

  // 加载对话消息
  const loadConversationMessages = async (conversationId: string) => {
    try {
      const messages = await chatApi.getConversationMessages(conversationId)
      setMessages(messages)
    } catch (error) {
      console.error('加载消息失败:', error)
      message.error('加载消息失败')
      // 如果加载失败，显示欢迎消息
      setMessages([
        {
          id: 'welcome',
          content: '您好！我是智能客服助手，有什么可以帮助您的吗？',
          sender: 'assistant',
          timestamp: new Date(),
        },
      ])
    }
  }

  // 删除对话
  const deleteConversation = async (conversationId: string) => {
    try {
      await chatApi.deleteConversation(conversationId)

      const updatedConversations = conversations.filter((conv) => conv.conversation_id !== conversationId)
      setConversations(updatedConversations)

      // 如果删除的是当前对话
      if (conversationId === currentConversationId) {
        if (updatedConversations.length > 0) {
          // 切换到第一个对话
          const firstConversation = updatedConversations[0]
          setCurrentConversationId(firstConversation.conversation_id)
          await loadConversationMessages(firstConversation.conversation_id)
        } else {
          // 创建新对话
          await createNewConversation()
        }
      }

      message.success('对话删除成功')
    } catch (error) {
      console.error('删除对话失败:', error)
      message.error('删除对话失败')
    }
  }

  // 编辑对话标题
  const startEditConversation = (conversation: ChatConversation) => {
    setEditingConversationId(conversation.conversation_id)
    setEditingTitle(conversation.title)
    setIsEditModalVisible(true)
  }

  // 保存对话标题
  const saveConversationTitle = async () => {
    if (!editingTitle.trim()) {
      message.warning('对话标题不能为空')
      return
    }

    try {
      await chatApi.updateConversation(editingConversationId, editingTitle.trim())

      setConversations((prev) =>
        prev.map((conv) => (conv.conversation_id === editingConversationId ? { ...conv, title: editingTitle.trim() } : conv)),
      )

      setIsEditModalVisible(false)
      setEditingConversationId('')
      setEditingTitle('')
      message.success('对话标题更新成功')
    } catch (error) {
      console.error('更新对话标题失败:', error)
      message.error('更新对话标题失败')
    }
  }

  // 发送消息（流式）
  const handleSendMessage = async () => {
    if (!inputValue.trim() || !currentConversationId) return

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      content: inputValue.trim(),
      sender: 'user',
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    const messageContent = inputValue.trim()
    setInputValue('')
    setIsLoading(true)

    // 创建助手消息占位符
    const assistantMessageId = `msg_${Date.now()}_assistant`
    const assistantMessage: ChatMessage = {
      id: assistantMessageId,
      content: '',
      sender: 'assistant',
      timestamp: new Date(),
    }
    setMessages((prev) => [...prev, assistantMessage])

    try {
      // 调用流式API
      const stream = await chatApi.sendMessageStream({
        message: messageContent,
        conversation_id: currentConversationId,
      })

      const reader = stream.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      // eslint-disable-next-line no-constant-condition
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')

        // 保留最后一行（可能不完整）
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6).trim()
            if (data === '[DONE]') {
              setIsLoading(false)
              return
            }

            try {
              const parsed = JSON.parse(data)
              if (parsed.error) {
                throw new Error(parsed.error)
              }

              if (parsed.content) {
                // 更新助手消息内容
                setMessages((prev) => prev.map((msg) => (msg.id === assistantMessageId ? { ...msg, content: msg.content + parsed.content } : msg)))
              }

              // 如果是完成标志，停止加载
              if (parsed.is_complete) {
                setIsLoading(false)
              }
            } catch (parseError) {
              console.error('解析流式数据失败:', parseError, 'data:', data)
            }
          }
        }
      }
    } catch (error) {
      console.error('发送消息失败:', error)
      message.error('发送消息失败，请稍后重试')

      // 更新助手消息为错误提示
      setMessages((prev) =>
        prev.map((msg) => (msg.id === assistantMessageId ? { ...msg, content: '抱歉，我暂时无法回复您的消息，请稍后重试或联系人工客服。' } : msg)),
      )
    } finally {
      setIsLoading(false)
    }
  }

  // 处理键盘事件
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  // 返回后台管理
  const handleBackToAdmin = () => {
    navigate('/dashboard/workbench')
    message.success('已返回后台管理系统')
  }

  // 快捷问题
  const quickQuestions = ['产品价格是多少？', '有哪些功能特性？', '如何联系技术支持？', '退款政策是什么？', '如何联系客服？']

  // 处理快捷问题点击
  const handleQuickQuestion = (question: string) => {
    setInputValue(question)
  }

  // 获取当前对话信息
  const currentConversation = conversations.find((conv) => conv.conversation_id === currentConversationId)

  return (
    <Layout className='h-screen'>
      {/* 顶部导航栏 */}
      <Header
        className={`flex items-center justify-between px-6 ${isDark ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}
        style={{
          borderBottom: '1px solid',
          height: '64px',
        }}
      >
        <div className='flex items-center'>
          <Button type='text' icon={<MenuOutlined />} onClick={() => setSidebarVisible(true)} className='mr-4'>
            对话列表
          </Button>
          <Button type='text' icon={<ArrowLeftOutlined />} onClick={handleBackToAdmin} className='mr-4'>
            返回后台
          </Button>
          <Title level={4} className='m-0'>
            {currentConversation?.title || '智能客服系统'}
          </Title>
        </div>

        <div className='flex items-center'>
          <Button type='primary' icon={<PlusOutlined />} onClick={createNewConversation} className='mr-4' size='small'>
            新对话
          </Button>
          <Avatar src={user?.avatar} icon={<UserOutlined />} size='small' className='mr-2' />
          <Text>{user?.username || '用户'}</Text>
        </div>
      </Header>

      {/* 对话列表侧边栏 */}
      <Drawer
        title='对话历史'
        placement='left'
        onClose={() => setSidebarVisible(false)}
        open={sidebarVisible}
        width={320}
        className={isDark ? 'dark-drawer' : ''}
      >
        <div className='mb-4'>
          <Button type='primary' icon={<PlusOutlined />} onClick={createNewConversation} block>
            新建对话
          </Button>
        </div>

        <Spin spinning={conversationsLoading}>
          {conversations.length === 0 ? (
            <Empty description='暂无对话历史' image={Empty.PRESENTED_IMAGE_SIMPLE} />
          ) : (
            <List
              dataSource={conversations}
              renderItem={(conversation) => (
                <List.Item
                  className={`conversation-item cursor-pointer p-3 ${
                    conversation.conversation_id === currentConversationId ? 'active' : ''
                  } ${isDark ? 'dark' : ''}`}
                  onClick={() => switchConversation(conversation.conversation_id)}
                >
                  <div className='w-full'>
                    <div className='flex items-center justify-between'>
                      <div className='flex-1 min-w-0'>
                        <div className='flex items-center'>
                          <MessageOutlined className='mr-2 text-blue-500' />
                          <Text
                            className={`conversation-title truncate ${
                              conversation.conversation_id === currentConversationId ? 'active' : ''
                            } ${isDark ? 'dark' : ''}`}
                          >
                            {conversation.title}
                          </Text>
                        </div>
                        <div className={`conversation-time flex items-center mt-1 ${isDark ? 'dark' : ''}`}>
                          <ClockCircleOutlined className='mr-1' />
                          {conversation.last_message_at
                            ? new Date(conversation.last_message_at).toLocaleString()
                            : new Date(conversation.created_at).toLocaleString()}
                        </div>
                      </div>
                      <div className='flex items-center ml-2'>
                        <Tooltip title='编辑标题'>
                          <Button
                            type='text'
                            size='small'
                            icon={<EditOutlined />}
                            onClick={(e) => {
                              e.stopPropagation()
                              startEditConversation(conversation)
                            }}
                          />
                        </Tooltip>
                        <Tooltip title='删除对话'>
                          <Popconfirm
                            title='确定要删除这个对话吗？'
                            description='删除后将无法恢复'
                            onConfirm={(e) => {
                              e?.stopPropagation()
                              deleteConversation(conversation.conversation_id)
                            }}
                            onCancel={(e) => e?.stopPropagation()}
                            okText='确定'
                            cancelText='取消'
                          >
                            <Button type='text' size='small' icon={<DeleteOutlined />} danger onClick={(e) => e.stopPropagation()} />
                          </Popconfirm>
                        </Tooltip>
                      </div>
                    </div>
                  </div>
                </List.Item>
              )}
            />
          )}
        </Spin>
      </Drawer>

      {/* 编辑对话标题模态框 */}
      <Modal
        title='编辑对话标题'
        open={isEditModalVisible}
        onOk={saveConversationTitle}
        onCancel={() => {
          setIsEditModalVisible(false)
          setEditingConversationId('')
          setEditingTitle('')
        }}
        okText='保存'
        cancelText='取消'
      >
        <Input
          value={editingTitle}
          onChange={(e) => setEditingTitle(e.target.value)}
          placeholder='请输入对话标题'
          maxLength={50}
          onPressEnter={saveConversationTitle}
        />
      </Modal>

      {/* 聊天内容区域 */}
      <Content className='flex flex-col h-full'>
        <div className='flex-1 overflow-hidden'>
          {/* 消息列表 */}
          <div
            className='h-full overflow-y-auto p-4'
            style={{
              background: isDark ? '#1f1f1f' : '#f5f5f5',
            }}
          >
            <div className='max-w-4xl mx-auto space-y-4'>
              {messages.map((message) => (
                <div key={message.id} className={`message-bubble flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`flex max-w-[70%] ${message.sender === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                    <Avatar
                      icon={message.sender === 'user' ? <UserOutlined /> : <RobotOutlined />}
                      className={`${message.sender === 'user' ? 'ml-3' : 'mr-3'} flex-shrink-0`}
                      style={{
                        backgroundColor: message.sender === 'user' ? '#1890ff' : '#52c41a',
                      }}
                    />
                    <Card
                      size='small'
                      className={`${message.sender === 'user' ? 'bg-blue-500 text-white' : isDark ? 'bg-gray-700 text-white' : 'bg-white'}`}
                      bodyStyle={{ padding: '12px 16px' }}
                    >
                      <div className='whitespace-pre-wrap'>{message.content}</div>
                      <div className={`text-xs mt-2 ${message.sender === 'user' ? 'text-blue-100' : isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                        {message.timestamp.toLocaleTimeString()}
                      </div>
                    </Card>
                  </div>
                </div>
              ))}

              {/* 加载指示器 */}
              {isLoading && (
                <div className='message-bubble flex justify-start'>
                  <div className='flex'>
                    <Avatar icon={<RobotOutlined />} className='mr-3 flex-shrink-0' style={{ backgroundColor: '#52c41a' }} />
                    <Card size='small' className={isDark ? 'bg-gray-700' : 'bg-white'} bodyStyle={{ padding: '12px 16px' }}>
                      <div className='typing-indicator'>
                        <div className='typing-dot'></div>
                        <div className='typing-dot'></div>
                        <div className='typing-dot'></div>
                        <Text className={`ml-2 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>正在输入...</Text>
                      </div>
                    </Card>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          </div>

          {/* 快捷问题 */}
          {messages.length <= 1 && isInitialized && currentConversationId && (
            <div className='max-w-4xl mx-auto px-4 pb-4'>
              <div className={`p-4 rounded-lg ${isDark ? 'bg-gray-800' : 'bg-white'}`}>
                <Text className='block mb-3 font-medium'>常见问题：</Text>
                <div className='flex flex-wrap gap-2'>
                  {quickQuestions.map((question, index) => (
                    <Button
                      key={index}
                      size='small'
                      onClick={() => handleQuickQuestion(question)}
                      className='text-left'
                      style={{ height: 'auto', padding: '6px 12px', whiteSpace: 'normal' }}
                    >
                      {question}
                    </Button>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* 输入区域 */}
        <div className={`border-t p-4 ${isDark ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
          <div className='max-w-4xl mx-auto'>
            <div className='flex space-x-3'>
              <TextArea
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={currentConversationId ? '请输入您的问题...' : '请先选择或创建一个对话'}
                autoSize={{ minRows: 1, maxRows: 4 }}
                className='flex-1'
                disabled={isLoading || !currentConversationId}
              />
              <Button
                type='primary'
                icon={<SendOutlined />}
                onClick={handleSendMessage}
                loading={isLoading}
                disabled={!inputValue.trim() || !currentConversationId}
                size='large'
              >
                发送
              </Button>
            </div>

            <div className='flex justify-center mt-3'>
              <Text type='secondary' className='text-xs'>
                按 Enter 发送消息，Shift + Enter 换行
              </Text>
            </div>
          </div>
        </div>
      </Content>
    </Layout>
  )
}

export default CustomerService
