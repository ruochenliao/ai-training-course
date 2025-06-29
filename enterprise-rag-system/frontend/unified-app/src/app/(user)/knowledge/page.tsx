'use client';

import {useState} from 'react';
import {Button, Card, Dropdown, Empty, Form, Input, message, Modal, Select, Space, Tag, Typography} from 'antd';
import {
    BookOutlined,
    DeleteOutlined,
    EditOutlined,
    EyeOutlined,
    FileTextOutlined,
    MoreOutlined,
    PlusOutlined,
    ShareAltOutlined,
} from '@ant-design/icons';
import {AnimatePresence, motion} from 'framer-motion';
import {useMutation, useQuery, useQueryClient} from '@tanstack/react-query';
import {apiClient} from '@/utils/api';
import {formatDate, formatNumber} from '@/utils';
import type {KnowledgeBase} from '@/types';

const { Search } = Input;
const { Title, Text, Paragraph } = Typography;
const { Option } = Select;

export default function KnowledgePage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState<string>('all');
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [editingKb, setEditingKb] = useState<KnowledgeBase | null>(null);
  const [form] = Form.useForm();
  const queryClient = useQueryClient();

  // 获取知识库列表
  const { data: knowledgeBases, isLoading } = useQuery({
    queryKey: ['knowledge-bases', searchQuery, filterType],
    queryFn: () => apiClient.getKnowledgeBases({
      search: searchQuery || undefined,
      knowledge_type: filterType === 'all' ? undefined : filterType,
    }),
  });

  // 创建知识库
  const createMutation = useMutation({
    mutationFn: (data: any) => apiClient.createKnowledgeBase(data),
    onSuccess: () => {
      message.success('知识库创建成功');
      setCreateModalVisible(false);
      form.resetFields();
      queryClient.invalidateQueries({ queryKey: ['knowledge-bases'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '创建失败');
    },
  });

  // 删除知识库
  const deleteMutation = useMutation({
    mutationFn: (id: number) => apiClient.deleteKnowledgeBase(id),
    onSuccess: () => {
      message.success('知识库删除成功');
      queryClient.invalidateQueries({ queryKey: ['knowledge-bases'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '删除失败');
    },
  });

  const handleCreateKnowledgeBase = (values: any) => {
    createMutation.mutate(values);
  };

  const handleDeleteKnowledgeBase = (kb: KnowledgeBase) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除知识库"${kb.name}"吗？此操作不可恢复。`,
      okText: '删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: () => deleteMutation.mutate(kb.id),
    });
  };

  const getKnowledgeBaseActions = (kb: KnowledgeBase) => [
    {
      key: 'view',
      label: '查看详情',
      icon: <EyeOutlined />,
      onClick: () => console.log('查看', kb.id),
    },
    {
      key: 'edit',
      label: '编辑',
      icon: <EditOutlined />,
      onClick: () => {
        setEditingKb(kb);
        form.setFieldsValue(kb);
        setCreateModalVisible(true);
      },
    },
    {
      key: 'share',
      label: '分享',
      icon: <ShareAltOutlined />,
      onClick: () => console.log('分享', kb.id),
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'delete',
      label: '删除',
      icon: <DeleteOutlined />,
      danger: true,
      onClick: () => handleDeleteKnowledgeBase(kb),
    },
  ];

  const renderKnowledgeBaseCard = (kb: KnowledgeBase, index: number) => (
    <motion.div
      key={kb.id}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.1 }}
    >
      <Card
        className="h-full hover:shadow-lg transition-all duration-300 cursor-pointer group"
        actions={[
          <Button
            key="view"
            type="text"
            icon={<EyeOutlined />}
            onClick={() => console.log('查看', kb.id)}
          >
            查看
          </Button>,
          <Button
            key="edit"
            type="text"
            icon={<EditOutlined />}
            onClick={() => {
              setEditingKb(kb);
              form.setFieldsValue(kb);
              setCreateModalVisible(true);
            }}
          >
            编辑
          </Button>,
          <Dropdown
            key="more"
            menu={{ items: getKnowledgeBaseActions(kb) }}
            trigger={['click']}
          >
            <Button type="text" icon={<MoreOutlined />} />
          </Dropdown>,
        ]}
      >
        <div className="flex items-start space-x-4">
          <div className="flex-shrink-0">
            <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
              <BookOutlined className="text-white text-lg" />
            </div>
          </div>
          
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between mb-2">
              <Title level={5} className="!mb-0 truncate">
                {kb.name}
              </Title>
              <div className="flex items-center space-x-1">
                <Tag color={kb.visibility === 'public' ? 'green' : 'blue'}>
                  {kb.visibility === 'public' ? '公开' : '私有'}
                </Tag>
                <Tag color="purple">
                  {kb.knowledge_type}
                </Tag>
              </div>
            </div>
            
            <Paragraph
              className="text-gray-600 dark:text-gray-300 mb-3"
              ellipsis={{ rows: 2 }}
            >
              {kb.description || '暂无描述'}
            </Paragraph>
            
            <div className="flex items-center justify-between text-sm text-gray-500">
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-1">
                  <FileTextOutlined />
                  <span>{formatNumber(kb.document_count)} 文档</span>
                </div>
                <span>创建于 {formatDate(kb.created_at)}</span>
              </div>
            </div>
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
              知识库管理
            </Title>
            <Text type="secondary">
              创建和管理您的知识库，组织企业知识资产
            </Text>
          </div>
          
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => {
              setEditingKb(null);
              form.resetFields();
              setCreateModalVisible(true);
            }}
            className="bg-gradient-to-r from-blue-500 to-purple-600 border-0"
          >
            创建知识库
          </Button>
        </div>
        
        {/* 搜索和筛选 */}
        <div className="flex items-center space-x-4">
          <Search
            placeholder="搜索知识库..."
            allowClear
            style={{ width: 300 }}
            onSearch={setSearchQuery}
            onChange={(e) => !e.target.value && setSearchQuery('')}
          />
          
          <Select
            value={filterType}
            onChange={setFilterType}
            style={{ width: 150 }}
          >
            <Option value="all">全部类型</Option>
            <Option value="general">通用</Option>
            <Option value="technical">技术</Option>
            <Option value="business">业务</Option>
            <Option value="academic">学术</Option>
          </Select>
        </div>
      </div>

      {/* 知识库列表 */}
      <div className="flex-1 overflow-y-auto custom-scrollbar p-6">
        <AnimatePresence mode="wait">
          {isLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[...Array(6)].map((_, index) => (
                <Card key={index} loading className="h-48" />
              ))}
            </div>
          ) : knowledgeBases?.items?.length > 0 ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.3 }}
              className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
            >
              {knowledgeBases.items.map((kb, index) => 
                renderKnowledgeBaseCard(kb, index)
              )}
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
                    <BookOutlined className="text-3xl text-white" />
                  </div>
                }
                description={
                  <div>
                    <Title level={3} className="!mb-2">还没有知识库</Title>
                    <Text type="secondary" className="text-base">
                      创建您的第一个知识库，开始管理企业知识
                    </Text>
                  </div>
                }
              >
                <Button
                  type="primary"
                  icon={<PlusOutlined />}
                  onClick={() => setCreateModalVisible(true)}
                  className="bg-gradient-to-r from-blue-500 to-purple-600 border-0"
                >
                  创建知识库
                </Button>
              </Empty>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* 创建/编辑知识库模态框 */}
      <Modal
        title={editingKb ? '编辑知识库' : '创建知识库'}
        open={createModalVisible}
        onCancel={() => {
          setCreateModalVisible(false);
          setEditingKb(null);
          form.resetFields();
        }}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleCreateKnowledgeBase}
          className="mt-4"
        >
          <Form.Item
            name="name"
            label="知识库名称"
            rules={[
              { required: true, message: '请输入知识库名称' },
              { min: 2, message: '名称至少2个字符' },
              { max: 50, message: '名称不能超过50个字符' },
            ]}
          >
            <Input placeholder="输入知识库名称" />
          </Form.Item>
          
          <Form.Item
            name="description"
            label="描述"
            rules={[{ max: 200, message: '描述不能超过200个字符' }]}
          >
            <Input.TextArea
              placeholder="输入知识库描述（可选）"
              rows={3}
            />
          </Form.Item>
          
          <Form.Item
            name="knowledge_type"
            label="知识库类型"
            initialValue="general"
          >
            <Select>
              <Option value="general">通用</Option>
              <Option value="technical">技术</Option>
              <Option value="business">业务</Option>
              <Option value="academic">学术</Option>
              <Option value="legal">法律</Option>
              <Option value="medical">医疗</Option>
            </Select>
          </Form.Item>
          
          <Form.Item
            name="visibility"
            label="可见性"
            initialValue="private"
          >
            <Select>
              <Option value="private">私有</Option>
              <Option value="public">公开</Option>
              <Option value="shared">共享</Option>
            </Select>
          </Form.Item>
          
          <Form.Item className="mb-0 text-right">
            <Space>
              <Button
                onClick={() => {
                  setCreateModalVisible(false);
                  setEditingKb(null);
                  form.resetFields();
                }}
              >
                取消
              </Button>
              <Button
                type="primary"
                htmlType="submit"
                loading={createMutation.isPending}
                className="bg-gradient-to-r from-blue-500 to-purple-600 border-0"
              >
                {editingKb ? '更新' : '创建'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
