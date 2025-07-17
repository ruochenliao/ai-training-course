import React, { useState, useEffect, useRef } from 'react';
import { Layout, Button, Input, Space, message, Typography } from 'antd';
import {
  FullscreenOutlined,
  SaveOutlined,
  FileOutlined,
  PrinterOutlined,
  FullscreenExitOutlined,
  HomeOutlined
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import QuillEditor, { QuillEditorRef } from '@/components/QuillEditor';
import QuillEditorWrapper from '@/components/QuillEditorWrapper';
import AIAssistantPopup from '@/components/AIAssistantPopup';
import ThemeSelectionModal from '@/components/ThemeSelectionModal';
import AIConfigurationModal from '@/components/AIConfigurationModal';
import { AIWritingTheme, aiWritingThemesService } from '@/services/aiWritingThemes';
import '@/styles/AIWritingEditor.css';

const { Content } = Layout;
const { Text } = Typography;

interface AIAssistantOption {
  id: string;
  name: string;
  description: string;
  icon: string;
}

const AIWritingEditorPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [content, setContent] = useState('');
  const [title, setTitle] = useState('');
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [wordCount, setWordCount] = useState(0);
  const editorRef = useRef<QuillEditorRef>(null);

  // AI助手相关状态
  const [showAIPopup, setShowAIPopup] = useState(false);
  const [aiPopupPosition, setAIPopupPosition] = useState({ x: 0, y: 0 });
  const [showThemeModal, setShowThemeModal] = useState(false);
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [selectedTheme, setSelectedTheme] = useState<AIWritingTheme | null>(null);

  // 流式输出相关状态
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingSessionId, setStreamingSessionId] = useState<string | null>(null);
  const [streamingContent, setStreamingContent] = useState('');
  const [placeholderIndex, setPlaceholderIndex] = useState<number | null>(null);

  // 处理编辑器内容变化
  const handleEditorChange = (content: string, delta: any, source: any, editor: any) => {
    setContent(content);
    const text = editor.getText();
    setWordCount(text.length);

    // 检测@符号触发AI助手
    if (source === 'user') {
      const currentText = editor.getText();
      const selection = editor.getSelection();
      
      if (selection && currentText.charAt(selection.index - 1) === '@') {
        // 获取光标位置
        const bounds = editor.getBounds(selection.index);
        const editorContainer = document.querySelector('.ql-editor');
        
        if (editorContainer && bounds) {
          const containerRect = editorContainer.getBoundingClientRect();
          setAIPopupPosition({
            x: containerRect.left + bounds.left,
            y: containerRect.top + bounds.top + bounds.height + 5
          });
          setShowAIPopup(true);
        }
      }
    }
  };

  // 处理AI助手选择
  const handleAIAssistantSelect = (option: AIAssistantOption) => {
    setShowAIPopup(false);
    
    if (option.id === 'ai_writing') {
      // 显示主题选择模态框
      setShowThemeModal(true);
    } else {
      // 其他AI功能的处理逻辑
      message.info(`${option.name} 功能正在开发中...`);
    }
  };

  // 处理主题选择
  const handleThemeSelect = (theme: AIWritingTheme) => {
    setSelectedTheme(theme);
    setShowThemeModal(false);
    setShowConfigModal(true);
  };

  // 处理开始流式输出
  const handleStartStreaming = async (sessionId: string) => {
    setIsStreaming(true);
    setStreamingSessionId(sessionId);
    setStreamingContent('');

    // 在编辑器中插入流式输出的占位符
    if (editorRef.current) {
      const quill = (editorRef.current as any).quillRef?.current?.getEditor();
      if (quill) {
        const selection = quill.getSelection();
        const insertIndex = selection ? selection.index : quill.getLength() - 1;

        // 插入一个带有特殊标识的占位符
        const placeholder = '\n\n🤖 AI正在生成内容...\n';
        quill.insertText(insertIndex, placeholder);
        quill.setSelection(insertIndex + placeholder.length);

        console.log('插入占位符，位置:', insertIndex, '内容:', placeholder);
      }
    }

    // 开始轮询获取流式内容
    pollStreamingContent(sessionId);
  };

  // 使用EventSource进行流式内容接收，带降级处理
  const pollStreamingContent = (sessionId: string) => {
    // 首先尝试使用EventSource
    try {
      const eventSource = new EventSource(`/api/ai-writing/stream/${sessionId}`);

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('收到流式数据:', data);

          if (data.content && data.is_complete) {
            // 生成完成，替换占位符
            console.log('AI生成完成，内容长度:', data.content.length);
            replaceStreamingPlaceholder(data.content);
            setIsStreaming(false);
            setStreamingSessionId(null);
            setStreamingContent('');
            eventSource.close();
            message.success('AI内容生成完成');
          } else if (data.error) {
            // 生成失败
            console.log('AI生成失败:', data.error);
            replaceStreamingPlaceholder('❌ AI内容生成失败，请重试');
            setIsStreaming(false);
            setStreamingSessionId(null);
            setStreamingContent('');
            eventSource.close();
            message.error('AI内容生成失败：' + data.error);
          } else if (data.status === 'processing') {
            // 更新进度提示
            console.log('AI生成进行中:', data.message);
            updateStreamingPlaceholder(data.message || '🤖 AI正在生成内容，请稍候...');
          } else if (data.content && !data.is_complete) {
            // 流式内容片段 - 实时替换整个内容（不是追加）
            console.log('收到流式内容片段，长度:', data.content.length);
            setStreamingContent(data.content);
            replaceStreamingContent(data.content);
          }
        } catch (error) {
          console.error('解析流式数据失败:', error, event.data);
        }
      };

      eventSource.onerror = (error) => {
        console.error('EventSource错误，降级到轮询模式:', error);
        eventSource.close();
        // 降级到轮询模式
        fallbackToPolling(sessionId);
      };

      // 设置超时保护
      setTimeout(() => {
        if (eventSource.readyState !== EventSource.CLOSED) {
          eventSource.close();
          if (isStreaming) {
            replaceStreamingPlaceholder('❌ 生成超时，请重试');
            setIsStreaming(false);
            setStreamingSessionId(null);
            message.error('生成超时，请重试');
          }
        }
      }, 300000); // 5分钟超时

    } catch (error) {
      console.error('EventSource不可用，使用轮询模式:', error);
      // 如果EventSource不可用，直接使用轮询
      fallbackToPolling(sessionId);
    }
  };

  // 降级轮询方法
  const fallbackToPolling = async (sessionId: string) => {
    const maxAttempts = 60; // 最多尝试60次
    let attempts = 0;

    const poll = async () => {
      if (attempts >= maxAttempts || !isStreaming) {
        if (isStreaming) {
          replaceStreamingPlaceholder('❌ 生成超时，请重试');
          setIsStreaming(false);
          setStreamingSessionId(null);
          message.error('生成超时，请重试');
        }
        return;
      }

      try {
        attempts++;
        const response = await aiWritingThemesService.getGenerationStatus(sessionId);
        console.log(`轮询第${attempts}次，状态:`, response);

        if (response.status === 'completed' && response.content) {
          console.log('轮询模式：AI生成完成，内容长度:', response.content.length);
          replaceStreamingPlaceholder(response.content);
          setIsStreaming(false);
          setStreamingSessionId(null);
          message.success('AI内容生成完成');
        } else if (response.status === 'failed') {
          console.log('轮询模式：AI生成失败:', response.error);
          replaceStreamingPlaceholder('❌ AI内容生成失败，请重试');
          setIsStreaming(false);
          setStreamingSessionId(null);
          message.error('AI内容生成失败：' + (response.error || '未知错误'));
        } else {
          // 继续轮询
          console.log(`继续轮询，当前状态: ${response.status}`);
          updateStreamingPlaceholder(`🤖 AI正在生成内容... (${attempts}/${maxAttempts})`);
          setTimeout(poll, 2000); // 2秒后再次轮询
        }
      } catch (error) {
        console.error('轮询失败:', error);
        setTimeout(poll, 2000); // 出错后继续尝试
      }
    };

    poll();
  };

  // 替换流式内容（用于实时更新整个内容）
  const replaceStreamingContent = (newContent: string) => {
    console.log('🔄 替换流式内容，长度:', newContent.length);

    if (editorRef.current) {
      try {
        // 使用QuillEditor组件暴露的方法
        const currentText = editorRef.current.getTextContent();
        const placeholderText = '🤖 AI正在生成内容';
        const placeholderIndex = currentText.indexOf(placeholderText);

        console.log('🔍 当前编辑器文本长度:', currentText.length);
        console.log('🔍 占位符位置:', placeholderIndex);

        if (placeholderIndex !== -1) {
          // 找到占位符，构建新的完整内容
          const beforePlaceholder = currentText.substring(0, placeholderIndex);

          // 将Markdown格式转换为HTML格式，保持良好的显示效果
          const formattedContent = formatContentForEditor(newContent);
          const newFullContent = beforePlaceholder + formattedContent;

          console.log('📝 设置新的完整内容，长度:', newFullContent.length);

          // 使用setContent方法直接设置内容
          editorRef.current.setContent(newFullContent);

          console.log('✅ 内容替换完成');
        } else {
          // 没有占位符，直接设置内容
          console.log('⚠️ 未找到占位符，直接设置内容');
          const formattedContent = formatContentForEditor(newContent);
          editorRef.current.setContent(formattedContent);
        }

        // 更新组件状态
        setContent(editorRef.current.getContent());
        console.log('📊 编辑器状态已更新');

      } catch (error) {
        console.error('❌ 替换内容时出错:', error);
      }
    } else {
      console.error('❌ 编辑器引用不存在');
    }
  };

  // 格式化内容以适应编辑器显示
  const formatContentForEditor = (content: string): string => {
    // 保持原始格式，让Quill编辑器自然处理
    let formatted = content;

    // 处理基本的Markdown格式
    // 处理标题（转换为纯文本格式，让编辑器自然显示）
    formatted = formatted.replace(/^# (.+)$/gm, '$1\n');
    formatted = formatted.replace(/^## (.+)$/gm, '$1\n');
    formatted = formatted.replace(/^### (.+)$/gm, '$1\n');

    // 处理粗体（保持**格式，让用户看到原始格式）
    // formatted = formatted.replace(/\*\*(.+?)\*\*/g, '$1');

    // 确保段落之间有适当的间距
    formatted = formatted.replace(/\n{3,}/g, '\n\n');

    // 清理开头和结尾的空白
    formatted = formatted.trim();

    return formatted;
  };

  // 追加流式内容（用于实时显示内容片段）
  const appendStreamingContent = (contentPiece: string) => {
    console.log('📝 追加流式内容:', contentPiece);

    if (editorRef.current) {
      const quill = (editorRef.current as any).quillRef?.current?.getEditor();
      if (quill) {
        const currentText = quill.getText();
        const placeholderText = '🤖 AI正在生成内容';
        const placeholderIndex = currentText.indexOf(placeholderText);

        console.log('🔍 当前编辑器文本:', currentText);
        console.log('🔍 占位符位置:', placeholderIndex);

        if (placeholderIndex !== -1) {
          // 找到占位符，替换为新内容
          const lineEnd = currentText.indexOf('\n', placeholderIndex);
          const endIndex = lineEnd !== -1 ? lineEnd + 1 : currentText.length;
          const lengthToReplace = endIndex - placeholderIndex;

          console.log('🗑️ 删除占位符，位置:', placeholderIndex, '长度:', lengthToReplace);
          quill.deleteText(placeholderIndex, lengthToReplace);

          // 插入新的内容片段
          console.log('📝 插入内容，位置:', placeholderIndex, '内容长度:', contentPiece.length);
          quill.insertText(placeholderIndex, contentPiece);

          // 移动光标到内容末尾
          quill.setSelection(placeholderIndex + contentPiece.length);

          console.log('✅ 内容插入完成');
        } else {
          // 没有占位符，直接在末尾追加
          console.log('📝 直接追加内容到末尾');
          const currentLength = quill.getLength();
          quill.insertText(currentLength - 1, contentPiece);
          quill.setSelection(currentLength - 1 + contentPiece.length);
        }

        // 更新组件状态
        setContent(quill.root.innerHTML);
        console.log('📊 编辑器状态已更新，新内容长度:', quill.getText().length);
      } else {
        console.error('❌ 无法获取Quill编辑器实例');
      }
    } else {
      console.error('❌ 编辑器引用不存在');
    }
  };

  // 更新流式输出占位符（用于进度更新）
  const updateStreamingPlaceholder = (newText: string) => {
    if (editorRef.current) {
      const quill = (editorRef.current as any).quillRef?.current?.getEditor();
      if (quill) {
        const currentText = quill.getText();
        const placeholderText = '🤖 AI正在生成内容';
        const placeholderIndex = currentText.indexOf(placeholderText);

        if (placeholderIndex !== -1) {
          // 找到占位符行的结束位置
          const lineEnd = currentText.indexOf('\n', placeholderIndex);
          const endIndex = lineEnd !== -1 ? lineEnd : currentText.length;
          const lengthToReplace = endIndex - placeholderIndex;

          // 替换占位符文本
          quill.deleteText(placeholderIndex, lengthToReplace);
          quill.insertText(placeholderIndex, newText);
        }
      }
    }
  };

  // 替换流式输出占位符（用于最终内容）
  const replaceStreamingPlaceholder = (finalContent: string) => {
    if (editorRef.current) {
      const quill = (editorRef.current as any).quillRef?.current?.getEditor();
      if (quill) {
        const currentText = quill.getText();
        const currentHTML = quill.root.innerHTML;

        // 查找占位符的位置
        const placeholderText = '🤖 AI正在生成内容';
        const placeholderIndex = currentText.indexOf(placeholderText);

        if (placeholderIndex !== -1) {
          // 删除占位符
          const placeholderLength = currentText.substring(placeholderIndex).split('\n')[0].length;
          quill.deleteText(placeholderIndex, placeholderLength + 1); // +1 for newline

          // 插入AI生成的内容
          quill.insertText(placeholderIndex, finalContent);

          // 移动光标到内容末尾
          const newLength = quill.getLength();
          quill.setSelection(newLength - 1);
        } else {
          // 如果找不到占位符，直接在当前位置插入内容
          const selection = quill.getSelection();
          const insertIndex = selection ? selection.index : quill.getLength() - 1;
          quill.insertText(insertIndex, '\n\n' + finalContent);
          quill.setSelection(insertIndex + finalContent.length + 2);
        }

        // 更新组件状态
        setContent(quill.root.innerHTML);
      }
    }
  };

  // 处理AI生成内容（保留原有方法作为备用）
  const handleAIGenerate = (generatedContent: string) => {
    if (editorRef.current) {
      // 获取当前光标位置
      const selection = editorRef.current.getSelection();
      if (selection) {
        // 在光标位置插入生成的内容
        const quill = (editorRef.current as any).quillRef?.current?.getEditor();
        if (quill) {
          quill.insertText(selection.index, generatedContent);
          // 移动光标到插入内容的末尾
          quill.setSelection(selection.index + generatedContent.length);
        }
      } else {
        // 如果没有选择，追加到末尾
        setContent(prev => prev + '\n\n' + generatedContent);
      }
    }
    message.success('AI生成的内容已插入到编辑器中');
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

  // 返回首页
  const handleGoHome = () => {
    navigate('/');
  };

  // 处理从其他页面传递的初始内容
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

  // 处理键盘事件
  const handleKeyDown = (event: any) => {
    // ESC键关闭AI弹窗
    if (event.key === 'Escape' && showAIPopup) {
      setShowAIPopup(false);
    }
  };

  return (
    <div className={isFullscreen ? 'ai-writing-editor-fullscreen' : ''}>
      <Layout style={{
        minHeight: isFullscreen ? '100vh' : '100%',
        background: '#f8f9fa'
      }}>
        {/* 工具栏 */}
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
            <Button 
              type="text" 
              size="small" 
              icon={<HomeOutlined />} 
              onClick={handleGoHome} 
              title="返回首页"
            >
              首页
            </Button>
            <Button 
              type="text" 
              size="small" 
              icon={<SaveOutlined />} 
              onClick={handleSave} 
              title="保存"
            >
              保存
            </Button>
            <Button 
              type="text" 
              size="small" 
              icon={<FileOutlined />} 
              onClick={handleNew} 
              title="新建"
            >
              新建
            </Button>
            <Button 
              type="text" 
              size="small" 
              icon={<PrinterOutlined />} 
              onClick={handlePrint} 
              title="打印"
            >
              打印
            </Button>
          </Space>

          {/* 中间标题 */}
          <div style={{ flex: 1, textAlign: 'center' }}>
            <Text strong style={{ fontSize: '16px', color: '#1890ff' }}>
              AI智能写作编辑器
            </Text>
          </div>

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
              minHeight: 0,
              overflow: 'hidden'
            }}>
              <QuillEditorWrapper>
                <QuillEditor
                  ref={editorRef}
                  value={content}
                  onChange={handleEditorChange}
                  placeholder="开始写作... (输入 @ 可以调用AI写作助手)"
                  style={{
                    flex: 1,
                    height: '100%',
                    minHeight: '400px'
                  }}
                  onKeyDown={handleKeyDown}
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
              <span>
                {isStreaming ? (
                  <span style={{ color: '#1890ff' }}>
                    🤖 AI正在生成内容...
                  </span>
                ) : (
                  '💡 输入 @ 调用AI助手'
                )}
              </span>
              <span>{new Date().toLocaleDateString()} {new Date().toLocaleTimeString()}</span>
            </div>
          </div>
        </Content>
      </Layout>

      {/* AI助手弹窗 */}
      <AIAssistantPopup
        visible={showAIPopup}
        position={aiPopupPosition}
        onSelect={handleAIAssistantSelect}
        onClose={() => setShowAIPopup(false)}
      />

      {/* 主题选择模态框 */}
      <ThemeSelectionModal
        visible={showThemeModal}
        onSelect={handleThemeSelect}
        onCancel={() => setShowThemeModal(false)}
      />

      {/* AI配置模态框 */}
      <AIConfigurationModal
        visible={showConfigModal}
        theme={selectedTheme}
        onGenerate={handleAIGenerate}
        onStartStreaming={handleStartStreaming}
        onCancel={() => {
          setShowConfigModal(false);
          setSelectedTheme(null);
        }}
      />
    </div>
  );
};

export default AIWritingEditorPage;
