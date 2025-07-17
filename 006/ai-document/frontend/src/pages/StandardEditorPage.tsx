import React, { useState, useEffect, useRef } from 'react';
import { Layout, Button, Input, Space, message, Card } from 'antd';
import {
  FullscreenOutlined,
  RobotOutlined,
  SaveOutlined,
  FileOutlined,
  PrinterOutlined,
  FullscreenExitOutlined
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import QuillEditor, { QuillEditorRef } from '@/components/QuillEditor';
import QuillEditorWrapper from '@/components/QuillEditorWrapper';

const { Content } = Layout;

const StandardEditorPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [content, setContent] = useState('');
  const [title, setTitle] = useState('');
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [wordCount, setWordCount] = useState(0);
  const editorRef = useRef<QuillEditorRef>(null);

  // 处理编辑器内容变化
  const handleEditorChange = (content: string, delta: any, source: any, editor: any) => {
    setContent(content);
    const text = editor.getText();
    setWordCount(text.length);
  };

  // 保存文档
  const handleSave = () => {
    const documentData = {
      title,
      content,
      wordCount,
      lastModified: new Date().toISOString()
    };
    console.log('保存文档:', documentData);
    message.success('文档已保存');
  };

  // 新建文档
  const handleNew = () => {
    setTitle('');
    setContent('');
    setWordCount(0);
    if (editorRef.current) {
      editorRef.current.setContent('');
    }
    message.success('新建文档');
  };

  // 打印文档
  const handlePrint = () => {
    window.print();
  };

  // 全屏切换
  const handleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  // AI写作
  const handleAIWriting = () => {
    navigate('/ai-writing');
  };

  // 处理从AI写作向导传递的初始内容
  useEffect(() => {
    const state = location.state as {
      initialContent?: string;
      initialTitle?: string;
    };

    if (state?.initialContent) {
      setContent(state.initialContent);
      if (editorRef.current) {
        editorRef.current.setContent(state.initialContent);
      }
    }

    if (state?.initialTitle) {
      setTitle(state.initialTitle);
    }

    // 清除location state以避免重复设置
    if (state && Object.keys(state).length > 0) {
      navigate(location.pathname, { replace: true, state: {} });
    }
  }, [location.state, navigate, location.pathname]);

  return (
    <div className={isFullscreen ? 'quill-editor-fullscreen' : ''}>
      <Layout style={{
        minHeight: isFullscreen ? '100vh' : '100%',
        background: '#f8f9fa'
      }}>
        {/* 简化的工具栏 */}
        <div style={{
          background: 'linear-gradient(to bottom, #fafafa, #f0f0f0)',
          borderBottom: '1px solid #d9d9d9',
          padding: '12px 16px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
        }}>
          {/* 左侧工具 */}
          <Space>
            <Button type="text" size="small" icon={<SaveOutlined />} onClick={handleSave} title="保存">
              保存
            </Button>
            <Button type="text" size="small" icon={<FileOutlined />} onClick={handleNew} title="新建">
              新建
            </Button>
            <Button type="text" size="small" icon={<PrinterOutlined />} onClick={handlePrint} title="打印">
              打印
            </Button>
          </Space>

          {/* 右侧工具 */}
          <Space>
            <Button
              type="text"
              size="small"
              icon={isFullscreen ? <FullscreenExitOutlined /> : <FullscreenOutlined />}
              onClick={handleFullscreen}
              title={isFullscreen ? "退出全屏" : "全屏"}
            >
              {isFullscreen ? "退出全屏" : "全屏"}
            </Button>
            <Button
              type="primary"
              size="small"
              icon={<RobotOutlined />}
              onClick={handleAIWriting}
            >
              AI写作
            </Button>
          </Space>
        </div>



        {/* 编辑区域 */}
        <Content style={{
          padding: isFullscreen ? '0' : '24px',
          background: '#f8f9fa',
          flex: 1,
          display: 'flex',
          flexDirection: 'column'
        }}>
          {/* 文档容器 */}
          <div style={{
            maxWidth: isFullscreen ? '100%' : '210mm',
            margin: '0 auto',
            background: '#fff',
            boxShadow: isFullscreen ? 'none' : '0 8px 24px rgba(0,0,0,0.12)',
            borderRadius: isFullscreen ? '0' : '8px',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
            height: isFullscreen ? 'calc(100vh - 60px)' : 'calc(100vh - 200px)',
            minHeight: '600px',
            transition: 'box-shadow 0.3s ease'
          }}>
            {/* 标题区域 */}
            <div style={{
              padding: '24px 40px 16px 40px',
              borderBottom: '1px solid #f0f0f0',
              background: '#fff'
            }}>
              <Input
                placeholder="请输入文档标题..."
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                style={{
                  fontSize: '20px',
                  fontWeight: '600',
                  textAlign: 'center',
                  border: 'none',
                  boxShadow: 'none'
                }}
                size="large"
              />
            </div>

            {/* Quill富文本编辑器 */}
            <div style={{
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              minHeight: 0, /* 重要：允许flex子项收缩 */
              overflow: 'hidden' /* 防止溢出 */
            }}>
              <QuillEditorWrapper>
                <QuillEditor
                  ref={editorRef}
                  value={content}
                  onChange={handleEditorChange}
                  placeholder="开始写作..."
                  style={{
                    flex: 1,
                    height: '100%',
                    minHeight: '400px'
                  }}
                  onFocus={() => console.log('编辑器获得焦点')}
                  onBlur={() => console.log('编辑器失去焦点')}
                />
              </QuillEditorWrapper>
            </div>

            {/* 页脚信息 */}
            <div style={{
              padding: '12px 40px',
              borderTop: '1px solid #e8e8e8',
              background: 'linear-gradient(to right, #fafafa, #f5f5f5)',
              fontSize: '12px',
              color: '#8c8c8c',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <span>字数统计: {wordCount} 字</span>
              <span>{new Date().toLocaleDateString()} {new Date().toLocaleTimeString()}</span>
            </div>
          </div>
        </Content>
      </Layout>
    </div>
  );
};

export default StandardEditorPage;
