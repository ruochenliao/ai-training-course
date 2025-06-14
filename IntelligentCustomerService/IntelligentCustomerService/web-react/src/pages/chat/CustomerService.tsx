import React, {useEffect, useRef, useState} from 'react'
import {Avatar, Button, Card, Input, Layout, message, Modal, Space, Tooltip, Typography} from 'antd'
import {
    Actions,
    Attachments,
    Bubble,
    Conversations,
    Prompts,
    Sender,
    Suggestion,
    ThoughtChain,
    useXAgent,
    useXChat,
    Welcome
} from '@ant-design/x'
import {
    ArrowLeftOutlined,
    DeleteOutlined,
    EditOutlined,
    MenuOutlined,
    PlusOutlined,
    QuestionCircleOutlined,
    ReloadOutlined,
    RobotOutlined,
    SendOutlined,
    SettingOutlined,
    StopOutlined,
    UserOutlined
} from '@ant-design/icons'
import {useNavigate} from 'react-router-dom'
import {useAuthStore} from '../../store/auth'
import {useTheme} from '../../contexts/ThemeContext'
import {chatApi, type ChatConversation, type ChatMessage} from '../../api/chat'
import '../../styles/chat.css'

const { Text, Title } = Typography
const { Header, Content, Sider } = Layout

/**
 * 智能客服前台页面
 * 使用 ant-design/x 重构，基于 RICH 设计范式
 * 采用最新的 useXChat 和 useXAgent 进行数据管理
 */
const CustomerService: React.FC = () => {
  const navigate = useNavigate()
  const senderRef = useRef<any>(null)

  const { user } = useAuthStore()
  const { isDark } = useTheme()

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
  const [showThinking, setShowThinking] = useState(false)
  const [attachments, setAttachments] = useState<any[]>([])

  // 使用 useXAgent 进行模型调度
  const agent = useXAgent({
    baseURL: '/api/v1/chat',
    dangerouslyApiKey: 'placeholder', // 实际使用 token 认证
  })

  // 使用 useXChat 进行数据管理
  const {
    messages: chatMessages,
    parsedMessages,
    onRequest,
    setMessages: setChatMessages
  } = useXChat({
    agent,
    defaultMessages: [],
    requestPlaceholder: () => ({
      id: `loading-${Date.now()}`,
      content: '正在思考中...',
      sender: 'assistant',
      timestamp: new Date(),
      loading: true
    }),
    requestFallback: () => ({
      id: `error-${Date.now()}`,
      content: '抱歉，我暂时无法回复您的消息，请稍后重试或联系人工客服。',
      sender: 'assistant',
      timestamp: new Date(),
      error: true
    }),
    parser: (message: any) => ({
      key: message.id || `msg-${Date.now()}`,
      role: message.sender === 'user' ? 'user' : 'assistant',
      content: message.content,
      timestamp: message.timestamp,
      loading: message.loading,
      error: message.error
    })
  })

  // 兼容原有的 messages 状态
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  // 转换消息格式为 Bubble.List 所需的格式
  const convertMessagesToBubbles = (messages: ChatMessage[]) => {
    return messages.map((message, index) => ({
      key: message.id || index.toString(),
      role: message.sender === 'user' ? 'user' : 'assistant',
      content: message.content,
      timestamp: message.timestamp,
    }))
  }

  // 转换对话列表为 Conversations 所需的格式
  const convertConversationsToItems = (conversations: ChatConversation[]) => {
    return conversations.map((conv) => ({
      key: conv.conversation_id,
      label: conv.title,
      timestamp: new Date(conv.last_message_at || conv.created_at).getTime(),
    }))
  }

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
        last_message_at: conversation.last_message_at || conversation.created_at,
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

  // 发送消息（流式）- 适配 Sender 组件
  const handleSendMessage = async (messageContent: string) => {
    if (!messageContent.trim() || !currentConversationId) return

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      content: messageContent.trim(),
      sender: 'user',
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
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
        message: messageContent.trim(),
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

  // 返回后台管理
  const handleBackToAdmin = () => {
    navigate('/dashboard/workbench')
    message.success('已返回后台管理系统')
  }

  // 快捷问题配置 - 基于 RICH 设计范式
  const quickQuestions = [
    { key: '1', label: '产品价格是多少？', description: '了解产品定价信息' },
    { key: '2', label: '有哪些功能特性？', description: '查看产品功能介绍' },
    { key: '3', label: '如何联系技术支持？', description: '获取技术支持方式' },
    { key: '4', label: '退款政策是什么？', description: '了解退款相关政策' },
    { key: '5', label: '如何联系客服？', description: '获取客服联系方式' },
  ]

  // 智能建议配置
  const suggestions = [
    { key: 'help', label: '帮助文档', icon: <QuestionCircleOutlined /> },
    { key: 'settings', label: '设置', icon: <SettingOutlined /> },
    { key: 'reload', label: '重新开始', icon: <ReloadOutlined /> },
  ]

  // 操作按钮配置
  const actionItems = [
    {
      key: 'copy',
      label: '复制',
      icon: '📋',
    },
    {
      key: 'regenerate',
      label: '重新生成',
      icon: '🔄',
    },
    {
      key: 'like',
      label: '点赞',
      icon: '👍',
    },
    {
      key: 'dislike',
      label: '点踩',
      icon: '👎',
    },
  ]

  // 处理快捷问题点击
  const handleQuickQuestion = (question: string) => {
    handleSendMessage(question)
  }

  // 处理文件上传
  const handleFileUpload = (files: File[]) => {
    const newAttachments = files.map(file => ({
      id: Date.now() + Math.random(),
      name: file.name,
      size: file.size,
      type: file.type,
      file: file
    }))
    setAttachments(prev => [...prev, ...newAttachments])
    message.success(`已添加 ${files.length} 个文件`)
  }

  // 处理思维链显示
  const handleShowThinking = (thoughts: any[]) => {
    setShowThinking(true)
    // 这里可以添加思维链的逻辑
  }

  // 处理操作按钮点击
  const handleActionClick = (action: any, messageId: string) => {
    switch (action.key) {
      case 'copy':
        const message = messages.find(msg => msg.id === messageId)
        if (message) {
          navigator.clipboard.writeText(message.content)
          message.success('已复制到剪贴板')
        }
        break
      case 'regenerate':
        // 重新生成回答
        message.info('正在重新生成回答...')
        break
      case 'like':
        message.success('感谢您的反馈！')
        break
      case 'dislike':
        message.info('我们会继续改进')
        break
      default:
        break
    }
  }

  // 获取当前对话信息
  const currentConversation = conversations.find((conv) => conv.conversation_id === currentConversationId)

  // Bubble 角色配置 - 增强版
  const bubbleRoles = {
    user: {
      placement: 'end' as const,
      avatar: {
        icon: <UserOutlined />,
        style: {
          backgroundColor: '#1890ff',
          color: '#fff'
        }
      },
      variant: 'filled' as const,
      shape: 'round' as const,
    },
    assistant: {
      placement: 'start' as const,
      avatar: {
        icon: <RobotOutlined />,
        style: {
          backgroundColor: '#52c41a',
          color: '#fff'
        }
      },
      typing: isLoading,
      variant: 'outlined' as const,
      shape: 'round' as const,
      messageRender: (content: any) => {
        // 如果是思维链内容，使用 ThoughtChain 组件
        if (content?.type === 'thinking') {
          return (
            <ThoughtChain
              items={content.thoughts || []}
              status={content.status || 'pending'}
            />
          )
        }
        return content
      },
      footer: (content: any) => {
        // 为助手消息添加操作按钮
        if (content && !isLoading) {
          return (
            <Actions
              items={actionItems}
              onActionClick={(action) => {
                console.log('Action clicked:', action)
                message.info(`执行操作: ${action.label}`)
              }}
            />
          )
        }
        return null
      }
    },
  }

  return (
    <Layout className='h-screen'>
      {/* 顶部导航栏 - 现代化设计 */}
      <Header
        className={`flex items-center justify-between px-6 shadow-sm ${isDark ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}
        style={{
          borderBottom: '1px solid',
          height: '64px',
          background: isDark
            ? 'linear-gradient(90deg, #1f2937 0%, #374151 100%)'
            : 'linear-gradient(90deg, #ffffff 0%, #f8fafc 100%)',
        }}
      >
        <div className='flex items-center'>
          <Tooltip title={sidebarVisible ? '隐藏对话列表' : '显示对话列表'}>
            <Button
              type='text'
              icon={<MenuOutlined />}
              onClick={() => setSidebarVisible(!sidebarVisible)}
              className='mr-4 hover:bg-blue-50'
              size='large'
            />
          </Tooltip>

          <Tooltip title='返回后台管理'>
            <Button
              type='text'
              icon={<ArrowLeftOutlined />}
              onClick={handleBackToAdmin}
              className='mr-4 hover:bg-blue-50'
              size='large'
            />
          </Tooltip>

          <div className='flex items-center'>
            <RobotOutlined className='text-green-500 text-xl mr-2' />
            <Title level={4} className='m-0 bg-gradient-to-r from-blue-600 to-green-600 bg-clip-text text-transparent'>
              {currentConversation?.title || '智能客服系统'}
            </Title>
          </div>
        </div>

        <div className='flex items-center space-x-3'>
          <Tooltip title='创建新对话'>
            <Button
              type='primary'
              icon={<PlusOutlined />}
              onClick={createNewConversation}
              size='small'
              className='bg-gradient-to-r from-blue-500 to-green-500 border-0 hover:from-blue-600 hover:to-green-600'
            >
              新对话
            </Button>
          </Tooltip>

          <div className='flex items-center space-x-2 px-3 py-1 rounded-full bg-gray-100 dark:bg-gray-700'>
            <Avatar
              src={user?.avatar}
              icon={<UserOutlined />}
              size='small'
              className='border-2 border-white shadow-sm'
            />
            <Text className='font-medium'>{user?.username || '用户'}</Text>
          </div>
        </div>
      </Header>

      {/* 对话列表侧边栏 */}
      <Layout>
        <Sider
          width={320}
          collapsed={!sidebarVisible}
          collapsedWidth={0}
          className={isDark ? 'bg-gray-800' : 'bg-white'}
          style={{
            borderRight: '1px solid',
            borderColor: isDark ? '#374151' : '#e5e7eb',
            background: isDark
              ? 'linear-gradient(180deg, #1f2937 0%, #111827 100%)'
              : 'linear-gradient(180deg, #ffffff 0%, #f8fafc 100%)',
          }}
        >
          <div className='p-4 h-full flex flex-col'>
            {/* 新建对话按钮 */}
            <div className='mb-4'>
              <Button
                type='primary'
                icon={<PlusOutlined />}
                onClick={createNewConversation}
                block
                size='large'
                className='bg-gradient-to-r from-blue-500 to-green-500 border-0 hover:from-blue-600 hover:to-green-600 shadow-lg'
              >
                ✨ 新建对话
              </Button>
            </div>

            {/* 对话统计 */}
            <div className='mb-4 p-3 rounded-lg bg-gradient-to-r from-blue-50 to-green-50 dark:from-gray-700 dark:to-gray-600'>
              <Space direction='vertical' size='small' className='w-full'>
                <Text className='text-sm font-medium'>📊 对话统计</Text>
                <Text className='text-xs text-gray-600 dark:text-gray-300'>
                  总对话: {conversations.length} 个
                </Text>
              </Space>
            </div>

            {/* 对话列表 */}
            <div className='flex-1 overflow-auto scrollbar-visible scroll-container scroll-fade-edges'>
              <Conversations
                activeKey={currentConversationId}
                items={convertConversationsToItems(conversations)}
                onActiveChange={(key) => switchConversation(key)}
                menu={(conversation) => ({
                  items: [
                    {
                      key: 'edit',
                      label: '编辑标题',
                      icon: <EditOutlined />,
                      onClick: () => {
                        const conv = conversations.find(c => c.conversation_id === conversation.key)
                        if (conv) startEditConversation(conv)
                      },
                    },
                    {
                      key: 'delete',
                      label: '删除对话',
                      icon: <DeleteOutlined />,
                      danger: true,
                      onClick: () => deleteConversation(conversation.key),
                    },
                  ],
                })}
                style={{
                  height: '100%',
                }}
              />
            </div>
          </div>
        </Sider>

        {/* 主要内容区域 */}
        <Content className='flex flex-col h-full'>
          {/* 聊天内容区域 */}
          <div className='flex-1 flex flex-col overflow-hidden'>
            {/* 消息列表或欢迎页面 */}
            {messages.length === 0 && isInitialized ? (
              <div className='flex-1 flex items-center justify-center p-8'>
                <div className='max-w-2xl w-full'>
                  <Welcome
                    icon={
                      <div className='relative'>
                        <RobotOutlined style={{ fontSize: 64, color: '#52c41a' }} />
                        <div className='absolute -top-2 -right-2 w-4 h-4 bg-green-500 rounded-full animate-pulse'></div>
                      </div>
                    }
                    title={
                      <div className='text-center'>
                        <Title level={2} className='mb-2'>
                          您好！我是智能客服助手 🤖
                        </Title>
                        <Text type='secondary' className='text-lg'>
                          基于 Ant Design X 的 RICH 设计范式，为您提供专业的 AI 服务支持
                        </Text>
                      </div>
                    }
                    description={
                      <div className='text-center mt-4'>
                        <Space direction='vertical' size='large' className='w-full'>
                          <Card className='bg-gradient-to-r from-blue-50 to-green-50 border-0'>
                            <Space direction='vertical' size='small' className='w-full'>
                              <Text strong>🎯 我能为您做什么：</Text>
                              <Text>• 产品咨询与技术支持</Text>
                              <Text>• 订单查询与售后服务</Text>
                              <Text>• 政策解答与问题解决</Text>
                            </Space>
                          </Card>

                          <Prompts
                            title='💡 热门问题'
                            items={quickQuestions}
                            onItemClick={(info) => handleQuickQuestion(info.data.label)}
                            wrap
                            style={{ marginTop: 16 }}
                          />
                        </Space>
                      </div>
                    }
                  />
                </div>
              </div>
            ) : (
              <div className='flex-1 overflow-auto scrollbar-visible scroll-container scroll-fade-edges p-4'>
                <div className='h-full max-w-4xl mx-auto'>
                  <Bubble.List
                    items={convertMessagesToBubbles(messages)}
                    roles={bubbleRoles}
                    autoScroll
                  />
                </div>
              </div>
            )}
          </div>

          {/* 输入区域 */}
          <div className={`border-t p-4 ${isDark ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
            <div className='max-w-4xl mx-auto'>
              <Sender
                ref={senderRef}
                value={inputValue}
                onChange={setInputValue}
                onSubmit={handleSendMessage}
                loading={isLoading}
                disabled={!currentConversationId}
                placeholder={currentConversationId ? '请输入您的问题...' : '请先选择或创建一个对话'}
                autoSize={{ minRows: 1, maxRows: 4 }}
                allowSpeech={true}
                submitType="enter"
                onPasteFile={(firstFile, files) => {
                  console.log('Files pasted:', files)
                  message.info(`已粘贴 ${files.length} 个文件`)
                }}
                header={
                  attachments.length > 0 ? (
                    <Sender.Header
                      title="附件"
                      open={true}
                      onOpenChange={() => setAttachments([])}
                    >
                      <Attachments
                        items={attachments}
                        onChange={setAttachments}
                      />
                    </Sender.Header>
                  ) : null
                }
                footer={
                  <Space size="small">
                    <Suggestion
                      items={suggestions}
                      onItemClick={(item) => {
                        console.log('Suggestion clicked:', item)
                        if (item.key === 'reload') {
                          setMessages([])
                          setInputValue('')
                          message.info('已重新开始对话')
                        }
                      }}
                    />
                  </Space>
                }
                actions={(oriNode, { components }) => (
                  <Space>
                    {isLoading ? (
                      <components.LoadingButton
                        onClick={() => {
                          setIsLoading(false)
                          message.info('已停止生成')
                        }}
                        icon={<StopOutlined />}
                      >
                        停止
                      </components.LoadingButton>
                    ) : (
                      <components.SendButton
                        disabled={!inputValue.trim() || !currentConversationId}
                        icon={<SendOutlined />}
                      >
                        发送
                      </components.SendButton>
                    )}
                  </Space>
                )}
              />
            </div>
          </div>
        </Content>
      </Layout>

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
    </Layout>
  )
}

export default CustomerService
