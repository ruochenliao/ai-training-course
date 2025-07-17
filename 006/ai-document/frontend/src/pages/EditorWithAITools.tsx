import React, { useState } from 'react';
import { Layout, Button, Divider, Space } from 'antd';
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
  EyeOutlined,
  BoldOutlined,
  ItalicOutlined,
  UnderlineOutlined,
  StrikethroughOutlined,
  FontColorsOutlined,
  AlignLeftOutlined,
  OrderedListOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';

const { Header, Content, Sider } = Layout;

// 工具栏按钮配置
const TOOLBAR_BUTTONS = [
  { icon: <ArrowLeftOutlined />, tooltip: '撤销' },
  { icon: <ArrowRightOutlined />, tooltip: '重做' },
  { icon: <SaveOutlined />, tooltip: '保存' },
  { type: 'divider' },
  { text: '宋体', tooltip: '字体', isDropdown: true },
  { type: 'divider' },
  { icon: <BoldOutlined />, tooltip: '加粗' },
  { icon: <ItalicOutlined />, tooltip: '斜体' },
  { icon: <UnderlineOutlined />, tooltip: '下划线' },
  { icon: <StrikethroughOutlined />, tooltip: '删除线' },
  { icon: <FontColorsOutlined />, tooltip: '字体颜色' },
  { type: 'divider' },
  { icon: <OrderedListOutlined />, tooltip: '段落格式' },
  { icon: <AlignLeftOutlined />, tooltip: '对齐方式' },
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

const EditorWithAITools: React.FC = () => {
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
      console.log('选择了工具:', tool.name);
      // 这里可以实现具体的工具功能
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
    <Layout style={{ minHeight: '100vh', background: '#f5f5f5' }}>
      {/* 顶部导航栏 */}
      <Header style={{ 
        background: '#fff', 
        padding: '0 16px',
        borderBottom: '1px solid #e8e8e8',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        height: '48px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <Button 
            type="text" 
            icon={<ArrowLeftOutlined />} 
            onClick={handleBack}
            size="small"
          />
          <Button 
            type="text" 
            icon={<SaveOutlined />} 
            size="small"
          />
          <Button 
            type="text" 
            icon={<ShareAltOutlined />} 
            size="small"
          />
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <Button type="text" size="small">开始</Button>
          <Button type="text" size="small">加入</Button>
          <Button type="primary" size="small">AI 妙笔AI</Button>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <Button 
            type="text" 
            icon={<UserOutlined />} 
            size="small"
            style={{ color: '#1890ff' }}
          />
        </div>
      </Header>

      {/* 工具栏 */}
      <div style={{
        background: '#fff',
        borderBottom: '1px solid #e8e8e8',
        padding: '8px 16px',
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        flexWrap: 'wrap'
      }}>
        {TOOLBAR_BUTTONS.map((btn, index) => {
          if (btn.type === 'divider') {
            return <Divider key={index} type="vertical" style={{ margin: '0 4px' }} />;
          }
          return (
            <Button
              key={index}
              type="text"
              size="small"
              icon={btn.icon}
              style={{
                minWidth: btn.text ? '48px' : '24px',
                height: '24px',
                padding: '0 4px',
                fontSize: '12px'
              }}
            >
              {btn.text}
            </Button>
          );
        })}
      </div>

      {/* AI工具栏 - 根据状态显示不同的工具组 */}
      {(showDocumentTools || showAITools) && (
        <div style={{
          background: '#fff',
          borderBottom: '1px solid #e8e8e8',
          padding: '8px 16px',
          display: 'flex',
          alignItems: 'center',
          gap: '16px',
          flexWrap: 'wrap'
        }}>
          {showDocumentTools && DOCUMENT_TOOLS.map((tool) => (
            <Button
              key={tool.key}
              type="text"
              size="small"
              icon={tool.icon}
              onClick={() => handleToolSelect(tool)}
              style={{
                height: '32px',
                padding: '0 12px',
                fontSize: '12px',
                border: '1px solid #d9d9d9',
                borderRadius: '4px'
              }}
            >
              {tool.name}
            </Button>
          ))}
          
          {showAITools && AI_TOOLS.map((tool) => (
            <Button
              key={tool.key}
              type="text"
              size="small"
              icon={tool.icon}
              onClick={() => handleToolSelect(tool)}
              style={{
                height: '32px',
                padding: '0 12px',
                fontSize: '12px',
                border: '1px solid #d9d9d9',
                borderRadius: '4px'
              }}
            >
              {tool.name}
            </Button>
          ))}
        </div>
      )}

      {/* 主要内容区域 */}
      <Layout style={{ background: '#f5f5f5' }}>
        {/* 左侧边栏 */}
        <Sider 
          width={300} 
          style={{
            background: '#e8e8e8',
            borderRight: '1px solid #d9d9d9'
          }}
        >
          {/* 左侧边栏内容可以放置文档大纲、目录等 */}
        </Sider>

        {/* 中间编辑区域 */}
        <Content style={{
          background: '#fff',
          margin: '20px',
          padding: '40px',
          borderRadius: '4px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          minHeight: 'calc(100vh - 160px)',
          position: 'relative'
        }}>
          <div style={{
            textAlign: 'center',
            color: '#999',
            fontSize: '14px',
            marginTop: '100px'
          }}>
            请在此输入内容
          </div>
          
          {/* 触发AI工具的按钮 */}
          <div style={{
            position: 'absolute',
            top: '20px',
            right: '20px',
            display: 'flex',
            gap: '8px'
          }}>
            <Button
              size="small"
              onClick={toggleDocumentTools}
              type={showDocumentTools ? 'primary' : 'default'}
            >
              文档工具
            </Button>
            <Button
              size="small"
              onClick={toggleAITools}
              type={showAITools ? 'primary' : 'default'}
            >
              AI工具
            </Button>
          </div>
        </Content>

        {/* 右侧边栏 */}
        <div style={{
          width: '60px',
          background: '#f5f5f5',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          padding: '20px 0'
        }}>
          <div style={{
            width: '40px',
            height: '40px',
            background: '#000',
            borderRadius: '50%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff',
            fontSize: '16px',
            fontWeight: 'bold',
            marginBottom: '20px'
          }}>
            K
          </div>
        </div>
      </Layout>

      {/* 底部状态栏 */}
      <div style={{
        background: '#fff',
        borderTop: '1px solid #e8e8e8',
        padding: '4px 16px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        height: '32px',
        fontSize: '12px',
        color: '#666'
      }}>
        <div>字数：0</div>
        <div>公开</div>
      </div>
    </Layout>
  );
};

export default EditorWithAITools;
