import React, { useEffect, useRef, useState } from 'react'
import { Avatar, Button, Card, Input, Layout, message, Space, Tooltip, Typography, Drawer } from 'antd'
import {
  Actions,
  Bubble,
  Conversations,
  Prompts,
  Sender,
  ThoughtChain,
  useXAgent,
  useXChat,
  Welcome
} from '@ant-design/x'
import {
  ArrowLeftOutlined,
  MenuOutlined,
  PlusOutlined,
  RobotOutlined,
  SendOutlined,
  StopOutlined,
  UserOutlined,
  StarOutlined,
  ThunderboltOutlined,
  BulbOutlined,
  HeartOutlined,
  PictureOutlined,
  SettingOutlined,
  MagicWandOutlined,
  FileTextOutlined,
  ApiOutlined
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../../store/auth'
import { useTheme } from '../../contexts/ThemeContext'
import { chatApi, type ChatConversation, type ChatMessage } from '../../api/chat'
import MultimodalSupport from './MultimodalSupport'
import SmartSuggestions from './SmartSuggestions'
import DocumentProcessor from '../document/DocumentProcessor'
import MCPToolPanel from '../mcp/MCPToolPanel'
import '../../styles/chat.css'
import './GeminiChatInterface.css'

const { Text, Title } = Typography
const { Header, Content, Sider } = Layout

interface GeminiChatInterfaceProps {
  conversations: ChatConversation[]
  currentConversationId: string
  messages: ChatMessage[]
  isLoading: boolean
  onSendMessage: (message: string) => void
  onCreateConversation: () => void
  onSwitchConversation: (id: string) => void
  onDeleteConversation: (id: string) => void
}

/**
 * Gemini风格聊天界面组件
 * 基于 Ant Design X 和 RICH 设计范式
 * 提供炫酷的视觉效果和流畅的用户体验
 */
const GeminiChatInterface: React.FC<GeminiChatInterfaceProps> = ({
  conversations,
  currentConversationId,
  messages,
  isLoading,
  onSendMessage,
  onCreateConversation,
  onSwitchConversation,
  onDeleteConversation
}) => {
  const navigate = useNavigate()
  const senderRef = useRef<any>(null)
  const { user } = useAuthStore()
  const { isDark } = useTheme()

  // UI状态
  const [sidebarVisible, setSidebarVisible] = useState(false)
  const [inputValue, setInputValue] = useState('')
  const [showSparkles, setShowSparkles] = useState(false)
  const [multimodalVisible, setMultimodalVisible] = useState(false)
  const [suggestionsVisible, setSuggestionsVisible] = useState(false)
  const [documentVisible, setDocumentVisible] = useState(false)
  const [mcpToolsVisible, setMcpToolsVisible] = useState(false)
  const [mcpSessionId, setMcpSessionId] = useState<string>('')
  const [uploadedFiles, setUploadedFiles] = useState<any[]>([])
  const [userContext, setUserContext] = useState({
    recentTopics: ['技术支持', '产品咨询'],
    preferences: ['AI助手', '智能分析'],
    conversationHistory: messages
  })

  // 使用 useXAgent 进行模型调度
  const agent = useXAgent({
    baseURL: '/api/v1/chat',
    dangerouslyApiKey: 'placeholder',
  })

  // 使用 useXChat 进行数据管理
  const {
    onRequest,
  } = useXChat({
    agent,
    defaultMessages: [],
  })

  // Gemini风格快捷问题
  const geminiPrompts = [
    { 
      key: '1', 
      label: '✨ 帮我解决技术问题', 
      description: '获取专业的技术支持和解决方案',
      icon: <ThunderboltOutlined />
    },
    { 
      key: '2', 
      label: '🎯 产品功能咨询', 
      description: '了解产品特性和使用方法',
      icon: <BulbOutlined />
    },
    { 
      key: '3', 
      label: '💡 创意建议和灵感', 
      description: '获取创新想法和建议',
      icon: <StarOutlined />
    },
    { 
      key: '4', 
      label: '❤️ 客户服务支持', 
      description: '专业的客户服务和售后支持',
      icon: <HeartOutlined />
    },
  ]

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

  // 处理发送消息
  const handleSendMessage = async (messageContent: string) => {
    if (!messageContent.trim()) return
    
    setShowSparkles(true)
    setTimeout(() => setShowSparkles(false), 2000)
    
    await onSendMessage(messageContent.trim())
    setInputValue('')
  }

  // 处理快捷问题点击
  const handlePromptClick = (prompt: any) => {
    handleSendMessage(prompt.data.label.replace(/^[✨🎯💡❤️]\s*/, ''))
  }

  // 处理智能建议点击
  const handleSuggestionClick = (suggestion: any) => {
    handleSendMessage(suggestion.text.replace(/^[✨🎯💡❤️🚀🔥👑🎁]\s*/, ''))
    setSuggestionsVisible(false)
  }

  // 处理文件分析
  const handleFileAnalyze = (file: any) => {
    const analysisPrompt = `请分析这个文件：${file.name}（${file.type}），文件大小：${(file.size / 1024 / 1024).toFixed(2)}MB`
    handleSendMessage(analysisPrompt)
    setMultimodalVisible(false)
  }

  // 处理文档处理完成
  const handleDocumentProcessed = (document: any) => {
    message.success(`文档 ${document.filename} 处理完成`)
    // 可以在这里添加更多逻辑，比如自动提问
  }

  // 处理文档搜索
  const handleDocumentSearch = (query: string) => {
    if (query.trim()) {
      handleSendMessage(`在文档中搜索：${query}`)
    }
    setDocumentVisible(false)
  }

  // 处理MCP工具调用
  const handleMCPToolCall = (toolName: string, parameters: any, result: any) => {
    const toolMessage = `使用工具 ${toolName}，参数：${JSON.stringify(parameters, null, 2)}`
    handleSendMessage(toolMessage)
    message.success(`工具 ${toolName} 调用成功`)
  }

  // 创建MCP会话
  const createMCPSession = async () => {
    if (!currentConversationId) {
      message.warning('请先创建对话')
      return
    }

    try {
      const response = await fetch('/api/v1/mcp/session', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          conversation_id: currentConversationId
        })
      })

      if (response.ok) {
        const data = await response.json()
        setMcpSessionId(data.session_id)
        message.success('MCP会话创建成功')
      } else {
        message.error('MCP会话创建失败')
      }
    } catch (error) {
      message.error('MCP会话创建失败')
    }
  }

  // 更新用户上下文
  useEffect(() => {
    setUserContext(prev => ({
      ...prev,
      conversationHistory: messages,
      recentTopics: extractTopicsFromMessages(messages)
    }))
  }, [messages])

  // 从消息中提取话题
  const extractTopicsFromMessages = (messages: ChatMessage[]) => {
    const topics = new Set<string>()
    messages.forEach(msg => {
      if (msg.content.includes('技术')) topics.add('技术支持')
      if (msg.content.includes('产品')) topics.add('产品咨询')
      if (msg.content.includes('价格')) topics.add('价格咨询')
      if (msg.content.includes('功能')) topics.add('功能介绍')
    })
    return Array.from(topics).slice(0, 5)
  }

  // 获取当前对话信息
  const currentConversation = conversations.find((conv) => conv.conversation_id === currentConversationId)

  // Gemini风格 Bubble 角色配置
  const geminiRoles = {
    user: {
      placement: 'end' as const,
      avatar: {
        icon: <UserOutlined />,
        style: {
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: '#fff',
          border: '2px solid rgba(255, 255, 255, 0.3)',
          boxShadow: '0 4px 16px rgba(102, 126, 234, 0.3)'
        }
      },
      variant: 'filled' as const,
      shape: 'round' as const,
      style: {
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: 'white',
        borderRadius: '18px 18px 4px 18px',
        boxShadow: '0 4px 16px rgba(102, 126, 234, 0.3)',
        border: '1px solid rgba(255, 255, 255, 0.2)'
      }
    },
    assistant: {
      placement: 'start' as const,
      avatar: {
        icon: <RobotOutlined />,
        style: {
          background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
          color: '#fff',
          border: '2px solid rgba(255, 255, 255, 0.3)',
          boxShadow: '0 4px 16px rgba(240, 147, 251, 0.3)'
        }
      },
      typing: isLoading,
      variant: 'outlined' as const,
      shape: 'round' as const,
      style: {
        background: 'rgba(255, 255, 255, 0.1)',
        backdropFilter: 'blur(20px)',
        border: '1px solid rgba(255, 255, 255, 0.2)',
        borderRadius: '18px 18px 18px 4px',
        boxShadow: '0 4px 16px rgba(240, 147, 251, 0.2)',
        color: isDark ? '#fff' : '#333'
      },
      footer: (content: any) => {
        if (content && !isLoading) {
          return (
            <Actions
              items={[
                { key: 'copy', label: '复制', icon: '📋' },
                { key: 'regenerate', label: '重新生成', icon: '🔄' },
                { key: 'like', label: '点赞', icon: '👍' },
                { key: 'share', label: '分享', icon: '🔗' },
              ]}
              onActionClick={(action) => {
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
    <Layout className={`h-screen gemini-chat-container ${isDark ? 'dark' : ''}`}>
      {/* Gemini风格顶部导航栏 */}
      <Header className={`gemini-header ${isDark ? 'dark' : ''}`}>
        <div className='flex items-center'>
          <Tooltip title={sidebarVisible ? '隐藏对话列表' : '显示对话列表'}>
            <Button
              type='text'
              icon={<MenuOutlined />}
              onClick={() => setSidebarVisible(!sidebarVisible)}
              className='gemini-nav-btn mr-4'
              size='large'
            />
          </Tooltip>

          <Tooltip title='返回后台管理'>
            <Button
              type='text'
              icon={<ArrowLeftOutlined />}
              onClick={() => navigate('/dashboard/workbench')}
              className='gemini-nav-btn mr-4'
              size='large'
            />
          </Tooltip>

          <div className='flex items-center'>
            <div className={`gemini-logo ${showSparkles ? 'sparkle' : ''}`}>
              <RobotOutlined className='text-2xl mr-3' />
            </div>
            <Title level={3} className='m-0 gemini-title'>
              {currentConversation?.title || 'Gemini AI Assistant'}
            </Title>
          </div>
        </div>

        <div className='flex items-center space-x-4'>
          <Tooltip title='多模态支持'>
            <Button
              type='text'
              icon={<PictureOutlined />}
              onClick={() => setMultimodalVisible(true)}
              className='gemini-nav-btn'
            />
          </Tooltip>

          <Tooltip title='智能建议'>
            <Button
              type='text'
              icon={<MagicWandOutlined />}
              onClick={() => setSuggestionsVisible(true)}
              className='gemini-nav-btn'
            />
          </Tooltip>

          <Tooltip title='文档处理'>
            <Button
              type='text'
              icon={<FileTextOutlined />}
              onClick={() => setDocumentVisible(true)}
              className='gemini-nav-btn'
            />
          </Tooltip>

          <Tooltip title='MCP工具'>
            <Button
              type='text'
              icon={<ApiOutlined />}
              onClick={() => {
                setMcpToolsVisible(true)
                if (!mcpSessionId) {
                  createMCPSession()
                }
              }}
              className='gemini-nav-btn'
            />
          </Tooltip>

          <Tooltip title='创建新对话'>
            <Button
              type='primary'
              icon={<PlusOutlined />}
              onClick={onCreateConversation}
              className='gemini-primary-btn'
            >
              新对话
            </Button>
          </Tooltip>

          <div className='gemini-user-info'>
            <Avatar
              src={user?.avatar}
              icon={<UserOutlined />}
              size='default'
              className='gemini-avatar'
            />
            <Text className='font-medium text-white ml-2'>{user?.username || '用户'}</Text>
          </div>
        </div>
      </Header>

      <Layout>
        {/* Gemini风格侧边栏 */}
        <Sider
          width={360}
          collapsed={!sidebarVisible}
          collapsedWidth={0}
          className={`gemini-sidebar ${isDark ? 'dark' : ''}`}
        >
          <div className='p-6 h-full flex flex-col'>
            <div className='mb-6'>
              <Button
                type='primary'
                icon={<PlusOutlined />}
                onClick={onCreateConversation}
                block
                size='large'
                className='gemini-new-chat-btn'
              >
                ✨ 开始新对话
              </Button>
            </div>

            <div className='flex-1 overflow-auto'>
              <Conversations
                activeKey={currentConversationId}
                items={convertConversationsToItems(conversations)}
                onActiveChange={onSwitchConversation}
                className='gemini-conversations'
              />
            </div>
          </div>
        </Sider>

        {/* 主要内容区域 */}
        <Content className='flex flex-col h-full gemini-content'>
          {/* 消息列表或欢迎页面 */}
          {messages.length === 0 ? (
            <div className='flex-1 flex items-center justify-center p-8'>
              <div className='max-w-3xl w-full'>
                <Welcome
                  icon={
                    <div className='gemini-welcome-icon'>
                      <RobotOutlined style={{ fontSize: 80 }} />
                      <div className='gemini-sparkles'></div>
                    </div>
                  }
                  title={
                    <div className='text-center'>
                      <Title level={1} className='gemini-welcome-title mb-4'>
                        Hello! I'm Gemini AI 🌟
                      </Title>
                      <Text className='text-xl gemini-welcome-subtitle'>
                        基于最新AI技术，为您提供智能、创新的对话体验
                      </Text>
                    </div>
                  }
                  description={
                    <div className='mt-8'>
                      <Prompts
                        title='💫 开始对话'
                        items={geminiPrompts}
                        onItemClick={handlePromptClick}
                        wrap
                        className='gemini-prompts'
                      />
                    </div>
                  }
                />
              </div>
            </div>
          ) : (
            <div className='flex-1 overflow-auto p-6'>
              <div className='max-w-4xl mx-auto'>
                <Bubble.List
                  items={convertMessagesToBubbles(messages)}
                  roles={geminiRoles}
                  autoScroll
                />
              </div>
            </div>
          )}

          {/* Gemini风格输入区域 */}
          <div className='gemini-input-area p-6'>
            <div className='max-w-4xl mx-auto'>
              <Sender
                ref={senderRef}
                value={inputValue}
                onChange={setInputValue}
                onSubmit={handleSendMessage}
                loading={isLoading}
                disabled={!currentConversationId}
                placeholder={currentConversationId ? '与 Gemini AI 对话...' : '请先选择或创建一个对话'}
                autoSize={{ minRows: 1, maxRows: 6 }}
                allowSpeech={true}
                submitType="enter"
                className='gemini-sender'
                actions={(oriNode, { components }) => (
                  <Space>
                    {isLoading ? (
                      <components.LoadingButton
                        onClick={() => message.info('已停止生成')}
                        icon={<StopOutlined />}
                        className='gemini-stop-btn'
                      >
                        停止
                      </components.LoadingButton>
                    ) : (
                      <components.SendButton
                        disabled={!inputValue.trim() || !currentConversationId}
                        icon={<SendOutlined />}
                        className='gemini-send-btn'
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

      {/* 多模态支持抽屉 */}
      <Drawer
        title={
          <div style={{ color: 'rgba(255, 255, 255, 0.9)' }}>
            <PictureOutlined style={{ marginRight: 8 }} />
            多模态内容支持
          </div>
        }
        placement="right"
        width={480}
        open={multimodalVisible}
        onClose={() => setMultimodalVisible(false)}
        className="gemini-drawer"
        style={{
          background: 'rgba(15, 15, 35, 0.95)',
          backdropFilter: 'blur(40px)'
        }}
        headerStyle={{
          background: 'rgba(102, 126, 234, 0.2)',
          borderBottom: '1px solid rgba(255, 255, 255, 0.1)'
        }}
        bodyStyle={{
          background: 'transparent',
          padding: '24px'
        }}
      >
        <MultimodalSupport
          files={uploadedFiles}
          onFilesChange={setUploadedFiles}
          onAnalyze={handleFileAnalyze}
          maxFiles={10}
          maxSize={50}
        />
      </Drawer>

      {/* 智能建议抽屉 */}
      <Drawer
        title={
          <div style={{ color: 'rgba(255, 255, 255, 0.9)' }}>
            <MagicWandOutlined style={{ marginRight: 8 }} />
            智能建议
          </div>
        }
        placement="right"
        width={600}
        open={suggestionsVisible}
        onClose={() => setSuggestionsVisible(false)}
        className="gemini-drawer"
        style={{
          background: 'rgba(15, 15, 35, 0.95)',
          backdropFilter: 'blur(40px)'
        }}
        headerStyle={{
          background: 'rgba(240, 147, 251, 0.2)',
          borderBottom: '1px solid rgba(255, 255, 255, 0.1)'
        }}
        bodyStyle={{
          background: 'transparent',
          padding: '24px'
        }}
      >
        <SmartSuggestions
          onSuggestionClick={handleSuggestionClick}
          userContext={userContext}
        />
      </Drawer>

      {/* 文档处理抽屉 */}
      <Drawer
        title={
          <div style={{ color: 'rgba(255, 255, 255, 0.9)' }}>
            <FileTextOutlined style={{ marginRight: 8 }} />
            文档处理器
          </div>
        }
        placement="right"
        width={720}
        open={documentVisible}
        onClose={() => setDocumentVisible(false)}
        className="gemini-drawer"
        style={{
          background: 'rgba(15, 15, 35, 0.95)',
          backdropFilter: 'blur(40px)'
        }}
        headerStyle={{
          background: 'rgba(52, 199, 89, 0.2)',
          borderBottom: '1px solid rgba(255, 255, 255, 0.1)'
        }}
        bodyStyle={{
          background: 'transparent',
          padding: '24px'
        }}
      >
        <DocumentProcessor
          conversationId={currentConversationId}
          onDocumentProcessed={handleDocumentProcessed}
          onDocumentSearch={handleDocumentSearch}
        />
      </Drawer>

      {/* MCP工具抽屉 */}
      <Drawer
        title={
          <div style={{ color: 'rgba(255, 255, 255, 0.9)' }}>
            <ApiOutlined style={{ marginRight: 8 }} />
            MCP工具面板
          </div>
        }
        placement="right"
        width={800}
        open={mcpToolsVisible}
        onClose={() => setMcpToolsVisible(false)}
        className="gemini-drawer"
        style={{
          background: 'rgba(15, 15, 35, 0.95)',
          backdropFilter: 'blur(40px)'
        }}
        headerStyle={{
          background: 'rgba(24, 144, 255, 0.2)',
          borderBottom: '1px solid rgba(255, 255, 255, 0.1)'
        }}
        bodyStyle={{
          background: 'transparent',
          padding: '24px'
        }}
      >
        <MCPToolPanel
          sessionId={mcpSessionId}
          onToolCall={handleMCPToolCall}
        />
      </Drawer>
    </Layout>
  )
}

export default GeminiChatInterface
