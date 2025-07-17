import React, { useState, useEffect } from 'react';
import { 
  Layout, 
  Steps, 
  Card, 
  Button, 
  Space, 
  Typography, 
  Tag, 
  Input, 
  Upload, 
  Select, 
  Switch,
  message,
  Spin,
  Modal
} from 'antd';
import { 
  ArrowLeftOutlined, 
  ArrowRightOutlined, 
  CloseOutlined,
  UploadOutlined,
  FileTextOutlined,
  RobotOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { WritingScenario, WritingWizardRequest, TemplateCategoryWithTypes, WritingScenarioConfig, WritingFieldConfig } from '@/types';
import { aiService } from '@/services/ai';
import { templateService } from '@/services/template';
import { agentConfigService } from '@/services/agentConfig';
import { aiGenerationService, FieldType } from '@/services/aiGeneration';
import { useQuery } from 'react-query';

const { Header, Content } = Layout;
const { Title, Text } = Typography;
const { TextArea } = Input;
const { Option } = Select;
const { Step } = Steps;

// 这个常量将被动态数据替代，保留作为备用
const FALLBACK_TEMPLATES = {
  '通报': ['表彰', '批评', '其它通报'],
  '会务': ['会议纪要'],
  '报告和上报信息': ['工作汇报'],
  '讲话': ['就职演讲'],
  '计划': ['工作方案'],
  '总结': ['年度总结'],
  '许可': ['批复'],
  '书信': ['感谢信']
};

const AIWritingWizard: React.FC = () => {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(0);
  const [scenario, setScenario] = useState<WritingScenario>({ step: 1 });
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedContent, setGeneratedContent] = useState('');
  const [checkSimilarity, setCheckSimilarity] = useState(false);
  const [selectedTypeId, setSelectedTypeId] = useState<number | null>(null);
  const [dynamicFormData, setDynamicFormData] = useState<Record<string, any>>({});
  const [generatingFields, setGeneratingFields] = useState<Set<string>>(new Set());

  // 获取模板数据
  const { data: templateData, isLoading: templatesLoading } = useQuery(
    'templates-with-types',
    () => templateService.getCategoriesWithTypes(),
    {
      staleTime: 5 * 60 * 1000, // 5分钟缓存
    }
  );

  // 获取写作场景配置
  const { data: writingScenarioConfig, isLoading: scenarioConfigLoading } = useQuery(
    ['writing-scenario-config', selectedTypeId],
    () => selectedTypeId ? templateService.getWritingScenarioConfig(selectedTypeId) : Promise.resolve(null),
    {
      enabled: selectedTypeId !== null,
      staleTime: 2 * 60 * 1000,
    }
  );

  const handleClose = () => {
    navigate('/');
  };

  const handleNext = () => {
    if (currentStep < 2) {
      setCurrentStep(currentStep + 1);
      setScenario(prev => ({ ...prev, step: currentStep + 2 }));
    } else {
      handleGenerate();
    }
  };

  const handlePrev = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
      setScenario(prev => ({ ...prev, step: currentStep }));
    }
  };

  const handleCategorySelect = (category: string) => {
    setScenario(prev => ({ ...prev, category, type: undefined }));
    setSelectedTypeId(null);
    setDynamicFormData({});
  };

  const handleTypeSelect = (type: string, typeId: number) => {
    setScenario(prev => ({ ...prev, type }));
    setSelectedTypeId(typeId);
    setDynamicFormData({});
  };

  const handleInputChange = (field: keyof WritingScenario, value: string) => {
    setScenario(prev => ({ ...prev, [field]: value }));
  };

  const handleDynamicFieldChange = (fieldKey: string, value: string) => {
    setDynamicFormData(prev => ({ ...prev, [fieldKey]: value }));
  };



  // 处理AI生成（动态字段）
  const handleAIGenerate = async (fieldConfig: WritingFieldConfig) => {
    if (!selectedTypeId) {
      message.error('请先选择模板类型');
      return;
    }

    const fieldKey = fieldConfig.field_key;
    setGeneratingFields(prev => new Set(prev).add(fieldKey));

    try {
      // 构建生成上下文
      const context = aiGenerationService.buildContext({
        category: scenario.category,
        type: scenario.type,
        title: dynamicFormData.title || scenario.title,
        keywords: dynamicFormData.keywords || scenario.keywords,
        content: dynamicFormData.content || scenario.content,
        reason: dynamicFormData.reason || scenario.reason,
        purpose: dynamicFormData.purpose || scenario.purpose,
        templateTypeId: selectedTypeId,
        extraData: dynamicFormData
      });

      // 使用配置的智能体生成（如果有配置）
      let result;
      if (fieldConfig.agent_config_id) {
        result = await aiGenerationService.generateWithConfiguredAgent(
          fieldKey,
          fieldConfig.field_name,
          fieldConfig.agent_config_id,
          context,
          dynamicFormData[fieldKey] || ''
        );
      } else {
        // 使用智能选择的智能体
        result = await aiGenerationService.generateField({
          field_key: fieldKey,
          field_name: fieldConfig.field_name,
          field_type: FieldType.SMART,
          context,
          user_input: dynamicFormData[fieldKey] || ''
        });
      }

      if (result.success && result.content) {
        // 更新字段值
        setDynamicFormData(prev => ({
          ...prev,
          [fieldKey]: result.content
        }));

        // 检查生成质量
        const qualityCheck = aiGenerationService.checkGenerationQuality(result);
        if (qualityCheck.isGoodQuality) {
          message.success(`${fieldConfig.field_name} 生成成功`);
        } else {
          message.warning(`${fieldConfig.field_name} 生成完成，但质量可能需要改进`);
        }
      } else {
        message.error(result.error || `${fieldConfig.field_name} 生成失败`);
      }

    } catch (error) {
      console.error('AI生成失败:', error);
      const errorMessage = aiGenerationService.handleGenerationError(error);
      message.error(`${fieldConfig.field_name} 生成失败：${errorMessage}`);
    } finally {
      setGeneratingFields(prev => {
        const newSet = new Set(prev);
        newSet.delete(fieldKey);
        return newSet;
      });
    }
  };

  // 处理默认字段的AI生成
  const handleDefaultFieldAIGenerate = async (fieldName: string, fieldKey: keyof WritingScenario) => {
    if (!scenario.category || !scenario.type) {
      message.error('请先选择写作场景');
      return;
    }

    setGeneratingFields(prev => new Set(prev).add(fieldKey));

    try {
      // 构建生成上下文
      const context = aiGenerationService.buildContext({
        category: scenario.category,
        type: scenario.type,
        title: scenario.title,
        keywords: scenario.keywords,
        content: scenario.content,
        reason: scenario.reason,
        purpose: scenario.purpose,
        extraData: { target_field: fieldKey, field_name: fieldName }
      });

      // 使用便捷方法生成内容
      let result;
      switch (fieldKey) {
        case 'title':
          result = await aiGenerationService.generateTitle(context, scenario.title);
          break;
        case 'keywords':
          result = await aiGenerationService.generateKeywords(context, scenario.keywords);
          break;
        case 'content':
          result = await aiGenerationService.generateContent(context, scenario.content);
          break;
        default:
          // 使用通用字段生成
          result = await aiGenerationService.generateField({
            field_key: fieldKey,
            field_name: fieldName,
            field_type: FieldType.SMART,
            context,
            user_input: scenario[fieldKey] || ''
          });
      }

      if (result.success && result.content) {
        // 更新对应字段的值
        setScenario(prev => ({
          ...prev,
          [fieldKey]: result.content
        }));

        // 检查生成质量
        const qualityCheck = aiGenerationService.checkGenerationQuality(result);
        if (qualityCheck.isGoodQuality) {
          message.success(`${fieldName} 生成成功`);
        } else {
          message.warning(`${fieldName} 生成完成，建议检查质量`);
        }
      } else {
        message.error(result.error || `${fieldName} 生成失败`);
      }

    } catch (error) {
      console.error('AI生成失败:', error);
      const errorMessage = aiGenerationService.handleGenerationError(error);
      message.error(`${fieldName} 生成失败：${errorMessage}`);
    } finally {
      setGeneratingFields(prev => {
        const newSet = new Set(prev);
        newSet.delete(fieldKey);
        return newSet;
      });
    }
  };

  // 批量生成所有字段
  const handleBatchGenerate = async () => {
    if (!scenario.category || !scenario.type) {
      message.error('请完成写作场景选择');
      return;
    }

    setIsGenerating(true);

    try {
      // 构建生成上下文
      const context = aiGenerationService.buildContext({
        category: scenario.category,
        type: scenario.type,
        templateTypeId: selectedTypeId,
        extraData: dynamicFormData
      });

      // 如果有动态字段配置，批量生成动态字段
      if (writingScenarioConfig && writingScenarioConfig.field_configs) {
        const fields = writingScenarioConfig.field_configs
          .filter(field => field.ai_enabled)
          .map(field => ({
            field_key: field.field_key,
            field_name: field.field_name,
            field_type: field.agent_config_id ? FieldType.CONFIGURED : FieldType.SMART,
            agent_id: field.agent_config_id,
            context,
            user_input: dynamicFormData[field.field_key] || ''
          }));

        if (fields.length > 0) {
          const batchResult = await aiGenerationService.generateBatch({
            fields,
            global_context: context,
            parallel: false, // 按顺序生成，利用前面的结果
            stop_on_error: false
          });

          // 更新字段值
          batchResult.results.forEach(result => {
            if (result.success && result.content) {
              setDynamicFormData(prev => ({
                ...prev,
                [result.field_key]: result.content
              }));
            }
          });

          message.success(`批量生成完成：${batchResult.success_count}/${batchResult.total_count} 个字段生成成功`);
        }
      } else {
        // 生成默认字段
        const batchResult = await aiGenerationService.generateAllBasicFields(context);

        // 更新字段值
        batchResult.results.forEach(result => {
          if (result.success && result.content) {
            setScenario(prev => ({
              ...prev,
              [result.field_key]: result.content
            }));
          }
        });

        message.success(`批量生成完成：${batchResult.success_count}/${batchResult.total_count} 个字段生成成功`);
      }

    } catch (error) {
      console.error('批量生成失败:', error);
      const errorMessage = aiGenerationService.handleGenerationError(error);
      message.error(`批量生成失败：${errorMessage}`);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleGenerate = async () => {
    if (!scenario.category || !scenario.type) {
      message.error('请完成写作场景选择');
      return;
    }

    setIsGenerating(true);
    setGeneratedContent('');

    try {
      // 使用写作向导API
      const session = await aiService.createWritingWizardSession({
        scenario,
        ai_type: 'ai_writer',
        prompt: buildPrompt(scenario),
        context: scenario.contentReference || scenario.dataReference,
        metadata: {
          writing_wizard: true,
          scenario,
          writing_type: scenario.type,
          category: scenario.category
        }
      });

      // 监听流式响应
      const eventSource = new EventSource(`/api/ai/stream/${session.session_id}`);

      eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.content) {
          setGeneratedContent(prev => prev + data.content);
        }

        if (data.is_complete) {
          eventSource.close();
          setIsGenerating(false);
          message.success('内容生成完成');
        }

        if (data.error) {
          eventSource.close();
          setIsGenerating(false);
          message.error('生成失败：' + data.error);
        }
      };

      eventSource.onerror = () => {
        eventSource.close();
        setIsGenerating(false);
        message.error('连接失败，请重试');
      };

    } catch (error) {
      setIsGenerating(false);
      message.error('生成失败，请重试');
    }
  };

  const buildPrompt = (scenario: WritingScenario): string => {
    let prompt = `请帮我写一份${scenario.category}类型的${scenario.type}文档。\n\n`;

    // 如果有写作场景配置，使用动态字段数据
    if (writingScenarioConfig && writingScenarioConfig.field_configs) {
      writingScenarioConfig.field_configs.forEach(fieldConfig => {
        const value = dynamicFormData[fieldConfig.field_key];
        if (value) {
          prompt += `${fieldConfig.field_name}：${value}\n`;
        }
      });
    } else {
      // 使用默认字段
      if (scenario.title) {
        prompt += `标题：${scenario.title}\n`;
      }

      if (scenario.keywords) {
        prompt += `关键词：${scenario.keywords}\n`;
      }

      if (scenario.reason) {
        prompt += `表彰原因：${scenario.reason}\n`;
      }

      if (scenario.content) {
        prompt += `表彰内容：${scenario.content}\n`;
      }

      if (scenario.purpose) {
        prompt += `表彰目的：${scenario.purpose}\n`;
      }
    }

    prompt += '\n请根据以上信息，生成一份专业、规范的文档。';

    return prompt;
  };

  const handleUseContent = () => {
    // 跳转到编辑器并使用生成的内容
    navigate('/editor', { 
      state: { 
        initialContent: generatedContent,
        initialTitle: scenario.title || `${scenario.category}-${scenario.type}`
      } 
    });
  };

  // 渲染动态字段
  const renderDynamicField = (fieldConfig: WritingFieldConfig) => {
    const { field_name, field_key, field_type, required, ai_enabled, doc_enabled, placeholder } = fieldConfig;
    const value = dynamicFormData[field_key] || '';



    // AI生成按钮
    const isGenerating = generatingFields.has(field_key);
    const aiButton = ai_enabled ? (
      <Button
        size="small"
        loading={isGenerating}
        style={{
          color: '#ff4d4f',
          border: '1px solid #ff4d4f',
          borderRadius: 4,
          padding: '2px 8px',
          height: 'auto',
          fontSize: 12
        }}
        onClick={() => handleAIGenerate(fieldConfig)}
        disabled={isGenerating}
      >
        {isGenerating ? '生成中...' : 'AI生成'}
      </Button>
    ) : null;

    // 选择文档按钮
    const docButton = doc_enabled ? (
      <Button
        size="small"
        style={{
          color: '#1890ff',
          border: '1px solid #1890ff',
          borderRadius: 4,
          padding: '2px 8px',
          height: 'auto',
          fontSize: 12,
          marginLeft: 8
        }}
        onClick={() => {
          // TODO: 实现文档选择逻辑
          console.log(`选择文档 ${field_name}`);
        }}
      >
        选择文档
      </Button>
    ) : null;

    // 对于单行输入框，按钮放在右侧
    const inputSuffix = (ai_enabled || doc_enabled) && field_type === 'text' ? (
      <Space size={4}>
        {aiButton}
        {docButton}
      </Space>
    ) : null;

    return (
      <div key={field_key} style={{ marginBottom: 24 }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 8
        }}>
          <Text strong>
            {field_name}
            {required && <span style={{ color: '#ff4d4f', marginLeft: 4 }}>*</span>}
          </Text>
          {/* 对于多行文本框，按钮放在标题右侧 */}
          {(ai_enabled || doc_enabled) && field_type === 'textarea' && (
            <Space size={4}>
              {aiButton}
              {docButton}
            </Space>
          )}
        </div>

        {field_type === 'textarea' ? (
          <>
            <TextArea
              placeholder={placeholder || `请输入${field_name}`}
              rows={4}
              value={value}
              onChange={(e) => handleDynamicFieldChange(field_key, e.target.value)}
              style={{ resize: 'vertical' }}
            />
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginTop: 4
            }}>
              <div></div>
              <Text type="secondary" style={{ fontSize: 12 }}>
                {value.length}/2000
              </Text>
            </div>
          </>
        ) : field_type === 'select' ? (
          <Select
            placeholder={placeholder || `请选择${field_name}`}
            style={{ width: '100%' }}
            value={value || undefined}
            onChange={(val) => handleDynamicFieldChange(field_key, val)}
          >
            {fieldConfig.options?.map(option => (
              <Option key={option} value={option}>{option}</Option>
            ))}
          </Select>
        ) : (
          <Input
            placeholder={placeholder || `请输入${field_name}`}
            value={value}
            onChange={(e) => handleDynamicFieldChange(field_key, e.target.value)}
            suffix={inputSuffix}
          />
        )}
      </div>
    );
  };

  // 渲染第一步：写作场景
  const renderStep1 = () => {
    if (templatesLoading) {
      return (
        <div style={{ padding: '24px 0', textAlign: 'center' }}>
          <Spin size="large" />
          <div style={{ marginTop: 16 }}>
            <Text>正在加载模板数据...</Text>
          </div>
        </div>
      );
    }

    const categories = templateData || [];
    const selectedCategory = categories.find(cat => cat.name === scenario.category);

    return (
      <div style={{ padding: '24px 0' }}>
        <div style={{ marginBottom: 24 }}>
          <Text strong style={{ fontSize: 16 }}>模板分类</Text>
        </div>

        <Space wrap size="middle" style={{ marginBottom: 32 }}>
          {categories.map(category => (
            <Button
              key={category.id}
              type={scenario.category === category.name ? 'primary' : 'default'}
              size="large"
              onClick={() => handleCategorySelect(category.name)}
              style={{ minWidth: 80 }}
            >
              {category.name}
            </Button>
          ))}
        </Space>

        {scenario.category && selectedCategory && (
          <>
            <div style={{ marginBottom: 24 }}>
              <Text strong style={{ fontSize: 16 }}>模板类型</Text>
            </div>

            <Space wrap size="middle">
              {selectedCategory.template_types.map(templateType => (
                <Button
                  key={templateType.id}
                  type={scenario.type === templateType.name ? 'primary' : 'default'}
                  onClick={() => handleTypeSelect(templateType.name, templateType.id)}
                  style={{ minWidth: 80 }}
                >
                  {templateType.name}
                </Button>
              ))}
            </Space>
          </>
        )}

        <div style={{ marginTop: 40, display: 'flex', alignItems: 'center' }}>
          <Switch
            checked={checkSimilarity}
            onChange={setCheckSimilarity}
            style={{ marginRight: 8 }}
          />
          <Text>检索学习同地</Text>
        </div>
      </div>
    );
  };

  // 渲染第二步：基础信息
  const renderStep2 = () => {
    if (scenarioConfigLoading) {
      return (
        <div style={{ padding: '24px 0', textAlign: 'center' }}>
          <Spin size="large" />
          <div style={{ marginTop: 16 }}>
            <Text>正在加载写作场景配置...</Text>
          </div>
        </div>
      );
    }

    // 如果有写作场景配置，使用动态字段
    if (writingScenarioConfig && writingScenarioConfig.field_configs) {
      return (
        <div style={{ padding: '24px 0' }}>
          <div style={{ marginBottom: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <Text strong style={{ fontSize: 16 }}>{writingScenarioConfig.config_name}</Text>
                {writingScenarioConfig.description && (
                  <div style={{ marginTop: 4 }}>
                    <Text type="secondary">{writingScenarioConfig.description}</Text>
                  </div>
                )}
              </div>
              <Button
                type="primary"
                size="small"
                loading={isGenerating}
                onClick={handleBatchGenerate}
                disabled={isGenerating}
                style={{ backgroundColor: '#52c41a', borderColor: '#52c41a' }}
              >
                {isGenerating ? '批量生成中...' : '批量生成所有字段'}
              </Button>
            </div>
          </div>

          <Space direction="vertical" style={{ width: '100%' }} size="large">
            {writingScenarioConfig.field_configs.map(fieldConfig =>
              renderDynamicField(fieldConfig)
            )}
          </Space>
        </div>
      );
    }

    // 如果没有写作场景配置，使用默认字段
    return (
      <div style={{ padding: '24px 0' }}>
        <div style={{ marginBottom: 16 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Text type="secondary">该模板类型暂无写作场景配置，使用默认字段</Text>
            <Button
              type="primary"
              size="small"
              loading={isGenerating}
              onClick={handleBatchGenerate}
              disabled={isGenerating}
              style={{ backgroundColor: '#52c41a', borderColor: '#52c41a' }}
            >
              {isGenerating ? '批量生成中...' : '批量生成所有字段'}
            </Button>
          </div>
        </div>

        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <div>
            <Text strong style={{ marginBottom: 8, display: 'block' }}>标题</Text>
            <Input
              placeholder="请输入文章标题"
              value={scenario.title || ''}
              onChange={(e) => handleInputChange('title', e.target.value)}
              suffix={
                <Button
                  type="link"
                  size="small"
                  style={{ color: '#ff4d4f' }}
                  loading={generatingFields.has('title')}
                  onClick={() => handleDefaultFieldAIGenerate('标题', 'title')}
                  disabled={generatingFields.has('title')}
                >
                  {generatingFields.has('title') ? '生成中...' : 'AI生成'}
                </Button>
              }
            />
          </div>

          <div>
            <Text strong style={{ marginBottom: 8, display: 'block' }}>关键词</Text>
            <Input
              placeholder="请输入关键词"
              value={scenario.keywords || ''}
              onChange={(e) => handleInputChange('keywords', e.target.value)}
              suffix={
                <Button
                  type="link"
                  size="small"
                  style={{ color: '#ff4d4f' }}
                  loading={generatingFields.has('keywords')}
                  onClick={() => handleDefaultFieldAIGenerate('关键词', 'keywords')}
                  disabled={generatingFields.has('keywords')}
                >
                  {generatingFields.has('keywords') ? '生成中...' : 'AI生成'}
                </Button>
              }
            />
          </div>

          <div>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: 8
            }}>
              <Text strong>主要内容</Text>
              <Button
                size="small"
                loading={generatingFields.has('content')}
                style={{
                  color: '#ff4d4f',
                  border: '1px solid #ff4d4f',
                  borderRadius: 4,
                  padding: '2px 8px',
                  height: 'auto',
                  fontSize: 12
                }}
                onClick={() => handleDefaultFieldAIGenerate('主要内容', 'content')}
                disabled={generatingFields.has('content')}
              >
                {generatingFields.has('content') ? '生成中...' : 'AI生成'}
              </Button>
            </div>
            <TextArea
              placeholder="请输入主要内容"
              rows={4}
              value={scenario.content || ''}
              onChange={(e) => handleInputChange('content', e.target.value)}
            />
            <div style={{ textAlign: 'right', marginTop: 4 }}>
              <Text type="secondary" style={{ fontSize: 12 }}>
                {(scenario.content || '').length}/2000
              </Text>
            </div>
          </div>
        </Space>
      </div>
    );
  };

  // 渲染第三步：参考文档
  const renderStep3 = () => (
    <div style={{ padding: '24px 0' }}>
      <div style={{ marginBottom: 24, textAlign: 'center' }}>
        <Text type="secondary">
          补充参考文档并关联大纲信息有助于提升文章质量，您也可以跳过此步，直接点击"开始生成"按钮
        </Text>
      </div>

      <Space direction="vertical" style={{ width: '100%' }} size="large">
        <div>
          <Text strong style={{ marginBottom: 8, display: 'block' }}>内容参考</Text>
          <Select
            placeholder="选择文档"
            style={{ width: '100%' }}
            suffixIcon={<FileTextOutlined />}
          >
            <Option value="doc1">参考文档1</Option>
            <Option value="doc2">参考文档2</Option>
          </Select>
        </div>

        <div>
          <Text strong style={{ marginBottom: 8, display: 'block' }}>数据参考</Text>
          <Select
            placeholder="选择文档"
            style={{ width: '100%' }}
            suffixIcon={<FileTextOutlined />}
          >
            <Option value="data1">数据文档1</Option>
            <Option value="data2">数据文档2</Option>
          </Select>
        </div>

        <div>
          <Text strong style={{ marginBottom: 8, display: 'block' }}>模板格式</Text>
          <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 8 }}>
            请选择
          </Text>
          <Select
            placeholder="选择文档"
            style={{ width: '100%' }}
            suffixIcon={<FileTextOutlined />}
          >
            <Option value="template1">模板1</Option>
            <Option value="template2">模板2</Option>
          </Select>
        </div>
      </Space>
    </div>
  );

  return (
    <Layout style={{ height: '100%', background: '#f0f2f5' }}>
      {/* 页面头部操作栏 */}
      <div style={{
        background: '#fff',
        padding: '16px 24px',
        borderBottom: '1px solid #f0f0f0',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <Button
            type="text"
            icon={<ArrowLeftOutlined />}
            onClick={() => navigate('/standard-editor')}
            style={{ marginRight: 16 }}
          >
            返回编辑器
          </Button>
          <Title level={4} style={{ margin: 0 }}>AI写作向导</Title>
        </div>
        <Button
          type="text"
          icon={<CloseOutlined />}
          onClick={handleClose}
        >
          关闭
        </Button>
      </div>

      <Content style={{ padding: '40px 0', flex: 1, overflow: 'auto' }}>
        <div style={{ 
          maxWidth: 800, 
          margin: '0 auto',
          background: '#fff',
          borderRadius: 8,
          padding: '40px 60px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
        }}>
          <Steps current={currentStep} style={{ marginBottom: 40 }}>
            <Step title="写作场景" />
            <Step title="基础信息" />
            <Step title="参考文档" />
          </Steps>

          {currentStep === 0 && renderStep1()}
          {currentStep === 1 && renderStep2()}
          {currentStep === 2 && renderStep3()}

          <div style={{ 
            marginTop: 40, 
            display: 'flex', 
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <Button 
              onClick={handlePrev}
              disabled={currentStep === 0}
              icon={<ArrowLeftOutlined />}
            >
              上一步
            </Button>

            <Button 
              type="primary"
              onClick={handleNext}
              disabled={currentStep === 0 && (!scenario.category || !scenario.type)}
              icon={currentStep === 2 ? <RobotOutlined /> : <ArrowRightOutlined />}
            >
              {currentStep === 2 ? '开始生成' : '下一步'}
            </Button>
          </div>
        </div>
      </Content>

      {/* 生成结果弹窗 */}
      <Modal
        title="AI生成结果"
        open={isGenerating || generatedContent}
        onCancel={() => {
          setIsGenerating(false);
          setGeneratedContent('');
        }}
        width={800}
        footer={generatedContent ? [
          <Button key="regenerate" onClick={handleGenerate}>
            重新生成
          </Button>,
          <Button key="use" type="primary" onClick={handleUseContent}>
            使用此内容
          </Button>
        ] : null}
      >
        {isGenerating && !generatedContent ? (
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <Spin size="large" />
            <div style={{ marginTop: 16 }}>
              <Text>AI正在生成内容，请稍候...</Text>
            </div>
          </div>
        ) : (
          <div style={{ 
            maxHeight: 400, 
            overflow: 'auto',
            padding: 16,
            background: '#f9f9f9',
            borderRadius: 4
          }}>
            <pre style={{ 
              whiteSpace: 'pre-wrap', 
              fontFamily: 'inherit',
              margin: 0
            }}>
              {generatedContent}
            </pre>
          </div>
        )}
      </Modal>
    </Layout>
  );
};

export default AIWritingWizard;
