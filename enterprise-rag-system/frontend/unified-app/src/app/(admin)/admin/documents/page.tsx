'use client';

import {useState} from 'react';
import {Button, Card, Dropdown, Input, message, Modal, Progress, Select, Table, Tag, Upload} from 'antd';
import {
    DeleteOutlined,
    DownloadOutlined,
    EyeOutlined,
    FileTextOutlined,
    MoreOutlined,
    ReloadOutlined,
    UploadOutlined,
} from '@ant-design/icons';
import {motion} from 'framer-motion';
import {useMutation, useQuery, useQueryClient} from '@tanstack/react-query';
import {apiClient} from '@/utils/api';
import {formatDate, formatFileSize, getFileTypeIcon} from '@/utils';
import type {Document} from '@/types';
import type {ColumnsType} from 'antd/es/table';

const { Search } = Input;
const { Option } = Select;
const { Dragger } = Upload;

export default function AdminDocumentsPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [uploadModalVisible, setUploadModalVisible] = useState(false);
  const queryClient = useQueryClient();

  // 获取文档列表
  const { data: documents, isLoading } = useQuery({
    queryKey: ['admin-documents', searchQuery, statusFilter, typeFilter],
    queryFn: () => apiClient.getDocuments({
      search: searchQuery || undefined,
      processing_status: statusFilter === 'all' ? undefined : statusFilter,
      file_type: typeFilter === 'all' ? undefined : typeFilter,
    }),
  });

  // 删除文档
  const deleteMutation = useMutation({
    mutationFn: (id: number) => apiClient.deleteDocument(id),
    onSuccess: () => {
      message.success('文档删除成功');
      queryClient.invalidateQueries({ queryKey: ['admin-documents'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '删除失败');
    },
  });

  const handleDeleteDocument = (document: Document) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除文档"${document.title}"吗？此操作不可恢复。`,
      okText: '删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: () => deleteMutation.mutate(document.id),
    });
  };

  const handleBatchUpload = (info: any) => {
    const { status } = info.file;
    if (status === 'done') {
      message.success(`${info.file.name} 文件上传成功`);
      queryClient.invalidateQueries({ queryKey: ['admin-documents'] });
    } else if (status === 'error') {
      message.error(`${info.file.name} 文件上传失败`);
    }
  };

  const getDocumentActions = (document: Document) => [
    {
      key: 'view',
      label: '查看详情',
      icon: <EyeOutlined />,
      onClick: () => {
        // 查看文档详情
        console.log('查看文档:', document.id);
      },
    },
    {
      key: 'download',
      label: '下载',
      icon: <DownloadOutlined />,
      onClick: () => {
        // 下载文档
        console.log('下载文档:', document.id);
      },
    },
    {
      key: 'reprocess',
      label: '重新处理',
      icon: <ReloadOutlined />,
      onClick: () => {
        Modal.confirm({
          title: '重新处理文档',
          content: `确定要重新处理文档"${document.title}"吗？`,
          onOk: () => {
            message.success('文档已加入处理队列');
          },
        });
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
      onClick: () => handleDeleteDocument(document),
    },
  ];

  const getStatusColor = (status: string) => {
    const colorMap: Record<string, string> = {
      pending: 'orange',
      processing: 'blue',
      completed: 'green',
      failed: 'red',
      cancelled: 'gray',
    };
    return colorMap[status] || 'default';
  };

  const getStatusText = (status: string) => {
    const textMap: Record<string, string> = {
      pending: '等待处理',
      processing: '处理中',
      completed: '已完成',
      failed: '处理失败',
      cancelled: '已取消',
    };
    return textMap[status] || status;
  };

  const columns: ColumnsType<Document> = [
    {
      title: '文档',
      key: 'document',
      render: (_, document) => (
        <div className="flex items-center space-x-3">
          <div className="text-2xl">
            {getFileTypeIcon(document.file_type)}
          </div>
          <div>
            <div className="font-medium truncate max-w-xs" title={document.title}>
              {document.title}
            </div>
            <div className="text-sm text-gray-500">
              {document.file_name}
            </div>
          </div>
        </div>
      ),
    },
    {
      title: '文件类型',
      dataIndex: 'file_type',
      key: 'file_type',
      render: (type) => (
        <Tag color="blue">{type.toUpperCase()}</Tag>
      ),
    },
    {
      title: '文件大小',
      dataIndex: 'file_size',
      key: 'file_size',
      render: (size) => formatFileSize(size),
    },
    {
      title: '处理状态',
      key: 'processing_status',
      render: (_, document) => (
        <div>
          <Tag color={getStatusColor(document.processing_status)}>
            {getStatusText(document.processing_status)}
          </Tag>
          {document.processing_status === 'processing' && (
            <Progress
              percent={Math.floor(Math.random() * 100)}
              size="small"
              className="mt-1"
            />
          )}
        </div>
      ),
    },
    {
      title: '知识库',
      key: 'knowledge_base',
      render: (_, document) => (
        <span className="text-blue-600 cursor-pointer hover:underline">
          {document.knowledge_base?.name || `ID: ${document.knowledge_base_id}`}
        </span>
      ),
    },
    {
      title: '分块数量',
      dataIndex: 'chunk_count',
      key: 'chunk_count',
      render: (count) => (
        <span className="text-sm text-gray-600">{count} 块</span>
      ),
    },
    {
      title: '上传时间',
      key: 'created_at',
      render: (_, document) => (
        <span className="text-sm text-gray-500">
          {formatDate(document.created_at)}
        </span>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, document) => (
        <Dropdown
          menu={{ items: getDocumentActions(document) }}
          trigger={['click']}
        >
          <Button type="text" icon={<MoreOutlined />} />
        </Dropdown>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      {/* 页面头部 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">
            文档管理
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            管理系统中的所有文档和处理状态
          </p>
        </div>
        
        <Button
          type="primary"
          icon={<UploadOutlined />}
          onClick={() => setUploadModalVisible(true)}
          className="bg-gradient-to-r from-blue-500 to-purple-600 border-0"
        >
          批量上传
        </Button>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[
          { title: '总文档数', value: documents?.total || 0, color: 'blue' },
          { title: '处理中', value: documents?.items?.filter(d => d.processing_status === 'processing').length || 0, color: 'orange' },
          { title: '已完成', value: documents?.items?.filter(d => d.processing_status === 'completed').length || 0, color: 'green' },
          { title: '处理失败', value: documents?.items?.filter(d => d.processing_status === 'failed').length || 0, color: 'red' },
        ].map((stat, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: index * 0.1 }}
          >
            <Card className="text-center">
              <div className={`text-2xl font-bold text-${stat.color}-500`}>
                {stat.value}
              </div>
              <div className="text-sm text-gray-500">{stat.title}</div>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* 搜索和筛选 */}
      <Card className="shadow-sm">
        <div className="flex items-center space-x-4">
          <Search
            placeholder="搜索文档标题、文件名..."
            allowClear
            style={{ width: 300 }}
            onSearch={setSearchQuery}
            onChange={(e) => !e.target.value && setSearchQuery('')}
          />
          
          <Select
            value={statusFilter}
            onChange={setStatusFilter}
            style={{ width: 150 }}
          >
            <Option value="all">全部状态</Option>
            <Option value="pending">等待处理</Option>
            <Option value="processing">处理中</Option>
            <Option value="completed">已完成</Option>
            <Option value="failed">处理失败</Option>
          </Select>
          
          <Select
            value={typeFilter}
            onChange={setTypeFilter}
            style={{ width: 120 }}
          >
            <Option value="all">全部类型</Option>
            <Option value="pdf">PDF</Option>
            <Option value="doc">DOC</Option>
            <Option value="docx">DOCX</Option>
            <Option value="txt">TXT</Option>
            <Option value="md">Markdown</Option>
          </Select>
        </div>
      </Card>

      {/* 文档列表 */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <Card className="shadow-sm">
          <Table
            columns={columns}
            dataSource={documents?.items || []}
            loading={isLoading}
            rowKey="id"
            pagination={{
              total: documents?.total || 0,
              pageSize: 20,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total, range) =>
                `第 ${range[0]}-${range[1]} 条，共 ${total} 条文档`,
            }}
          />
        </Card>
      </motion.div>

      {/* 批量上传模态框 */}
      <Modal
        title="批量上传文档"
        open={uploadModalVisible}
        onCancel={() => setUploadModalVisible(false)}
        footer={null}
        width={600}
      >
        <div className="space-y-4">
          <Dragger
            name="files"
            multiple
            action="/api/v1/documents/upload"
            onChange={handleBatchUpload}
            accept=".pdf,.doc,.docx,.txt,.md"
          >
            <p className="ant-upload-drag-icon">
              <FileTextOutlined className="text-4xl text-blue-500" />
            </p>
            <p className="ant-upload-text">
              点击或拖拽文件到此区域上传
            </p>
            <p className="ant-upload-hint">
              支持单个或批量上传。支持 PDF、DOC、DOCX、TXT、MD 格式
            </p>
          </Dragger>
          
          <div className="text-sm text-gray-500">
            <p>上传说明：</p>
            <ul className="list-disc list-inside space-y-1 ml-4">
              <li>单个文件大小不超过 50MB</li>
              <li>支持的格式：PDF、DOC、DOCX、TXT、Markdown</li>
              <li>文档将自动进行内容提取和向量化处理</li>
              <li>处理完成后可在知识库中使用</li>
            </ul>
          </div>
        </div>
      </Modal>
    </div>
  );
}
