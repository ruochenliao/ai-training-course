'use client';

import {useEffect, useRef, useState} from 'react';
import {
    Avatar,
    Button,
    Card,
    Divider,
    Drawer,
    Empty,
    Input,
    message,
    Select,
    Slider,
    Space,
    Spin,
    Switch,
    Tag,
    Tooltip,
    Typography
} from 'antd';
import {
    NodeIndexOutlined,
    PlusOutlined,
    RobotOutlined,
    SearchOutlined,
    SendOutlined,
    SettingOutlined,
    ShareAltOutlined,
    ThunderboltOutlined,
    UserOutlined
} from '@ant-design/icons';
import {AnimatePresence, motion} from 'framer-motion';
import {useAuth} from '@/contexts/AuthContext';
import {apiClient} from '@/utils/api';
import {formatDate} from '@/utils';
import ReactMarkdown from 'react-markdown';

const { TextArea } = Input;
const { Text, Title } = Typography;

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: any[];
  loading?: boolean;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [searchMode, setSearchMode] = useState<'vector' | 'graph' | 'hybrid' | 'autogen'>('autogen');
  const [selectedKnowledgeBases, setSelectedKnowledgeBases] = useState<number[]>([]);
  const [showSettings, setShowSettings] = useState(false);
  const [temperature, setTemperature] = useState(0.7);
  const [maxTokens, setMaxTokens] = useState(2000);
  const [enableStreaming, setEnableStreaming] = useState(true);
  const { user } = useAuth();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || loading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setLoading(true);

    // 添加加载中的助手消息
    const loadingMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      loading: true,
    };
    setMessages(prev => [...prev, loadingMessage]);

    try {
      // 根据选择的检索模式调用不同的API
      let response;

      if (searchMode === 'autogen') {
        // 使用AutoGen多智能体协作
        response = await apiClient.post('/api/v1/autogen/chat', {
          query: userMessage.content,
          knowledge_base_ids: selectedKnowledgeBases.length > 0 ? selectedKnowledgeBases : undefined,
          conversation_id: conversationId,
          temperature,
          max_tokens: maxTokens,
        });
      } else {
        // 使用传统聊天接口
        response = await apiClient.sendChatMessage({
          message: userMessage.content,
          conversation_id: conversationId,
          search_mode: searchMode,
          knowledge_base_ids: selectedKnowledgeBases.length > 0 ? selectedKnowledgeBases : undefined,
          temperature,
          max_tokens: maxTokens,
          stream: enableStreaming,
        });
      }

      // 更新对话ID
      if (!conversationId && response.conversation_id) {
        setConversationId(response.conversation_id);
      }

      // 替换加载消息为实际响应
      setMessages(prev => prev.map(msg =>
        msg.id === loadingMessage.id
          ? {
              ...msg,
              content: response.message || response.answer || response.content,
              sources: response.sources,
              loading: false,
              metadata: {
                search_mode: searchMode,
                processing_time: response.processing_time,
                confidence: response.confidence,
              }
            }
          : msg
      ));
    } catch (error) {
      console.error('发送消息失败:', error);
      message.error('发送消息失败，请重试');
      
      // 移除加载消息
      setMessages(prev => prev.filter(msg => msg.id !== loadingMessage.id));
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const startNewConversation = () => {
    setMessages([]);
    setConversationId(null);
    setInputValue('');
  };

  const renderMessage = (message: Message) => {
    const isUser = message.role === 'user';
    
    return (
      <motion.div
        key={message.id}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-6`}
      >
        <div className={`flex max-w-[80%] ${isUser ? 'flex-row-reverse' : 'flex-row'} items-start space-x-3`}>
          <Avatar
            size="small"
            icon={isUser ? <UserOutlined /> : <RobotOutlined />}
            className={isUser 
              ? 'bg-gradient-to-r from-blue-500 to-purple-600' 
              : 'bg-gradient-to-r from-green-500 to-blue-500'
            }
          />
          
          <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}>
            <Card
              className={`${
                isUser 
                  ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white border-0' 
                  : 'bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700'
              } shadow-md rounded-2xl`}
              bodyStyle={{ padding: '12px 16px' }}
            >
              {message.loading ? (
                <div className="flex items-center space-x-2">
                  <Spin size="small" />
                  <Text className="text-gray-500">AI正在思考...</Text>
                </div>
              ) : (
                <div className={`prose prose-sm max-w-none ${isUser ? 'text-white' : 'dark:text-white'}`}>
                  <ReactMarkdown>{message.content}</ReactMarkdown>
                </div>
              )}
            </Card>
            
            <Text type="secondary" className="text-xs mt-1">
              {formatDate(message.timestamp, 'relative')}
            </Text>
            
            {message.sources && message.sources.length > 0 && (
              <div className="mt-2 text-xs text-gray-500">
                <Text type="secondary">来源: {message.sources.length} 个相关文档</Text>
              </div>
            )}
          </div>
        </div>
      </motion.div>
    );
  };

  return (
    <div className="h-full flex flex-col bg-gray-50 dark:bg-gray-900">
      {/* 聊天头部 */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <Title level={4} className="!mb-1">智能问答助手</Title>
            <Text type="secondary">基于企业知识库的AI助手，为您提供准确的答案</Text>
          </div>

          <Space>
            {/* 检索模式选择器 */}
            <Select
              value={searchMode}
              onChange={setSearchMode}
              style={{ width: 140 }}
              size="small"
            >
              <Select.Option value="autogen">
                <Space>
                  <ThunderboltOutlined />
                  智能体协作
                </Space>
              </Select.Option>
              <Select.Option value="hybrid">
                <Space>
                  <ShareAltOutlined />
                  混合检索
                </Space>
              </Select.Option>
              <Select.Option value="vector">
                <Space>
                  <SearchOutlined />
                  向量检索
                </Space>
              </Select.Option>
              <Select.Option value="graph">
                <Space>
                  <NodeIndexOutlined />
                  图谱检索
                </Space>
              </Select.Option>
            </Select>

            <Tooltip title="设置">
              <Button
                icon={<SettingOutlined />}
                onClick={() => setShowSettings(true)}
                size="small"
              />
            </Tooltip>

            <Button
              icon={<PlusOutlined />}
              onClick={startNewConversation}
              className="flex items-center"
            >
              新对话
            </Button>
          </Space>
        </div>

        {/* 检索模式说明 */}
        <div className="mt-3">
          <Tag color={
            searchMode === 'autogen' ? 'purple' :
            searchMode === 'hybrid' ? 'blue' :
            searchMode === 'vector' ? 'green' :
            'orange'
          }>
            {searchMode === 'autogen' && '🤖 多智能体协作模式：使用AutoGen框架进行智能体协作分析'}
            {searchMode === 'hybrid' && '🔄 混合检索模式：结合向量检索和图谱检索'}
            {searchMode === 'vector' && '🔍 向量检索模式：基于语义相似度搜索'}
            {searchMode === 'graph' && '🕸️ 图谱检索模式：基于知识图谱关系搜索'}
          </Tag>
        </div>
      </div>

      {/* 消息列表 */}
      <div className="flex-1 overflow-y-auto custom-scrollbar p-6">
        <div className="max-w-4xl mx-auto">
          <AnimatePresence>
            {messages.length === 0 ? (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-center py-20"
              >
                <Empty
                  image={
                    <div className="w-24 h-24 mx-auto mb-4 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                      <RobotOutlined className="text-3xl text-white" />
                    </div>
                  }
                  description={
                    <div>
                      <Title level={3} className="!mb-2">欢迎使用智能问答</Title>
                      <Text type="secondary" className="text-base">
                        我是您的AI助手，可以帮您查找企业知识库中的信息
                      </Text>
                    </div>
                  }
                >
                  <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4 max-w-2xl mx-auto">
                    {[
                      '如何使用RAG系统？',
                      '企业知识库包含哪些内容？',
                      '如何上传和管理文档？',
                      '系统有哪些高级功能？',
                    ].map((question, index) => (
                      <motion.div
                        key={index}
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                      >
                        <Card
                          hoverable
                          className="cursor-pointer border-dashed"
                          onClick={() => setInputValue(question)}
                        >
                          <Text className="text-sm">{question}</Text>
                        </Card>
                      </motion.div>
                    ))}
                  </div>
                </Empty>
              </motion.div>
            ) : (
              messages.map(renderMessage)
            )}
          </AnimatePresence>
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* 输入区域 */}
      <div className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 p-6">
        <div className="max-w-4xl mx-auto">
          <div className="flex space-x-4">
            <div className="flex-1">
              <TextArea
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="输入您的问题... (Shift+Enter 换行，Enter 发送)"
                autoSize={{ minRows: 1, maxRows: 4 }}
                className="rounded-lg resize-none"
                disabled={loading}
              />
            </div>
            
            <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
              <Button
                type="primary"
                icon={<SendOutlined />}
                onClick={handleSendMessage}
                loading={loading}
                disabled={!inputValue.trim()}
                size="large"
                className="h-full bg-gradient-to-r from-blue-500 to-purple-600 border-0 rounded-lg shadow-md hover:shadow-lg transition-all duration-300"
              >
                发送
              </Button>
            </motion.div>
          </div>
          
          <div className="mt-2 text-center">
            <Text type="secondary" className="text-xs">
              AI助手可能会出错，请核实重要信息
            </Text>
          </div>
        </div>
      </div>

      {/* 设置抽屉 */}
      <Drawer
        title="聊天设置"
        placement="right"
        onClose={() => setShowSettings(false)}
        open={showSettings}
        width={400}
      >
        <div className="space-y-6">
          {/* 知识库选择 */}
          <div>
            <Text strong className="block mb-2">知识库选择</Text>
            <Select
              mode="multiple"
              placeholder="选择知识库（留空表示使用所有可访问的知识库）"
              value={selectedKnowledgeBases}
              onChange={setSelectedKnowledgeBases}
              style={{ width: '100%' }}
              allowClear
            >
              {/* 这里应该从API获取知识库列表 */}
              <Select.Option value={1}>技术文档</Select.Option>
              <Select.Option value={2}>业务知识</Select.Option>
              <Select.Option value={3}>产品手册</Select.Option>
            </Select>
          </div>

          <Divider />

          {/* 模型参数 */}
          <div>
            <Text strong className="block mb-4">模型参数</Text>

            <div className="space-y-4">
              <div>
                <Text className="block mb-2">温度 (Temperature): {temperature}</Text>
                <Slider
                  min={0}
                  max={1}
                  step={0.1}
                  value={temperature}
                  onChange={setTemperature}
                  marks={{
                    0: '保守',
                    0.5: '平衡',
                    1: '创新'
                  }}
                />
                <Text type="secondary" style={{ fontSize: '12px' }}>
                  较低的温度使回答更保守和一致，较高的温度使回答更有创意
                </Text>
              </div>

              <div>
                <Text className="block mb-2">最大令牌数: {maxTokens}</Text>
                <Slider
                  min={500}
                  max={4000}
                  step={100}
                  value={maxTokens}
                  onChange={setMaxTokens}
                  marks={{
                    500: '500',
                    2000: '2000',
                    4000: '4000'
                  }}
                />
                <Text type="secondary" style={{ fontSize: '12px' }}>
                  控制回答的最大长度
                </Text>
              </div>
            </div>
          </div>

          <Divider />

          {/* 高级选项 */}
          <div>
            <Text strong className="block mb-4">高级选项</Text>

            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <div>
                  <Text>启用流式输出</Text>
                  <br />
                  <Text type="secondary" style={{ fontSize: '12px' }}>
                    实时显示回答内容
                  </Text>
                </div>
                <Switch
                  checked={enableStreaming}
                  onChange={setEnableStreaming}
                />
              </div>
            </div>
          </div>

          <Divider />

          {/* 检索模式详细说明 */}
          <div>
            <Text strong className="block mb-4">检索模式说明</Text>

            <div className="space-y-3">
              <Card size="small">
                <div className="flex items-center mb-2">
                  <ThunderboltOutlined className="text-purple-500 mr-2" />
                  <Text strong>智能体协作模式</Text>
                </div>
                <Text type="secondary" style={{ fontSize: '12px' }}>
                  使用AutoGen框架，多个专业智能体协作分析问题，提供最全面和准确的答案。推荐用于复杂问题。
                </Text>
              </Card>

              <Card size="small">
                <div className="flex items-center mb-2">
                  <ShareAltOutlined className="text-blue-500 mr-2" />
                  <Text strong>混合检索模式</Text>
                </div>
                <Text type="secondary" style={{ fontSize: '12px' }}>
                  结合向量检索和图谱检索的优势，平衡语义理解和关系推理。适合大多数场景。
                </Text>
              </Card>

              <Card size="small">
                <div className="flex items-center mb-2">
                  <SearchOutlined className="text-green-500 mr-2" />
                  <Text strong>向量检索模式</Text>
                </div>
                <Text type="secondary" style={{ fontSize: '12px' }}>
                  基于语义相似度进行搜索，擅长理解问题的深层含义。适合概念性问题。
                </Text>
              </Card>

              <Card size="small">
                <div className="flex items-center mb-2">
                  <NodeIndexOutlined className="text-orange-500 mr-2" />
                  <Text strong>图谱检索模式</Text>
                </div>
                <Text type="secondary" style={{ fontSize: '12px' }}>
                  基于知识图谱中的实体关系进行搜索，擅长处理关系性问题。适合"什么与什么相关"类型的问题。
                </Text>
              </Card>
            </div>
          </div>
        </div>
      </Drawer>
    </div>
  );
}
