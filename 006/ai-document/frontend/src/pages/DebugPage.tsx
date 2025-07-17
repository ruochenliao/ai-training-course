import React, { useState, useEffect } from 'react';
import { Card, Button, Space, Alert, Descriptions, Tag, message } from 'antd';
import { CheckCircleOutlined, CloseCircleOutlined, LoadingOutlined } from '@ant-design/icons';

interface DebugInfo {
  component: string;
  status: 'loading' | 'success' | 'error';
  message: string;
  details?: any;
}

const DebugPage: React.FC = () => {
  const [debugInfo, setDebugInfo] = useState<DebugInfo[]>([]);
  const [loading, setLoading] = useState(false);

  const addDebugInfo = (info: DebugInfo) => {
    setDebugInfo(prev => [...prev, { ...info, timestamp: new Date().toLocaleTimeString() }]);
  };

  const clearDebugInfo = () => {
    setDebugInfo([]);
  };

  const testWritingThemeService = async () => {
    setLoading(true);
    clearDebugInfo();

    try {
      // 测试服务导入
      addDebugInfo({
        component: '服务导入',
        status: 'loading',
        message: '正在导入 writingThemeService...'
      });

      const { default: writingThemeService } = await import('@/services/writingThemeService');
      
      addDebugInfo({
        component: '服务导入',
        status: 'success',
        message: 'writingThemeService 导入成功'
      });

      // 测试API连接
      addDebugInfo({
        component: 'API连接',
        status: 'loading',
        message: '正在测试API连接...'
      });

      try {
        const themes = await writingThemeService.getThemesSimple();
        addDebugInfo({
          component: 'API连接',
          status: 'success',
          message: `成功获取 ${themes.length} 个主题`,
          details: themes
        });
      } catch (apiError: any) {
        addDebugInfo({
          component: 'API连接',
          status: 'error',
          message: `API调用失败: ${apiError.message}`,
          details: apiError
        });
      }

      // 测试分类获取
      try {
        const categories = await writingThemeService.getCategories();
        addDebugInfo({
          component: '分类获取',
          status: 'success',
          message: `成功获取 ${categories.length} 个分类`,
          details: categories
        });
      } catch (catError: any) {
        addDebugInfo({
          component: '分类获取',
          status: 'error',
          message: `分类获取失败: ${catError.message}`,
          details: catError
        });
      }

      // 测试统计信息
      try {
        const stats = await writingThemeService.getStatistics();
        addDebugInfo({
          component: '统计信息',
          status: 'success',
          message: '成功获取统计信息',
          details: stats
        });
      } catch (statsError: any) {
        addDebugInfo({
          component: '统计信息',
          status: 'error',
          message: `统计信息获取失败: ${statsError.message}`,
          details: statsError
        });
      }

    } catch (importError: any) {
      addDebugInfo({
        component: '服务导入',
        status: 'error',
        message: `导入失败: ${importError.message}`,
        details: importError
      });
    }

    setLoading(false);
  };

  const testPageComponents = async () => {
    setLoading(true);
    clearDebugInfo();

    try {
      // 测试主题管理页面导入
      addDebugInfo({
        component: '页面组件',
        status: 'loading',
        message: '正在导入 WritingThemeManagementPage...'
      });

      const { default: WritingThemeManagementPage } = await import('./WritingThemeManagementPage');
      
      addDebugInfo({
        component: '页面组件',
        status: 'success',
        message: 'WritingThemeManagementPage 导入成功'
      });

      // 测试字段配置页面导入
      addDebugInfo({
        component: '页面组件',
        status: 'loading',
        message: '正在导入 ThemeFieldConfigPage...'
      });

      const { default: ThemeFieldConfigPage } = await import('./ThemeFieldConfigPage');
      
      addDebugInfo({
        component: '页面组件',
        status: 'success',
        message: 'ThemeFieldConfigPage 导入成功'
      });

      // 测试模板管理页面导入
      addDebugInfo({
        component: '页面组件',
        status: 'loading',
        message: '正在导入 TemplateManagementPage...'
      });

      const { default: TemplateManagementPage } = await import('./TemplateManagementPage');
      
      addDebugInfo({
        component: '页面组件',
        status: 'success',
        message: 'TemplateManagementPage 导入成功'
      });

    } catch (error: any) {
      addDebugInfo({
        component: '页面组件',
        status: 'error',
        message: `页面组件导入失败: ${error.message}`,
        details: error
      });
    }

    setLoading(false);
  };

  const testBackendConnection = async () => {
    setLoading(true);
    clearDebugInfo();

    try {
      // 测试后端健康检查
      addDebugInfo({
        component: '后端连接',
        status: 'loading',
        message: '正在检查后端服务...'
      });

      const response = await fetch('/api/health');
      if (response.ok) {
        addDebugInfo({
          component: '后端连接',
          status: 'success',
          message: '后端服务正常'
        });
      } else {
        addDebugInfo({
          component: '后端连接',
          status: 'error',
          message: `后端服务异常: ${response.status}`
        });
      }

      // 测试写作主题API
      addDebugInfo({
        component: '写作主题API',
        status: 'loading',
        message: '正在测试写作主题API...'
      });

      const themesResponse = await fetch('/api/writing-themes/themes/simple');
      if (themesResponse.ok) {
        const themes = await themesResponse.json();
        addDebugInfo({
          component: '写作主题API',
          status: 'success',
          message: `写作主题API正常，返回 ${themes.length} 个主题`,
          details: themes
        });
      } else {
        addDebugInfo({
          component: '写作主题API',
          status: 'error',
          message: `写作主题API异常: ${themesResponse.status}`
        });
      }

    } catch (error: any) {
      addDebugInfo({
        component: '后端连接',
        status: 'error',
        message: `连接失败: ${error.message}`,
        details: error
      });
    }

    setLoading(false);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'loading':
        return <LoadingOutlined style={{ color: '#1890ff' }} />;
      case 'success':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'error':
        return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />;
      default:
        return null;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'loading':
        return 'processing';
      case 'success':
        return 'success';
      case 'error':
        return 'error';
      default:
        return 'default';
    }
  };

  return (
    <div style={{ padding: '24px' }}>
      <Card title="写作主题管理系统 - 调试页面" style={{ marginBottom: '24px' }}>
        <Alert
          message="调试说明"
          description="此页面用于诊断写作主题管理系统的各个组件是否正常工作。请按顺序执行测试。"
          type="info"
          showIcon
          style={{ marginBottom: '24px' }}
        />

        <Space size="large">
          <Button 
            type="primary" 
            onClick={testBackendConnection}
            loading={loading}
          >
            测试后端连接
          </Button>
          <Button 
            onClick={testWritingThemeService}
            loading={loading}
          >
            测试服务层
          </Button>
          <Button 
            onClick={testPageComponents}
            loading={loading}
          >
            测试页面组件
          </Button>
          <Button onClick={clearDebugInfo}>
            清空日志
          </Button>
        </Space>
      </Card>

      {debugInfo.length > 0 && (
        <Card title="调试日志">
          {debugInfo.map((info, index) => (
            <Card 
              key={index} 
              size="small" 
              style={{ marginBottom: '8px' }}
              title={
                <Space>
                  {getStatusIcon(info.status)}
                  <span>{info.component}</span>
                  <Tag color={getStatusColor(info.status)}>
                    {info.status}
                  </Tag>
                </Space>
              }
            >
              <p>{info.message}</p>
              {info.details && (
                <details>
                  <summary>详细信息</summary>
                  <pre style={{ 
                    background: '#f5f5f5', 
                    padding: '8px', 
                    borderRadius: '4px',
                    fontSize: '12px',
                    overflow: 'auto',
                    maxHeight: '200px'
                  }}>
                    {JSON.stringify(info.details, null, 2)}
                  </pre>
                </details>
              )}
            </Card>
          ))}
        </Card>
      )}

      <Card title="系统信息" style={{ marginTop: '24px' }}>
        <Descriptions column={2}>
          <Descriptions.Item label="当前路径">
            {window.location.pathname}
          </Descriptions.Item>
          <Descriptions.Item label="用户代理">
            {navigator.userAgent.split(' ')[0]}
          </Descriptions.Item>
          <Descriptions.Item label="本地存储">
            {localStorage.length} 项
          </Descriptions.Item>
          <Descriptions.Item label="会话存储">
            {sessionStorage.length} 项
          </Descriptions.Item>
        </Descriptions>
      </Card>
    </div>
  );
};

export default DebugPage;
