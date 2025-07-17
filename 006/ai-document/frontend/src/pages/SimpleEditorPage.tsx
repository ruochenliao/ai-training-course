import React from 'react';
import { Layout, Button, Space } from 'antd';
import { 
  RobotOutlined,
  FileTextOutlined,
  HighlightOutlined,
  SearchOutlined,
  CheckCircleOutlined,
  BookOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';

const { Content } = Layout;

// AI工具配置 - 与图片中的内容保持一致
const AI_TOOLS = [
  { key: 'ai_writer', name: 'AI写作', icon: <RobotOutlined />, route: '/ai-writing' },
  { key: 'ai_effect', name: 'AI对效', icon: <FileTextOutlined /> },
  { key: 'ai_polish', name: 'AI润色', icon: <HighlightOutlined /> },
  { key: 'deepseek', name: 'deepseek', icon: <SearchOutlined /> },
  { key: 'ai_compare', name: 'AI对比', icon: <CheckCircleOutlined /> },
  { key: 'typesetting', name: '排版', icon: <BookOutlined /> }
];

const SimpleEditorPage: React.FC = () => {
  const navigate = useNavigate();

  const handleToolSelect = (tool: typeof AI_TOOLS[0]) => {
    if (tool.key === 'ai_writer') {
      navigate('/ai-writing');
    } else {
      console.log('选择了工具:', tool.name);
      // 这里可以实现具体的工具功能
    }
  };

  return (
    <Layout style={{ 
      minHeight: '100vh', 
      background: '#f5f5f5'
    }}>
      {/* AI工具栏 */}
      <div style={{
        background: '#fff',
        borderBottom: '1px solid #e8e8e8',
        padding: '12px 0',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center'
      }}>
        <Space size="large">
          {AI_TOOLS.map((tool) => (
            <Button
              key={tool.key}
              type="text"
              icon={tool.icon}
              onClick={() => handleToolSelect(tool)}
              style={{
                height: '40px',
                padding: '0 16px',
                fontSize: '14px',
                color: '#666',
                border: 'none',
                background: 'transparent',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                borderRadius: '4px',
                transition: 'all 0.3s ease'
              }}
              className="ai-tool-simple-btn"
            >
              {tool.name}
            </Button>
          ))}
        </Space>
      </div>

      {/* 主要内容区域 */}
      <Content style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        flex: 1,
        background: '#f5f5f5'
      }}>
        <div style={{
          textAlign: 'center',
          color: '#999',
          fontSize: '16px',
          fontWeight: 'normal'
        }}>
          请在此输入内容
        </div>
      </Content>
    </Layout>
  );
};

export default SimpleEditorPage;
