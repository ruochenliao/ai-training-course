import React, { useState } from 'react';
import {
  Layout, Table, Button, Modal, Form, Input, Select, Switch, Space, 
  Typography, message, Popconfirm, Tag, Card, Row, Col, Statistic,
  Tooltip, Divider
} from 'antd';
import {
  PlusOutlined, EditOutlined, DeleteOutlined, SettingOutlined,
  RobotOutlined, BulbOutlined, ThunderboltOutlined
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { agentConfigService, AgentConfigCreate, AgentConfigUpdate } from '@/services/agentConfig';
import { AgentConfig, AgentModel, AgentTool } from '@/types';

const { Header, Content } = Layout;
const { Title, Text } = Typography;
const { TextArea } = Input;
const { Option } = Select;

const AgentManagement: React.FC = () => {
  const queryClient = useQueryClient();
  
  // 状态管理
  const [modalVisible, setModalVisible] = useState(false);
  const [editingAgent, setEditingAgent] = useState<AgentConfig | null>(null);
  const [form] = Form.useForm();

  // 获取智能体列表
  const { data: agents, isLoading } = useQuery(
    'agent-configs',
    () => agentConfigService.getAgentConfigs(),
    {
      staleTime: 2 * 60 * 1000, // 2分钟缓存
    }
  );

  // 获取可用模型列表
  const { data: models } = useQuery(
    'agent-models',
    () => agentConfigService.getAgentModels(),
    {
      staleTime: 5 * 60 * 1000, // 5分钟缓存
    }
  );

  // 获取可用工具列表
  const { data: tools } = useQuery(
    'agent-tools',
    () => agentConfigService.getAgentTools(),
    {
      staleTime: 5 * 60 * 1000, // 5分钟缓存
    }
  );

  // 创建智能体
  const createAgentMutation = useMutation(
    (data: AgentConfigCreate) => agentConfigService.createAgentConfig(data),
    {
      onSuccess: () => {
        message.success('智能体创建成功');
        setModalVisible(false);
        form.resetFields();
        queryClient.invalidateQueries('agent-configs');
      },
      onError: (error: any) => {
        message.error(`创建失败: ${error.response?.data?.detail || error.message}`);
      }
    }
  );

  // 更新智能体
  const updateAgentMutation = useMutation(
    ({ agentId, data }: { agentId: number; data: AgentConfigUpdate }) =>
      agentConfigService.updateAgentConfig(agentId, data),
    {
      onSuccess: () => {
        message.success('智能体更新成功');
        setModalVisible(false);
        setEditingAgent(null);
        form.resetFields();
        queryClient.invalidateQueries('agent-configs');
      },
      onError: (error: any) => {
        message.error(`更新失败: ${error.response?.data?.detail || error.message}`);
      }
    }
  );

  // 删除智能体
  const deleteAgentMutation = useMutation(
    (agentId: number) => agentConfigService.deleteAgentConfig(agentId),
    {
      onSuccess: () => {
        message.success('智能体删除成功');
        queryClient.invalidateQueries('agent-configs');
      },
      onError: (error: any) => {
        message.error(`删除失败: ${error.response?.data?.detail || error.message}`);
      }
    }
  );

  // 处理创建
  const handleCreate = () => {
    setEditingAgent(null);
    form.resetFields();
    // 设置默认值
    form.setFieldsValue({
      model_name: 'deepseek-chat',
      temperature: '0.7',
      max_tokens: 2000,
      tools: [],
      tool_choice: 'auto',
      max_consecutive_auto_reply: 3,
      human_input_mode: 'NEVER',
      code_execution_config: {},
      is_active: true
    });
    setModalVisible(true);
  };

  // 处理编辑
  const handleEdit = (agent: AgentConfig) => {
    setEditingAgent(agent);
    form.setFieldsValue({
      ...agent,
      code_execution_config: JSON.stringify(agent.code_execution_config, null, 2)
    });
    setModalVisible(true);
  };

  // 处理表单提交
  const handleSubmit = async (values: any) => {
    try {
      // 处理 code_execution_config
      let codeExecutionConfig = {};
      if (values.code_execution_config) {
        try {
          codeExecutionConfig = JSON.parse(values.code_execution_config);
        } catch (e) {
          message.error('代码执行配置格式错误，请输入有效的JSON');
          return;
        }
      }

      const submitData = {
        ...values,
        code_execution_config: codeExecutionConfig
      };

      if (editingAgent) {
        updateAgentMutation.mutate({
          agentId: editingAgent.id,
          data: submitData
        });
      } else {
        createAgentMutation.mutate(submitData);
      }
    } catch (error) {
      message.error('提交失败，请检查输入');
    }
  };

  // 表格列定义
  const columns = [
    {
      title: '智能体名称',
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record: AgentConfig) => (
        <Space>
          <RobotOutlined style={{ color: record.is_active ? '#1890ff' : '#d9d9d9' }} />
          <Text strong={record.is_active}>{name}</Text>
        </Space>
      )
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
      render: (description: string) => (
        <Tooltip title={description}>
          <Text type="secondary">{description || '-'}</Text>
        </Tooltip>
      )
    },
    {
      title: '模型',
      dataIndex: 'model_name',
      key: 'model_name',
      render: (modelName: string) => (
        <Tag color="blue">{modelName}</Tag>
      )
    },
    {
      title: '温度',
      dataIndex: 'temperature',
      key: 'temperature',
      width: 80,
      render: (temperature: string) => (
        <Tag color="orange">{temperature}</Tag>
      )
    },
    {
      title: '最大Token',
      dataIndex: 'max_tokens',
      key: 'max_tokens',
      width: 100,
      render: (maxTokens: number) => (
        <Text>{maxTokens.toLocaleString()}</Text>
      )
    },
    {
      title: '工具',
      dataIndex: 'tools',
      key: 'tools',
      render: (tools: string[]) => (
        <Space wrap>
          {tools.length > 0 ? (
            tools.slice(0, 2).map(tool => (
              <Tag key={tool} color="green" size="small">{tool}</Tag>
            ))
          ) : (
            <Text type="secondary">无</Text>
          )}
          {tools.length > 2 && (
            <Tag color="default" size="small">+{tools.length - 2}</Tag>
          )}
        </Space>
      )
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 80,
      render: (isActive: boolean) => (
        <Tag color={isActive ? 'success' : 'default'}>
          {isActive ? '启用' : '禁用'}
        </Tag>
      )
    },
    {
      title: '操作',
      key: 'actions',
      width: 150,
      render: (_, record: AgentConfig) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这个智能体吗？"
            description="删除后将无法恢复，且会影响使用此智能体的字段配置"
            onConfirm={() => deleteAgentMutation.mutate(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button
              type="link"
              size="small"
              danger
              icon={<DeleteOutlined />}
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      )
    }
  ];

  // 统计信息
  const statistics = {
    total: agents?.length || 0,
    active: agents?.filter(a => a.is_active).length || 0,
    inactive: agents?.filter(a => !a.is_active).length || 0
  };

  return (
    <Layout style={{ height: '100%' }}>
      {/* 页面头部操作栏 */}
      <div style={{
        background: '#fff',
        padding: '16px 24px',
        borderBottom: '1px solid #f0f0f0',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <Title level={4} style={{ margin: 0 }}>
          <RobotOutlined style={{ marginRight: 8, color: '#1890ff' }} />
          智能体管理
        </Title>
        <Space>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleCreate}
          >
            新建智能体
          </Button>
          <Button
            icon={<SettingOutlined />}
            onClick={() => queryClient.invalidateQueries('agent-configs')}
          >
            刷新
          </Button>
        </Space>
      </div>

      <Content style={{ padding: 24, flex: 1, overflow: 'auto' }}>
        {/* 统计卡片 */}
        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col span={6}>
            <Card>
              <Statistic
                title="总智能体数"
                value={statistics.total}
                prefix={<RobotOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="启用中"
                value={statistics.active}
                prefix={<ThunderboltOutlined />}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="已禁用"
                value={statistics.inactive}
                prefix={<BulbOutlined />}
                valueStyle={{ color: '#faad14' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="可用模型"
                value={models?.length || 0}
                prefix={<SettingOutlined />}
                valueStyle={{ color: '#722ed1' }}
              />
            </Card>
          </Col>
        </Row>

        {/* 智能体列表 */}
        <Card>
          <Table
            columns={columns}
            dataSource={agents}
            rowKey="id"
            loading={isLoading}
            pagination={{
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
            }}
          />
        </Card>
      </Content>

      {/* 创建/编辑模态框 */}
      <Modal
        title={editingAgent ? '编辑智能体' : '新建智能体'}
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          setEditingAgent(null);
          form.resetFields();
        }}
        onOk={() => form.submit()}
        confirmLoading={createAgentMutation.isLoading || updateAgentMutation.isLoading}
        width={800}
        destroyOnClose
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="name"
                label="智能体名称"
                rules={[{ required: true, message: '请输入智能体名称' }]}
              >
                <Input placeholder="请输入智能体名称" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="model_name"
                label="使用模型"
                rules={[{ required: true, message: '请选择模型' }]}
              >
                <Select placeholder="请选择模型">
                  {models?.map(model => (
                    <Option key={model.name} value={model.name}>
                      {model.display_name} ({model.provider})
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="description"
            label="描述"
          >
            <TextArea rows={2} placeholder="请输入智能体描述" />
          </Form.Item>

          <Form.Item
            name="system_prompt"
            label="系统提示词"
            rules={[{ required: true, message: '请输入系统提示词' }]}
          >
            <TextArea rows={4} placeholder="请输入系统提示词" />
          </Form.Item>

          <Form.Item
            name="user_prompt_template"
            label="用户提示词模板"
          >
            <TextArea rows={3} placeholder="请输入用户提示词模板（可选）" />
          </Form.Item>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                name="temperature"
                label="温度参数"
                rules={[{ required: true, message: '请输入温度参数' }]}
              >
                <Input placeholder="0.7" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="max_tokens"
                label="最大Token数"
                rules={[{ required: true, message: '请输入最大Token数' }]}
              >
                <Input type="number" placeholder="2000" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="max_consecutive_auto_reply"
                label="最大连续回复"
              >
                <Input type="number" placeholder="3" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="tools"
                label="可用工具"
              >
                <Select
                  mode="multiple"
                  placeholder="请选择可用工具"
                  allowClear
                >
                  {tools?.map(tool => (
                    <Option key={tool.function_name} value={tool.function_name}>
                      {tool.name}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="tool_choice"
                label="工具选择策略"
              >
                <Select placeholder="请选择工具选择策略">
                  <Option value="auto">自动选择</Option>
                  <Option value="none">不使用工具</Option>
                  <Option value="required">必须使用工具</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="human_input_mode"
            label="人工输入模式"
          >
            <Select placeholder="请选择人工输入模式">
              <Option value="NEVER">从不</Option>
              <Option value="TERMINATE">终止时</Option>
              <Option value="ALWAYS">总是</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="code_execution_config"
            label="代码执行配置"
            extra="请输入有效的JSON格式配置"
          >
            <TextArea
              rows={3}
              placeholder='{"work_dir": "/tmp", "use_docker": false}'
            />
          </Form.Item>

          <Form.Item
            name="is_active"
            label="启用状态"
            valuePropName="checked"
          >
            <Switch checkedChildren="启用" unCheckedChildren="禁用" />
          </Form.Item>
        </Form>
      </Modal>
    </Layout>
  );
};

export default AgentManagement;
