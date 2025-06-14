import React from 'react'
import type { MenuProps } from 'antd'
import { Avatar, Dropdown, Modal } from 'antd'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Icon } from '@iconify/react'
import { useAuthStore } from '../../store/auth'

/**
 * 用户头像组件 - 对应Vue版本的UserAvatar.vue
 *
 * 功能特性：
 * 1. 显示用户头像和姓名
 * 2. 下拉菜单（个人资料、退出登录）
 * 3. 退出确认对话框
 * 4. 国际化支持
 */
const UserAvatar: React.FC = () => {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const { user, logout } = useAuthStore()

  const handleMenuClick = ({ key }: { key: string }) => {
    if (key === 'profile') {
      navigate('/dashboard/profile')
    } else if (key === 'frontend') {
      navigate('/chat')
    } else if (key === 'logout') {
      Modal.confirm({
        title: t('header.label_logout_dialog_title', '确认退出'),
        content: t('header.text_logout_confirm', '确定要退出登录吗？'),
        onOk: () => {
          logout()
          // 这里可以添加成功提示
          // message.success(t('header.text_logout_success', '退出成功'))
        },
      })
    }
  }

  const menuItems: MenuProps['items'] = [
    {
      key: 'profile',
      label: t('header.label_profile', '个人资料'),
      icon: <Icon icon='mdi:account-arrow-right-outline' style={{ fontSize: '14px' }} />,
    },
    {
      key: 'frontend',
      label: '前往前台',
      icon: <Icon icon='mdi:chat-outline' style={{ fontSize: '14px' }} />,
    },
    {
      key: 'logout',
      label: t('header.label_logout', '退出登录'),
      icon: <Icon icon='mdi:exit-to-app' style={{ fontSize: '14px' }} />,
    },
  ]

  return (
    <Dropdown
      menu={{
        items: menuItems,
        onClick: handleMenuClick,
      }}
      placement='bottomRight'
    >
      <div className='flex cursor-pointer items-center'>
        <Avatar src={user?.avatar} size={35} className='mr-10' />
        <span>{user?.username || '用户'}</span>
      </div>
    </Dropdown>
  )
}

export default UserAvatar
