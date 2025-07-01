import React, { useState, useEffect, useRef } from 'react'
import {
  Avatar,
  Button,
  Card,
  Divider,
  Input,
  Space,
  Typography,
  Select,
  Switch,
  Tooltip,
  Tag,
  Dropdown,
  Modal,
  List,
  Empty,
  Spin,
} from 'antd'
import {
  RobotOutlined,
  SendOutlined,
  UserOutlined,
  SettingOutlined,
  HistoryOutlined,
  PlusOutlined,
  DeleteOutlined,
  DatabaseOutlined,
  ThunderboltOutlined,
  BranchesOutlined,
} from '@ant-design/icons'
import { useChatStore } from '@/store/chat'
import { useKnowledgeStore } from '@/store/knowledge'
import type { ChatRequest } from '@/api/chat'

const { Title, Text, Paragraph } = Typography
const { TextArea } = Input
const { Option } = Select

const ChatPage: React.FC = () => {
  const {
    conversations,
    currentConversation,
    messages,
    sending,
    fetchConversations,
    createConversation,
    setCurrentConversation,
    sendMessage,
    deleteConversation,
  } = useChatStore()

  const { knowledgeBases, fetchKnowledgeBases } = useKnowledgeStore()

  const [inputValue, setInputValue] = useState('')
  const [selectedKnowledgeBases, setSelectedKnowledgeBases] = useState<number[]>([])
  const [searchMode, setSearchMode] = useState<'auto' | 'vector' | 'hybrid' | 'graph'>('auto')
  const [useAutoGen, setUseAutoGen] = useState(false)
  const [settingsVisible, setSettingsVisible] = useState(false)
  const [conversationListVisible, setConversationListVisible] = useState(false)

  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    fetchConversations()
    fetchKnowledgeBases()
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  // 发送消息
  const handleSendMessage = async () => {
    if (!inputValue.trim() || sending) return

    const chatRequest: ChatRequest = {
      message: inputValue.trim(),
      conversation_id: currentConversation?.id,
      knowledge_base_ids: selectedKnowledgeBases.length > 0 ? selectedKnowledgeBases : undefined,
      search_mode: searchMode,
      stream: false,
    }

    setInputValue('')

    const success = await sendMessage(chatRequest)
    if (!success) {
      // 如果发送失败，恢复输入内容
      setInputValue(chatRequest.message)
    }
  }

  // 创建新对话
  const handleNewConversation = async () => {
    const conversation = await createConversation({
      title: '新对话',
      knowledge_base_ids: selectedKnowledgeBases,
    })

    if (conversation) {
      setCurrentConversation(conversation)
    }
  }

  // 删除对话
  const handleDeleteConversation = async (conversationId: number) => {
    await deleteConversation(conversationId)
    if (currentConversation?.id === conversationId) {
      setCurrentConversation(null)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  // 渲染消息
  const renderMessage = (message: any, index: number) => {
    const isUser = message.role === 'user'

    return (
      <div
        key={message.id}
        style={{
          display: 'flex',
          justifyContent: isUser ? 'flex-end' : 'flex-start',
          marginBottom: 16,
          animation: 'fadeIn 0.3s ease-in',
        }}
      >
        <div
          style={{
            maxWidth: '70%',
            display: 'flex',
            flexDirection: isUser ? 'row-reverse' : 'row',
            alignItems: 'flex-start',
            gap: 8,
          }}
        >
          <Avatar
            icon={isUser ? <UserOutlined /> : <RobotOutlined />}
            style={{
              backgroundColor: isUser ? '#1890ff' : '#52c41a',
              flexShrink: 0,
            }}
          />
          <div
            style={{
              backgroundColor: isUser ? '#1890ff' : '#f6f6f6',
              color: isUser ? 'white' : '#333',
              padding: '12px 16px',
              borderRadius: isUser ? '18px 18px 4px 18px' : '18px 18px 18px 4px',
              boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
              position: 'relative',
            }}
          >
            <div style={{ marginBottom: 4 }}>{message.content}</div>
            <div
              style={{
                fontSize: 12,
                opacity: 0.7,
                textAlign: isUser ? 'right' : 'left',
              }}
            >
              {formatTime(message.timestamp)}
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div style={{ padding: 24, height: 'calc(100vh - 64px)', display: 'flex', flexDirection: 'column' }}>
      {/* 页面标题和工具栏 */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
          <div>
            <Title level={2} style={{ margin: 0, color: '#1e293b' }}>
              智能对话
            </Title>
            <Text style={{ color: '#64748b' }}>基于企业知识库的智能问答系统</Text>
          </div>
          <Space>
            <Button icon={<HistoryOutlined />} onClick={() => setConversationListVisible(true)}>
              对话历史
            </Button>
            <Button icon={<SettingOutlined />} onClick={() => setSettingsVisible(true)}>
              设置
            </Button>
            <Button
              type='primary'
              icon={<PlusOutlined />}
              onClick={handleNewConversation}
              style={{
                background: 'linear-gradient(135deg, #0ea5e9, #8b5cf6)',
                border: 'none',
              }}
            >
              新对话
            </Button>
          </Space>
        </div>

        {/* 当前对话信息 */}
        {currentConversation && (
          <Card size='small' style={{ backgroundColor: '#f8fafc' }}>
            <Space>
              <Text strong>当前对话:</Text>
              <Text>{currentConversation.title}</Text>
              {selectedKnowledgeBases.length > 0 && (
                <>
                  <Divider type='vertical' />
                  <Text type='secondary'>知识库:</Text>
                  {selectedKnowledgeBases.map(id => {
                    const kb = knowledgeBases.find(k => k.id === id)
                    return kb ? (
                      <Tag key={id} color='blue'>
                        {kb.name}
                      </Tag>
                    ) : null
                  })}
                </>
              )}
              <Divider type='vertical' />
              <Tag color={useAutoGen ? 'purple' : 'green'}>{useAutoGen ? '多智能体模式' : '标准模式'}</Tag>
              <Tag color='cyan'>{searchMode === 'auto' ? '智能检索' : searchMode}</Tag>
            </Space>
          </Card>
        )}
      </div>

      {/* 聊天区域 */}
      <Card
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
        }}
        styles={{
          body: {
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            padding: 0,
          },
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

            {sending && (
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
              disabled={sending}
              style={{
                resize: 'none',
                borderRadius: '8px 0 0 8px',
              }}
            />
            <Button
              type='primary'
              icon={<SendOutlined />}
              onClick={handleSendMessage}
              loading={sending}
              disabled={!inputValue.trim() || sending}
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

      {/* 设置模态框 */}
      <Modal
        title='聊天设置'
        open={settingsVisible}
        onCancel={() => setSettingsVisible(false)}
        footer={null}
        width={500}
      >
        <Space direction='vertical' style={{ width: '100%' }} size='large'>
          <div>
            <Text strong>知识库选择：</Text>
            <Select
              mode='multiple'
              placeholder='选择要使用的知识库'
              value={selectedKnowledgeBases}
              onChange={setSelectedKnowledgeBases}
              style={{ width: '100%', marginTop: 8 }}
            >
              {knowledgeBases.map(kb => (
                <Option key={kb.id} value={kb.id}>
                  <Space>
                    <DatabaseOutlined />
                    {kb.name}
                  </Space>
                </Option>
              ))}
            </Select>
          </div>

          <div>
            <Text strong>检索模式：</Text>
            <Select value={searchMode} onChange={setSearchMode} style={{ width: '100%', marginTop: 8 }}>
              <Option value='auto'>
                <Space>
                  <ThunderboltOutlined />
                  智能检索
                </Space>
              </Option>
              <Option value='vector'>向量检索</Option>
              <Option value='hybrid'>混合检索</Option>
              <Option value='graph'>图谱检索</Option>
            </Select>
          </div>

          <div>
            <Space>
              <Text strong>多智能体模式：</Text>
              <Switch
                checked={useAutoGen}
                onChange={setUseAutoGen}
                checkedChildren={<BranchesOutlined />}
                unCheckedChildren='关闭'
              />
            </Space>
            <div style={{ marginTop: 4 }}>
              <Text type='secondary' style={{ fontSize: 12 }}>
                启用后将使用多个AI智能体协作回答问题
              </Text>
            </div>
          </div>
        </Space>
      </Modal>

      {/* 对话历史模态框 */}
      <Modal
        title='对话历史'
        open={conversationListVisible}
        onCancel={() => setConversationListVisible(false)}
        footer={null}
        width={600}
      >
        {conversations.length === 0 ? (
          <Empty description='暂无对话历史' />
        ) : (
          <List
            dataSource={conversations}
            renderItem={conversation => (
              <List.Item
                actions={[
                  <Button
                    type='link'
                    onClick={() => {
                      setCurrentConversation(conversation)
                      setConversationListVisible(false)
                    }}
                  >
                    打开
                  </Button>,
                  <Button type='link' danger onClick={() => handleDeleteConversation(conversation.id)}>
                    删除
                  </Button>,
                ]}
              >
                <List.Item.Meta
                  title={conversation.title}
                  description={
                    <Space>
                      <Text type='secondary'>{conversation.message_count} 条消息</Text>
                      <Text type='secondary'>{new Date(conversation.updated_at).toLocaleDateString()}</Text>
                    </Space>
                  }
                />
              </List.Item>
            )}
          />
        )}
      </Modal>

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

          @keyframes fadeIn {
            from {
              opacity: 0;
              transform: translateY(10px);
            }
            to {
              opacity: 1;
              transform: translateY(0);
            }
          }
        `}
      </style>
    </div>
  )
}

export default ChatPage
