import React, { useState } from 'react';
import { Layout, Typography, Button, Space, Divider } from 'antd';
import {
  ArrowLeftOutlined,
  ArrowRightOutlined,
  SaveOutlined,
  ShareAltOutlined,
  UserOutlined,
  RobotOutlined,
  FileTextOutlined,
  HighlightOutlined,
  SearchOutlined,
  CheckCircleOutlined,
  BookOutlined,
  MenuOutlined,
  FormOutlined,
  ReadOutlined,
  ExperimentOutlined,
  FileProtectOutlined,
  FolderOpenOutlined,
  EyeOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';

const { Header, Content } = Layout;
const { Text } = Typography;

// 工具栏按钮配置
const TOOLBAR_BUTTONS = [
  { icon: <ArrowLeftOutlined />, tooltip: '撤销' },
  { icon: <ArrowRightOutlined />, tooltip: '重做' },
  { icon: <SaveOutlined />, tooltip: '保存' },
  { type: 'divider' },
  { text: '宋体', tooltip: '字体' },
  { type: 'divider' },
  { text: 'B', tooltip: '加粗', style: { fontWeight: 'bold' } },
  { text: 'I', tooltip: '斜体', style: { fontStyle: 'italic' } },
  { text: 'U', tooltip: '下划线', style: { textDecoration: 'underline' } },
  { text: 'S', tooltip: '删除线', style: { textDecoration: 'line-through' } },
  { text: 'A', tooltip: '字体颜色' },
  { type: 'divider' },
  { text: '|||', tooltip: '段落格式' },
  { text: '≡', tooltip: '对齐方式' },
  { type: 'divider' },
  { icon: <ShareAltOutlined />, tooltip: '分享' }
];

// 第一组AI工具 - 文档功能
const DOCUMENT_TOOLS = [
  { key: 'catalog', name: '目录', icon: <MenuOutlined /> },
  { key: 'format', name: '公文格式', icon: <FormOutlined /> },
  { key: 'content', name: '内容中间', icon: <ReadOutlined /> },
  { key: 'training', name: '学习训练', icon: <ExperimentOutlined /> },
  { key: 'legal', name: '公文法文', icon: <FileProtectOutlined /> },
  { key: 'reference', name: '参考资料', icon: <FolderOpenOutlined /> },
  { key: 'viewpoint', name: '观点', icon: <EyeOutlined /> }
];

// 第二组AI工具 - AI功能
const AI_TOOLS = [
  { key: 'ai_writer', name: 'AI写作', icon: <RobotOutlined />, route: '/ai-writing' },
  { key: 'ai_effect', name: 'AI对效', icon: <FileTextOutlined /> },
  { key: 'ai_polish', name: 'AI润色', icon: <HighlightOutlined /> },
  { key: 'deepseek', name: 'deepseek', icon: <SearchOutlined /> },
  { key: 'ai_compare', name: 'AI对比', icon: <CheckCircleOutlined /> },
  { key: 'typesetting', name: '排版', icon: <BookOutlined /> }
];

const AIToolsPage: React.FC = () => {
  const navigate = useNavigate();
  const [showDocumentTools, setShowDocumentTools] = useState(false);
  const [showAITools, setShowAITools] = useState(false);

  const handleBack = () => {
    navigate('/');
  };

  const handleToolSelect = (tool: any) => {
    if (tool.key === 'ai_writer') {
      navigate('/ai-writing');
    } else {
      navigate('/editor', {
        state: {
          aiTool: tool.key,
          toolName: tool.name
        }
      });
    }
  };

  const toggleDocumentTools = () => {
    setShowDocumentTools(!showDocumentTools);
    setShowAITools(false);
  };

  const toggleAITools = () => {
    setShowAITools(!showAITools);
    setShowDocumentTools(false);
  };

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
          <Button 
            type="text" 
            icon={<ArrowLeftOutlined />} 
            onClick={handleBack}
            style={{ marginRight: 16 }}
          />
          <Space>
            <Text type="secondary">开始</Text>
            <Text type="secondary">/</Text>
            <Text type="secondary">加入</Text>
            <Text type="secondary">/</Text>
            <Text strong style={{ color: '#1890ff' }}>AI 妙笔AI</Text>
          </Space>
        </div>
        <Button 
          type="text" 
          icon={<CloseOutlined />} 
          onClick={handleClose}
        />
      </Header>

      <Content style={{ padding: '40px 24px' }}>
        <div style={{
          maxWidth: 1200,
          margin: '0 auto',
          textAlign: 'center',
          marginBottom: 80,
          marginTop: 80
        }}>
          <Text type="secondary" style={{ fontSize: 16, color: '#999' }}>
            请在此输入内容
          </Text>
        </div>

        <div style={{
          display: 'flex',
          justifyContent: 'center',
          flexWrap: 'wrap',
          gap: '32px',
          maxWidth: '800px',
          margin: '0 auto'
        }}>
          {AI_TOOLS.map((tool) => (
            <Button
              key={tool.key}
              type="default"
              size="large"
              icon={tool.icon}
              onClick={() => handleToolSelect(tool)}
              style={{
                height: '48px',
                padding: '0 24px',
                borderRadius: '6px',
                border: '1px solid #d9d9d9',
                background: '#fff',
                color: '#262626',
                fontSize: '14px',
                fontWeight: 'normal',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                transition: 'all 0.3s ease'
              }}
              className="ai-tool-button"
            >
              {tool.name}
            </Button>
          ))}
        </div>


      </Content>
    </Layout>
  );
};

export default AIToolsPage;
