import React from 'react'
import {Alert, Card, Descriptions, Spin, Tag, Tree} from 'antd'
import {usePermissionStore} from '@/store/permission.ts'

/**
 * 动态菜单测试页面
 * 用于验证动态菜单功能是否正常工作
 */
const DynamicMenuTest: React.FC = () => {
  const { menus, rawMenus, permissions, menuLoading } = usePermissionStore()

  // 将菜单数据转换为Tree组件格式
  const convertToTreeData = (menuData: any[]): any[] => {
    return menuData.map((item) => ({
      title: (
        <span>
          {item.label || item.name}
          <Tag color='blue' style={{ marginLeft: 8 }}>
            {item.key || item.path}
          </Tag>
        </span>
      ),
      key: item.key || item.id,
      children: item.children ? convertToTreeData(item.children) : undefined,
    }))
  }

  const convertRawToTreeData = (rawData: any[]): any[] => {
    return rawData.map((item) => ({
      title: (
        <span>
          {item.name}
          <Tag color='green' style={{ marginLeft: 8 }}>
            {item.menu_type}
          </Tag>
          <Tag color='orange' style={{ marginLeft: 4 }}>
            {item.path}
          </Tag>
          {item.is_hidden && (
            <Tag color='red' style={{ marginLeft: 4 }}>
              隐藏
            </Tag>
          )}
        </span>
      ),
      key: item.id,
      children: item.children && item.children.length > 0 ? convertRawToTreeData(item.children) : undefined,
    }))
  }

  if (menuLoading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size='large' />
        <p style={{ marginTop: 16 }}>正在加载动态菜单...</p>
      </div>
    )
  }

  return (
    <div style={{ padding: '24px' }}>
      <Card title='🎯 动态菜单测试页面 - 参考vue-fastapi-admin设计' style={{ marginBottom: '24px' }}>
        <Alert
          message='企业级动态菜单功能测试'
          description='此页面用于测试从API获取的动态菜单数据是否正确加载和显示，菜单设计参考vue-fastapi-admin的企业级风格。'
          type='info'
          showIcon
          style={{ marginBottom: '24px' }}
        />

        <Descriptions title='菜单统计信息' bordered column={2}>
          <Descriptions.Item label='菜单总数'>{menus.length}</Descriptions.Item>
          <Descriptions.Item label='原始菜单数据'>{rawMenus.length}</Descriptions.Item>
          <Descriptions.Item label='用户权限数量'>{permissions.length}</Descriptions.Item>
          <Descriptions.Item label='加载状态'>
            <Tag color={menuLoading ? 'processing' : 'success'}>{menuLoading ? '加载中' : '已加载'}</Tag>
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title='📋 转换后的菜单数据 (Ant Design Menu格式)' style={{ marginBottom: '24px' }}>
        {menus.length > 0 ? (
          <>
            <Alert message='路由测试' description='点击下方菜单项可以测试路由跳转是否正确' type='info' style={{ marginBottom: '16px' }} />
            <Tree treeData={convertToTreeData(menus)} defaultExpandAll showLine showIcon={false} />
          </>
        ) : (
          <Alert message='暂无菜单数据' type='warning' />
        )}
      </Card>

      <Card title='🔧 原始菜单数据 (API返回格式)' style={{ marginBottom: '24px' }}>
        {rawMenus.length > 0 ? (
          <Tree treeData={convertRawToTreeData(rawMenus)} defaultExpandAll showLine showIcon={false} />
        ) : (
          <Alert message='暂无原始菜单数据' type='warning' />
        )}
      </Card>

      <Card title='🔑 用户API权限列表'>
        {permissions.length > 0 ? (
          <div>
            {permissions.map((permission, index) => (
              <Tag key={index} color='blue' style={{ margin: '4px' }}>
                {permission}
              </Tag>
            ))}
          </div>
        ) : (
          <Alert message='暂无权限数据' type='warning' />
        )}
      </Card>

      <Card title='📊 调试信息' style={{ marginTop: '24px' }}>
        <Descriptions column={1} bordered>
          <Descriptions.Item label='菜单数据 JSON'>
            <pre
              style={{
                background: '#f5f5f5',
                padding: '12px',
                borderRadius: '4px',
                fontSize: '12px',
                maxHeight: '200px',
                overflow: 'auto',
              }}
            >
              {JSON.stringify(menus, null, 2)}
            </pre>
          </Descriptions.Item>
          <Descriptions.Item label='原始数据 JSON'>
            <pre
              style={{
                background: '#f5f5f5',
                padding: '12px',
                borderRadius: '4px',
                fontSize: '12px',
                maxHeight: '200px',
                overflow: 'auto',
              }}
            >
              {JSON.stringify(rawMenus, null, 2)}
            </pre>
          </Descriptions.Item>
        </Descriptions>
      </Card>
    </div>
  )
}

export default DynamicMenuTest
