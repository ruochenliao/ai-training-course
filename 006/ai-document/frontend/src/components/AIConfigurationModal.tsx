import React, { useState, useEffect } from 'react';
import { Modal, Form, Input, Button, Space, Typography, Card, message, Spin } from 'antd';
import { SendOutlined, ReloadOutlined, CheckOutlined } from '@ant-design/icons';
import { AIWritingTheme, AIWritingField, aiWritingThemesService } from '@/services/aiWritingThemes';

const { Text, Title } = Typography;
const { TextArea } = Input;

interface AIConfigurationModalProps {
  visible: boolean;
  theme: AIWritingTheme | null;
  onGenerate: (content: string) => void;
  onStartStreaming: (sessionId: string) => void;
  onCancel: () => void;
}

const AIConfigurationModal: React.FC<AIConfigurationModalProps> = ({
  visible,
  theme,
  onGenerate,
  onStartStreaming,
  onCancel
}) => {
  const [form] = Form.useForm();
  const [generating, setGenerating] = useState(false);
  const [generatedContent, setGeneratedContent] = useState('');
  const [sessionId, setSessionId] = useState<string | null>(null);

  // 重置表单和状态
  useEffect(() => {
    if (visible && theme) {
      form.resetFields();
      setGeneratedContent('');
      setSessionId(null);
      setGenerating(false);
    }
  }, [visible, theme, form]);

  // 处理生成内容
  const handleGenerate = async () => {
    try {
      const values = await form.validateFields();
      setGenerating(true);
      setGeneratedContent('');

      // 构建生成请求
      const request = {
        theme_id: theme!.id,
        fields: values,
        additional_context: values.additional_context || ''
      };

      // 调用AI生成服务
      const response = await aiWritingThemesService.generateContent(request);
      setSessionId(response.session_id);

      // 通知父组件开始流式输出
      onStartStreaming(response.session_id);

      // 关闭配置模态框
      handleCancel();

    } catch (error) {
      console.error('生成失败:', error);
      message.error('生成失败，请重试');
      setGenerating(false);
    }
  };

  // 轮询生成状态
  const pollGenerationStatus = async (sessionId: string) => {
    try {
      const response = await aiWritingThemesService.getGenerationStatus(sessionId);
      
      if (response.status === 'completed') {
        setGeneratedContent(response.content || '');
        setGenerating(false);
        message.success('内容生成完成');
      } else if (response.status === 'failed') {
        setGenerating(false);
        message.error('生成失败：' + (response.error || '未知错误'));
      } else {
        // 继续轮询
        setTimeout(() => pollGenerationStatus(sessionId), 1000);
      }
    } catch (error) {
      console.error('获取生成状态失败:', error);
      setGenerating(false);
      message.error('获取生成状态失败');
    }
  };

  // 使用生成的内容
  const handleUseContent = () => {
    if (generatedContent) {
      onGenerate(generatedContent);
      handleCancel();
    }
  };

  // 重新生成
  const handleRegenerate = () => {
    handleGenerate();
  };

  const handleCancel = () => {
    form.resetFields();
    setGeneratedContent('');
    setSessionId(null);
    setGenerating(false);
    onCancel();
  };

  // 渲染表单字段
  const renderFormField = (field: AIWritingField) => {
    const commonProps = {
      placeholder: field.placeholder,
      style: { width: '100%' }
    };

    switch (field.type) {
      case 'textarea':
        return (
          <TextArea
            {...commonProps}
            rows={3}
            showCount
            maxLength={500}
          />
        );
      case 'select':
        return (
          <Input {...commonProps} />
        );
      case 'number':
        return (
          <Input
            {...commonProps}
            type="number"
          />
        );
      default:
        return <Input {...commonProps} />;
    }
  };

  if (!theme) return null;

  return (
    <Modal
      title={
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <span style={{ fontSize: '16px', marginRight: '8px' }}>
            {theme.icon || '📝'}
          </span>
          <span>{theme.name} - 配置生成</span>
        </div>
      }
      open={visible}
      onCancel={handleCancel}
      width={600}
      centered
      destroyOnClose
      footer={null}
      styles={{
        body: { padding: '16px 24px' }
      }}
    >
      <div style={{ maxHeight: '500px', overflowY: 'auto' }}>
        <Card
          title="填写生成信息"
          size="small"
          bodyStyle={{ padding: '16px' }}
        >
            <Form
              form={form}
              layout="vertical"
              size="middle"
            >
              {theme.fields?.map((field) => (
                <Form.Item
                  key={field.key}
                  name={field.key}
                  label={
                    <span>
                      {field.label}
                      {field.required && <span style={{ color: 'red' }}> *</span>}
                    </span>
                  }
                  rules={[
                    {
                      required: field.required,
                      message: `请输入${field.label}`
                    }
                  ]}
                  style={{ marginBottom: '16px' }}
                >
                  {renderFormField(field)}
                </Form.Item>
              ))}

              {/* 额外上下文 */}
              <Form.Item
                name="additional_context"
                label="补充说明"
                style={{ marginBottom: '16px' }}
              >
                <TextArea
                  placeholder="如有其他特殊要求或补充信息，请在此说明..."
                  rows={2}
                  showCount
                  maxLength={200}
                />
              </Form.Item>

              {/* 生成按钮 */}
              <Form.Item style={{ marginBottom: 0 }}>
                <Button
                  type="primary"
                  icon={<SendOutlined />}
                  onClick={handleGenerate}
                  loading={generating}
                  block
                  size="large"
                >
                  {generating ? '正在生成...' : '开始生成'}
                </Button>
              </Form.Item>
            </Form>
          </Card>
        </div>

      {/* 底部提示 */}
      <div style={{
        marginTop: '16px',
        padding: '12px',
        backgroundColor: '#f0f8ff',
        borderRadius: '6px',
        border: '1px solid #e6f7ff'
      }}>
        <Text style={{ fontSize: '12px', color: '#1890ff' }}>
          💡 提示：填写的信息越详细，生成的内容质量越高。点击"开始生成"后，内容将直接在编辑器中流式显示。
        </Text>
      </div>
    </Modal>
  );
};

export default AIConfigurationModal;
