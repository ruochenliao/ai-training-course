import React, { Component, ErrorInfo, ReactNode } from 'react'
import { Result, Button } from 'antd'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error?: Error
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false
  }

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo)
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: 24 }}>
          <Result
            status="error"
            title="页面加载失败"
            subTitle="抱歉，页面遇到了一些问题。请尝试刷新页面或联系管理员。"
            extra={[
              <Button type="primary" key="refresh" onClick={() => window.location.reload()}>
                刷新页面
              </Button>,
              <Button key="home" onClick={() => window.location.href = '/'}>
                返回首页
              </Button>
            ]}
          >
            {process.env.NODE_ENV === 'development' && (
              <div style={{ textAlign: 'left', marginTop: 16 }}>
                <details>
                  <summary>错误详情（开发模式）</summary>
                  <pre style={{ marginTop: 8, fontSize: 12 }}>
                    {this.state.error?.stack}
                  </pre>
                </details>
              </div>
            )}
          </Result>
        </div>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary
