import React, { useState, useEffect, useRef } from 'react'
import {
  Button,
  Input,
  Card,
  Space,
  Typography,
  Avatar,
  Spin,
  Tag,
  Checkbox,
  Tooltip,
  Divider,
  Progress,
  Badge,
  Select,
  message as antMessage
} from 'antd'
import {
  SendOutlined,
  RobotOutlined,
  UserOutlined,
  SearchOutlined,
  BranchesOutlined,
  ThunderboltOutlined,
  DatabaseOutlined,
  SettingOutlined,
  StarOutlined,
  CopyOutlined,
  ReloadOutlined
} from '@ant-design/icons'
import { motion, AnimatePresence } from 'framer-motion'
import ReactMarkdown from 'react-markdown'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism'
import './GeminiChatPage.css'

const { TextArea } = Input
const { Text, Title } = Typography
const { Option } = Select

interface SearchMode {
  key: string
  name: string
  description: string
  icon: React.ReactNode
  color: string
}

interface ChatMessage {
  id: string
  type: 'user' | 'assistant'
  content: string
  timestamp: Date
  searchModes?: string[]
  searchResults?: any[]
  processingTime?: number
  qualityScore?: number
}

const searchModes: SearchMode[] = [
  {
    key: 'semantic',
    name: '语义检索',
    description: '基于Qwen3-8B嵌入模型的向量相似度搜索',
    icon: <SearchOutlined />,
    color: '#1890ff'
  },
  {
    key: 'hybrid',
    name: '混合检索',
    description: '结合语义检索和关键词检索，使用RRF算法融合',
    icon: <ThunderboltOutlined />,
    color: '#52c41a'
  },
  {
    key: 'graph',
    name: '图谱检索',
    description: '基于Neo4j知识图谱的实体关系搜索',
    icon: <BranchesOutlined />,
    color: '#722ed1'
  }
]

const GeminiChatPage: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputValue, setInputValue] = useState('')
  const [selectedModes, setSelectedModes] = useState<string[]>(['semantic'])
  const [isLoading, setIsLoading] = useState(false)
  const [knowledgeBases, setKnowledgeBases] = useState<any[]>([])
  const [selectedKnowledgeBases, setSelectedKnowledgeBases] = useState<number[]>([])
  const [streamingMessage, setStreamingMessage] = useState('')
  const [currentStage, setCurrentStage] = useState('')

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<any>(null)

  useEffect(() => {
    scrollToBottom()
  }, [messages, streamingMessage])

  useEffect(() => {
    // 加载知识库列表
    loadKnowledgeBases()
  }, [])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const loadKnowledgeBases = async () => {
    try {
      // 这里应该调用API获取知识库列表
      // const response = await api.get('/knowledge-bases')
      // setKnowledgeBases(response.data)
      
      // 模拟数据
      setKnowledgeBases([
        { id: 1, name: '技术文档库', description: '包含技术相关文档' },
        { id: 2, name: '产品手册库', description: '产品使用手册和说明' },
        { id: 3, name: '法律法规库', description: '相关法律法规文档' }
      ])
    } catch (error) {
      console.error('加载知识库失败:', error)
    }
  }

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue.trim(),
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInputValue('')
    setIsLoading(true)
    setStreamingMessage('')
    setCurrentStage('正在启动多智能体协作...')

    try {
      // 调用多智能体协作API
      const response = await fetch('/api/v1/multi-agent/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          query: userMessage.content,
          search_modes: selectedModes,
          top_k: 10,
          knowledge_base_ids: selectedKnowledgeBases.length > 0 ? selectedKnowledgeBases : null
        })
      })

      if (!response.ok) {
        throw new Error('请求失败')
      }

      const result = await response.json()

      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: result.answer,
        timestamp: new Date(),
        searchModes: result.modes_used,
        searchResults: result.search_results,
        processingTime: result.processing_time,
        qualityScore: result.quality_assessment?.confidence
      }

      setMessages(prev => [...prev, assistantMessage])
      
    } catch (error) {
      console.error('发送消息失败:', error)
      antMessage.error('发送消息失败，请重试')
      
      // 添加错误消息
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: '抱歉，处理您的请求时出现了错误。请稍后重试。',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
      setCurrentStage('')
      setStreamingMessage('')
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const handleModeChange = (mode: string, checked: boolean) => {
    if (checked) {
      setSelectedModes(prev => [...prev, mode])
    } else {
      setSelectedModes(prev => prev.filter(m => m !== mode))
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    antMessage.success('已复制到剪贴板')
  }

  const renderMessage = (msg: ChatMessage) => {
    const isUser = msg.type === 'user'
    
    return (
      <motion.div
        key={msg.id}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className={`message-container ${isUser ? 'user-message' : 'assistant-message'}`}
      >
        <div className="message-avatar">
          <Avatar 
            icon={isUser ? <UserOutlined /> : <RobotOutlined />}
            style={{ 
              backgroundColor: isUser ? '#1890ff' : '#52c41a',
              color: 'white'
            }}
          />
        </div>
        
        <div className="message-content">
          <Card 
            className={`message-card ${isUser ? 'user-card' : 'assistant-card'}`}
            bodyStyle={{ padding: '16px' }}
          >
            {isUser ? (
              <Text>{msg.content}</Text>
            ) : (
              <div>
                <ReactMarkdown
                  components={{
                    code({ node, inline, className, children, ...props }) {
                      const match = /language-(\w+)/.exec(className || '')
                      return !inline && match ? (
                        <SyntaxHighlighter
                          style={tomorrow}
                          language={match[1]}
                          PreTag="div"
                          {...props}
                        >
                          {String(children).replace(/\n$/, '')}
                        </SyntaxHighlighter>
                      ) : (
                        <code className={className} {...props}>
                          {children}
                        </code>
                      )
                    }
                  }}
                >
                  {msg.content}
                </ReactMarkdown>
                
                {/* 显示检索信息 */}
                {msg.searchModes && (
                  <div className="search-info">
                    <Divider style={{ margin: '12px 0' }} />
                    <Space wrap>
                      <Text type="secondary">检索模式:</Text>
                      {msg.searchModes.map(mode => {
                        const modeInfo = searchModes.find(m => m.key === mode)
                        return (
                          <Tag key={mode} color={modeInfo?.color}>
                            {modeInfo?.icon} {modeInfo?.name}
                          </Tag>
                        )
                      })}
                    </Space>
                    
                    {msg.processingTime && (
                      <div style={{ marginTop: '8px' }}>
                        <Text type="secondary">
                          处理时间: {msg.processingTime.toFixed(2)}s
                        </Text>
                        {msg.qualityScore && (
                          <Text type="secondary" style={{ marginLeft: '16px' }}>
                            质量评分: {(msg.qualityScore * 100).toFixed(1)}%
                          </Text>
                        )}
                      </div>
                    )}
                  </div>
                )}
                
                {/* 操作按钮 */}
                <div className="message-actions">
                  <Space>
                    <Button 
                      type="text" 
                      size="small" 
                      icon={<CopyOutlined />}
                      onClick={() => copyToClipboard(msg.content)}
                    >
                      复制
                    </Button>
                    <Button 
                      type="text" 
                      size="small" 
                      icon={<StarOutlined />}
                    >
                      收藏
                    </Button>
                  </Space>
                </div>
              </div>
            )}
          </Card>
          
          <div className="message-time">
            <Text type="secondary" style={{ fontSize: '12px' }}>
              {msg.timestamp.toLocaleTimeString()}
            </Text>
          </div>
        </div>
      </motion.div>
    )
  }

  return (
    <div className="gemini-chat-container">
      {/* 头部 */}
      <div className="chat-header">
        <div className="header-content">
          <div className="header-left">
            <Avatar size="large" icon={<RobotOutlined />} style={{ backgroundColor: '#52c41a' }} />
            <div className="header-info">
              <Title level={4} style={{ margin: 0, color: 'white' }}>
                企业级RAG智能助手
              </Title>
              <Text style={{ color: 'rgba(255,255,255,0.8)', fontSize: '14px' }}>
                基于多智能体协作的知识问答系统
              </Text>
            </div>
          </div>
          
          <div className="header-right">
            <Button type="text" icon={<SettingOutlined />} style={{ color: 'white' }}>
              设置
            </Button>
          </div>
        </div>
      </div>

      {/* 检索模式选择 */}
      <div className="search-mode-selector">
        <Card size="small" style={{ margin: '16px', borderRadius: '12px' }}>
          <div style={{ marginBottom: '12px' }}>
            <Text strong>选择检索模式:</Text>
          </div>
          <Space wrap>
            {searchModes.map(mode => (
              <Checkbox
                key={mode.key}
                checked={selectedModes.includes(mode.key)}
                onChange={(e) => handleModeChange(mode.key, e.target.checked)}
              >
                <Tooltip title={mode.description}>
                  <Tag color={mode.color} style={{ margin: 0 }}>
                    {mode.icon} {mode.name}
                  </Tag>
                </Tooltip>
              </Checkbox>
            ))}
          </Space>
          
          {knowledgeBases.length > 0 && (
            <div style={{ marginTop: '12px' }}>
              <Text strong style={{ marginRight: '8px' }}>知识库:</Text>
              <Select
                mode="multiple"
                placeholder="选择知识库（可选）"
                style={{ minWidth: '200px' }}
                value={selectedKnowledgeBases}
                onChange={setSelectedKnowledgeBases}
              >
                {knowledgeBases.map(kb => (
                  <Option key={kb.id} value={kb.id}>
                    {kb.name}
                  </Option>
                ))}
              </Select>
            </div>
          )}
        </Card>
      </div>

      {/* 消息列表 */}
      <div className="messages-container">
        <AnimatePresence>
          {messages.map(renderMessage)}
        </AnimatePresence>
        
        {/* 流式消息显示 */}
        {isLoading && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="message-container assistant-message"
          >
            <div className="message-avatar">
              <Avatar icon={<RobotOutlined />} style={{ backgroundColor: '#52c41a' }} />
            </div>
            <div className="message-content">
              <Card className="message-card assistant-card">
                <Space direction="vertical" style={{ width: '100%' }}>
                  <Spin size="small" />
                  <Text type="secondary">{currentStage}</Text>
                  {streamingMessage && (
                    <ReactMarkdown>{streamingMessage}</ReactMarkdown>
                  )}
                </Space>
              </Card>
            </div>
          </motion.div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* 输入区域 */}
      <div className="input-container">
        <Card className="input-card">
          <div className="input-wrapper">
            <TextArea
              ref={inputRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="输入您的问题，支持多智能体协作问答..."
              autoSize={{ minRows: 1, maxRows: 4 }}
              style={{ 
                border: 'none',
                resize: 'none',
                fontSize: '16px'
              }}
              disabled={isLoading}
            />
            <div className="input-actions">
              <Button
                type="primary"
                icon={<SendOutlined />}
                onClick={handleSendMessage}
                loading={isLoading}
                disabled={!inputValue.trim()}
                style={{
                  borderRadius: '8px',
                  height: '40px'
                }}
              >
                发送
              </Button>
            </div>
          </div>
        </Card>
      </div>
    </div>
  )
}

export default GeminiChatPage
