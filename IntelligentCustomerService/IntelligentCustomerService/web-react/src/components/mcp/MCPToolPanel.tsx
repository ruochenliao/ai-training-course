import React, { useState, useEffect } from 'react'
import { 
  Card, 
  List, 
  Button, 
  Space, 
  Typography, 
  Tag, 
  Modal, 
  Form, 
  Input, 
  Select, 
  message, 
  Collapse,
  Badge,
  Tooltip,
  Divider,
  Alert
} from 'antd'
import {
  ToolOutlined,
  PlayCircleOutlined,
  InfoCircleOutlined,
  ApiOutlined,
  SearchOutlined,
  FileTextOutlined,
  ShoppingCartOutlined,
  SettingOutlined,
  ThunderboltOutlined
} from '@ant-design/icons'

const { Text, Title, Paragraph } = Typography
const { Panel } = Collapse
const { Option } = Select
const { TextArea } = Input

interface MCPTool {
  name: string
  description: string
  parameters: any
  category: string
  version: string
}

interface MCPToolPanelProps {
  sessionId?: string
  onToolCall?: (toolName: string, parameters: any, result: any) => void
  className?: string
}

/**
 * MCP工具面板组件
 * 提供MCP工具的浏览、测试和调用功能
 */
const MCPToolPanel: React.FC<MCPToolPanelProps> = ({
  sessionId,
  onToolCall,
  className
}) => {
  const [tools, setTools] = useState<MCPTool[]>([])
  const [categories, setCategories] = useState<Record<string, string[]>>({})
  const [loading, setLoading] = useState(false)
  const [selectedTool, setSelectedTool] = useState<MCPTool | null>(null)
  const [testModalVisible, setTestModalVisible] = useState(false)
  const [testForm] = Form.useForm()
  const [testResult, setTestResult] = useState<any>(null)
  const [testLoading, setTestLoading] = useState(false)

  // 获取工具图标
  const getToolIcon = (category: string) => {
    switch (category) {
      case 'ecommerce':
        return <ShoppingCartOutlined style={{ color: '#52c41a' }} />
      case 'search':
        return <SearchOutlined style={{ color: '#1890ff' }} />
      case 'file':
        return <FileTextOutlined style={{ color: '#fa8c16' }} />
      default:
        return <ToolOutlined style={{ color: '#666' }} />
    }
  }

  // 获取分类颜色
  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'ecommerce':
        return 'green'
      case 'search':
        return 'blue'
      case 'file':
        return 'orange'
      default:
        return 'default'
    }
  }

  // 获取分类名称
  const getCategoryName = (category: string) => {
    switch (category) {
      case 'ecommerce':
        return '电商工具'
      case 'search':
        return '搜索工具'
      case 'file':
        return '文件工具'
      default:
        return '通用工具'
    }
  }

  // 加载工具列表
  const loadTools = async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/v1/mcp/tools', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      })
      
      if (response.ok) {
        const toolsData = await response.json()
        setTools(toolsData)
        
        // 获取分类信息
        const categoriesResponse = await fetch('/api/v1/mcp/tools/categories', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        })
        
        if (categoriesResponse.ok) {
          const categoriesData = await categoriesResponse.json()
          setCategories(categoriesData.categories)
        }
      } else {
        message.error('加载工具列表失败')
      }
    } catch (error) {
      message.error('加载工具列表失败')
    } finally {
      setLoading(false)
    }
  }

  // 测试工具
  const testTool = async (values: any) => {
    if (!selectedTool) return
    
    setTestLoading(true)
    try {
      const response = await fetch(`/api/v1/mcp/tools/${selectedTool.name}/test`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          parameters: values,
          session_id: sessionId
        })
      })
      
      if (response.ok) {
        const result = await response.json()
        setTestResult(result)
        
        if (result.success) {
          message.success('工具测试成功')
          
          // 通知父组件
          if (onToolCall) {
            onToolCall(selectedTool.name, values, result.result)
          }
        } else {
          message.warning('工具测试完成，但返回了错误')
        }
      } else {
        message.error('工具测试失败')
      }
    } catch (error) {
      message.error('工具测试失败')
    } finally {
      setTestLoading(false)
    }
  }

  // 打开测试模态框
  const openTestModal = (tool: MCPTool) => {
    setSelectedTool(tool)
    setTestModalVisible(true)
    setTestResult(null)
    testForm.resetFields()
  }

  // 渲染参数表单
  const renderParameterForm = (parameters: any) => {
    if (!parameters || !parameters.properties) {
      return <Text type="secondary">此工具无需参数</Text>
    }

    const { properties, required = [] } = parameters

    return (
      <div>
        {Object.entries(properties).map(([key, prop]: [string, any]) => (
          <Form.Item
            key={key}
            name={key}
            label={key}
            rules={[
              {
                required: required.includes(key),
                message: `请输入${key}`
              }
            ]}
            tooltip={prop.description}
          >
            {prop.type === 'string' && prop.enum ? (
              <Select placeholder={`请选择${key}`}>
                {prop.enum.map((option: string) => (
                  <Option key={option} value={option}>
                    {option}
                  </Option>
                ))}
              </Select>
            ) : prop.type === 'boolean' ? (
              <Select placeholder={`请选择${key}`}>
                <Option value={true}>是</Option>
                <Option value={false}>否</Option>
              </Select>
            ) : prop.type === 'number' || prop.type === 'integer' ? (
              <Input
                type="number"
                placeholder={prop.description || `请输入${key}`}
                min={prop.minimum}
                max={prop.maximum}
              />
            ) : prop.type === 'array' ? (
              <TextArea
                placeholder={`请输入${key}（JSON格式）`}
                rows={3}
              />
            ) : (
              <Input
                placeholder={prop.description || `请输入${key}`}
                maxLength={prop.maxLength}
              />
            )}
          </Form.Item>
        ))}
      </div>
    )
  }

  useEffect(() => {
    loadTools()
  }, [])

  return (
    <div className={`mcp-tool-panel ${className || ''}`}>
      <Card
        title={
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span>
              <ApiOutlined style={{ marginRight: 8 }} />
              MCP工具面板
            </span>
            <Space>
              <Badge count={tools.length} showZero>
                <Button 
                  type="text" 
                  icon={<ToolOutlined />}
                  onClick={loadTools}
                  loading={loading}
                />
              </Badge>
            </Space>
          </div>
        }
        style={{
          background: 'rgba(255, 255, 255, 0.1)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(255, 255, 255, 0.2)',
          borderRadius: '16px'
        }}
        headStyle={{
          background: 'rgba(24, 144, 255, 0.2)',
          borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
          color: 'rgba(255, 255, 255, 0.9)'
        }}
        bodyStyle={{
          background: 'transparent',
          maxHeight: '600px',
          overflowY: 'auto'
        }}
      >
        {/* 工具统计 */}
        <Alert
          message="MCP工具统计"
          description={
            <div>
              <Text style={{ color: 'rgba(255, 255, 255, 0.8)' }}>
                共 {tools.length} 个工具，分为 {Object.keys(categories).length} 个分类
              </Text>
              <div style={{ marginTop: '8px' }}>
                {Object.entries(categories).map(([category, toolNames]) => (
                  <Tag key={category} color={getCategoryColor(category)} style={{ margin: '2px' }}>
                    {getCategoryName(category)} ({toolNames.length})
                  </Tag>
                ))}
              </div>
            </div>
          }
          type="info"
          showIcon
          style={{
            background: 'rgba(24, 144, 255, 0.1)',
            border: '1px solid rgba(24, 144, 255, 0.3)',
            marginBottom: '16px'
          }}
        />

        {/* 工具列表 */}
        <Collapse
          defaultActiveKey={Object.keys(categories)}
          style={{ background: 'transparent' }}
        >
          {Object.entries(categories).map(([category, toolNames]) => (
            <Panel
              key={category}
              header={
                <div style={{ display: 'flex', alignItems: 'center' }}>
                  {getToolIcon(category)}
                  <span style={{ marginLeft: 8, color: 'rgba(255, 255, 255, 0.9)' }}>
                    {getCategoryName(category)}
                  </span>
                  <Badge count={toolNames.length} style={{ marginLeft: 8 }} />
                </div>
              }
              style={{
                background: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                marginBottom: '8px',
                borderRadius: '8px'
              }}
            >
              <List
                dataSource={tools.filter(tool => tool.category === category)}
                renderItem={(tool) => (
                  <List.Item
                    style={{
                      background: 'rgba(255, 255, 255, 0.05)',
                      borderRadius: '8px',
                      marginBottom: '8px',
                      padding: '12px',
                      border: '1px solid rgba(255, 255, 255, 0.1)'
                    }}
                    actions={[
                      <Tooltip title="查看详情">
                        <Button
                          type="text"
                          icon={<InfoCircleOutlined />}
                          onClick={() => {
                            Modal.info({
                              title: tool.name,
                              content: (
                                <div>
                                  <Paragraph>{tool.description}</Paragraph>
                                  <Divider />
                                  <Text strong>参数:</Text>
                                  <pre style={{ 
                                    background: 'rgba(0,0,0,0.1)', 
                                    padding: '8px', 
                                    borderRadius: '4px',
                                    fontSize: '12px',
                                    overflow: 'auto'
                                  }}>
                                    {JSON.stringify(tool.parameters, null, 2)}
                                  </pre>
                                </div>
                              ),
                              width: 600
                            })
                          }}
                          style={{ color: 'rgba(255, 255, 255, 0.8)' }}
                        />
                      </Tooltip>,
                      <Tooltip title="测试工具">
                        <Button
                          type="text"
                          icon={<PlayCircleOutlined />}
                          onClick={() => openTestModal(tool)}
                          style={{ color: 'rgba(52, 199, 89, 0.8)' }}
                        />
                      </Tooltip>
                    ]}
                  >
                    <List.Item.Meta
                      avatar={getToolIcon(tool.category)}
                      title={
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <Text style={{ color: 'rgba(255, 255, 255, 0.9)', fontWeight: 500 }}>
                            {tool.name}
                          </Text>
                          <Tag color={getCategoryColor(tool.category)} size="small">
                            v{tool.version}
                          </Tag>
                        </div>
                      }
                      description={
                        <Text style={{ color: 'rgba(255, 255, 255, 0.6)', fontSize: '12px' }}>
                          {tool.description}
                        </Text>
                      }
                    />
                  </List.Item>
                )}
              />
            </Panel>
          ))}
        </Collapse>

        {/* 空状态 */}
        {tools.length === 0 && !loading && (
          <div style={{ textAlign: 'center', padding: '40px', color: 'rgba(255, 255, 255, 0.6)' }}>
            <ToolOutlined style={{ fontSize: '48px', marginBottom: '16px' }} />
            <Text style={{ color: 'rgba(255, 255, 255, 0.6)' }}>
              暂无可用工具
            </Text>
          </div>
        )}
      </Card>

      {/* 工具测试模态框 */}
      <Modal
        title={
          <div>
            <ThunderboltOutlined style={{ marginRight: 8 }} />
            测试工具: {selectedTool?.name}
          </div>
        }
        open={testModalVisible}
        onCancel={() => setTestModalVisible(false)}
        footer={null}
        width={800}
        style={{
          background: 'rgba(15, 15, 35, 0.95)',
          backdropFilter: 'blur(40px)'
        }}
      >
        {selectedTool && (
          <div>
            <Alert
              message={selectedTool.description}
              type="info"
              showIcon
              style={{ marginBottom: '16px' }}
            />
            
            <Form
              form={testForm}
              layout="vertical"
              onFinish={testTool}
            >
              {renderParameterForm(selectedTool.parameters)}
              
              <Form.Item>
                <Space>
                  <Button 
                    type="primary" 
                    htmlType="submit" 
                    loading={testLoading}
                    icon={<PlayCircleOutlined />}
                  >
                    测试工具
                  </Button>
                  <Button onClick={() => testForm.resetFields()}>
                    重置
                  </Button>
                </Space>
              </Form.Item>
            </Form>

            {/* 测试结果 */}
            {testResult && (
              <div style={{ marginTop: '16px' }}>
                <Divider>测试结果</Divider>
                <Alert
                  message={testResult.success ? "测试成功" : "测试失败"}
                  type={testResult.success ? "success" : "error"}
                  showIcon
                  style={{ marginBottom: '8px' }}
                />
                <pre style={{
                  background: 'rgba(0,0,0,0.1)',
                  padding: '12px',
                  borderRadius: '8px',
                  fontSize: '12px',
                  overflow: 'auto',
                  maxHeight: '300px',
                  color: 'rgba(255, 255, 255, 0.8)'
                }}>
                  {JSON.stringify(testResult, null, 2)}
                </pre>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  )
}

export default MCPToolPanel
