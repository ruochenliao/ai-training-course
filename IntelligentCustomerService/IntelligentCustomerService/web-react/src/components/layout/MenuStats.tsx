import React from 'react'
import { Badge, Space, Tooltip } from 'antd'
import { Icon } from '@iconify/react'
import { usePermissionStore } from '../../store/permission'

/**
 * 菜单统计组件 - 参考vue-fastapi-admin的设计风格
 * 显示菜单加载状态和统计信息
 */
const MenuStats: React.FC = () => {
  const { rawMenus, permissions, menuLoading } = usePermissionStore()

  // 计算菜单统计
  const stats = React.useMemo(() => {
    const countMenuItems = (items: any[]): { total: number; catalog: number; menu: number } => {
      let total = 0
      let catalog = 0
      let menu = 0

      items.forEach((item) => {
        total++
        if (item.menu_type === 'catalog') {
          catalog++
        } else {
          menu++
        }

        if (item.children && item.children.length > 0) {
          const childStats = countMenuItems(item.children)
          total += childStats.total
          catalog += childStats.catalog
          menu += childStats.menu
        }
      })

      return { total, catalog, menu }
    }

    return countMenuItems(rawMenus)
  }, [rawMenus])

  if (menuLoading) {
    return (
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          padding: '8px 16px',
          background: 'rgba(24, 144, 255, 0.05)',
          borderRadius: '6px',
          margin: '8px 12px',
          border: '1px solid rgba(24, 144, 255, 0.1)',
        }}
      >
        <div
          style={{
            width: '12px',
            height: '12px',
            border: '1px solid #f0f0f0',
            borderTop: '1px solid #1890ff',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            marginRight: '8px',
          }}
        />
        <span style={{ fontSize: '11px', color: '#1890ff' }}>加载中...</span>
      </div>
    )
  }

  return (
    <div
      style={{
        padding: '8px 16px',
        background: 'rgba(24, 144, 255, 0.05)',
        borderRadius: '6px',
        margin: '8px 12px',
        border: '1px solid rgba(24, 144, 255, 0.1)',
      }}
    >
      <Space size={12}>
        <Tooltip title='菜单总数'>
          <Badge count={stats.total} size='small' style={{ backgroundColor: '#1890ff' }}>
            <Icon icon='mdi:menu' style={{ fontSize: '14px', color: '#1890ff' }} />
          </Badge>
        </Tooltip>

        <Tooltip title='目录数量'>
          <Badge count={stats.catalog} size='small' style={{ backgroundColor: '#52c41a' }}>
            <Icon icon='mdi:folder-outline' style={{ fontSize: '14px', color: '#52c41a' }} />
          </Badge>
        </Tooltip>

        <Tooltip title='菜单数量'>
          <Badge count={stats.menu} size='small' style={{ backgroundColor: '#faad14' }}>
            <Icon icon='mdi:file-outline' style={{ fontSize: '14px', color: '#faad14' }} />
          </Badge>
        </Tooltip>

        <Tooltip title='权限数量'>
          <Badge count={permissions.length} size='small' style={{ backgroundColor: '#722ed1' }}>
            <Icon icon='mdi:shield-check-outline' style={{ fontSize: '14px', color: '#722ed1' }} />
          </Badge>
        </Tooltip>
      </Space>
    </div>
  )
}

export default MenuStats
