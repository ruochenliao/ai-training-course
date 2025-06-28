'use client';

import { useState } from 'react';
import { Card, Input, Button, List, Typography, Empty, Modal, Space, Tag, Dropdown } from 'antd';
import {
  SearchOutlined,
  MessageOutlined,
  DeleteOutlined,
  EyeOutlined,
  MoreOutlined,
  CalendarOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/utils/api';
import { formatDate, formatRelativeTime } from '@/utils';
import type { Conversation } from '@/types';

const { Search } = Input;
const { Title, Text, Paragraph } = Typography;

export default function HistoryPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const queryClient = useQueryClient();

  // 获取对话历史
  const { data: conversations, isLoading } = useQuery({
    queryKey: ['conversations', searchQuery],
    queryFn: () => apiClient.getConversations({
      search: searchQuery || undefined,
    }),
  });

  // 删除对话
  const deleteMutation = useMutation({
    mutationFn: (id: number) => apiClient.deleteConversation(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
    },
  });

  const handleDeleteConversation = (conversation: Conversation) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除对话"${conversation.title}"吗？此操作不可恢复。`,
      okText: '删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: () => deleteMutation.mutate(conversation.id),
    });
  };

  const handleViewConversation = (conversation: Conversation) => {
    setSelectedConversation(conversation);
    setDetailModalVisible(true);
  };

  const getConversationActions = (conversation: Conversation) => [
    {
      key: 'view',
      label: '查看详情',
      icon: <EyeOutlined />,
      onClick: () => handleViewConversation(conversation),
    },
    {
      key: 'continue',
      label: '继续对话',
      icon: <MessageOutlined />,
      onClick: () => {
        // 跳转到聊天页面并加载对话
        window.location.href = `/chat?conversation_id=${conversation.id}`;
      },
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'delete',
      label: '删除',
      icon: <DeleteOutlined />,
      danger: true,
      onClick: () => handleDeleteConversation(conversation),
    },
  ];

  const renderConversationItem = (conversation: Conversation) => (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Card
        className="mb-4 hover:shadow-lg transition-shadow duration-300 cursor-pointer"
        onClick={() => handleViewConversation(conversation)}
      >
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <div className="flex items-center space-x-3 mb-2">
              <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <MessageOutlined className="text-white" />
              </div>
              <div className="flex-1 min-w-0">
                <Title level={5} className="!mb-1 truncate">
                  {conversation.title}
                </Title>
                <div className="flex items-center space-x-4 text-sm text-gray-500">
                  <div className="flex items-center space-x-1">
                    <CalendarOutlined />
                    <span>{formatDate(conversation.created_at)}</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <ClockCircleOutlined />
                    <span>{formatRelativeTime(new Date(conversation.created_at))}</span>
                  </div>
                  <Tag color="blue">{conversation.message_count} 条消息</Tag>
                </div>
              </div>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <Button
              type="text"
              icon={<MessageOutlined />}
              onClick={(e) => {
                e.stopPropagation();
                window.location.href = `/chat?conversation_id=${conversation.id}`;
              }}
            >
              继续
            </Button>
            <Dropdown
              menu={{ items: getConversationActions(conversation) }}
              trigger={['click']}
              onClick={(e) => e.stopPropagation()}
            >
              <Button type="text" icon={<MoreOutlined />} />
            </Dropdown>
          </div>
        </div>
      </Card>
    </motion.div>
  );

  return (
    <div className="h-full flex flex-col bg-gray-50 dark:bg-gray-900">
      {/* 页面头部 */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <Title level={2} className="!mb-2">
              对话历史
            </Title>
            <Text type="secondary">
              查看和管理您的所有对话记录
            </Text>
          </div>
        </div>
        
        {/* 搜索框 */}
        <Search
          placeholder="搜索对话..."
          allowClear
          style={{ width: 400 }}
          onSearch={setSearchQuery}
          onChange={(e) => !e.target.value && setSearchQuery('')}
        />
      </div>

      {/* 对话列表 */}
      <div className="flex-1 overflow-y-auto custom-scrollbar p-6">
        <div className="max-w-4xl mx-auto">
          <AnimatePresence mode="wait">
            {isLoading ? (
              <div className="space-y-4">
                {[...Array(5)].map((_, index) => (
                  <Card key={index} loading className="h-24" />
                ))}
              </div>
            ) : conversations?.items?.length > 0 ? (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.3 }}
              >
                <List
                  dataSource={conversations.items}
                  renderItem={renderConversationItem}
                  pagination={{
                    total: conversations.total,
                    pageSize: 10,
                    showSizeChanger: false,
                    showQuickJumper: true,
                    showTotal: (total, range) =>
                      `第 ${range[0]}-${range[1]} 条，共 ${total} 条对话`,
                  }}
                />
              </motion.div>
            ) : (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-center py-20"
              >
                <Empty
                  image={
                    <div className="w-24 h-24 mx-auto mb-4 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                      <MessageOutlined className="text-3xl text-white" />
                    </div>
                  }
                  description={
                    <div>
                      <Title level={3} className="!mb-2">还没有对话记录</Title>
                      <Text type="secondary" className="text-base">
                        开始您的第一次AI对话吧
                      </Text>
                    </div>
                  }
                >
                  <Button
                    type="primary"
                    icon={<MessageOutlined />}
                    onClick={() => window.location.href = '/chat'}
                    className="bg-gradient-to-r from-blue-500 to-purple-600 border-0"
                  >
                    开始对话
                  </Button>
                </Empty>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* 对话详情模态框 */}
      <Modal
        title="对话详情"
        open={detailModalVisible}
        onCancel={() => {
          setDetailModalVisible(false);
          setSelectedConversation(null);
        }}
        footer={[
          <Button key="close" onClick={() => setDetailModalVisible(false)}>
            关闭
          </Button>,
          <Button
            key="continue"
            type="primary"
            icon={<MessageOutlined />}
            onClick={() => {
              window.location.href = `/chat?conversation_id=${selectedConversation?.id}`;
            }}
            className="bg-gradient-to-r from-blue-500 to-purple-600 border-0"
          >
            继续对话
          </Button>,
        ]}
        width={600}
      >
        {selectedConversation && (
          <div className="space-y-4">
            <div>
              <Text strong>对话标题：</Text>
              <div className="mt-1">
                <Text>{selectedConversation.title}</Text>
              </div>
            </div>
            
            <div>
              <Text strong>创建时间：</Text>
              <div className="mt-1">
                <Text>{formatDate(selectedConversation.created_at, 'long')}</Text>
              </div>
            </div>
            
            <div>
              <Text strong>消息数量：</Text>
              <div className="mt-1">
                <Tag color="blue">{selectedConversation.message_count} 条消息</Tag>
              </div>
            </div>
            
            <div>
              <Text strong>最后活动：</Text>
              <div className="mt-1">
                <Text>
                  {selectedConversation.last_message_at 
                    ? formatRelativeTime(new Date(selectedConversation.last_message_at))
                    : '暂无记录'
                  }
                </Text>
              </div>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
