import {Component, ErrorInfo, ReactNode} from 'react';
import {Button, Result} from 'antd';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

/**
 * 错误边界组件
 * 用于捕获子组件树中的 JavaScript 错误，记录错误并展示备用 UI
 */
class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    // 更新 state，下次渲染时展示备用 UI
    return { hasError: true, error };
  }

  override componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // 可以将错误日志上报给服务器
    this.setState({ errorInfo });
    
    // 调用错误处理回调
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
    
    // 可以在这里添加错误上报逻辑
    console.error('Error caught by ErrorBoundary:', error, errorInfo);
  }

  handleReset = (): void => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null
    });
  }

  override render(): ReactNode {
    if (this.state.hasError) {
      // 如果提供了自定义的 fallback，则使用它
      if (this.props.fallback) {
        return this.props.fallback;
      }
      
      // 默认的错误 UI
      return (
        <Result
          status="error"
          title="组件出错了"
          subTitle={this.state.error?.message || '发生了未知错误'}
          extra={[
            <Button key="reload" type="primary" onClick={() => window.location.reload()}>
              刷新页面
            </Button>,
            <Button key="reset" onClick={this.handleReset}>
              重试
            </Button>
          ]}
        >
          {import.meta.env.DEV && this.state.errorInfo && (
            <div className="mt-4 p-4 bg-gray-100 rounded overflow-auto max-h-96">
              <details>
                <summary className="cursor-pointer font-medium mb-2">错误详情</summary>
                <pre className="whitespace-pre-wrap text-sm text-red-600">
                  {this.state.error && this.state.error.toString()}
                </pre>
                <pre className="whitespace-pre-wrap text-xs text-gray-600 mt-2">
                  {this.state.errorInfo.componentStack}
                </pre>
              </details>
            </div>
          )}
        </Result>
      );
    }

    // 正常渲染子组件
    return this.props.children;
  }
}

export default ErrorBoundary;