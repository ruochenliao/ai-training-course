import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Tag,
  Modal,
  Form,
  Input,
  Select,
  Switch,
  InputNumber,
  message,
  Popconfirm,
  Tabs,
  Row,
  Col,
  Statistic,
  Tooltip
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  SettingOutlined,
  FileTextOutlined,
  BulbOutlined,
  BarChartOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import writingThemeService, { WritingTheme, WritingThemeSimple, ThemeCategory } from '@/services/writingThemeService';

const { TabPane } = Tabs;
const { TextArea } = Input;
const { Option } = Select;

const WritingThemeManagementPage: React.FC = () => {
  // 状态管理
  const [themes, setThemes] = useState<WritingThemeSimple[]>([]);
  const [categories, setCategories] = useState<ThemeCategory[]>([]);
  const [statistics, setStatistics] = useState<any>({});
  const [loading, setLoading] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  
  // 模态框状态
  const [themeModalVisible, setThemeModalVisible] = useState(false);
  const [editingTheme, setEditingTheme] = useState<WritingTheme | null>(null);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [selectedTheme, setSelectedTheme] = useState<WritingTheme | null>(null);
  
  // 表单
  const [form] = Form.useForm();

  // 初始化数据
  useEffect(() => {
    loadData();
  }, [selectedCategory]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [themesData, categoriesData, statsData] = await Promise.all([
        writingThemeService.getThemesSimple({ 
          category: selectedCategory || undefined 
        }),
        writingThemeService.getCategories(),
        writingThemeService.getStatistics()
      ]);
      
      setThemes(themesData);
      setCategories(categoriesData);
      setStatistics(statsData);
    } catch (error) {
      message.error('加载数据失败');
      console.error('加载数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 表格列定义
  const columns: ColumnsType<WritingThemeSimple> = [
    {
      title: '主题名称',
      dataIndex: 'name',
      key: 'name',
      render: (text, record) => (
        <Space>
          <span style={{ fontSize: '18px' }}>{record.icon}</span>
          <span>{text}</span>
        </Space>
      ),
    },
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category',
      render: (category) => {
        const cat = categories.find(c => c.name === category);
        return (
          <Tag color={cat?.color || 'blue'}>
            {cat?.icon} {category}
          </Tag>
        );
      },
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: '字段数',
      dataIndex: 'field_count',
      key: 'field_count',
      width: 80,
      render: (count) => (
        <Tag color="green">{count}</Tag>
      ),
    },
    {
      title: '模板数',
      dataIndex: 'template_count',
      key: 'template_count',
      width: 80,
      render: (count) => (
        <Tag color="blue">{count}</Tag>
      ),
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
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 120,
      render: (date) => new Date(date).toLocaleDateString(),
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="查看详情">
            <Button
              type="text"
              icon={<EyeOutlined />}
              onClick={() => handleViewDetail(record.id)}
            />
          </Tooltip>
          <Tooltip title="编辑">
            <Button
              type="text"
              icon={<EditOutlined />}
              onClick={() => handleEdit(record.id)}
            />
          </Tooltip>
          <Tooltip title="配置字段">
            <Button
              type="text"
              icon={<SettingOutlined />}
              onClick={() => handleConfigFields(record.id)}
            />
          </Tooltip>
          <Tooltip title="管理模板">
            <Button
              type="text"
              icon={<FileTextOutlined />}
              onClick={() => handleManageTemplates(record.id)}
            />
          </Tooltip>
          <Popconfirm
            title="确定要删除这个主题吗？"
            onConfirm={() => handleDelete(record.id)}
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
  const handleCreate = () => {
    setEditingTheme(null);
    form.resetFields();
    setThemeModalVisible(true);
  };

  const handleEdit = async (themeId: number) => {
    try {
      const theme = await writingThemeService.getTheme(themeId);
      setEditingTheme(theme);
      form.setFieldsValue(theme);
      setThemeModalVisible(true);
    } catch (error) {
      message.error('获取主题详情失败');
    }
  };

  const handleViewDetail = async (themeId: number) => {
    try {
      const theme = await writingThemeService.getTheme(themeId);
      setSelectedTheme(theme);
      setDetailModalVisible(true);
    } catch (error) {
      message.error('获取主题详情失败');
    }
  };

  const handleConfigFields = (themeId: number) => {
    // 跳转到字段配置页面
    window.open(`/writing-themes/${themeId}/fields`, '_blank');
  };

  const handleManageTemplates = (themeId: number) => {
    // 跳转到模板管理页面
    window.open(`/writing-themes/${themeId}/templates`, '_blank');
  };

  const handleDelete = async (themeId: number) => {
    try {
      await writingThemeService.deleteTheme(themeId);
      message.success('删除成功');
      loadData();
    } catch (error) {
      message.error('删除失败');
    }
  };

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      
      if (editingTheme) {
        await writingThemeService.updateTheme(editingTheme.id!, values);
        message.success('更新成功');
      } else {
        await writingThemeService.createTheme({
          ...values,
          fields: [],
          prompt_templates: []
        });
        message.success('创建成功');
      }
      
      setThemeModalVisible(false);
      loadData();
    } catch (error) {
      message.error('保存失败');
    }
  };

  return (
    <div style={{ padding: '24px' }}>
      {/* 页面标题和统计 */}
      <Row gutter={16} style={{ marginBottom: '24px' }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="总主题数"
              value={statistics.total_themes || 0}
              prefix={<FileTextOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="启用主题"
              value={statistics.active_themes || 0}
              prefix={<BulbOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="分类数量"
              value={statistics.total_categories || 0}
              prefix={<BarChartOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="使用率"
              value={statistics.active_themes && statistics.total_themes ? 
                Math.round((statistics.active_themes / statistics.total_themes) * 100) : 0}
              suffix="%"
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 主要内容 */}
      <Card
        title="写作主题管理"
        extra={
          <Space>
            <Select
              placeholder="选择分类"
              allowClear
              style={{ width: 120 }}
              value={selectedCategory}
              onChange={setSelectedCategory}
            >
              {categories.map(cat => (
                <Option key={cat.name} value={cat.name}>
                  {cat.icon} {cat.name}
                </Option>
              ))}
            </Select>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={handleCreate}
            >
              新建主题
            </Button>
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={themes}
          rowKey="id"
          loading={loading}
          pagination={{
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条记录`,
          }}
        />
      </Card>

      {/* 创建/编辑主题模态框 */}
      <Modal
        title={editingTheme ? '编辑主题' : '新建主题'}
        open={themeModalVisible}
        onOk={handleSave}
        onCancel={() => setThemeModalVisible(false)}
        width={600}
        destroyOnClose
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            is_active: true,
            sort_order: 0
          }}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="name"
                label="主题名称"
                rules={[{ required: true, message: '请输入主题名称' }]}
              >
                <Input placeholder="请输入主题名称" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="theme_key"
                label="主题标识"
                rules={[
                  { required: true, message: '请输入主题标识' },
                  { pattern: /^[a-z_]+$/, message: '只能包含小写字母和下划线' }
                ]}
              >
                <Input placeholder="例如: commendation_notice" />
              </Form.Item>
            </Col>
          </Row>
          
          <Form.Item
            name="description"
            label="主题描述"
          >
            <TextArea rows={3} placeholder="请输入主题描述" />
          </Form.Item>
          
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                name="category"
                label="分类"
                rules={[{ required: true, message: '请选择分类' }]}
              >
                <Select placeholder="请选择分类">
                  {categories.map(cat => (
                    <Option key={cat.name} value={cat.name}>
                      {cat.icon} {cat.name}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="icon"
                label="图标"
              >
                <Input placeholder="例如: 🏆" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="sort_order"
                label="排序"
              >
                <InputNumber min={0} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          
          <Form.Item
            name="is_active"
            label="状态"
            valuePropName="checked"
          >
            <Switch checkedChildren="启用" unCheckedChildren="禁用" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 主题详情模态框 */}
      <Modal
        title="主题详情"
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={null}
        width={800}
      >
        {selectedTheme && (
          <Tabs defaultActiveKey="basic">
            <TabPane tab="基本信息" key="basic">
              <div style={{ padding: '16px 0' }}>
                <Row gutter={16}>
                  <Col span={12}>
                    <p><strong>主题名称：</strong>{selectedTheme.name}</p>
                    <p><strong>主题标识：</strong>{selectedTheme.theme_key}</p>
                    <p><strong>分类：</strong>{selectedTheme.category}</p>
                  </Col>
                  <Col span={12}>
                    <p><strong>图标：</strong>{selectedTheme.icon}</p>
                    <p><strong>状态：</strong>{selectedTheme.is_active ? '启用' : '禁用'}</p>
                    <p><strong>排序：</strong>{selectedTheme.sort_order}</p>
                  </Col>
                </Row>
                <p><strong>描述：</strong>{selectedTheme.description}</p>
              </div>
            </TabPane>
            <TabPane tab={`字段配置 (${selectedTheme.fields.length})`} key="fields">
              <Table
                dataSource={selectedTheme.fields}
                columns={[
                  { title: '字段名', dataIndex: 'field_label', key: 'field_label' },
                  { title: '字段键', dataIndex: 'field_key', key: 'field_key' },
                  { title: '类型', dataIndex: 'field_type', key: 'field_type' },
                  { title: '必填', dataIndex: 'is_required', key: 'is_required', render: (val) => val ? '是' : '否' },
                ]}
                pagination={false}
                size="small"
              />
            </TabPane>
            <TabPane tab={`提示词模板 (${selectedTheme.prompt_templates.length})`} key="templates">
              <Table
                dataSource={selectedTheme.prompt_templates}
                columns={[
                  { title: '模板名称', dataIndex: 'template_name', key: 'template_name' },
                  { title: '类型', dataIndex: 'template_type', key: 'template_type' },
                  { title: 'AI模型', dataIndex: 'ai_model', key: 'ai_model' },
                  { title: '状态', dataIndex: 'is_active', key: 'is_active', render: (val) => val ? '启用' : '禁用' },
                ]}
                pagination={false}
                size="small"
              />
            </TabPane>
          </Tabs>
        )}
      </Modal>
    </div>
  );
};

export default WritingThemeManagementPage;
