import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Card,
  Table,
  Button,
  Space,
  Modal,
  Form,
  Input,
  Select,
  Switch,
  InputNumber,
  message,
  Popconfirm,
  Tag,
  Tooltip,
  Row,
  Col,
  Breadcrumb,
  Tabs,
  Typography,
  Divider
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  PlayCircleOutlined,
  HomeOutlined,
  FileTextOutlined,
  BulbOutlined,
  CodeOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import writingThemeService, { 
  PromptTemplate, 
  WritingTheme, 
  TemplatePreviewRequest,
  TemplatePreviewResponse 
} from '@/services/writingThemeService';

const { TextArea } = Input;
const { Option } = Select;
const { TabPane } = Tabs;
const { Text, Paragraph } = Typography;

const TemplateManagementPage: React.FC = () => {
  const { themeId } = useParams<{ themeId: string }>();
  const navigate = useNavigate();
  
  // 状态管理
  const [theme, setTheme] = useState<WritingTheme | null>(null);
  const [templates, setTemplates] = useState<PromptTemplate[]>([]);
  const [loading, setLoading] = useState(false);
  
  // 模态框状态
  const [templateModalVisible, setTemplateModalVisible] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState<PromptTemplate | null>(null);
  const [previewModalVisible, setPreviewModalVisible] = useState(false);
  const [previewData, setPreviewData] = useState<TemplatePreviewResponse | null>(null);
  const [testModalVisible, setTestModalVisible] = useState(false);
  
  // 表单
  const [form] = Form.useForm();
  const [testForm] = Form.useForm();

  // 选项数据
  const templateTypeOptions = writingThemeService.getTemplateTypeOptions();
  const aiModelOptions = writingThemeService.getAIModelOptions();

  // 初始化数据
  useEffect(() => {
    if (themeId) {
      loadData();
    }
  }, [themeId]);

  const loadData = async () => {
    if (!themeId) return;
    
    setLoading(true);
    try {
      const [themeData, templatesData] = await Promise.all([
        writingThemeService.getTheme(parseInt(themeId)),
        writingThemeService.getThemeTemplates(parseInt(themeId))
      ]);
      
      setTheme(themeData);
      setTemplates(templatesData);
    } catch (error) {
      message.error('加载数据失败');
      console.error('加载数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 表格列定义
  const columns: ColumnsType<PromptTemplate> = [
    {
      title: '模板名称',
      dataIndex: 'template_name',
      key: 'template_name',
    },
    {
      title: '模板类型',
      dataIndex: 'template_type',
      key: 'template_type',
      render: (type) => {
        const option = templateTypeOptions.find(opt => opt.value === type);
        return <Tag color="blue">{option?.label || type}</Tag>;
      },
    },
    {
      title: 'AI模型',
      dataIndex: 'ai_model',
      key: 'ai_model',
      render: (model) => model ? <Tag color="green">{model}</Tag> : '-',
    },
    {
      title: '温度',
      dataIndex: 'temperature',
      key: 'temperature',
      width: 80,
      render: (temp) => temp || '-',
    },
    {
      title: '版本',
      dataIndex: 'version',
      key: 'version',
      width: 80,
    },
    {
      title: '使用次数',
      dataIndex: 'usage_count',
      key: 'usage_count',
      width: 100,
      render: (count) => <Tag color="orange">{count || 0}</Tag>,
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 80,
      render: (isActive) => (
        <Tag color={isActive ? 'success' : 'default'}>
          {isActive ? '启用' : '禁用'}
        </Tag>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="预览">
            <Button
              type="text"
              icon={<EyeOutlined />}
              onClick={() => handleViewTemplate(record)}
            />
          </Tooltip>
          <Tooltip title="测试">
            <Button
              type="text"
              icon={<PlayCircleOutlined />}
              onClick={() => handleTestTemplate(record)}
            />
          </Tooltip>
          <Tooltip title="编辑">
            <Button
              type="text"
              icon={<EditOutlined />}
              onClick={() => handleEditTemplate(record)}
            />
          </Tooltip>
          <Popconfirm
            title="确定要删除这个模板吗？"
            onConfirm={() => handleDeleteTemplate(record)}
            okText="确定"
            cancelText="取消"
          >
            <Tooltip title="删除">
              <Button
                type="text"
                danger
                icon={<DeleteOutlined />}
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  // 事件处理函数
  const handleCreateTemplate = () => {
    setEditingTemplate(null);
    form.resetFields();
    form.setFieldsValue({
      template_type: 'main',
      is_active: true,
      version: '1.0',
      ai_model: 'deepseek-chat',
      temperature: '0.7'
    });
    setTemplateModalVisible(true);
  };

  const handleEditTemplate = (template: PromptTemplate) => {
    setEditingTemplate(template);
    form.setFieldsValue(template);
    setTemplateModalVisible(true);
  };

  const handleViewTemplate = (template: PromptTemplate) => {
    setEditingTemplate(template);
    setPreviewModalVisible(true);
  };

  const handleTestTemplate = (template: PromptTemplate) => {
    setEditingTemplate(template);
    
    // 初始化测试表单
    const testValues: Record<string, any> = {};
    if (theme?.fields) {
      theme.fields.forEach(field => {
        testValues[field.field_key] = field.default_value || '';
      });
    }
    testForm.setFieldsValue(testValues);
    
    setTestModalVisible(true);
  };

  const handleDeleteTemplate = async (template: PromptTemplate) => {
    try {
      await writingThemeService.deleteTemplate(template.id!);
      message.success('删除成功');
      loadData();
    } catch (error) {
      message.error('删除失败');
    }
  };

  const handleSaveTemplate = async () => {
    try {
      const values = await form.validateFields();
      
      if (editingTemplate) {
        await writingThemeService.updateTemplate(editingTemplate.id!, values);
        message.success('更新成功');
      } else {
        await writingThemeService.createTemplate(parseInt(themeId!), values);
        message.success('创建成功');
      }
      
      setTemplateModalVisible(false);
      loadData();
    } catch (error) {
      message.error('保存失败');
    }
  };

  const handleRunTest = async () => {
    if (!editingTemplate) return;
    
    try {
      const fieldValues = await testForm.validateFields();
      
      const previewRequest: TemplatePreviewRequest = {
        template_id: editingTemplate.id!,
        field_values: fieldValues
      };
      
      const result = await writingThemeService.previewTemplate(previewRequest);
      setPreviewData(result);
      message.success('测试完成');
    } catch (error) {
      message.error('测试失败');
    }
  };

  return (
    <div style={{ padding: '24px' }}>
      {/* 面包屑导航 */}
      <Breadcrumb style={{ marginBottom: '24px' }}>
        <Breadcrumb.Item>
          <HomeOutlined />
        </Breadcrumb.Item>
        <Breadcrumb.Item>
          <a onClick={() => navigate('/writing-themes')}>写作主题管理</a>
        </Breadcrumb.Item>
        <Breadcrumb.Item>
          <FileTextOutlined />
          提示词模板
        </Breadcrumb.Item>
      </Breadcrumb>

      {/* 主题信息 */}
      {theme && (
        <Card style={{ marginBottom: '24px' }}>
          <Row gutter={16}>
            <Col span={18}>
              <h2>
                <span style={{ fontSize: '24px', marginRight: '8px' }}>{theme.icon}</span>
                {theme.name} - 提示词模板管理
              </h2>
              <p style={{ color: '#666', marginBottom: 0 }}>{theme.description}</p>
            </Col>
            <Col span={6} style={{ textAlign: 'right' }}>
              <Space>
                <Tag color="blue">{theme.category}</Tag>
                <Tag color={theme.is_active ? 'success' : 'default'}>
                  {theme.is_active ? '启用' : '禁用'}
                </Tag>
              </Space>
            </Col>
          </Row>
        </Card>
      )}

      {/* 模板列表 */}
      <Card
        title={`提示词模板 (${templates.length})`}
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleCreateTemplate}
          >
            新建模板
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={templates}
          rowKey="id"
          loading={loading}
          pagination={false}
        />
      </Card>

      {/* 模板编辑模态框 */}
      <Modal
        title={editingTemplate ? '编辑模板' : '新建模板'}
        open={templateModalVisible}
        onOk={handleSaveTemplate}
        onCancel={() => setTemplateModalVisible(false)}
        width={800}
        destroyOnClose
      >
        <Form
          form={form}
          layout="vertical"
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="template_name"
                label="模板名称"
                rules={[{ required: true, message: '请输入模板名称' }]}
              >
                <Input placeholder="请输入模板名称" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="template_type"
                label="模板类型"
                rules={[{ required: true, message: '请选择模板类型' }]}
              >
                <Select placeholder="请选择模板类型">
                  {templateTypeOptions.map(option => (
                    <Option key={option.value} value={option.value}>
                      {option.label}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="system_prompt"
            label="系统提示词"
          >
            <TextArea 
              rows={3} 
              placeholder="请输入系统提示词（可选）"
              showCount
            />
          </Form.Item>

          <Form.Item
            name="user_prompt_template"
            label="用户提示词模板"
            rules={[{ required: true, message: '请输入用户提示词模板' }]}
          >
            <TextArea 
              rows={8} 
              placeholder="请输入用户提示词模板，使用 {field_key} 格式引用字段"
              showCount
            />
          </Form.Item>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                name="ai_model"
                label="推荐AI模型"
              >
                <Select placeholder="请选择AI模型">
                  {aiModelOptions.map(option => (
                    <Option key={option.value} value={option.value}>
                      {option.label}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="temperature"
                label="温度参数"
              >
                <Input placeholder="例如: 0.7" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="max_tokens"
                label="最大令牌数"
              >
                <InputNumber min={1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="version"
                label="版本号"
              >
                <Input placeholder="例如: 1.0" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="is_active"
                label="状态"
                valuePropName="checked"
              >
                <Switch checkedChildren="启用" unCheckedChildren="禁用" />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>

      {/* 模板预览模态框 */}
      <Modal
        title="模板预览"
        open={previewModalVisible}
        onCancel={() => setPreviewModalVisible(false)}
        footer={null}
        width={800}
      >
        {editingTemplate && (
          <Tabs defaultActiveKey="basic">
            <TabPane tab="基本信息" key="basic">
              <Row gutter={16}>
                <Col span={12}>
                  <p><strong>模板名称：</strong>{editingTemplate.template_name}</p>
                  <p><strong>模板类型：</strong>{editingTemplate.template_type}</p>
                  <p><strong>AI模型：</strong>{editingTemplate.ai_model || '-'}</p>
                </Col>
                <Col span={12}>
                  <p><strong>温度参数：</strong>{editingTemplate.temperature || '-'}</p>
                  <p><strong>版本号：</strong>{editingTemplate.version}</p>
                  <p><strong>状态：</strong>{editingTemplate.is_active ? '启用' : '禁用'}</p>
                </Col>
              </Row>
            </TabPane>
            <TabPane tab="系统提示词" key="system">
              <Paragraph>
                <Text code style={{ whiteSpace: 'pre-wrap' }}>
                  {editingTemplate.system_prompt || '无系统提示词'}
                </Text>
              </Paragraph>
            </TabPane>
            <TabPane tab="用户提示词模板" key="user">
              <Paragraph>
                <Text code style={{ whiteSpace: 'pre-wrap' }}>
                  {editingTemplate.user_prompt_template}
                </Text>
              </Paragraph>
            </TabPane>
          </Tabs>
        )}
      </Modal>

      {/* 模板测试模态框 */}
      <Modal
        title="模板测试"
        open={testModalVisible}
        onCancel={() => setTestModalVisible(false)}
        width={1000}
        footer={
          <Space>
            <Button onClick={() => setTestModalVisible(false)}>取消</Button>
            <Button type="primary" icon={<PlayCircleOutlined />} onClick={handleRunTest}>
              运行测试
            </Button>
          </Space>
        }
      >
        <Row gutter={16}>
          <Col span={12}>
            <h4>测试数据</h4>
            <Form form={testForm} layout="vertical">
              {theme?.fields.map(field => (
                <Form.Item
                  key={field.field_key}
                  name={field.field_key}
                  label={field.field_label}
                  rules={field.is_required ? [{ required: true, message: `请输入${field.field_label}` }] : []}
                >
                  {field.field_type === 'textarea' ? (
                    <TextArea rows={2} placeholder={field.placeholder} />
                  ) : (
                    <Input placeholder={field.placeholder} />
                  )}
                </Form.Item>
              ))}
            </Form>
          </Col>
          <Col span={12}>
            <h4>生成的提示词</h4>
            {previewData ? (
              <div>
                <Card size="small" style={{ marginBottom: '16px' }}>
                  <Text strong>使用的变量：</Text>
                  <div style={{ marginTop: '8px' }}>
                    {previewData.variables_used.map(variable => (
                      <Tag key={variable} color="blue">{variable}</Tag>
                    ))}
                  </div>
                  {previewData.estimated_tokens && (
                    <p style={{ marginTop: '8px', marginBottom: 0 }}>
                      <Text type="secondary">预估令牌数：{previewData.estimated_tokens}</Text>
                    </p>
                  )}
                </Card>
                <Card size="small">
                  <Text code style={{ whiteSpace: 'pre-wrap', fontSize: '12px' }}>
                    {previewData.rendered_prompt}
                  </Text>
                </Card>
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
                <BulbOutlined style={{ fontSize: '48px', marginBottom: '16px' }} />
                <p>点击"运行测试"查看生成的提示词</p>
              </div>
            )}
          </Col>
        </Row>
      </Modal>
    </div>
  );
};

export default TemplateManagementPage;
