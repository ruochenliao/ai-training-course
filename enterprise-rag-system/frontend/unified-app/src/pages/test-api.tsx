import React, {useState} from 'react';
import {Alert, Button, Card, Divider, Space, Spin, Typography} from 'antd';
import {apiClient} from '@/utils/api';

const { Title, Text, Paragraph } = Typography;

interface TestResult {
  endpoint: string;
  success: boolean;
  error?: string;
  data?: any;
}

const TestApiPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<TestResult[]>([]);

  const testEndpoints = async () => {
    setLoading(true);
    setResults([]);
    
    const tests: Array<{ name: string; test: () => Promise<any> }> = [
      {
        name: 'GET /api/v1/users',
        test: () => apiClient.getUsers({ size: 10 })
      },
      {
        name: 'GET /api/v1/rbac/departments',
        test: () => apiClient.getDepartments()
      },
      {
        name: 'GET /api/v1/rbac/roles',
        test: () => apiClient.getRoles({ size: 10 })
      },
      {
        name: 'GET /api/v1/rbac/permissions',
        test: () => apiClient.getPermissions({ size: 10 })
      },
      {
        name: 'GET /api/v1/rbac/menu-tree',
        test: () => apiClient.getMenuTree()
      }
    ];

    const testResults: TestResult[] = [];

    for (const { name, test } of tests) {
      try {
        const data = await test();
        testResults.push({
          endpoint: name,
          success: true,
          data: data
        });
      } catch (error: any) {
        testResults.push({
          endpoint: name,
          success: false,
          error: error.message || '未知错误'
        });
      }
    }

    setResults(testResults);
    setLoading(false);
  };

  const getStatusColor = (success: boolean, error?: string) => {
    if (success) return 'success';
    if (error?.includes('401') || error?.includes('认证')) return 'warning';
    return 'error';
  };

  const getStatusText = (success: boolean, error?: string) => {
    if (success) return '✅ 成功';
    if (error?.includes('401') || error?.includes('认证')) return '🔐 需要认证（正常）';
    return '❌ 失败';
  };

  return (
    <div style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto' }}>
      <Card>
        <Title level={2}>API路由测试页面</Title>
        <Paragraph>
          此页面用于测试前后端API路由配置是否正确匹配。
          点击下方按钮测试各个API端点的连通性。
        </Paragraph>

        <Space style={{ marginBottom: '24px' }}>
          <Button 
            type="primary" 
            onClick={testEndpoints}
            loading={loading}
            size="large"
          >
            开始测试API端点
          </Button>
        </Space>

        {loading && (
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <Spin size="large" />
            <div style={{ marginTop: '16px' }}>
              <Text>正在测试API端点...</Text>
            </div>
          </div>
        )}

        {results.length > 0 && (
          <>
            <Divider />
            <Title level={3}>测试结果</Title>
            
            <div style={{ marginBottom: '16px' }}>
              <Alert
                message={`测试完成：${results.filter(r => r.success).length}/${results.length} 个端点成功`}
                type={results.every(r => r.success || r.error?.includes('401')) ? 'success' : 'warning'}
                showIcon
              />
            </div>

            <Space direction="vertical" style={{ width: '100%' }} size="middle">
              {results.map((result, index) => (
                <Card 
                  key={index}
                  size="small"
                  style={{ 
                    borderLeft: `4px solid ${
                      result.success ? '#52c41a' : 
                      result.error?.includes('401') ? '#faad14' : '#ff4d4f'
                    }`
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <Text strong>{result.endpoint}</Text>
                      <div style={{ marginTop: '4px' }}>
                        <Text type={getStatusColor(result.success, result.error) as any}>
                          {getStatusText(result.success, result.error)}
                        </Text>
                      </div>
                    </div>
                    
                    {result.error && (
                      <div style={{ textAlign: 'right', maxWidth: '400px' }}>
                        <Text type="secondary" style={{ fontSize: '12px' }}>
                          {result.error}
                        </Text>
                      </div>
                    )}
                    
                    {result.success && result.data && (
                      <div style={{ textAlign: 'right' }}>
                        <Text type="success" style={{ fontSize: '12px' }}>
                          数据获取成功
                        </Text>
                      </div>
                    )}
                  </div>
                </Card>
              ))}
            </Space>

            <Divider />
            
            <Alert
              message="说明"
              description={
                <div>
                  <p>• ✅ 成功：API端点正常工作，数据获取成功</p>
                  <p>• 🔐 需要认证：API端点存在但需要登录认证，这是正常的安全行为</p>
                  <p>• ❌ 失败：API端点不存在或配置错误，需要检查路由配置</p>
                </div>
              }
              type="info"
              showIcon
            />
          </>
        )}
      </Card>
    </div>
  );
};

export default TestApiPage;
