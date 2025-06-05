import React, { useState, useEffect, useRef } from 'react';
import {
  Layout,
  Card,
  List,
  Input,
  Button,
  Avatar,
  Badge,
  Space,
  Divider,
  Typography,
  Tag,
  Dropdown,
  Modal,
  Form,
  Select,
  message,
  Row,
  Col,
  Tooltip,
  Empty,
} from 'antd';
import {
  SendOutlined,
  UserOutlined,
  RobotOutlined,
  MoreOutlined,
  CloseOutlined,
  TransferOutlined,
  FileTextOutlined,
  PhoneOutlined,
  MailOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { StateWrapper } from '../components/common/LoadingEmpty';
import { useRequest } from '../hooks/useRequest';
import { customerServiceApi } from '../api/customerService';

const { Sider, Content } = Layout;
const { TextArea } = Input;
const { Text, Title } = Typography;
const { Option } = Select;

// 会话状态枚举
enum SessionStatus {
  WAITING = 'waiting',
  ACTIVE = 'active',
  CLOSED = 'closed',
  TRANSFERRED = 'transferred',
}

// 消息类型枚举
enum MessageType {
  TEXT = 'text',
  IMAGE = 'image',
  FILE = 'file',
  SYSTEM = 'system',
}

// 消息发送者类型
enum SenderType {
  USER = 'user',
  AGENT = 'agent',
  SYSTEM = 'system',
  BOT = 'bot',
}

// 会话接口
interface Session {
  id: string;
  userId: string;
  userName: string;
  userAvatar?: string;
  status: SessionStatus;
  lastMessage: string;
  lastMessageTime: string;
  unreadCount: number;
  tags: string[];
  priority: 'low' | 'medium' | 'high' | 'urgent';
  source: 'web' | 'mobile' | 'wechat' | 'qq' | 'phone';
  agentId?: string;
  agentName?: string;
  createdAt: string;
  updatedAt: string;
}

// 消息接口
interface Message {
  id: string;
  sessionId: string;
  content: string;
  type: MessageType;
  senderType: SenderType;
  senderId: string;
  senderName: string;
  senderAvatar?: string;
  timestamp: string;
  isRead: boolean;
  metadata?: Record<string, any>;
}

// 用户信息接口
interface UserInfo {
  id: string;
  name: string;
  avatar?: string;
  email?: string;
  phone?: string;
  location?: string;
  lastActiveTime: string;
  totalSessions: number;
  tags: string[];
}

const CustomerService: React.FC = () => {
  const { t } = useTranslation();
  const [selectedSession, setSelectedSession] = useState<Session | null>(null);
  const [messageInput, setMessageInput] = useState('');
  const [transferModalVisible, setTransferModalVisible] = useState(false);
  const [userInfoVisible, setUserInfoVisible] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [form] = Form.useForm();

  // 获取会话列表
  const {
    data: sessions = [],
    loading: sessionsLoading,
    error: sessionsError,
    run: fetchSessions,
  } = useRequest(customerServiceApi.getSessions, {
    defaultParams: [{ status: 'active' }],
  });

  // 获取消息列表
  const {
    data: messages = [],
    loading: messagesLoading,
    error: messagesError,
    run: fetchMessages,
  } = useRequest(customerServiceApi.getMessages, {
    manual: true,
  });

  // 获取用户信息
  const {
    data: userInfo,
    loading: userInfoLoading,
    run: fetchUserInfo,
  } = useRequest(customerServiceApi.getUserInfo, {
    manual: true,
  });

  // 发送消息
  const { loading: sendingMessage, run: sendMessage } = useRequest(
    customerServiceApi.sendMessage,
    {
      manual: true,
      onSuccess: () => {
        setMessageInput('');
        if (selectedSession) {
          fetchMessages(selectedSession.id);
        }
      },
    }
  );

  // 转接会话
  const { loading: transferring, run: transferSession } = useRequest(
    customerServiceApi.transferSession,
    {
      manual: true,
      onSuccess: () => {
        setTransferModalVisible(false);
        form.resetFields();
        message.success(t('customerService.transferSuccess'));
        fetchSessions();
      },
    }
  );

  // 关闭会话
  const { loading: closing, run: closeSession } = useRequest(
    customerServiceApi.closeSession,
    {
      manual: true,
      onSuccess: () => {
        message.success(t('customerService.closeSuccess'));
        setSelectedSession(null);
        fetchSessions();
      },
    }
  );

  // 选择会话
  const handleSelectSession = (session: Session) => {
    setSelectedSession(session);
    fetchMessages(session.id);
    fetchUserInfo(session.userId);
  };

  // 发送消息
  const handleSendMessage = () => {
    if (!messageInput.trim() || !selectedSession) return;

    sendMessage({
      sessionId: selectedSession.id,
      content: messageInput.trim(),
      type: MessageType.TEXT,
    });
  };

  // 处理转接
  const handleTransfer = (values: any) => {
    if (!selectedSession) return;
    transferSession(selectedSession.id, values);
  };

  // 处理关闭会话
  const handleCloseSession = () => {
    if (!selectedSession) return;

    Modal.confirm({
      title: t('customerService.confirmClose'),
      content: t('customerService.confirmCloseMessage'),
      onOk: () => closeSession(selectedSession.id),
    });
  };

  // 滚动到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 获取状态颜色
  const getStatusColor = (status: SessionStatus) => {
    switch (status) {
      case SessionStatus.WAITING:
        return 'orange';
      case SessionStatus.ACTIVE:
        return 'green';
      case SessionStatus.CLOSED:
        return 'default';
      case SessionStatus.TRANSFERRED:
        return 'blue';
      default:
        return 'default';
    }
  };

  // 获取优先级颜色
  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent':
        return 'red';
      case 'high':
        return 'orange';
      case 'medium':
        return 'blue';
      case 'low':
        return 'default';
      default:
        return 'default';
    }
  };

  // 获取发送者头像
  const getSenderAvatar = (message: Message) => {
    switch (message.senderType) {
      case SenderType.USER:
        return message.senderAvatar || <UserOutlined />;
      case SenderType.BOT:
        return <RobotOutlined />;
      default:
        return message.senderAvatar || <UserOutlined />;
    }
  };

  // 会话操作菜单
  const sessionMenuItems = [
    {
      key: 'transfer',
      label: t('customerService.transfer'),
      icon: <TransferOutlined />,
      onClick: () => setTransferModalVisible(true),
    },
    {
      key: 'close',
      label: t('customerService.close'),
      icon: <CloseOutlined />,
      onClick: handleCloseSession,
      danger: true,
    },
  ];

  return (
    <Layout style={{ height: 'calc(100vh - 64px)' }}>
      {/* 会话列表 */}
      <Sider width={320} theme="light" style={{ borderRight: '1px solid #f0f0f0' }}>
        <div style={{ padding: '16px', borderBottom: '1px solid #f0f0f0' }}>
          <Title level={4} style={{ margin: 0 }}>
            {t('customerService.sessions')}
          </Title>
        </div>
        <StateWrapper
          loading={sessionsLoading}
          error={sessionsError}
          empty={sessions.length === 0}
          onRetry={fetchSessions}
        >
          <List
            dataSource={sessions}
            renderItem={(session) => (
              <List.Item
                style={{
                  padding: '12px 16px',
                  cursor: 'pointer',
                  backgroundColor:
                    selectedSession?.id === session.id ? '#f6ffed' : 'transparent',
                }}
                onClick={() => handleSelectSession(session)}
              >
                <List.Item.Meta
                  avatar={
                    <Badge count={session.unreadCount} size="small">
                      <Avatar src={session.userAvatar} icon={<UserOutlined />} />
                    </Badge>
                  }
                  title={
                    <Space>
                      <Text strong>{session.userName}</Text>
                      <Tag color={getStatusColor(session.status)} size="small">
                        {t(`customerService.status.${session.status}`)}
                      </Tag>
                      <Tag color={getPriorityColor(session.priority)} size="small">
                        {t(`customerService.priority.${session.priority}`)}
                      </Tag>
                    </Space>
                  }
                  description={
                    <div>
                      <Text ellipsis style={{ display: 'block', marginBottom: 4 }}>
                        {session.lastMessage}
                      </Text>
                      <Text type="secondary" style={{ fontSize: '12px' }}>
                        {session.lastMessageTime}
                      </Text>
                    </div>
                  }
                />
              </List.Item>
            )}
          />
        </StateWrapper>
      </Sider>

      {/* 聊天区域 */}
      <Content style={{ display: 'flex', flexDirection: 'column' }}>
        {selectedSession ? (
          <>
            {/* 聊天头部 */}
            <div
              style={{
                padding: '16px',
                borderBottom: '1px solid #f0f0f0',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              <Space>
                <Avatar src={selectedSession.userAvatar} icon={<UserOutlined />} />
                <div>
                  <Title level={5} style={{ margin: 0 }}>
                    {selectedSession.userName}
                  </Title>
                  <Text type="secondary">
                    {t(`customerService.source.${selectedSession.source}`)}
                  </Text>
                </div>
              </Space>
              <Space>
                <Button
                  icon={<FileTextOutlined />}
                  onClick={() => setUserInfoVisible(true)}
                >
                  {t('customerService.userInfo')}
                </Button>
                <Dropdown menu={{ items: sessionMenuItems }} trigger={['click']}>
                  <Button icon={<MoreOutlined />} />
                </Dropdown>
              </Space>
            </div>

            {/* 消息列表 */}
            <div style={{ flex: 1, overflow: 'auto', padding: '16px' }}>
              <StateWrapper
                loading={messagesLoading}
                error={messagesError}
                empty={messages.length === 0}
                onRetry={() => fetchMessages(selectedSession.id)}
              >
                <List
                  dataSource={messages}
                  renderItem={(message) => (
                    <List.Item
                      style={{
                        padding: '8px 0',
                        border: 'none',
                        justifyContent:
                          message.senderType === SenderType.AGENT ? 'flex-end' : 'flex-start',
                      }}
                    >
                      <div
                        style={{
                          display: 'flex',
                          flexDirection:
                            message.senderType === SenderType.AGENT ? 'row-reverse' : 'row',
                          alignItems: 'flex-start',
                          maxWidth: '70%',
                        }}
                      >
                        <Avatar
                          size="small"
                          src={message.senderAvatar}
                          icon={getSenderAvatar(message)}
                          style={{ margin: '0 8px' }}
                        />
                        <div
                          style={{
                            backgroundColor:
                              message.senderType === SenderType.AGENT ? '#1890ff' : '#f0f0f0',
                            color: message.senderType === SenderType.AGENT ? 'white' : 'black',
                            padding: '8px 12px',
                            borderRadius: '8px',
                            maxWidth: '100%',
                            wordBreak: 'break-word',
                          }}
                        >
                          <div>{message.content}</div>
                          <div
                            style={{
                              fontSize: '12px',
                              opacity: 0.7,
                              marginTop: '4px',
                              textAlign:
                                message.senderType === SenderType.AGENT ? 'right' : 'left',
                            }}
                          >
                            {message.timestamp}
                          </div>
                        </div>
                      </div>
                    </List.Item>
                  )}
                />
                <div ref={messagesEndRef} />
              </StateWrapper>
            </div>

            {/* 消息输入框 */}
            <div style={{ padding: '16px', borderTop: '1px solid #f0f0f0' }}>
              <Space.Compact style={{ width: '100%' }}>
                <TextArea
                  value={messageInput}
                  onChange={(e) => setMessageInput(e.target.value)}
                  placeholder={t('customerService.inputPlaceholder')}
                  autoSize={{ minRows: 1, maxRows: 4 }}
                  onPressEnter={(e) => {
                    if (!e.shiftKey) {
                      e.preventDefault();
                      handleSendMessage();
                    }
                  }}
                />
                <Button
                  type="primary"
                  icon={<SendOutlined />}
                  loading={sendingMessage}
                  onClick={handleSendMessage}
                  disabled={!messageInput.trim()}
                >
                  {t('common.send')}
                </Button>
              </Space.Compact>
            </div>
          </>
        ) : (
          <div
            style={{
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              height: '100%',
            }}
          >
            <Empty
              description={t('customerService.selectSession')}
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            />
          </div>
        )}      </Content>

      {/* 转接模态框 */}
      <Modal
        title={t('customerService.transfer')}
        open={transferModalVisible}
        onCancel={() => setTransferModalVisible(false)}
        onOk={() => form.submit()}
        confirmLoading={transferring}
      >
        <Form form={form} onFinish={handleTransfer} layout="vertical">
          <Form.Item
            name="agentId"
            label={t('customerService.selectAgent')}
            rules={[{ required: true, message: t('customerService.selectAgent') }]}
          >
            <Select placeholder={t('customerService.selectAgent')}>
              <Option value="agent1">张三 - 技术支持</Option>
              <Option value="agent2">李四 - 售后服务</Option>
              <Option value="agent3">王五 - 销售顾问</Option>
            </Select>
          </Form.Item>
          <Form.Item
            name="reason"
            label={t('customerService.transferReason')}
          >
            <TextArea
              rows={3}
              placeholder={t('customerService.transferReason')}
            />
          </Form.Item>
        </Form>
      </Modal>

      {/* 用户信息模态框 */}
      <Modal
        title={t('customerService.userProfile')}
        open={userInfoVisible}
        onCancel={() => setUserInfoVisible(false)}
        footer={null}
        width={600}
      >
        <StateWrapper
          loading={userInfoLoading}
          error={false}
          empty={!userInfo}
        >
          {userInfo && (
            <div>
              <Row gutter={[16, 16]}>
                <Col span={24}>
                  <Card size="small" title={t('customerService.contactInfo')}>
                    <Row gutter={[16, 8]}>
                      <Col span={12}>
                        <Space>
                          <MailOutlined />
                          <Text>{userInfo.email || t('customerService.noData')}</Text>
                        </Space>
                      </Col>
                      <Col span={12}>
                        <Space>
                          <PhoneOutlined />
                          <Text>{userInfo.phone || t('customerService.noData')}</Text>
                        </Space>
                      </Col>
                      <Col span={12}>
                        <Space>
                          <ClockCircleOutlined />
                          <Text>
                            {t('customerService.registeredAt')}: {userInfo.registeredAt}
                          </Text>
                        </Space>
                      </Col>
                      <Col span={12}>
                        <Space>
                          <CheckCircleOutlined />
                          <Text>
                            {t('customerService.lastActiveAt')}: {userInfo.lastActiveAt}
                          </Text>
                        </Space>
                      </Col>
                    </Row>
                  </Card>
                </Col>
                <Col span={24}>
                  <Card size="small" title={t('customerService.sessionHistory')}>
                    <Row gutter={[16, 8]}>
                      <Col span={12}>
                        <Tooltip title={t('customerService.totalSessions')}>
                          <Text>
                            {t('customerService.totalSessions')}: {userInfo.totalSessions}
                          </Text>
                        </Tooltip>
                      </Col>
                      <Col span={12}>
                        <Tooltip title={t('customerService.vipLevel')}>
                          <Text>
                            {t('customerService.vipLevel')}: {userInfo.vipLevel}
                          </Text>
                        </Tooltip>
                      </Col>
                    </Row>
                    {userInfo.tags && userInfo.tags.length > 0 && (
                      <div style={{ marginTop: 8 }}>
                        <Text type="secondary">{t('customerService.tags')}: </Text>
                        {userInfo.tags.map((tag, index) => (
                          <Tag key={index} color="blue">
                            {tag}
                          </Tag>
                        ))}
                      </div>
                    )}
                  </Card>
                </Col>
              </Row>
            </div>
          )}
        </StateWrapper>
      </Modal>
    </Layout>
  );
};

export default CustomerService;