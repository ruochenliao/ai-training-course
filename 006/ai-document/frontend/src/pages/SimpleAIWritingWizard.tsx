import React, { useState } from 'react';
import { 
  Layout, 
  Steps, 
  Card, 
  Button, 
  Space, 
  Typography, 
  Input, 
  Select, 
  Switch,
  message,
  Modal
} from 'antd';
import { 
  ArrowLeftOutlined, 
  ArrowRightOutlined, 
  CloseOutlined,
  RobotOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';

const { Header, Content } = Layout;
const { Title, Text } = Typography;
const { TextArea } = Input;
const { Option } = Select;
const { Step } = Steps;

// 简化的模板数据
const SIMPLE_TEMPLATES = {
  '通报': ['表彰', '批评', '其它通报'],
  '会务': ['会议纪要', '政协提案'],
  '报告和上报信息': ['工作汇报', '调研报告'],
  '讲话': ['就职演讲', '开幕致辞'],
  '计划': ['工作方案', '年度计划'],
  '总结': ['年度总结', '工作总结'],
  '许可': ['批复', '审批'],
  '书信': ['感谢信', '邀请函']
};

interface WritingScenario {
  step: number;
  category?: string;
  type?: string;
  title?: string;
  keywords?: string;
  reason?: string;
  content?: string;
  purpose?: string;
}

const SimpleAIWritingWizard: React.FC = () => {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(0);
  const [scenario, setScenario] = useState<WritingScenario>({ step: 1 });
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedContent, setGeneratedContent] = useState('');
  const [checkSimilarity, setCheckSimilarity] = useState(false);

  const handleClose = () => {
    navigate('/standard-editor');
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
  };

  const handleTypeSelect = (type: string) => {
    setScenario(prev => ({ ...prev, type }));
  };

  const handleInputChange = (field: keyof WritingScenario, value: string) => {
    setScenario(prev => ({ ...prev, [field]: value }));
  };

  const handleGenerate = async () => {
    if (!scenario.category || !scenario.type) {
      message.error('请完成写作场景选择');
      return;
    }

    setIsGenerating(true);
    setGeneratedContent('');

    // 模拟AI生成过程
    const mockContent = `# ${scenario.title || `${scenario.category}-${scenario.type}`}

## 基本信息
- 文档类型：${scenario.category} - ${scenario.type}
- 关键词：${scenario.keywords || '暂无'}

## 主要内容

${scenario.reason ? `### 原因说明\n${scenario.reason}\n\n` : ''}
${scenario.content ? `### 具体内容\n${scenario.content}\n\n` : ''}
${scenario.purpose ? `### 目的意义\n${scenario.purpose}\n\n` : ''}

## 结语

这是一个由AI生成的${scenario.type}文档示例。在实际应用中，这里会调用真正的AI服务来生成更专业的内容。

---
*本文档由AI写作助手生成*`;

    // 模拟流式输出
    let index = 0;
    const interval = setInterval(() => {
      if (index < mockContent.length) {
        setGeneratedContent(prev => prev + mockContent[index]);
        index++;
      } else {
        clearInterval(interval);
        setIsGenerating(false);
        message.success('内容生成完成');
      }
    }, 50);
  };

  const handleUseContent = () => {
    // 跳转到编辑器并使用生成的内容
    navigate('/standard-editor', { 
      state: { 
        initialContent: generatedContent,
        initialTitle: scenario.title || `${scenario.category}-${scenario.type}`
      } 
    });
  };

  // 渲染第一步：写作场景
  const renderStep1 = () => (
    <div style={{ padding: '24px 0' }}>
      <div style={{ marginBottom: 24 }}>
        <Text strong style={{ fontSize: 16 }}>模板分类</Text>
      </div>
      
      <Space wrap size="middle" style={{ marginBottom: 32 }}>
        {Object.keys(SIMPLE_TEMPLATES).map(category => (
          <Button
            key={category}
            type={scenario.category === category ? 'primary' : 'default'}
            size="large"
            onClick={() => handleCategorySelect(category)}
            style={{ minWidth: 80 }}
          >
            {category}
          </Button>
        ))}
      </Space>

      {scenario.category && (
        <>
          <div style={{ marginBottom: 24 }}>
            <Text strong style={{ fontSize: 16 }}>模板类型</Text>
          </div>
          
          <Space wrap size="middle">
            {SIMPLE_TEMPLATES[scenario.category as keyof typeof SIMPLE_TEMPLATES].map(type => (
              <Button
                key={type}
                type={scenario.type === type ? 'primary' : 'default'}
                onClick={() => handleTypeSelect(type)}
                style={{ minWidth: 80 }}
              >
                {type}
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

  // 渲染第二步：基础信息
  const renderStep2 = () => (
    <div style={{ padding: '24px 0' }}>
      <Space direction="vertical" style={{ width: '100%' }} size="large">
        <div>
          <Text strong style={{ marginBottom: 8, display: 'block' }}>标题</Text>
          <Input
            placeholder="请输入文章标题"
            value={scenario.title || ''}
            onChange={(e) => handleInputChange('title', e.target.value)}
          />
        </div>

        <div>
          <Text strong style={{ marginBottom: 8, display: 'block' }}>关键词</Text>
          <Input
            placeholder="请输入关键词"
            value={scenario.keywords || ''}
            onChange={(e) => handleInputChange('keywords', e.target.value)}
          />
        </div>

        {(scenario.category === '通报' || scenario.category === '表彰') && (
          <>
            <div>
              <Text strong style={{ marginBottom: 8, display: 'block' }}>表彰原因</Text>
              <TextArea
                placeholder="请输入表彰原因"
                rows={4}
                value={scenario.reason || ''}
                onChange={(e) => handleInputChange('reason', e.target.value)}
              />
            </div>

            <div>
              <Text strong style={{ marginBottom: 8, display: 'block' }}>表彰内容</Text>
              <TextArea
                placeholder="请输入表彰内容，表彰等级或者号"
                rows={4}
                value={scenario.content || ''}
                onChange={(e) => handleInputChange('content', e.target.value)}
              />
            </div>

            <div>
              <Text strong style={{ marginBottom: 8, display: 'block' }}>表彰目的</Text>
              <TextArea
                placeholder="请输入表彰目的"
                rows={4}
                value={scenario.purpose || ''}
                onChange={(e) => handleInputChange('purpose', e.target.value)}
              />
            </div>
          </>
        )}
      </Space>
    </div>
  );

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
          >
            <Option value="data1">数据文档1</Option>
            <Option value="data2">数据文档2</Option>
          </Select>
        </div>

        <div>
          <Text strong style={{ marginBottom: 8, display: 'block' }}>模板格式</Text>
          <Select
            placeholder="选择文档"
            style={{ width: '100%' }}
          >
            <Option value="template1">模板1</Option>
            <Option value="template2">模板2</Option>
          </Select>
        </div>
      </Space>
    </div>
  );

  return (
    <Layout style={{ minHeight: '100vh', background: '#f0f2f5' }}>
      <Header style={{ 
        background: '#fff', 
        padding: '0 24px',
        borderBottom: '1px solid #f0f0f0',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <Title level={4} style={{ margin: 0 }}>AI写作向导</Title>
        </div>
        <Button 
          type="text" 
          icon={<CloseOutlined />} 
          onClick={handleClose}
        />
      </Header>

      <Content style={{ padding: '40px 0' }}>
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
            <Text>正在生成内容，请稍候...</Text>
          </div>
        ) : (
          <div style={{ 
            maxHeight: '400px', 
            overflow: 'auto',
            padding: '16px',
            background: '#f9f9f9',
            borderRadius: '4px',
            whiteSpace: 'pre-wrap'
          }}>
            {generatedContent}
          </div>
        )}
      </Modal>
    </Layout>
  );
};

export default SimpleAIWritingWizard;
