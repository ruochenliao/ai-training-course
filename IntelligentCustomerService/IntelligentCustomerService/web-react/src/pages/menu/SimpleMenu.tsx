import React from 'react'
import { Button, Card, List, Typography } from 'antd'

const { Title, Paragraph } = Typography

const SimpleMenu: React.FC = () => {
  // 示例菜单项
  const menuItems = [
    { title: '基础功能', description: '系统基础功能和操作说明', link: '#basic' },
    { title: '高级设置', description: '系统高级设置和配置选项', link: '#advanced' },
    { title: '使用帮助', description: '系统使用帮助和常见问题', link: '#help' },
    { title: '关于系统', description: '系统版本信息和更新日志', link: '#about' },
  ]

  return (
    <div className='p-6'>
      <Title level={2} className='mb-6'>
        一级菜单示例
      </Title>

      <Paragraph className='mb-6'>这是一个简单的一级菜单页面示例，展示了基本的菜单布局和功能。您可以根据实际需求进行扩展和定制。</Paragraph>

      <div className='grid grid-cols-1 md:grid-cols-2 gap-6'>
        {menuItems.map((item, index) => (
          <Card key={index} hoverable className='transition-all duration-300 hover:shadow-md'>
            <Title level={4}>{item.title}</Title>
            <Paragraph className='mb-4'>{item.description}</Paragraph>
            <Button type='primary' href={item.link}>
              查看详情
            </Button>
          </Card>
        ))}
      </div>

      <Card className='mt-8'>
        <Title level={3}>菜单使用说明</Title>
        <Paragraph>一级菜单通常用于展示系统的主要功能模块，提供清晰的导航入口。 在实际应用中，可以根据业务需求自定义菜单项的内容和样式。</Paragraph>

        <Title level={4} className='mt-4'>
          配置方法
        </Title>
        <List
          bordered
          className='mt-2'
          dataSource={['在侧边栏配置中添加一级菜单项', '创建对应的页面组件', '在路由配置中添加相应的路由', '根据权限控制菜单的显示和访问']}
          renderItem={(item) => <List.Item>{item}</List.Item>}
        />
      </Card>
    </div>
  )
}

export default SimpleMenu
