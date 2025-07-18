import React, { useState, useEffect } from 'react'
import {
  Card,
  Tabs,
  Table,
  Button,
  Space,
  Input,
  Select,
  Modal,
  Form,
  Switch,
  InputNumber,
  Tag,
  Alert,
  Descriptions,
  Upload,
  message,
  Popconfirm,
  Tooltip,
  Badge,
  Statistic,
  Row,
  Col
} from 'antd'
import {
  SettingOutlined,
  ReloadOutlined,
  ExportOutlined,
  ImportOutlined,
  SearchOutlined,
  EditOutlined,
  UndoOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  WarningOutlined,
  SaveOutlined,
  UploadOutlined
} from '@ant-design/icons'
import { motion } from 'framer-motion'
import './SystemManagementPage.css'

const { TabPane } = Tabs
const { Search } = Input
const { Option } = Select
const { TextArea } = Input

interface ConfigItem {
  key: string
  value: any
  description: string
  category: string
  data_type: string
  is_sensitive: boolean
  requires_restart: boolean
  created_at?: string
  updated_at?: string
  updated_by?: number
}

interface ConfigCategory {
  name: string
  description: string
  items: ConfigItem[]
}

interface SystemHealth {
  status: string
  timestamp: string
  services: Record<string, any>
  system_metrics: Record<string, any>
  application_metrics: Record<string, any>
}

const SystemManagementPage: React.FC = () => {
  const [loading, setLoading] = useState(false)
  const [categories, setCategories] = useState<ConfigCategory[]>([])
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null)
  const [selectedCategory, setSelectedCategory] = useState<string>('system')
  const [searchKeyword, setSearchKeyword] = useState('')
  const [editModalVisible, setEditModalVisible] = useState(false)
  const [editingConfig, setEditingConfig] = useState<ConfigItem | null>(null)
  const [importModalVisible, setImportModalVisible] = useState(false)
  const [validationErrors, setValidationErrors] = useState<Record<string, string[]>>({})
  const [form] = Form.useForm()

  useEffect(() => {
    loadConfigCategories()
    loadSystemHealth()
  }, [])

  const loadConfigCategories = async () => {
    setLoading(true)
    try {
      // 模拟API调用
      const mockCategories: ConfigCategory[] = [
        {
          name: 'system',
          description: '系统基础配置',
          items: [
            {
              key: 'system.max_upload_size',
              value: 104857600,
              description: '最大文件上传大小（字节）',
              category: 'system',
              data_type: 'int',
              is_sensitive: false,
              requires_restart: false
            },
            {
              key: 'system.session_timeout',
              value: 3600,
              description: '会话超时时间（秒）',
              category: 'system',
              data_type: 'int',
              is_sensitive: false,
              requires_restart: true
            }
          ]
        },
        {
          name: 'security',
          description: '安全相关配置',
          items: [
            {
              key: 'security.password_min_length',
              value: 8,
              description: '密码最小长度',
              category: 'security',
              data_type: 'int',
              is_sensitive: false,
              requires_restart: false
            },
            {
              key: 'security.enable_2fa',
              value: false,
              description: '启用双因素认证',
              category: 'security',
              data_type: 'bool',
              is_sensitive: false,
              requires_restart: true
            }
          ]
        },
        {
          name: 'rag',
          description: 'RAG检索配置',
          items: [
            {
              key: 'rag.default_top_k',
              value: 10,
              description: '默认检索结果数量',
              category: 'rag',
              data_type: 'int',
              is_sensitive: false,
              requires_restart: false
            },
            {
              key: 'rag.similarity_threshold',
              value: 0.7,
              description: '相似度阈值',
              category: 'rag',
              data_type: 'float',
              is_sensitive: false,
              requires_restart: false
            }
          ]
        }
      ]
      
      setCategories(mockCategories)
    } catch (error) {
      message.error('加载配置失败')
    } finally {
      setLoading(false)
    }
  }

  const loadSystemHealth = async () => {
    try {
      // 模拟API调用
      const mockHealth: SystemHealth = {
        status: 'healthy',
        timestamp: new Date().toISOString(),
        services: {
          database: { status: 'healthy', response_time: 0.05 },
          redis: { status: 'healthy', response_time: 0.02 },
          milvus: { status: 'healthy', response_time: 0.08 },
          neo4j: { status: 'degraded', response_time: 0.15 }
        },
        system_metrics: {
          cpu_percent: 45.2,
          memory_percent: 68.5,
          disk_percent: 32.1,
          process_count: 156,
          uptime: 86400
        },
        application_metrics: {
          active_users: 23,
          total_requests: 1547,
          error_rate: 0.02,
          avg_response_time: 0.25,
          cache_hit_rate: 0.85
        }
      }
      
      setSystemHealth(mockHealth)
    } catch (error) {
      console.error('加载系统健康状态失败:', error)
    }
  }

  const handleEditConfig = (config: ConfigItem) => {
    setEditingConfig(config)
    form.setFieldsValue({
      key: config.key,
      value: config.value,
      description: config.description
    })
    setEditModalVisible(true)
  }

  const handleSaveConfig = async () => {
    try {
      const values = await form.validateFields()
      
      // 模拟API调用
      console.log('保存配置:', values)
      
      message.success('配置保存成功')
      setEditModalVisible(false)
      loadConfigCategories()
      
      if (editingConfig?.requires_restart) {
        Modal.info({
          title: '需要重启',
          content: '此配置项需要重启系统才能生效',
          okText: '知道了'
        })
      }
    } catch (error) {
      message.error('保存配置失败')
    }
  }

  const handleResetConfig = async (configKey: string) => {
    try {
      // 模拟API调用
      console.log('重置配置:', configKey)
      
      message.success('配置已重置为默认值')
      loadConfigCategories()
    } catch (error) {
      message.error('重置配置失败')
    }
  }

  const handleValidateConfigs = async () => {
    try {
      // 模拟API调用
      const mockErrors = {
        'security.password_min_length': ['密码长度不能少于6位'],
        'rag.similarity_threshold': ['相似度阈值必须在0-1之间']
      }
      
      setValidationErrors(mockErrors)
      
      if (Object.keys(mockErrors).length === 0) {
        message.success('所有配置验证通过')
      } else {
        message.warning(`发现${Object.keys(mockErrors).length}个配置错误`)
      }
    } catch (error) {
      message.error('配置验证失败')
    }
  }

  const handleExportConfigs = async () => {
    try {
      // 模拟导出
      const exportData = {
        export_time: new Date().toISOString(),
        configs: categories.reduce((acc, cat) => {
          cat.items.forEach(item => {
            acc[item.key] = item
          })
          return acc
        }, {} as Record<string, ConfigItem>)
      }
      
      const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `system_config_${Date.now()}.json`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
      
      message.success('配置导出成功')
    } catch (error) {
      message.error('配置导出失败')
    }
  }

  const handleImportConfigs = async (file: File) => {
    try {
      const text = await file.text()
      const importData = JSON.parse(text)
      
      // 模拟导入
      console.log('导入配置:', importData)
      
      message.success('配置导入成功')
      setImportModalVisible(false)
      loadConfigCategories()
    } catch (error) {
      message.error('配置导入失败')
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'success'
      case 'degraded': return 'warning'
      case 'unhealthy': return 'error'
      default: return 'default'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy': return <CheckCircleOutlined />
      case 'degraded': return <ExclamationCircleOutlined />
      case 'unhealthy': return <WarningOutlined />
      default: return null
    }
  }

  const configColumns = [
    {
      title: '配置项',
      dataIndex: 'key',
      key: 'key',
      width: 250,
      render: (key: string, record: ConfigItem) => (
        <div>
          <div style={{ fontWeight: 600 }}>{key}</div>
          <div style={{ fontSize: '12px', color: '#666' }}>{record.description}</div>
        </div>
      )
    },
    {
      title: '当前值',
      dataIndex: 'value',
      key: 'value',
      width: 200,
      render: (value: any, record: ConfigItem) => {
        if (record.is_sensitive) {
          return <span style={{ color: '#999' }}>***</span>
        }
        
        if (record.data_type === 'bool') {
          return <Tag color={value ? 'green' : 'red'}>{value ? '启用' : '禁用'}</Tag>
        }
        
        return <span>{String(value)}</span>
      }
    },
    {
      title: '类型',
      dataIndex: 'data_type',
      key: 'data_type',
      width: 80,
      render: (type: string) => <Tag>{type}</Tag>
    },
    {
      title: '状态',
      key: 'status',
      width: 120,
      render: (_, record: ConfigItem) => (
        <Space>
          {record.requires_restart && (
            <Tooltip title="需要重启生效">
              <Tag color="orange">重启</Tag>
            </Tooltip>
          )}
          {record.is_sensitive && (
            <Tooltip title="敏感配置">
              <Tag color="red">敏感</Tag>
            </Tooltip>
          )}
          {validationErrors[record.key] && (
            <Tooltip title={validationErrors[record.key].join(', ')}>
              <Tag color="red">错误</Tag>
            </Tooltip>
          )}
        </Space>
      )
    },
    {
      title: '操作',
      key: 'actions',
      width: 150,
      render: (_, record: ConfigItem) => (
        <Space>
          <Button
            type="text"
            icon={<EditOutlined />}
            onClick={() => handleEditConfig(record)}
            size="small"
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要重置为默认值吗？"
            onConfirm={() => handleResetConfig(record.key)}
            okText="确定"
            cancelText="取消"
          >
            <Button
              type="text"
              icon={<UndoOutlined />}
              size="small"
            >
              重置
            </Button>
          </Popconfirm>
        </Space>
      )
    }
  ]

  const getCurrentCategoryItems = () => {
    const category = categories.find(cat => cat.name === selectedCategory)
    if (!category) return []
    
    if (!searchKeyword) return category.items
    
    return category.items.filter(item =>
      item.key.toLowerCase().includes(searchKeyword.toLowerCase()) ||
      item.description.toLowerCase().includes(searchKeyword.toLowerCase())
    )
  }

  const renderValueInput = (config: ConfigItem) => {
    switch (config.data_type) {
      case 'bool':
        return (
          <Form.Item name="value" valuePropName="checked">
            <Switch />
          </Form.Item>
        )
      case 'int':
        return (
          <Form.Item name="value">
            <InputNumber style={{ width: '100%' }} />
          </Form.Item>
        )
      case 'float':
        return (
          <Form.Item name="value">
            <InputNumber step={0.1} style={{ width: '100%' }} />
          </Form.Item>
        )
      case 'json':
        return (
          <Form.Item name="value">
            <TextArea rows={4} />
          </Form.Item>
        )
      default:
        return (
          <Form.Item name="value">
            <Input />
          </Form.Item>
        )
    }
  }

  return (
    <div className="system-management-page">
      <Card className="page-header" title="系统管理" size="small">
        <Tabs activeKey={selectedCategory} onChange={setSelectedCategory}>
          <TabPane tab="系统配置" key="config">
            <div className="config-management">
              {/* 操作栏 */}
              <div className="config-toolbar">
                <Row gutter={[16, 16]} align="middle">
                  <Col flex="auto">
                    <Space>
                      <Search
                        placeholder="搜索配置项..."
                        value={searchKeyword}
                        onChange={(e) => setSearchKeyword(e.target.value)}
                        style={{ width: 300 }}
                      />
                      <Select
                        value={selectedCategory}
                        onChange={setSelectedCategory}
                        style={{ width: 150 }}
                      >
                        {categories.map(cat => (
                          <Option key={cat.name} value={cat.name}>
                            {cat.description}
                          </Option>
                        ))}
                      </Select>
                    </Space>
                  </Col>
                  <Col>
                    <Space>
                      <Button
                        icon={<CheckCircleOutlined />}
                        onClick={handleValidateConfigs}
                      >
                        验证配置
                      </Button>
                      <Button
                        icon={<ExportOutlined />}
                        onClick={handleExportConfigs}
                      >
                        导出配置
                      </Button>
                      <Button
                        icon={<ImportOutlined />}
                        onClick={() => setImportModalVisible(true)}
                      >
                        导入配置
                      </Button>
                      <Button
                        icon={<ReloadOutlined />}
                        onClick={loadConfigCategories}
                        loading={loading}
                      >
                        刷新
                      </Button>
                    </Space>
                  </Col>
                </Row>
              </div>

              {/* 验证错误提示 */}
              {Object.keys(validationErrors).length > 0 && (
                <Alert
                  message="配置验证错误"
                  description={`发现${Object.keys(validationErrors).length}个配置项存在错误，请及时修正`}
                  type="error"
                  showIcon
                  style={{ marginBottom: 16 }}
                />
              )}

              {/* 配置表格 */}
              <Table
                columns={configColumns}
                dataSource={getCurrentCategoryItems()}
                rowKey="key"
                loading={loading}
                pagination={{
                  pageSize: 20,
                  showSizeChanger: true,
                  showQuickJumper: true,
                  showTotal: (total, range) => 
                    `第 ${range[0]}-${range[1]} 条，共 ${total} 条配置项`
                }}
              />
            </div>
          </TabPane>

          <TabPane tab="系统状态" key="health">
            {systemHealth && (
              <div className="system-health">
                {/* 整体状态 */}
                <Card title="系统整体状态" style={{ marginBottom: 16 }}>
                  <Row gutter={[16, 16]}>
                    <Col xs={24} sm={12} md={6}>
                      <Statistic
                        title="系统状态"
                        value={systemHealth.status}
                        prefix={getStatusIcon(systemHealth.status)}
                        valueStyle={{ 
                          color: systemHealth.status === 'healthy' ? '#52c41a' : 
                                systemHealth.status === 'degraded' ? '#faad14' : '#ff4d4f'
                        }}
                      />
                    </Col>
                    <Col xs={24} sm={12} md={6}>
                      <Statistic
                        title="CPU使用率"
                        value={systemHealth.system_metrics.cpu_percent}
                        suffix="%"
                        precision={1}
                      />
                    </Col>
                    <Col xs={24} sm={12} md={6}>
                      <Statistic
                        title="内存使用率"
                        value={systemHealth.system_metrics.memory_percent}
                        suffix="%"
                        precision={1}
                      />
                    </Col>
                    <Col xs={24} sm={12} md={6}>
                      <Statistic
                        title="活跃用户"
                        value={systemHealth.application_metrics.active_users}
                      />
                    </Col>
                  </Row>
                </Card>

                {/* 服务状态 */}
                <Card title="服务状态" style={{ marginBottom: 16 }}>
                  <Row gutter={[16, 16]}>
                    {Object.entries(systemHealth.services).map(([service, status]: [string, any]) => (
                      <Col xs={24} sm={12} md={6} key={service}>
                        <Card size="small">
                          <Statistic
                            title={service.toUpperCase()}
                            value={status.status}
                            prefix={
                              <Badge
                                status={getStatusColor(status.status) as any}
                                text=""
                              />
                            }
                            suffix={`${(status.response_time * 1000).toFixed(0)}ms`}
                          />
                        </Card>
                      </Col>
                    ))}
                  </Row>
                </Card>

                {/* 应用指标 */}
                <Card title="应用指标">
                  <Row gutter={[16, 16]}>
                    <Col xs={24} sm={12} md={6}>
                      <Statistic
                        title="总请求数"
                        value={systemHealth.application_metrics.total_requests}
                      />
                    </Col>
                    <Col xs={24} sm={12} md={6}>
                      <Statistic
                        title="错误率"
                        value={systemHealth.application_metrics.error_rate * 100}
                        suffix="%"
                        precision={2}
                      />
                    </Col>
                    <Col xs={24} sm={12} md={6}>
                      <Statistic
                        title="平均响应时间"
                        value={systemHealth.application_metrics.avg_response_time * 1000}
                        suffix="ms"
                        precision={0}
                      />
                    </Col>
                    <Col xs={24} sm={12} md={6}>
                      <Statistic
                        title="缓存命中率"
                        value={systemHealth.application_metrics.cache_hit_rate * 100}
                        suffix="%"
                        precision={1}
                      />
                    </Col>
                  </Row>
                </Card>
              </div>
            )}
          </TabPane>
        </Tabs>
      </Card>

      {/* 编辑配置模态框 */}
      <Modal
        title="编辑配置"
        open={editModalVisible}
        onOk={handleSaveConfig}
        onCancel={() => setEditModalVisible(false)}
        width={600}
      >
        {editingConfig && (
          <Form form={form} layout="vertical">
            <Form.Item label="配置项" name="key">
              <Input disabled />
            </Form.Item>
            <Form.Item label="描述" name="description">
              <Input disabled />
            </Form.Item>
            <Form.Item label="配置值" required>
              {renderValueInput(editingConfig)}
            </Form.Item>
            {editingConfig.requires_restart && (
              <Alert
                message="注意"
                description="此配置项修改后需要重启系统才能生效"
                type="warning"
                showIcon
              />
            )}
          </Form>
        )}
      </Modal>

      {/* 导入配置模态框 */}
      <Modal
        title="导入配置"
        open={importModalVisible}
        onCancel={() => setImportModalVisible(false)}
        footer={null}
      >
        <Upload.Dragger
          accept=".json"
          beforeUpload={(file) => {
            handleImportConfigs(file)
            return false
          }}
          showUploadList={false}
        >
          <p className="ant-upload-drag-icon">
            <UploadOutlined />
          </p>
          <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
          <p className="ant-upload-hint">
            支持JSON格式的配置文件
          </p>
        </Upload.Dragger>
      </Modal>
    </div>
  )
}

export default SystemManagementPage
