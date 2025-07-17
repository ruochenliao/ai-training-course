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
  Divider
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
  HomeOutlined,
  SettingOutlined,
  EyeOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import writingThemeService, { ThemeField, WritingTheme } from '@/services/writingThemeService';

const { TextArea } = Input;
const { Option } = Select;

const ThemeFieldConfigPage: React.FC = () => {
  const { themeId } = useParams<{ themeId: string }>();
  const navigate = useNavigate();
  
  // 状态管理
  const [theme, setTheme] = useState<WritingTheme | null>(null);
  const [fields, setFields] = useState<ThemeField[]>([]);
  const [loading, setLoading] = useState(false);
  
  // 模态框状态
  const [fieldModalVisible, setFieldModalVisible] = useState(false);
  const [editingField, setEditingField] = useState<ThemeField | null>(null);
  const [previewModalVisible, setPreviewModalVisible] = useState(false);
  
  // 表单
  const [form] = Form.useForm();

  // 字段类型选项
  const fieldTypeOptions = writingThemeService.getFieldTypeOptions();

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
      const [themeData, fieldsData] = await Promise.all([
        writingThemeService.getTheme(parseInt(themeId)),
        writingThemeService.getThemeFields(parseInt(themeId))
      ]);
      
      setTheme(themeData);
      setFields(fieldsData.sort((a, b) => a.sort_order - b.sort_order));
    } catch (error) {
      message.error('加载数据失败');
      console.error('加载数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 表格列定义
  const columns: ColumnsType<ThemeField> = [
    {
      title: '排序',
      dataIndex: 'sort_order',
      key: 'sort_order',
      width: 80,
      render: (_, record, index) => (
        <Space>
          <Button
            type="text"
            size="small"
            icon={<ArrowUpOutlined />}
            disabled={index === 0}
            onClick={() => handleMoveField(record, 'up')}
          />
          <Button
            type="text"
            size="small"
            icon={<ArrowDownOutlined />}
            disabled={index === fields.length - 1}
            onClick={() => handleMoveField(record, 'down')}
          />
        </Space>
      ),
    },
    {
      title: '字段标签',
      dataIndex: 'field_label',
      key: 'field_label',
    },
    {
      title: '字段键名',
      dataIndex: 'field_key',
      key: 'field_key',
      render: (text) => <code>{text}</code>,
    },
    {
      title: '字段类型',
      dataIndex: 'field_type',
      key: 'field_type',
      render: (type) => {
        const option = fieldTypeOptions.find(opt => opt.value === type);
        return <Tag color="blue">{option?.label || type}</Tag>;
      },
    },
    {
      title: '必填',
      dataIndex: 'is_required',
      key: 'is_required',
      width: 80,
      render: (required) => (
        <Tag color={required ? 'red' : 'default'}>
          {required ? '必填' : '可选'}
        </Tag>
      ),
    },
    {
      title: '显示',
      dataIndex: 'is_visible',
      key: 'is_visible',
      width: 80,
      render: (visible) => (
        <Tag color={visible ? 'success' : 'default'}>
          {visible ? '显示' : '隐藏'}
        </Tag>
      ),
    },
    {
      title: '占位符',
      dataIndex: 'placeholder',
      key: 'placeholder',
      ellipsis: true,
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="预览">
            <Button
              type="text"
              icon={<EyeOutlined />}
              onClick={() => handlePreviewField(record)}
            />
          </Tooltip>
          <Tooltip title="编辑">
            <Button
              type="text"
              icon={<EditOutlined />}
              onClick={() => handleEditField(record)}
            />
          </Tooltip>
          <Popconfirm
            title="确定要删除这个字段吗？"
            onConfirm={() => handleDeleteField(record)}
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
  const handleCreateField = () => {
    setEditingField(null);
    form.resetFields();
    form.setFieldsValue({
      is_required: false,
      is_visible: true,
      sort_order: fields.length,
      field_type: 'text'
    });
    setFieldModalVisible(true);
  };

  const handleEditField = (field: ThemeField) => {
    setEditingField(field);
    form.setFieldsValue(field);
    setFieldModalVisible(true);
  };

  const handlePreviewField = (field: ThemeField) => {
    setEditingField(field);
    setPreviewModalVisible(true);
  };

  const handleMoveField = async (field: ThemeField, direction: 'up' | 'down') => {
    const currentIndex = fields.findIndex(f => f.id === field.id);
    const targetIndex = direction === 'up' ? currentIndex - 1 : currentIndex + 1;
    
    if (targetIndex < 0 || targetIndex >= fields.length) return;
    
    try {
      // 交换排序值
      const currentField = fields[currentIndex];
      const targetField = fields[targetIndex];
      
      await Promise.all([
        writingThemeService.updateThemeField(currentField.id!, { sort_order: targetField.sort_order }),
        writingThemeService.updateThemeField(targetField.id!, { sort_order: currentField.sort_order })
      ]);
      
      message.success('排序更新成功');
      loadData();
    } catch (error) {
      message.error('排序更新失败');
    }
  };

  const handleDeleteField = async (field: ThemeField) => {
    try {
      await writingThemeService.deleteThemeField(field.id!);
      message.success('删除成功');
      loadData();
    } catch (error) {
      message.error('删除失败');
    }
  };

  const handleSaveField = async () => {
    try {
      const values = await form.validateFields();
      
      if (editingField) {
        await writingThemeService.updateThemeField(editingField.id!, values);
        message.success('更新成功');
      } else {
        await writingThemeService.createThemeField(parseInt(themeId!), values);
        message.success('创建成功');
      }
      
      setFieldModalVisible(false);
      loadData();
    } catch (error) {
      message.error('保存失败');
    }
  };

  const renderFieldPreview = (field: ThemeField) => {
    const commonProps = {
      placeholder: field.placeholder,
      disabled: true,
      style: { width: '100%' }
    };

    switch (field.field_type) {
      case 'text':
        return <Input {...commonProps} />;
      case 'textarea':
        return <TextArea {...commonProps} rows={3} />;
      case 'number':
        return <InputNumber {...commonProps} />;
      case 'select':
        return (
          <Select {...commonProps}>
            <Option value="option1">选项1</Option>
            <Option value="option2">选项2</Option>
          </Select>
        );
      case 'date':
        return <Input {...commonProps} type="date" />;
      case 'email':
        return <Input {...commonProps} type="email" />;
      case 'url':
        return <Input {...commonProps} type="url" />;
      default:
        return <Input {...commonProps} />;
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
          <SettingOutlined />
          字段配置
        </Breadcrumb.Item>
      </Breadcrumb>

      {/* 主题信息 */}
      {theme && (
        <Card style={{ marginBottom: '24px' }}>
          <Row gutter={16}>
            <Col span={18}>
              <h2>
                <span style={{ fontSize: '24px', marginRight: '8px' }}>{theme.icon}</span>
                {theme.name} - 字段配置
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

      {/* 字段列表 */}
      <Card
        title={`字段配置 (${fields.length})`}
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleCreateField}
          >
            新建字段
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={fields}
          rowKey="id"
          loading={loading}
          pagination={false}
        />
      </Card>

      {/* 字段编辑模态框 */}
      <Modal
        title={editingField ? '编辑字段' : '新建字段'}
        open={fieldModalVisible}
        onOk={handleSaveField}
        onCancel={() => setFieldModalVisible(false)}
        width={600}
        destroyOnClose
      >
        <Form
          form={form}
          layout="vertical"
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="field_label"
                label="字段标签"
                rules={[{ required: true, message: '请输入字段标签' }]}
              >
                <Input placeholder="请输入字段标签" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="field_key"
                label="字段键名"
                rules={[
                  { required: true, message: '请输入字段键名' },
                  { pattern: /^[a-z_]+$/, message: '只能包含小写字母和下划线' }
                ]}
              >
                <Input placeholder="例如: recipient_name" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="field_type"
                label="字段类型"
                rules={[{ required: true, message: '请选择字段类型' }]}
              >
                <Select placeholder="请选择字段类型">
                  {fieldTypeOptions.map(option => (
                    <Option key={option.value} value={option.value}>
                      {option.label}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="sort_order"
                label="排序顺序"
              >
                <InputNumber min={0} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="placeholder"
            label="占位符文本"
          >
            <Input placeholder="请输入占位符文本" />
          </Form.Item>

          <Form.Item
            name="default_value"
            label="默认值"
          >
            <Input placeholder="请输入默认值" />
          </Form.Item>

          <Form.Item
            name="help_text"
            label="帮助文本"
          >
            <TextArea rows={2} placeholder="请输入帮助文本" />
          </Form.Item>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                name="is_required"
                label="是否必填"
                valuePropName="checked"
              >
                <Switch checkedChildren="必填" unCheckedChildren="可选" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="is_visible"
                label="是否显示"
                valuePropName="checked"
              >
                <Switch checkedChildren="显示" unCheckedChildren="隐藏" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="max_length"
                label="最大长度"
              >
                <InputNumber min={1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>

      {/* 字段预览模态框 */}
      <Modal
        title="字段预览"
        open={previewModalVisible}
        onCancel={() => setPreviewModalVisible(false)}
        footer={null}
        width={500}
      >
        {editingField && (
          <div>
            <h4>{editingField.field_label}</h4>
            {editingField.help_text && (
              <p style={{ color: '#666', fontSize: '12px', marginBottom: '8px' }}>
                {editingField.help_text}
              </p>
            )}
            {renderFieldPreview(editingField)}
            <Divider />
            <Row gutter={16}>
              <Col span={12}>
                <p><strong>字段键名：</strong><code>{editingField.field_key}</code></p>
                <p><strong>字段类型：</strong>{fieldTypeOptions.find(opt => opt.value === editingField.field_type)?.label}</p>
              </Col>
              <Col span={12}>
                <p><strong>是否必填：</strong>{editingField.is_required ? '是' : '否'}</p>
                <p><strong>是否显示：</strong>{editingField.is_visible ? '是' : '否'}</p>
              </Col>
            </Row>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default ThemeFieldConfigPage;
