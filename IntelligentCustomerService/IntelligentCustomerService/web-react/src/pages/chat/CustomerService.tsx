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
import GeminiChatInterface from '../../components/chat/GeminiChatInterface'
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
  const [editingConversationId, setEditingConversationId] = useState<string>('')
  const [editingTitle, setEditingTitle] = useState('')
  const [isEditModalVisible, setIsEditModalVisible] = useState(false)

  // 兼容原有的 messages 状态
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)



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

    // 清空输入框
    setInputValue('')

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
                // 根据发送者类型处理消息内容
                if (parsed.sender === 'user') {
                  // 用户消息：不处理，因为前端已经添加了
                  return
                } else {
                  // 助手消息：累积内容
                  setMessages((prev) => prev.map((msg) => (msg.id === assistantMessageId ? { ...msg, content: msg.content + parsed.content } : msg)))
                }
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



  // 使用新的Gemini风格界面
  return (
    <>
      <GeminiChatInterface
        conversations={conversations}
        currentConversationId={currentConversationId}
        messages={messages}
        isLoading={isLoading}
        onSendMessage={handleSendMessage}
        onCreateConversation={createNewConversation}
        onSwitchConversation={switchConversation}
        onDeleteConversation={deleteConversation}
      />

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
    </>
  )

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
