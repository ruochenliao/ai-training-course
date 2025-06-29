import React from 'react'
import {Link} from 'react-router-dom'
import {Icon} from '@iconify/react'
import {useAppStore} from '@/store/app.ts'

/**
 * 企业级侧边栏Logo组件
 */
const SideLogo: React.FC = () => {
  const { collapsed } = useAppStore()

  // 从环境变量获取标题
  const title = import.meta.env.VITE_TITLE || '智能客服系统'

  return (
    <Link
      to='/'
      className='enterprise-logo-container'
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: collapsed ? 'center' : 'flex-start',
        height: '64px',
        padding: collapsed ? '0' : '0 24px',
        borderBottom: '1px solid #f0f0f0',
        background: '#ffffff',
        transition: 'all 0.2s ease-in-out',
        textDecoration: 'none',
        overflow: 'hidden',
      }}
    >
      {/* 企业级Logo图标 */}
      <div
        className='enterprise-logo-icon'
        style={{
          width: '32px',
          height: '32px',
          background: 'linear-gradient(135deg, #1890ff 0%, #096dd9 100%)',
          borderRadius: '8px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
          boxShadow: '0 2px 8px rgba(24, 144, 255, 0.2)',
        }}
      >
        <Icon
          icon='mdi:customer-service'
          style={{
            fontSize: '18px',
            color: '#ffffff',
          }}
        />
      </div>

      {/* 企业级标题 */}
      {!collapsed && (
        <div
          className='enterprise-logo-text'
          style={{
            marginLeft: '12px',
            overflow: 'hidden',
          }}
        >
          <h1
            style={{
              fontSize: '16px',
              fontWeight: 600,
              color: '#262626',
              margin: 0,
              lineHeight: '22px',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            }}
          >
            {title}
          </h1>
          <p
            style={{
              fontSize: '12px',
              color: '#8c8c8c',
              margin: 0,
              lineHeight: '16px',
            }}
          >
            Enterprise Edition
          </p>
        </div>
      )}
    </Link>
  )
}

export default SideLogo
