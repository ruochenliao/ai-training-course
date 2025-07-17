import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Alert } from 'antd';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

class QuillEditorWrapper extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.warn('QuillEditor错误:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <Alert
          message="编辑器加载失败"
          description="富文本编辑器遇到问题，请刷新页面重试。"
          type="error"
          showIcon
          style={{ margin: '20px 0' }}
        />
      );
    }

    return this.props.children;
  }
}

export default QuillEditorWrapper;
