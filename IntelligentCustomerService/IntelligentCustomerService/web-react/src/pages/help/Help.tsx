import React from 'react';
import { Card, Typography, Collapse, Tag, Alert, Space, Button } from 'antd';
import { 
  QuestionCircleOutlined, 
  BookOutlined, 
  CustomerServiceOutlined,
  SafetyOutlined,
  ToolOutlined
} from '@ant-design/icons';

const { Title, Paragraph, Text } = Typography;
const { Panel } = Collapse;

/**
 * 帮助文档页面
 */
const Help: React.FC = () => {
  const faqData = [
    {
      key: '1',
      label: '如何重置密码？',
      children: (
        <div>
          <Paragraph>
            1. 点击右上角用户头像，选择"个人中心"
          </Paragraph>
          <Paragraph>
            2. 在个人信息页面中找到"修改密码"选项
          </Paragraph>
          <Paragraph>
            3. 输入当前密码和新密码，点击确认即可
          </Paragraph>
        </div>
      ),
    },
    {
      key: '2',
      label: '如何管理用户权限？',
      children: (
        <div>
          <Paragraph>
            1. 进入"系统管理" → "用户管理"
          </Paragraph>
          <Paragraph>
            2. 选择要修改的用户，点击"编辑"
          </Paragraph>
          <Paragraph>
            3. 在角色选择中分配相应的角色权限
          </Paragraph>
        </div>
      ),
    },
    {
      key: '3',
      label: '如何添加新的菜单？',
      children: (
        <div>
          <Paragraph>
            1. 进入"系统管理" → "菜单管理"
          </Paragraph>
          <Paragraph>
            2. 点击"新增菜单"按钮
          </Paragraph>
          <Paragraph>
            3. 填写菜单信息，包括名称、路径、图标等
          </Paragraph>
          <Paragraph>
            4. 设置菜单权限和显示顺序
          </Paragraph>
        </div>
      ),
    },
    {
      key: '4',
      label: '系统运行缓慢怎么办？',
      children: (
        <div>
          <Paragraph>
            1. 检查网络连接是否正常
          </Paragraph>
          <Paragraph>
            2. 清除浏览器缓存和Cookie
          </Paragraph>
          <Paragraph>
            3. 关闭不必要的浏览器标签页
          </Paragraph>
          <Paragraph>
            4. 如问题持续，请联系系统管理员
          </Paragraph>
        </div>
      ),
    },
  ];

  const quickGuides = [
    {
      title: '快速入门',
      description: '了解系统基本功能和操作流程',
      icon: <BookOutlined style={{ color: '#1890ff' }} />,
      tags: ['新手必读', '基础操作'],
    },
    {
      title: '用户管理指南',
      description: '学习如何管理用户账户和权限',
      icon: <CustomerServiceOutlined style={{ color: '#52c41a' }} />,
      tags: ['用户管理', '权限控制'],
    },
    {
      title: '系统配置',
      description: '掌握系统参数配置和优化技巧',
      icon: <ToolOutlined style={{ color: '#faad14' }} />,
      tags: ['系统设置', '性能优化'],
    },
    {
      title: '安全设置',
      description: '了解系统安全策略和防护措施',
      icon: <SafetyOutlined style={{ color: '#f5222d' }} />,
      tags: ['安全防护', '数据保护'],
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      {/* 页面标题 */}
      <div style={{ marginBottom: '32px' }}>
        <Title level={1}>
          <QuestionCircleOutlined style={{ marginRight: '12px', color: '#1890ff' }} />
          帮助文档
        </Title>
        <Paragraph style={{ fontSize: '16px', color: '#666' }}>
          系统使用指南和常见问题解答
        </Paragraph>
      </div>

      {/* 联系支持 */}
      <Alert
        message="需要帮助？"
        description={
          <Space direction="vertical" size="small">
            <Text>如果您在使用过程中遇到问题，可以通过以下方式获取帮助：</Text>
            <Space>
              <Button type="primary" size="small">在线客服</Button>
              <Button size="small">提交工单</Button>
              <Button size="small">查看文档</Button>
            </Space>
          </Space>
        }
        type="info"
        showIcon
        style={{ marginBottom: '32px' }}
      />

      {/* 快速指南 */}
      <Title level={2} style={{ marginBottom: '24px' }}>
        <BookOutlined style={{ marginRight: '8px', color: '#1890ff' }} />
        快速指南
      </Title>

      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', 
        gap: '16px',
        marginBottom: '48px'
      }}>
        {quickGuides.map((guide, index) => (
          <Card
            key={index}
            hoverable
            style={{ borderRadius: '8px' }}
            bodyStyle={{ padding: '20px' }}
          >
            <div style={{ display: 'flex', alignItems: 'flex-start', marginBottom: '12px' }}>
              <div style={{ fontSize: '24px', marginRight: '12px' }}>
                {guide.icon}
              </div>
              <div style={{ flex: 1 }}>
                <Title level={4} style={{ margin: '0 0 8px 0' }}>
                  {guide.title}
                </Title>
                <Paragraph style={{ margin: '0 0 12px 0', color: '#666' }}>
                  {guide.description}
                </Paragraph>
                <Space size={[0, 4]} wrap>
                  {guide.tags.map((tag, idx) => (
                    <Tag key={idx} color="blue" style={{ fontSize: '11px' }}>
                      {tag}
                    </Tag>
                  ))}
                </Space>
              </div>
            </div>
            <Button type="link" style={{ padding: 0 }}>
              查看详情 →
            </Button>
          </Card>
        ))}
      </div>

      {/* 常见问题 */}
      <Title level={2} style={{ marginBottom: '24px' }}>
        <QuestionCircleOutlined style={{ marginRight: '8px', color: '#52c41a' }} />
        常见问题
      </Title>

      <Card style={{ borderRadius: '8px' }}>
        <Collapse 
          items={faqData}
          size="large"
          ghost
        />
      </Card>

      {/* 系统信息 */}
      <Card 
        title="系统信息" 
        style={{ marginTop: '32px', borderRadius: '8px' }}
      >
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
          gap: '16px' 
        }}>
          <div>
            <Text strong>系统版本：</Text>
            <Text>v1.0.0</Text>
          </div>
          <div>
            <Text strong>更新时间：</Text>
            <Text>2024-12-19</Text>
          </div>
          <div>
            <Text strong>技术支持：</Text>
            <Text>support@example.com</Text>
          </div>
          <div>
            <Text strong>服务热线：</Text>
            <Text>400-123-4567</Text>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default Help;
