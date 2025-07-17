import React, { useRef, useEffect, useState, forwardRef, useImperativeHandle } from 'react';
import ReactQuill from 'react-quill';
import 'quill/dist/quill.snow.css';
import './QuillEditor.css';

export interface QuillEditorRef {
  getContent: () => string;
  setContent: (content: string) => void;
  getTextContent: () => string;
  focus: () => void;
  blur: () => void;
  insertText: (text: string) => void;
  formatText: (format: string, value: any) => void;
  getSelection: () => any;
  setSelection: (range: any) => void;
}

interface QuillEditorProps {
  value?: string;
  onChange?: (content: string, delta: any, source: any, editor: any) => void;
  placeholder?: string;
  readOnly?: boolean;
  theme?: 'snow' | 'bubble';
  style?: React.CSSProperties;
  className?: string;
  modules?: any;
  formats?: string[];
  bounds?: string | HTMLElement;
  scrollingContainer?: string | HTMLElement;
  onFocus?: () => void;
  onBlur?: () => void;
  onKeyPress?: (event: any) => void;
  onKeyDown?: (event: any) => void;
  onKeyUp?: (event: any) => void;
}

const QuillEditor = forwardRef<QuillEditorRef, QuillEditorProps>(({
  value = '',
  onChange,
  placeholder = '开始写作...',
  readOnly = false,
  theme = 'snow',
  style,
  className = '',
  modules: customModules,
  formats: customFormats,
  bounds,
  scrollingContainer,
  onFocus,
  onBlur,
  onKeyPress,
  onKeyDown,
  onKeyUp
}, ref) => {
  const quillRef = useRef<ReactQuill>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [wordCount, setWordCount] = useState(0);
  const [isReady, setIsReady] = useState(false);

  // 简化的工具栏配置 - 确保稳定显示
  const defaultModules = {
    toolbar: [
      [{ 'header': [1, 2, 3, false] }],
      ['bold', 'italic', 'underline', 'strike'],
      [{ 'color': [] }, { 'background': [] }],
      [{ 'list': 'ordered' }, { 'list': 'bullet' }],
      [{ 'indent': '-1' }, { 'indent': '+1' }],
      [{ 'align': [] }],
      ['blockquote', 'code-block'],
      ['link', 'clean']
    ],
    clipboard: {
      matchVisual: false,
    },
    history: {
      delay: 1000,
      maxStack: 100,
      userOnly: true
    }
  };

  // 简化的格式配置
  const defaultFormats = [
    'header',
    'bold', 'italic', 'underline', 'strike',
    'color', 'background',
    'list', 'bullet', 'indent',
    'align',
    'blockquote', 'code-block',
    'link'
  ];

  const modules = customModules || defaultModules;
  const formats = customFormats || defaultFormats;

  // 暴露给父组件的方法 - 简化版本
  useImperativeHandle(ref, () => ({
    getContent: () => {
      const quill = quillRef.current?.getEditor();
      return quill?.root.innerHTML || '';
    },
    setContent: (content: string) => {
      const quill = quillRef.current?.getEditor();
      if (quill) {
        quill.root.innerHTML = content;
      }
    },
    getTextContent: () => {
      const quill = quillRef.current?.getEditor();
      return quill?.getText() || '';
    },
    focus: () => {
      const quill = quillRef.current?.getEditor();
      quill?.focus();
    },
    blur: () => {
      const quill = quillRef.current?.getEditor();
      quill?.blur();
    },
    insertText: (text: string) => {
      const quill = quillRef.current?.getEditor();
      if (quill) {
        const range = quill.getSelection();
        if (range) {
          quill.insertText(range.index, text);
        }
      }
    },
    formatText: (format: string, value: any) => {
      const quill = quillRef.current?.getEditor();
      if (quill) {
        const range = quill.getSelection();
        if (range) {
          quill.formatText(range.index, range.length, format, value);
        }
      }
    },
    getSelection: () => {
      const quill = quillRef.current?.getEditor();
      return quill?.getSelection();
    },
    setSelection: (range: any) => {
      const quill = quillRef.current?.getEditor();
      quill?.setSelection(range);
    }
  }));

  // 处理内容变化
  const handleChange = (content: string, delta: any, source: any, editor: any) => {
    const text = editor.getText();
    setWordCount(text.length);
    onChange?.(content, delta, source, editor);
  };

  // 处理编辑器准备就绪
  const handleReady = () => {
    setIsReady(true);
    console.log('✅ Quill编辑器已准备就绪');
  };

  // 简单可靠的工具栏保护机制
  useEffect(() => {
    // 等待组件完全挂载
    const timer = setTimeout(() => {
      const ensureToolbarVisible = () => {
        // 查找当前组件内的工具栏
        const container = containerRef.current;
        if (!container) return false;

        const toolbar = container.querySelector('.ql-toolbar') as HTMLElement;
        if (!toolbar) return false;

        // 直接设置内联样式，确保最高优先级
        toolbar.style.cssText = `
          display: block !important;
          visibility: visible !important;
          opacity: 1 !important;
          height: auto !important;
          min-height: 42px !important;
          background: linear-gradient(to bottom, #fafafa, #f0f0f0) !important;
          border: none !important;
          border-bottom: 1px solid #e8e8e8 !important;
          padding: 12px 16px !important;
          position: relative !important;
          z-index: 1000 !important;
        `;

        // 确保工具栏按钮也可见
        const buttons = toolbar.querySelectorAll('button, .ql-picker, .ql-formats');
        buttons.forEach(btn => {
          (btn as HTMLElement).style.cssText = `
            display: inline-block !important;
            visibility: visible !important;
            opacity: 1 !important;
          `;
        });

        return true;
      };

      // 立即执行一次
      if (ensureToolbarVisible()) {
        console.log('✅ 工具栏已确保可见');
        handleReady();
      }

      // 设置短期密集检查
      let checkCount = 0;
      const checkInterval = setInterval(() => {
        checkCount++;
        if (ensureToolbarVisible() || checkCount >= 50) {
          clearInterval(checkInterval);
          if (checkCount < 50) {
            console.log(`✅ 工具栏在第 ${checkCount} 次检查后确保可见`);
          }
        }
      }, 100);

    }, 100);

    return () => clearTimeout(timer);
  }, []);

  // 监听value变化，更新字数统计
  useEffect(() => {
    if (value) {
      const tempDiv = document.createElement('div');
      tempDiv.innerHTML = value;
      setWordCount(tempDiv.textContent?.length || 0);
    }
  }, [value]);

  return (
    <div
      ref={containerRef}
      className={`quill-editor-container ${className}`}
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        minHeight: '400px',
        background: '#fff',
        borderRadius: '8px',
        overflow: 'hidden',
        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
        position: 'relative',
        ...style
      }}
    >
      <ReactQuill
        ref={quillRef}
        theme={theme}
        value={value}
        onChange={handleChange}
        onFocus={onFocus}
        onBlur={onBlur}
        onKeyPress={onKeyPress}
        onKeyDown={onKeyDown}
        onKeyUp={onKeyUp}
        readOnly={readOnly}
        placeholder={placeholder}
        modules={modules}
        formats={formats}
        bounds={bounds}
        scrollingContainer={scrollingContainer}
        style={{
          height: '100%',
          display: 'flex',
          flexDirection: 'column'
        }}
      />

      {/* 字数统计 */}
      <div className="quill-word-count" style={{
        padding: '8px 16px',
        background: '#fafafa',
        borderTop: '1px solid #e8e8e8',
        fontSize: '12px',
        color: '#8c8c8c',
        textAlign: 'right'
      }}>
        字数: {wordCount} | 状态: {isReady ? '就绪' : '加载中...'}
      </div>
    </div>
  );
});

QuillEditor.displayName = 'QuillEditor';

export default QuillEditor;
