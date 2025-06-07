import React, {useCallback, useEffect, useRef, useState} from 'react'
import {Avatar, Button, Card, Dropdown, Input, List, message, Modal, Rate, Tag, Upload} from 'antd'
import {
    CloseOutlined,
    FileOutlined,
    MoreOutlined,
    PaperClipOutlined,
    SendOutlined,
    SmileOutlined,
    StarOutlined,
    SwapOutlined
} from '@ant-design/icons'
import {customerServiceApi, Message, MessageType, SenderType, Session} from '@/api/customerService'
import {formatTime} from '@/utils/time'
import './ChatInterface.less'

interface ChatInterfaceProps {
  session: Session
  onSessionClose?: (sessionId: string) => void
}

const { TextArea } = Input

const ChatInterface: React.FC<ChatInterfaceProps> = ({
  session,
  onSessionClose
}) => {
  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState('')
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [showFeedbackModal, setShowFeedbackModal] = useState(false)
  const [feedbackData, setFeedbackData] = useState({ satisfaction: 5, feedback: '' })
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<any>(null)
  const wsRef = useRef<WebSocket | null>(null)

  // 滚动到底部
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  // 加载消息
  const loadMessages = useCallback(async () => {
    try {
      setLoading(true)
      const response = await customerServiceApi.getMessages({
        sessionId: session.id,
        page: 1,
        pageSize: 100
      })
      setMessages(response.list)
      setTimeout(scrollToBottom, 100)
    } catch (error) {
      message.error('加载消息失败')
    } finally {
      setLoading(false)
    }
  }, [session.id, scrollToBottom])

  // 发送消息
  const sendMessage = useCallback(async (content: string, type: MessageType = MessageType.TEXT, metadata?: any) => {
    if (!content.trim() && type === MessageType.TEXT) return

    try {
      const newMessage = await customerServiceApi.sendMessage({
        sessionId: session.id,
        type,
        content,
        metadata
      })
      
      setMessages(prev => [...prev, newMessage])
      setInputValue('')
      setTimeout(scrollToBottom, 100)
    } catch (error) {
      message.error('发送消息失败')
    }
  }, [session.id, scrollToBottom])

  // 处理输入
  const handleSend = useCallback(() => {
    if (inputValue.trim()) {
      sendMessage(inputValue)
    }
  }, [inputValue, sendMessage])

  // 处理键盘事件
  const handleKeyPress = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }, [handleSend])

  // 文件上传
  const handleFileUpload = useCallback(async (file: File) => {
    try {
      setUploading(true)
      const uploadResult = await customerServiceApi.uploadFile(file, session.id)
      
      let messageType: MessageType
      if (file.type.startsWith('image/')) {
        messageType = MessageType.IMAGE
      } else if (file.type.startsWith('video/')) {
        messageType = MessageType.VIDEO
      } else if (file.type.startsWith('audio/')) {
        messageType = MessageType.VOICE
      } else {
        messageType = MessageType.FILE
      }

      await sendMessage(uploadResult.filename, messageType, {
        fileName: uploadResult.filename,
        fileSize: uploadResult.size,
        fileUrl: uploadResult.url,
        fileType: uploadResult.type
      })
      
      message.success('文件上传成功')
    } catch (error) {
      message.error('文件上传失败')
    } finally {
      setUploading(false)
    }
  }, [session.id, sendMessage])

  // 关闭会话
  const handleCloseSession = useCallback(async () => {
    Modal.confirm({
      title: '确认关闭会话',
      content: '关闭后将无法继续对话，是否确认？',
      onOk: async () => {
        try {
          await customerServiceApi.closeSession(session.id, {})
          onSessionClose?.(session.id)
          message.success('会话已关闭')
        } catch (error) {
          message.error('关闭会话失败')
        }
      }
    })
  }, [session.id, onSessionClose])

  // 转移会话
  const handleTransferSession = useCallback(() => {
    // 这里应该打开一个选择客服的弹窗
    Modal.info({
      title: '转移会话',
      content: '转移功能需要选择目标客服，请在实际项目中实现选择器组件'
    })
  }, [])

  // 提交反馈
  const handleSubmitFeedback = useCallback(async () => {
    try {
      await customerServiceApi.submitFeedback(session.id, feedbackData)
      setShowFeedbackModal(false)
      message.success('反馈提交成功')
    } catch (error) {
      message.error('反馈提交失败')
    }
  }, [session.id, feedbackData])

  // WebSocket连接
  useEffect(() => {
    const token = localStorage.getItem('token')
    if (token) {
      wsRef.current = customerServiceApi.connectWebSocket(token)
      
      wsRef.current.onmessage = (event) => {
        const data = JSON.parse(event.data)
        if (data.type === 'new_message' && data.sessionId === session.id) {
          setMessages(prev => [...prev, data.message])
          setTimeout(scrollToBottom, 100)
        }
      }

      wsRef.current.onerror = () => {
        message.error('WebSocket连接失败')
      }
    }

    return () => {
      wsRef.current?.close()
    }
  }, [session.id, scrollToBottom])

  // 初始化加载消息
  useEffect(() => {
    loadMessages()
  }, [loadMessages])

  // 渲染消息内容
  const renderMessageContent = useCallback((msg: Message) => {
    switch (msg.type) {
      case MessageType.TEXT:
        return <div className="message-text">{msg.content}</div>
      
      case MessageType.IMAGE:
        return (
          <div className="message-image">
            <img src={msg.metadata?.fileUrl} alt={msg.metadata?.fileName} />
          </div>
        )
      
      case MessageType.FILE:
        return (
          <div className="message-file">
            <FileOutlined />
            <span>{msg.metadata?.fileName}</span>
            <span className="file-size">({(msg.metadata?.fileSize ? (msg.metadata.fileSize / 1024).toFixed(1) : '0')}KB)</span>
          </div>
        )
      
      case MessageType.VIDEO:
        return (
          <div className="message-video">
            <video controls src={msg.metadata?.fileUrl} />
          </div>
        )
      
      case MessageType.VOICE:
        return (
          <div className="message-voice">
            <audio controls src={msg.metadata?.fileUrl} />
          </div>
        )
      
      case MessageType.SYSTEM:
        return <div className="message-system">{msg.content}</div>
      
      default:
        return <div className="message-text">{msg.content}</div>
    }
  }, [])

  // 操作菜单
  const actionMenuItems = [
    {
      key: 'transfer',
      icon: <SwapOutlined />,
      label: '转移会话',
      onClick: handleTransferSession
    },
    {
      key: 'feedback',
      icon: <StarOutlined />,
      label: '评价反馈',
      onClick: () => setShowFeedbackModal(true)
    },
    {
      key: 'close',
      icon: <CloseOutlined />,
      label: '关闭会话',
      onClick: handleCloseSession,
      danger: true
    }
  ]

  return (
    <div className="chat-interface">
      {/* 会话头部 */}
      <Card className="chat-header" size="small">
        <div className="chat-header-content">
          <div className="user-info">
            <Avatar src={session.userInfo.avatar} size={40}>
              {session.userInfo.nickname?.[0]}
            </Avatar>
            <div className="user-details">
              <div className="user-name">{session.userInfo.nickname}</div>
              <div className="user-meta">
                <Tag color={session.priority === 'urgent' ? 'red' : session.priority === 'high' ? 'orange' : 'blue'}>
                  {session.priority}
                </Tag>
                <Tag>{session.source}</Tag>
                <span className="session-time">{formatTime(session.createdAt)}</span>
              </div>
            </div>
          </div>
          
          <div className="chat-actions">
            <Dropdown menu={{ items: actionMenuItems }} trigger={['click']}>
              <Button type="text" icon={<MoreOutlined />} />
            </Dropdown>
          </div>
        </div>
      </Card>

      {/* 消息列表 */}
      <div className="chat-messages">
        <List
          loading={loading}
          dataSource={messages}
          renderItem={(msg) => (
            <List.Item className={`message-item ${msg.sender === SenderType.AGENT ? 'agent' : 'user'}`}>
              <div className="message-wrapper">
                <Avatar 
                  src={msg.senderAvatar} 
                  size={32}
                  className="message-avatar"
                >
                  {msg.senderName?.[0]}
                </Avatar>
                <div className="message-content">
                  <div className="message-header">
                    <span className="sender-name">{msg.senderName}</span>
                    <span className="message-time">{formatTime(msg.timestamp)}</span>
                  </div>
                  <div className="message-body">
                    {renderMessageContent(msg)}
                  </div>
                </div>
              </div>
            </List.Item>
          )}
        />
        <div ref={messagesEndRef} />
      </div>

      {/* 输入区域 */}
      <Card className="chat-input" size="small">
        <div className="input-wrapper">
          <div className="input-tools">
            <Upload
              beforeUpload={(file) => {
                handleFileUpload(file)
                return false
              }}
              showUploadList={false}
              multiple={false}
            >
              <Button 
                type="text" 
                icon={<PaperClipOutlined />} 
                loading={uploading}
                title="上传文件"
              />
            </Upload>
            
            <Button 
              type="text" 
              icon={<SmileOutlined />} 
              title="表情"
            />
          </div>
          
          <TextArea
            ref={inputRef}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="输入消息..."
            autoSize={{ minRows: 1, maxRows: 4 }}
            className="message-input"
          />
          
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={handleSend}
            disabled={!inputValue.trim()}
            className="send-button"
          >
            发送
          </Button>
        </div>
      </Card>

      {/* 反馈弹窗 */}
      <Modal
        title="会话评价"
        open={showFeedbackModal}
        onOk={handleSubmitFeedback}
        onCancel={() => setShowFeedbackModal(false)}
        okText="提交"
        cancelText="取消"
      >
        <div className="feedback-form">
          <div className="feedback-item">
            <label>满意度评分：</label>
            <Rate
              value={feedbackData.satisfaction}
              onChange={(value) => setFeedbackData(prev => ({ ...prev, satisfaction: value }))}
            />
          </div>
          
          <div className="feedback-item">
            <label>意见反馈：</label>
            <TextArea
              value={feedbackData.feedback}
              onChange={(e) => setFeedbackData(prev => ({ ...prev, feedback: e.target.value }))}
              placeholder="请输入您的意见和建议..."
              rows={4}
            />
          </div>
        </div>
      </Modal>
    </div>
  )
}

export default ChatInterface