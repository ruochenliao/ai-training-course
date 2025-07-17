import React, { useState } from 'react';
import {
  Layout,
  Tree,
  Table,
  Button,
  Space,
  Typography,
  Input,
  Modal,
  Form,
  message,
  Upload,
  Popconfirm,
  Tag,
  Tooltip,
  Card,
  Statistic,
  Row,
  Col,
  Tabs,
  Switch,
  Select
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  UploadOutlined,
  FileTextOutlined,
  FolderOutlined,
  SearchOutlined,
  ReloadOutlined,
  SettingOutlined,
  ToolOutlined,
  RobotOutlined
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { useNavigate } from 'react-router-dom';
import { templateService } from '@/services/template';
import { agentConfigService } from '@/services/agentConfig';
import {
  TemplateTreeNode,
  TemplateCategory,
  TemplateType,
  TemplateFile,
  TemplateCategoryCreate,
  TemplateTypeCreate,
  TemplateFileCreate,
  WritingScenarioConfig,
  WritingFieldConfig,
  WritingScenarioConfigCreate,
  WritingScenarioConfigUpdate,
  AgentConfig
} from '@/types';

const { Header, Sider, Content } = Layout;
const { Title, Text } = Typography;
const { Search } = Input;
const { TextArea } = Input;
const { TabPane } = Tabs;
const { Option } = Select;

const TemplateManagement: React.FC = () => {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [selectedNode, setSelectedNode] = useState<TemplateTreeNode | null>(null);
  const [selectedNodeType, setSelectedNodeType] = useState<'category' | 'type' | 'file' | null>(null);
  const [searchKeyword, setSearchKeyword] = useState('');
  const [modalVisible, setModalVisible] = useState(false);
  const [modalType, setModalType] = useState<'create' | 'edit'>('create');
  const [editingItem, setEditingItem] = useState<any>(null);
  const [form] = Form.useForm();

  // 写作场景配置相关状态
  const [scenarioModalVisible, setScenarioModalVisible] = useState(false);
  const [scenarioForm] = Form.useForm();
  const [editingScenarioConfig, setEditingScenarioConfig] = useState<WritingScenarioConfig | null>(null);

  // 智能体配置相关状态
  const [agentModalVisible, setAgentModalVisible] = useState(false);
  const [selectedFieldId, setSelectedFieldId] = useState<number | null>(null);
  const [selectedAgentId, setSelectedAgentId] = useState<number | null>(null);

  // 获取模板树
  const { data: templateTree, isLoading: treeLoading } = useQuery(
    'template-tree',
    () => templateService.getTemplateTree(),
    {
      staleTime: 2 * 60 * 1000, // 2分钟缓存
    }
  );

  // 获取统计信息
  const { data: statistics } = useQuery(
    'template-statistics',
    () => templateService.getTemplateStatistics(),
    {
      staleTime: 5 * 60 * 1000, // 5分钟缓存
    }
  );

  // 获取写作场景配置
  const { data: writingScenarioConfig, refetch: refetchScenarioConfig } = useQuery(
    ['writing-scenario-config', selectedNode?.id],
    () => selectedNode && selectedNodeType === 'type'
      ? templateService.getWritingScenarioConfig(selectedNode.id)
      : Promise.resolve(null),
    {
      enabled: selectedNode !== null && selectedNodeType === 'type',
      staleTime: 2 * 60 * 1000,
    }
  );

  // 获取智能体配置列表
  const { data: agentConfigs } = useQuery(
    'agent-configs',
    () => agentConfigService.getAgentConfigs(),
    {
      staleTime: 5 * 60 * 1000, // 5分钟缓存
    }
  );

  // 获取字段配置（新版本，包含智能体信息）
  const { data: fieldConfigs, refetch: refetchFieldConfigs } = useQuery(
    ['field-configs', writingScenarioConfig?.id],
    () => writingScenarioConfig?.id
      ? agentConfigService.getFieldConfigsByScenario(writingScenarioConfig.id)
      : Promise.resolve([]),
    {
      enabled: !!writingScenarioConfig?.id,
      staleTime: 2 * 60 * 1000,
    }
  );

  // 创建分类
  const createCategoryMutation = useMutation(
    (data: TemplateCategoryCreate) => templateService.createCategory(data),
    {
      onSuccess: () => {
        message.success('分类创建成功');
        queryClient.invalidateQueries('template-tree');
        queryClient.invalidateQueries('template-statistics');
        setModalVisible(false);
        form.resetFields();
      },
      onError: () => {
        message.error('分类创建失败');
      }
    }
  );

  // 创建类型
  const createTypeMutation = useMutation(
    (data: TemplateTypeCreate) => templateService.createType(data),
    {
      onSuccess: () => {
        message.success('类型创建成功');
        queryClient.invalidateQueries('template-tree');
        queryClient.invalidateQueries('template-statistics');
        setModalVisible(false);
        form.resetFields();
      },
      onError: () => {
        message.error('类型创建失败');
      }
    }
  );

  // 创建文件
  const createFileMutation = useMutation(
    (data: TemplateFileCreate) => templateService.createFile(data),
    {
      onSuccess: () => {
        message.success('模板文件创建成功');
        queryClient.invalidateQueries('template-tree');
        setModalVisible(false);
        form.resetFields();
      },
      onError: () => {
        message.error('模板文件创建失败');
      }
    }
  );

  // 删除操作
  const deleteMutation = useMutation(
    async ({ type, id }: { type: 'category' | 'type' | 'file'; id: number }) => {
      switch (type) {
        case 'category':
          return templateService.deleteCategory(id);
        case 'type':
          return templateService.deleteType(id);
        case 'file':
          return templateService.deleteFile(id);
      }
    },
    {
      onSuccess: () => {
        message.success('删除成功');
        queryClient.invalidateQueries('template-tree');
        queryClient.invalidateQueries('template-statistics');
        setSelectedNode(null);
        setSelectedNodeType(null);
      },
      onError: () => {
        message.error('删除失败');
      }
    }
  );

  // 初始化数据
  const initDataMutation = useMutation(
    () => templateService.initTemplateData(),
    {
      onSuccess: (data) => {
        if (data.success) {
          message.success(data.message);
          queryClient.invalidateQueries('template-tree');
          queryClient.invalidateQueries('template-statistics');
        } else {
          message.warning(data.message);
        }
      },
      onError: () => {
        message.error('初始化失败');
      }
    }
  );

  // 创建写作场景配置
  const createScenarioConfigMutation = useMutation(
    ({ typeId, data }: { typeId: number; data: WritingScenarioConfigCreate }) =>
      templateService.createWritingScenarioConfig(typeId, data),
    {
      onSuccess: () => {
        message.success('写作场景配置创建成功');
        refetchScenarioConfig();
        setScenarioModalVisible(false);
        scenarioForm.resetFields();
      },
      onError: () => {
        message.error('写作场景配置创建失败');
      }
    }
  );

  // 更新写作场景配置
  const updateScenarioConfigMutation = useMutation(
    ({ configId, data }: { configId: number; data: WritingScenarioConfigUpdate }) =>
      templateService.updateWritingScenarioConfig(configId, data),
    {
      onSuccess: () => {
        message.success('写作场景配置更新成功');
        refetchScenarioConfig();
        setScenarioModalVisible(false);
        scenarioForm.resetFields();
        setEditingScenarioConfig(null);
      },
      onError: () => {
        message.error('写作场景配置更新失败');
      }
    }
  );

  // 删除写作场景配置
  const deleteScenarioConfigMutation = useMutation(
    (configId: number) => templateService.deleteWritingScenarioConfig(configId),
    {
      onSuccess: () => {
        message.success('写作场景配置删除成功');
        refetchScenarioConfig();
      },
      onError: () => {
        message.error('写作场景配置删除失败');
      }
    }
  );

  // 分配智能体到字段
  const assignAgentMutation = useMutation(
    ({ fieldId, agentId }: { fieldId: number; agentId: number }) =>
      agentConfigService.assignAgentToField(fieldId, agentId),
    {
      onSuccess: () => {
        message.success('智能体分配成功');
        refetchFieldConfigs();
        setAgentModalVisible(false);
        setSelectedFieldId(null);
        setSelectedAgentId(null);
      },
      onError: () => {
        message.error('智能体分配失败');
      }
    }
  );

  // 移除字段的智能体
  const removeAgentMutation = useMutation(
    (fieldId: number) => agentConfigService.removeAgentFromField(fieldId),
    {
      onSuccess: () => {
        message.success('智能体移除成功');
        refetchFieldConfigs();
      },
      onError: () => {
        message.error('智能体移除失败');
      }
    }
  );

  // 处理树节点选择
  const handleTreeSelect = (selectedKeys: React.Key[], info: any) => {
    if (selectedKeys.length > 0) {
      const node = info.node;
      setSelectedNode(node);
      setSelectedNodeType(node.type);
    } else {
      setSelectedNode(null);
      setSelectedNodeType(null);
    }
  };

  // 转换树数据格式
  const convertTreeData = (nodes: TemplateTreeNode[]): any[] => {
    if (!nodes || !Array.isArray(nodes)) {
      return [];
    }

    return nodes.map(node => {
      if (!node || !node.name) {
        return null;
      }

      // 创建树节点，确保所有必需的属性都存在
      const treeNode: any = {
        key: `${node.type}-${node.id}`,
        title: node.name,
        icon: node.type === 'category' ? <FolderOutlined /> : <FileTextOutlined />,
        // 保留原始节点数据，供点击事件使用
        ...node
      };

      // 处理子节点
      if (node.children && Array.isArray(node.children) && node.children.length > 0) {
        treeNode.children = convertTreeData(node.children);
      }

      return treeNode;
    }).filter(Boolean);
  };

  // 打开创建模态框
  const handleCreate = (type: 'category' | 'type' | 'file') => {
    setModalType('create');
    setEditingItem(null);
    form.resetFields();
    
    // 如果创建类型或文件，需要选中父节点
    if (type === 'type' && selectedNodeType !== 'category') {
      message.warning('请先选择一个分类');
      return;
    }
    if (type === 'file' && selectedNodeType !== 'type') {
      message.warning('请先选择一个类型');
      return;
    }
    
    setModalVisible(true);
  };

  // 处理表单提交
  const handleSubmit = async (values: any) => {
    try {
      if (modalType === 'create') {
        if (selectedNodeType === null) {
          // 创建分类
          await createCategoryMutation.mutateAsync(values);
        } else if (selectedNodeType === 'category') {
          // 创建类型
          await createTypeMutation.mutateAsync({
            ...values,
            category_id: selectedNode!.id
          });
        } else if (selectedNodeType === 'type') {
          // 创建文件
          await createFileMutation.mutateAsync({
            ...values,
            template_type_id: selectedNode!.id
          });
        }
      }
    } catch (error) {
      console.error('提交失败:', error);
    }
  };

  // 处理删除
  const handleDelete = () => {
    if (!selectedNode || !selectedNodeType) return;
    
    deleteMutation.mutate({
      type: selectedNodeType,
      id: selectedNode.id
    });
  };

  // 渲染写作场景配置
  const renderWritingScenarioConfig = () => {
    if (!writingScenarioConfig) {
      return (
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <ToolOutlined style={{ fontSize: 48, color: '#d9d9d9' }} />
          <div style={{ marginTop: 16 }}>
            <Text type="secondary">暂无写作场景配置</Text>
          </div>
          <div style={{ marginTop: 16 }}>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => {
                setEditingScenarioConfig(null);
                scenarioForm.resetFields();
                setScenarioModalVisible(true);
              }}
            >
              创建写作场景配置
            </Button>
          </div>
        </div>
      );
    }

    const fieldColumns = [
      {
        title: '字段名称',
        dataIndex: 'field_name',
        key: 'field_name',
      },
      {
        title: '字段键名',
        dataIndex: 'field_key',
        key: 'field_key',
      },
      {
        title: '字段类型',
        dataIndex: 'field_type',
        key: 'field_type',
        render: (type: string) => {
          const typeMap: Record<string, string> = {
            text: '文本',
            textarea: '多行文本',
            select: '选择框'
          };
          return typeMap[type] || type;
        }
      },
      {
        title: '必填',
        dataIndex: 'required',
        key: 'required',
        render: (required: boolean) => (
          <Tag color={required ? 'red' : 'default'}>
            {required ? '是' : '否'}
          </Tag>
        )
      },
      {
        title: 'AI生成',
        dataIndex: 'ai_enabled',
        key: 'ai_enabled',
        render: (enabled: boolean) => (
          <Tag color={enabled ? 'blue' : 'default'}>
            {enabled ? '支持' : '不支持'}
          </Tag>
        )
      },
      {
        title: '智能体配置',
        key: 'agent_config',
        render: (record: WritingFieldConfig) => {
          if (!record.ai_enabled) {
            return <Text type="secondary">-</Text>;
          }

          if (record.agent_config) {
            return (
              <Space>
                <Tag color="blue">{record.agent_config.name}</Tag>
                <Button
                  size="small"
                  type="link"
                  onClick={() => {
                    setSelectedFieldId(record.id!);
                    setSelectedAgentId(record.agent_config_id!);
                    setAgentModalVisible(true);
                  }}
                >
                  更换
                </Button>
                <Popconfirm
                  title="确定要移除智能体配置吗？"
                  onConfirm={() => removeAgentMutation.mutate(record.id!)}
                  okText="确定"
                  cancelText="取消"
                >
                  <Button size="small" type="link" danger>
                    移除
                  </Button>
                </Popconfirm>
              </Space>
            );
          }

          return (
            <Button
              size="small"
              type="link"
              onClick={() => {
                setSelectedFieldId(record.id!);
                setSelectedAgentId(null);
                setAgentModalVisible(true);
              }}
            >
              配置智能体
            </Button>
          );
        }
      },
      {
        title: '文档选择',
        dataIndex: 'doc_enabled',
        key: 'doc_enabled',
        render: (enabled: boolean) => (
          <Tag color={enabled ? 'green' : 'default'}>
            {enabled ? '支持' : '不支持'}
          </Tag>
        )
      }
    ];

    return (
      <div>
        <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <Text strong style={{ fontSize: 16 }}>{writingScenarioConfig.config_name}</Text>
            <div style={{ marginTop: 4 }}>
              <Text type="secondary">{writingScenarioConfig.description}</Text>
            </div>
          </div>
          <Space>
            <Button
              icon={<EditOutlined />}
              onClick={() => {
                setEditingScenarioConfig(writingScenarioConfig);
                scenarioForm.setFieldsValue({
                  config_name: writingScenarioConfig.config_name,
                  description: writingScenarioConfig.description,
                  field_configs: writingScenarioConfig.field_configs
                });
                setScenarioModalVisible(true);
              }}
            >
              编辑
            </Button>
            <Popconfirm
              title="确定要删除写作场景配置吗？"
              onConfirm={() => deleteScenarioConfigMutation.mutate(writingScenarioConfig.id)}
              okText="确定"
              cancelText="取消"
            >
              <Button danger icon={<DeleteOutlined />}>删除</Button>
            </Popconfirm>
          </Space>
        </div>

        <Table
          columns={fieldColumns}
          dataSource={fieldConfigs || writingScenarioConfig.field_configs || []}
          rowKey={(record) => record.id ? `field-${record.id}` : record.field_key}
          size="small"
          pagination={false}
        />
      </div>
    );
  };

  // 渲染详情面板
  const renderDetailPanel = () => {
    if (!selectedNode) {
      return (
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <FileTextOutlined style={{ fontSize: 48, color: '#d9d9d9' }} />
          <div style={{ marginTop: 16 }}>
            <Text type="secondary">请选择一个节点查看详情</Text>
          </div>
        </div>
      );
    }

    return (
      <Card
        title={
          <Space>
            {selectedNodeType === 'category' && <FolderOutlined />}
            {selectedNodeType === 'type' && <FileTextOutlined />}
            {selectedNodeType === 'file' && <FileTextOutlined />}
            {selectedNode.name}
            <Tag color={selectedNode.is_active ? 'green' : 'red'}>
              {selectedNode.is_active ? '启用' : '禁用'}
            </Tag>
          </Space>
        }
        extra={
          <Space>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => {
                if (selectedNodeType === 'category') {
                  handleCreate('type');
                } else if (selectedNodeType === 'type') {
                  handleCreate('file');
                }
              }}
              disabled={selectedNodeType === 'file'}
            >
              {selectedNodeType === 'category' ? '添加类型' : 
               selectedNodeType === 'type' ? '添加文件' : ''}
            </Button>
            <Button icon={<EditOutlined />}>编辑</Button>
            <Popconfirm
              title="确定要删除吗？"
              onConfirm={handleDelete}
              okText="确定"
              cancelText="取消"
            >
              <Button danger icon={<DeleteOutlined />}>删除</Button>
            </Popconfirm>
          </Space>
        }
      >
        {selectedNodeType === 'type' ? (
          <Tabs defaultActiveKey="basic">
            <TabPane tab="基本信息" key="basic">
              <div>
                <Text strong>描述：</Text>
                <div style={{ marginBottom: 16 }}>
                  {selectedNode.description || '暂无描述'}
                </div>

                <Text strong>排序：</Text>
                <div style={{ marginBottom: 16 }}>
                  {selectedNode.sort_order}
                </div>
              </div>
            </TabPane>
            <TabPane
              tab={
                <span>
                  <ToolOutlined />
                  写作场景配置
                </span>
              }
              key="scenario"
            >
              {renderWritingScenarioConfig()}
            </TabPane>
          </Tabs>
        ) : (
          <div>
            <Text strong>描述：</Text>
            <div style={{ marginBottom: 16 }}>
              {selectedNode.description || '暂无描述'}
            </div>

            <Text strong>排序：</Text>
            <div style={{ marginBottom: 16 }}>
              {selectedNode.sort_order}
            </div>

            {selectedNodeType === 'file' && (
              <>
                <Text strong>使用次数：</Text>
                <div style={{ marginBottom: 16 }}>
                  {(selectedNode as any).usage_count || 0}
                </div>
              </>
            )}
          </div>
        )}
      </Card>
    );
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
        <Title level={4} style={{ margin: 0 }}>模板库管理</Title>
        <Space>
          <Button
            icon={<RobotOutlined />}
            onClick={() => navigate('/agents')}
          >
            管理智能体
          </Button>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => handleCreate('category')}
          >
            新建分类
          </Button>
          <Button
            icon={<ReloadOutlined />}
            onClick={() => queryClient.invalidateQueries('template-tree')}
          >
            刷新
          </Button>
          <Button
            icon={<SettingOutlined />}
            onClick={() => initDataMutation.mutate()}
            loading={initDataMutation.isLoading}
          >
            初始化数据
          </Button>
        </Space>
      </div>

      <Layout style={{ flex: 1 }}>
        <Sider width={300} style={{ background: '#fff', borderRight: '1px solid #f0f0f0' }}>
          <div style={{ padding: 16 }}>
            <Search
              placeholder="搜索模板"
              value={searchKeyword}
              onChange={(e) => setSearchKeyword(e.target.value)}
              style={{ marginBottom: 16 }}
            />
            
            {statistics && (
              <Row gutter={16} style={{ marginBottom: 16 }}>
                <Col span={12}>
                  <Statistic title="分类" value={statistics.total_categories} />
                </Col>
                <Col span={12}>
                  <Statistic title="类型" value={statistics.total_types} />
                </Col>
              </Row>
            )}





            <Tree
              showIcon={true}
              showLine={true}
              defaultExpandAll={true}
              treeData={templateTree ? convertTreeData(templateTree) : []}
              onSelect={handleTreeSelect}
              loading={treeLoading}
              titleRender={(nodeData) => {
                // 确保title正确显示
                return <span>{nodeData.title || nodeData.name || '未命名'}</span>;
              }}
            />
          </div>
        </Sider>

        <Content style={{ padding: 24 }}>
          {renderDetailPanel()}
        </Content>
      </Layout>

      {/* 创建/编辑模态框 */}
      <Modal
        title={modalType === 'create' ? '创建' : '编辑'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        onOk={() => form.submit()}
        confirmLoading={
          createCategoryMutation.isLoading ||
          createTypeMutation.isLoading ||
          createFileMutation.isLoading
        }
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Form.Item
            name="name"
            label="名称"
            rules={[{ required: true, message: '请输入名称' }]}
          >
            <Input placeholder="请输入名称" />
          </Form.Item>

          <Form.Item
            name="description"
            label="描述"
          >
            <TextArea rows={3} placeholder="请输入描述" />
          </Form.Item>

          <Form.Item
            name="sort_order"
            label="排序"
            initialValue={0}
          >
            <Input type="number" placeholder="排序值，数字越小越靠前" />
          </Form.Item>

          {selectedNodeType === 'type' && (
            <Form.Item
              name="content"
              label="模板内容"
            >
              <TextArea rows={6} placeholder="请输入模板内容" />
            </Form.Item>
          )}
        </Form>
      </Modal>

      {/* 写作场景配置模态框 */}
      <Modal
        title={editingScenarioConfig ? '编辑写作场景配置' : '创建写作场景配置'}
        open={scenarioModalVisible}
        onCancel={() => {
          setScenarioModalVisible(false);
          setEditingScenarioConfig(null);
          scenarioForm.resetFields();
        }}
        onOk={() => scenarioForm.submit()}
        confirmLoading={
          createScenarioConfigMutation.isLoading ||
          updateScenarioConfigMutation.isLoading
        }
        width={800}
      >
        <Form
          form={scenarioForm}
          layout="vertical"
          onFinish={(values) => {
            if (editingScenarioConfig) {
              updateScenarioConfigMutation.mutate({
                configId: editingScenarioConfig.id,
                data: values
              });
            } else if (selectedNode) {
              createScenarioConfigMutation.mutate({
                typeId: selectedNode.id,
                data: {
                  ...values,
                  template_type_id: selectedNode.id
                }
              });
            }
          }}
        >
          <Form.Item
            name="config_name"
            label="配置名称"
            rules={[{ required: true, message: '请输入配置名称' }]}
          >
            <Input placeholder="请输入配置名称" />
          </Form.Item>

          <Form.Item
            name="description"
            label="配置描述"
          >
            <TextArea rows={2} placeholder="请输入配置描述" />
          </Form.Item>

          <Form.Item
            label="字段配置"
            required
          >
            <Form.List name="field_configs">
              {(fields, { add, remove }) => (
                <>
                  {fields.map(({ key, name, ...restField }) => (
                    <Card key={key} size="small" style={{ marginBottom: 8 }}>
                      <Row gutter={16}>
                        <Col span={6}>
                          <Form.Item
                            {...restField}
                            name={[name, 'field_name']}
                            label="字段名称"
                            rules={[{ required: true, message: '请输入字段名称' }]}
                          >
                            <Input placeholder="字段名称" />
                          </Form.Item>
                        </Col>
                        <Col span={6}>
                          <Form.Item
                            {...restField}
                            name={[name, 'field_key']}
                            label="字段键名"
                            rules={[{ required: true, message: '请输入字段键名' }]}
                          >
                            <Input placeholder="字段键名" />
                          </Form.Item>
                        </Col>
                        <Col span={6}>
                          <Form.Item
                            {...restField}
                            name={[name, 'field_type']}
                            label="字段类型"
                            initialValue="text"
                          >
                            <Select>
                              <Option value="text">文本</Option>
                              <Option value="textarea">多行文本</Option>
                              <Option value="select">选择框</Option>
                            </Select>
                          </Form.Item>
                        </Col>
                        <Col span={6}>
                          <div style={{ display: 'flex', alignItems: 'center', height: '100%', paddingTop: 30 }}>
                            <Button
                              type="link"
                              danger
                              onClick={() => remove(name)}
                              icon={<DeleteOutlined />}
                            >
                              删除
                            </Button>
                          </div>
                        </Col>
                      </Row>
                      <Row gutter={16}>
                        <Col span={12}>
                          <Form.Item
                            {...restField}
                            name={[name, 'placeholder']}
                            label="占位符"
                          >
                            <Input placeholder="占位符文本" />
                          </Form.Item>
                        </Col>
                        <Col span={12}>
                          <Row gutter={8}>
                            <Col span={8}>
                              <Form.Item
                                {...restField}
                                name={[name, 'required']}
                                valuePropName="checked"
                                label="必填"
                              >
                                <Switch />
                              </Form.Item>
                            </Col>
                            <Col span={8}>
                              <Form.Item
                                {...restField}
                                name={[name, 'ai_enabled']}
                                valuePropName="checked"
                                label="AI生成"
                              >
                                <Switch />
                              </Form.Item>
                            </Col>
                            <Col span={8}>
                              <Form.Item
                                {...restField}
                                name={[name, 'doc_enabled']}
                                valuePropName="checked"
                                label="文档选择"
                              >
                                <Switch />
                              </Form.Item>
                            </Col>
                          </Row>
                        </Col>
                      </Row>
                    </Card>
                  ))}
                  <Form.Item>
                    <Button
                      type="dashed"
                      onClick={() => add()}
                      block
                      icon={<PlusOutlined />}
                    >
                      添加字段
                    </Button>
                  </Form.Item>
                </>
              )}
            </Form.List>
          </Form.Item>
        </Form>
      </Modal>

      {/* 智能体配置模态框 */}
      <Modal
        title="配置智能体"
        open={agentModalVisible}
        onOk={() => {
          if (selectedFieldId && selectedAgentId) {
            assignAgentMutation.mutate({
              fieldId: selectedFieldId,
              agentId: selectedAgentId
            });
          }
        }}
        onCancel={() => {
          setAgentModalVisible(false);
          setSelectedFieldId(null);
          setSelectedAgentId(null);
        }}
        okText="确定"
        cancelText="取消"
        confirmLoading={assignAgentMutation.isLoading}
      >
        <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Text>请选择要分配给此字段的智能体：</Text>
          <Button
            size="small"
            type="link"
            icon={<PlusOutlined />}
            onClick={() => {
              setAgentModalVisible(false);
              navigate('/agents');
            }}
          >
            新建智能体
          </Button>
        </div>
        <Select
          style={{ width: '100%' }}
          placeholder="选择智能体"
          value={selectedAgentId}
          onChange={setSelectedAgentId}
          showSearch
          optionFilterProp="children"
        >
          {agentConfigs?.map(agent => (
            <Option key={agent.id} value={agent.id}>
              <div>
                <div style={{ fontWeight: 'bold' }}>{agent.name}</div>
                <div style={{ fontSize: 12, color: '#666' }}>{agent.description}</div>
              </div>
            </Option>
          ))}
        </Select>

        {selectedAgentId && agentConfigs && (
          <div style={{ marginTop: 16, padding: 12, background: '#f5f5f5', borderRadius: 4 }}>
            {(() => {
              const agent = agentConfigs.find(a => a.id === selectedAgentId);
              if (!agent) return null;

              return (
                <div>
                  <div style={{ marginBottom: 8 }}>
                    <Text strong>智能体详情：</Text>
                  </div>
                  <div style={{ marginBottom: 4 }}>
                    <Text>名称：{agent.name}</Text>
                  </div>
                  <div style={{ marginBottom: 4 }}>
                    <Text>模型：{agent.model_name}</Text>
                  </div>
                  <div style={{ marginBottom: 4 }}>
                    <Text>工具：{agent.tools.length > 0 ? agent.tools.join(', ') : '无'}</Text>
                  </div>
                  <div>
                    <Text>描述：{agent.description || '无描述'}</Text>
                  </div>
                </div>
              );
            })()}
          </div>
        )}
      </Modal>
    </Layout>
  );
};

export default TemplateManagement;
