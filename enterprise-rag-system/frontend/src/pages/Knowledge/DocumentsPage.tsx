import React, { useEffect, useState } from 'react'
import {
  Button,
  Card,
  Col,
  Row,
  Space,
  Typography,
  Table,
  Tag,
  Progress,
  Upload,
  Modal,
  Select,
  Input,
  Tooltip,
  Dropdown,
  message,
  Statistic,
  Alert,
} from 'antd'
import {
  FileTextOutlined,
  UploadOutlined,
  EyeOutlined,
  DownloadOutlined,
  DeleteOutlined,
  ReloadOutlined,
  InboxOutlined,
  SearchOutlined,
  FilterOutlined,
  MoreOutlined,
  ClockCircleOutlined,
  UserOutlined,
  FileOutlined,
} from '@ant-design/icons'
import { documentsApi, type Document, type DocumentListParams } from '@/api/documents'
import { knowledgeApi, type KnowledgeBase } from '@/api/knowledge'

const { Title, Paragraph, Text } = Typography
const { Option } = Select
const { Dragger } = Upload

const DocumentsPage: React.FC = () => {
  const [documents, setDocuments] = useState<Document[]>([])
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([])
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadModalVisible, setUploadModalVisible] = useState(false)
  const [selectedKnowledgeBase, setSelectedKnowledgeBase] = useState<number | undefined>()
  const [searchText, setSearchText] = useState('')
  const [statusFilter, setStatusFilter] = useState<string | undefined>()
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)

  // 获取文档列表
  const fetchDocuments = async (params: DocumentListParams = {}) => {
    try {
      setLoading(true)
      const response = await documentsApi.getDocuments({
        page,
        size: pageSize,
        search: searchText,
        status: statusFilter,
        knowledge_base_id: selectedKnowledgeBase,
        ...params,
      })

      if (response.data) {
        setDocuments(response.data.items)
        setTotal(response.data.total)
      }
    } catch (error: any) {
      message.error(error.response?.data?.message || '获取文档列表失败')
    } finally {
      setLoading(false)
    }
  }

  // 获取知识库列表
  const fetchKnowledgeBases = async () => {
    try {
      const response = await knowledgeApi.getKnowledgeBases()
      if (response.data) {
        setKnowledgeBases(response.data.items)
      }
    } catch (error: any) {
      message.error(error.response?.data?.message || '获取知识库列表失败')
    }
  }

  useEffect(() => {
    fetchDocuments()
    fetchKnowledgeBases()
  }, [page, pageSize, searchText, statusFilter, selectedKnowledgeBase])

  // 上传文档
  const handleUpload = async (info: any) => {
    if (!selectedKnowledgeBase) {
      message.error('请先选择知识库')
      return
    }

    const { fileList } = info
    const files = fileList.map((file: any) => file.originFileObj).filter(Boolean)

    if (files.length === 0) return

    try {
      setUploading(true)
      await documentsApi.uploadDocuments({
        knowledge_base_id: selectedKnowledgeBase,
        files,
        auto_process: true,
      })

      message.success('文档上传成功')
      setUploadModalVisible(false)
      fetchDocuments()
    } catch (error: any) {
      message.error(error.response?.data?.message || '文档上传失败')
    } finally {
      setUploading(false)
    }
  }

  // 删除文档
  const handleDelete = async (id: number) => {
    try {
      await documentsApi.deleteDocument(id)
      message.success('文档删除成功')
      fetchDocuments()
    } catch (error: any) {
      message.error(error.response?.data?.message || '删除文档失败')
    }
  }

  // 重新处理文档
  const handleReprocess = async (id: number) => {
    try {
      await documentsApi.reprocessDocument(id)
      message.success('文档重新处理中...')
      fetchDocuments()
    } catch (error: any) {
      message.error(error.response?.data?.message || '重新处理失败')
    }
  }

  // 下载文档
  const handleDownload = async (id: number, filename: string) => {
    try {
      const blob = await documentsApi.downloadDocument(id)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error: any) {
      message.error(error.response?.data?.message || '下载文档失败')
    }
  }

  // 状态渲染
  const renderStatus = (status: string, progress: number) => {
    const statusConfig = {
      pending: { color: 'default', text: '待处理' },
      processing: { color: 'processing', text: '处理中' },
      completed: { color: 'success', text: '已完成' },
      failed: { color: 'error', text: '处理失败' },
    }

    const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.pending

    return (
      <Space direction='vertical' size={4}>
        <Tag color={config.color}>{config.text}</Tag>
        {status === 'processing' && <Progress percent={progress} size='small' />}
      </Space>
    )
  }

  // 表格列定义
  const columns = [
    {
      title: '文档名称',
      dataIndex: 'original_filename',
      key: 'filename',
      render: (text: string, record: Document) => (
        <Space>
          <FileOutlined style={{ color: '#1890ff' }} />
          <Text strong>{text}</Text>
          <Text type='secondary'>({(record.file_size / 1024 / 1024).toFixed(2)} MB)</Text>
        </Space>
      ),
    },
    {
      title: '知识库',
      dataIndex: 'knowledge_base_name',
      key: 'knowledge_base',
      render: (text: string) => text || '-',
    },
    {
      title: '文件类型',
      dataIndex: 'file_type',
      key: 'file_type',
      render: (type: string) => <Tag color='blue'>{type.toUpperCase()}</Tag>,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string, record: Document) => renderStatus(status, record.processing_progress),
    },
    {
      title: '分块数',
      dataIndex: 'chunk_count',
      key: 'chunk_count',
      render: (count: number) => count || 0,
    },
    {
      title: '向量数',
      dataIndex: 'vector_count',
      key: 'vector_count',
      render: (count: number) => count || 0,
    },
    {
      title: '上传时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => (
        <Tooltip title={new Date(date).toLocaleString()}>
          <Space>
            <ClockCircleOutlined />
            <Text>{new Date(date).toLocaleDateString()}</Text>
          </Space>
        </Tooltip>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      width: 120,
      render: (_, record: Document) => (
        <Dropdown
          menu={{
            items: [
              {
                key: 'preview',
                icon: <EyeOutlined />,
                label: '预览',
              },
              {
                key: 'download',
                icon: <DownloadOutlined />,
                label: '下载',
                onClick: () => handleDownload(record.id, record.original_filename),
              },
              {
                key: 'reprocess',
                icon: <ReloadOutlined />,
                label: '重新处理',
                onClick: () => handleReprocess(record.id),
                disabled: record.status === 'processing',
              },
              {
                type: 'divider',
              },
              {
                key: 'delete',
                icon: <DeleteOutlined />,
                label: '删除',
                danger: true,
                onClick: () => {
                  Modal.confirm({
                    title: '确认删除',
                    content: `确定要删除文档"${record.original_filename}"吗？此操作不可恢复。`,
                    okText: '删除',
                    okType: 'danger',
                    cancelText: '取消',
                    onOk: () => handleDelete(record.id),
                  })
                },
              },
            ],
          }}
          trigger={['click']}
        >
          <Button type='text' icon={<MoreOutlined />} />
        </Dropdown>
      ),
    },
  ]

  return (
    <div style={{ padding: 24 }}>
      {/* 页面标题 */}
      <div style={{ marginBottom: 24 }}>
        <Title level={2} style={{ margin: 0, color: '#1e293b' }}>
          文档管理
        </Title>
        <Paragraph style={{ margin: '8px 0 0 0', color: '#64748b', fontSize: 16 }}>上传和管理知识库文档</Paragraph>
      </div>

      {/* 统计卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic title='总文档数' value={total} prefix={<FileTextOutlined style={{ color: '#1890ff' }} />} />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title='处理中'
              value={documents.filter(doc => doc.status === 'processing').length}
              prefix={<ReloadOutlined style={{ color: '#faad14' }} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title='已完成'
              value={documents.filter(doc => doc.status === 'completed').length}
              prefix={<FileOutlined style={{ color: '#52c41a' }} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title='处理失败'
              value={documents.filter(doc => doc.status === 'failed').length}
              prefix={<DeleteOutlined style={{ color: '#ff4d4f' }} />}
            />
          </Card>
        </Col>
      </Row>

      {/* 筛选和操作栏 */}
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={16} align='middle'>
          <Col flex='auto'>
            <Space>
              <Input
                placeholder='搜索文档名称'
                prefix={<SearchOutlined />}
                value={searchText}
                onChange={e => setSearchText(e.target.value)}
                style={{ width: 200 }}
              />
              <Select
                placeholder='选择知识库'
                value={selectedKnowledgeBase}
                onChange={setSelectedKnowledgeBase}
                style={{ width: 200 }}
                allowClear
              >
                {knowledgeBases.map(kb => (
                  <Option key={kb.id} value={kb.id}>
                    {kb.name}
                  </Option>
                ))}
              </Select>
              <Select
                placeholder='状态筛选'
                value={statusFilter}
                onChange={setStatusFilter}
                style={{ width: 120 }}
                allowClear
              >
                <Option value='pending'>待处理</Option>
                <Option value='processing'>处理中</Option>
                <Option value='completed'>已完成</Option>
                <Option value='failed'>处理失败</Option>
              </Select>
            </Space>
          </Col>
          <Col>
            <Button
              type='primary'
              icon={<UploadOutlined />}
              onClick={() => setUploadModalVisible(true)}
              style={{
                background: 'linear-gradient(135deg, #0ea5e9, #8b5cf6)',
                border: 'none',
              }}
            >
              上传文档
            </Button>
          </Col>
        </Row>
      </Card>

      {/* 文档表格 */}
      <Card>
        <Table
          columns={columns}
          dataSource={documents}
          rowKey='id'
          loading={loading}
          pagination={{
            current: page,
            pageSize,
            total,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
            onChange: (page, size) => {
              setPage(page)
              setPageSize(size || 20)
            },
          }}
        />
      </Card>

      {/* 上传文档模态框 */}
      <Modal
        title='上传文档'
        open={uploadModalVisible}
        onCancel={() => setUploadModalVisible(false)}
        footer={null}
        width={600}
      >
        <Space direction='vertical' style={{ width: '100%' }} size='large'>
          <Alert
            message='上传说明'
            description='支持 PDF、Word、PowerPoint、TXT、Markdown 等格式文档，单个文件最大 100MB'
            type='info'
            showIcon
          />

          <div>
            <Text strong>选择知识库：</Text>
            <Select
              placeholder='请选择知识库'
              value={selectedKnowledgeBase}
              onChange={setSelectedKnowledgeBase}
              style={{ width: '100%', marginTop: 8 }}
            >
              {knowledgeBases.map(kb => (
                <Option key={kb.id} value={kb.id}>
                  {kb.name}
                </Option>
              ))}
            </Select>
          </div>

          <Dragger
            name='files'
            multiple
            accept='.pdf,.doc,.docx,.ppt,.pptx,.txt,.md'
            beforeUpload={() => false}
            onChange={handleUpload}
            disabled={!selectedKnowledgeBase || uploading}
          >
            <p className='ant-upload-drag-icon'>
              <InboxOutlined />
            </p>
            <p className='ant-upload-text'>点击或拖拽文件到此区域上传</p>
            <p className='ant-upload-hint'>支持单个或批量上传，严禁上传公司数据或其他敏感文件</p>
          </Dragger>

          {uploading && (
            <Alert message='正在上传文档...' description='请稍候，文档上传完成后将自动开始处理' type='info' showIcon />
          )}
        </Space>
      </Modal>
    </div>
  )
}

export default DocumentsPage
