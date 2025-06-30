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
  Dropdown,
  Modal,
  Form,
  Input,
  Select,
  Switch,
  message,
  Popconfirm,
  Tooltip,
  Statistic
} from 'antd'
import {
  DatabaseOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  MoreOutlined,
  FileTextOutlined,
  UserOutlined,
  ClockCircleOutlined
} from '@ant-design/icons'
import { useKnowledgeStore } from '@/store/knowledge'
import type { KnowledgeBase, KnowledgeBaseCreateRequest } from '@/api/knowledge'

const { Title, Paragraph, Text } = Typography
const { Option } = Select

const KnowledgeBasesPage: React.FC = () => {
  const {
    knowledgeBases,
    loading,
    total,
    fetchKnowledgeBases,
    createKnowledgeBase,
    updateKnowledgeBase,
    deleteKnowledgeBase
  } = useKnowledgeStore()

  const [createModalVisible, setCreateModalVisible] = useState(false)
  const [editModalVisible, setEditModalVisible] = useState(false)
  const [editingKb, setEditingKb] = useState<KnowledgeBase | null>(null)
  const [createForm] = Form.useForm()
  const [editForm] = Form.useForm()

  useEffect(() => {
    fetchKnowledgeBases()
  }, [fetchKnowledgeBases])

  // 创建知识库
  const handleCreate = async (values: KnowledgeBaseCreateRequest) => {
    const success = await createKnowledgeBase(values)
    if (success) {
      setCreateModalVisible(false)
      createForm.resetFields()
    }
  }

  // 编辑知识库
  const handleEdit = (kb: KnowledgeBase) => {
    setEditingKb(kb)
    editForm.setFieldsValue({
      name: kb.name,
      description: kb.description,
      visibility: kb.visibility
    })
    setEditModalVisible(true)
  }

  // 更新知识库
  const handleUpdate = async (values: any) => {
    if (!editingKb) return

    const success = await updateKnowledgeBase(editingKb.id, values)
    if (success) {
      setEditModalVisible(false)
      setEditingKb(null)
      editForm.resetFields()
    }
  }

  // 删除知识库
  const handleDelete = async (id: number) => {
    await deleteKnowledgeBase(id)
  }

  // 表格列定义
  const columns = [
    {
      title: '知识库名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: KnowledgeBase) => (
        <Space>
          <DatabaseOutlined style={{ color: '#1890ff' }} />
          <Text strong>{text}</Text>
        </Space>
      )
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
      render: (text: string) => text || '-'
    },
    {
      title: '可见性',
      dataIndex: 'visibility',
      key: 'visibility',
      render: (visibility: string) => (
        <Tag color={visibility === 'public' ? 'green' : 'blue'}>
          {visibility === 'public' ? '公开' : '私有'}
        </Tag>
      )
    },
    {
      title: '文档数量',
      dataIndex: 'document_count',
      key: 'document_count',
      render: (count: number) => (
        <Space>
          <FileTextOutlined />
          <Text>{count}</Text>
        </Space>
      )
    },
    {
      title: '向量数量',
      dataIndex: 'vector_count',
      key: 'vector_count',
      render: (count: number) => (
        <Text type="secondary">{count.toLocaleString()}</Text>
      )
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => (
        <Tooltip title={new Date(date).toLocaleString()}>
          <Space>
            <ClockCircleOutlined />
            <Text>{new Date(date).toLocaleDateString()}</Text>
          </Space>
        </Tooltip>
      )
    },
    {
      title: '操作',
      key: 'actions',
      width: 120,
      render: (_, record: KnowledgeBase) => (
        <Dropdown
          menu={{
            items: [
              {
                key: 'view',
                icon: <EyeOutlined />,
                label: '查看详情'
              },
              {
                key: 'edit',
                icon: <EditOutlined />,
                label: '编辑',
                onClick: () => handleEdit(record)
              },
              {
                type: 'divider'
              },
              {
                key: 'delete',
                icon: <DeleteOutlined />,
                label: '删除',
                danger: true,
                onClick: () => {
                  Modal.confirm({
                    title: '确认删除',
                    content: `确定要删除知识库"${record.name}"吗？此操作不可恢复。`,
                    okText: '删除',
                    okType: 'danger',
                    cancelText: '取消',
                    onOk: () => handleDelete(record.id)
                  })
                }
              }
            ]
          }}
          trigger={['click']}
        >
          <Button type="text" icon={<MoreOutlined />} />
        </Dropdown>
      )
    }
  ]

  return (
    <div style={{ padding: 24 }}>
      {/* 页面标题 */}
      <div style={{ marginBottom: 24 }}>
        <Title level={2} style={{ margin: 0, color: '#1e293b' }}>
          知识库管理
        </Title>
        <Paragraph style={{ margin: '8px 0 0 0', color: '#64748b', fontSize: 16 }}>
          管理和维护企业知识库
        </Paragraph>
      </div>

      {/* 统计卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="总知识库数"
              value={total}
              prefix={<DatabaseOutlined style={{ color: '#1890ff' }} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="总文档数"
              value={knowledgeBases.reduce((sum, kb) => sum + kb.document_count, 0)}
              prefix={<FileTextOutlined style={{ color: '#52c41a' }} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="总向量数"
              value={knowledgeBases.reduce((sum, kb) => sum + kb.vector_count, 0)}
              prefix={<UserOutlined style={{ color: '#722ed1' }} />}
            />
          </Card>
        </Col>
      </Row>

      {/* 操作栏 */}
      <Card style={{ marginBottom: 16 }}>
        <Row justify="space-between" align="middle">
          <Col>
            <Space>
              <Text strong>知识库列表</Text>
              <Text type="secondary">({total} 个知识库)</Text>
            </Space>
          </Col>
          <Col>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => setCreateModalVisible(true)}
              style={{
                background: 'linear-gradient(135deg, #0ea5e9, #8b5cf6)',
                border: 'none',
              }}
            >
              创建知识库
            </Button>
          </Col>
        </Row>
      </Card>

      {/* 知识库表格 */}
      <Card>
        <Table
          columns={columns}
          dataSource={knowledgeBases}
          rowKey="id"
          loading={loading}
          pagination={{
            total,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
          }}
        />
      </Card>

      {/* 创建知识库模态框 */}
      <Modal
        title="创建知识库"
        open={createModalVisible}
        onCancel={() => {
          setCreateModalVisible(false)
          createForm.resetFields()
        }}
        footer={null}
        width={600}
      >
        <Form
          form={createForm}
          layout="vertical"
          onFinish={handleCreate}
        >
          <Form.Item
            name="name"
            label="知识库名称"
            rules={[
              { required: true, message: '请输入知识库名称' },
              { max: 100, message: '名称不能超过100个字符' }
            ]}
          >
            <Input placeholder="请输入知识库名称" />
          </Form.Item>

          <Form.Item
            name="description"
            label="描述"
            rules={[{ max: 500, message: '描述不能超过500个字符' }]}
          >
            <Input.TextArea
              placeholder="请输入知识库描述"
              rows={3}
            />
          </Form.Item>

          <Form.Item
            name="is_public"
            label="可见性"
            valuePropName="checked"
            initialValue={false}
          >
            <Switch
              checkedChildren="公开"
              unCheckedChildren="私有"
            />
          </Form.Item>

          <Form.Item
            name="knowledge_type"
            label="知识库类型"
            initialValue="general"
          >
            <Select placeholder="请选择知识库类型">
              <Option value="general">通用知识库</Option>
              <Option value="technical">技术文档</Option>
              <Option value="business">业务知识</Option>
              <Option value="legal">法律法规</Option>
              <Option value="other">其他</Option>
            </Select>
          </Form.Item>

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button onClick={() => {
                setCreateModalVisible(false)
                createForm.resetFields()
              }}>
                取消
              </Button>
              <Button type="primary" htmlType="submit" loading={loading}>
                创建
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 编辑知识库模态框 */}
      <Modal
        title="编辑知识库"
        open={editModalVisible}
        onCancel={() => {
          setEditModalVisible(false)
          setEditingKb(null)
          editForm.resetFields()
        }}
        footer={null}
        width={600}
      >
        <Form
          form={editForm}
          layout="vertical"
          onFinish={handleUpdate}
        >
          <Form.Item
            name="name"
            label="知识库名称"
            rules={[
              { required: true, message: '请输入知识库名称' },
              { max: 100, message: '名称不能超过100个字符' }
            ]}
          >
            <Input placeholder="请输入知识库名称" />
          </Form.Item>

          <Form.Item
            name="description"
            label="描述"
            rules={[{ max: 500, message: '描述不能超过500个字符' }]}
          >
            <Input.TextArea
              placeholder="请输入知识库描述"
              rows={3}
            />
          </Form.Item>

          <Form.Item
            name="visibility"
            label="可见性"
          >
            <Select>
              <Option value="public">公开</Option>
              <Option value="private">私有</Option>
            </Select>
          </Form.Item>

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button onClick={() => {
                setEditModalVisible(false)
                setEditingKb(null)
                editForm.resetFields()
              }}>
                取消
              </Button>
              <Button type="primary" htmlType="submit" loading={loading}>
                更新
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default KnowledgeBasesPage
