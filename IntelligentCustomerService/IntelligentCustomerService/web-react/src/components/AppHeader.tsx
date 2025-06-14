import React from 'react'
import type {MenuProps} from 'antd'
import {Avatar, Button, Dropdown, Layout, Space, Typography} from 'antd'
import {
    BulbOutlined,
    LogoutOutlined,
    MenuFoldOutlined,
    MenuUnfoldOutlined,
    SettingOutlined,
    TranslationOutlined,
    UserOutlined,
} from '@ant-design/icons'
import {useTheme} from '../contexts/ThemeContext'
import ThemeSettings from './ThemeSettings'
import {useTranslation} from 'react-i18next'

const { Header } = Layout
const { Text } = Typography

interface AppHeaderProps {
  collapsed: boolean
  toggle: () => void
  onLogout?: () => void
}

const AppHeader: React.FC<AppHeaderProps> = ({ collapsed, toggle, onLogout }) => {
  const { isDark, toggleTheme } = useTheme()
  const { t, i18n } = useTranslation()

  const changeLanguage = () => {
    const currentLang = i18n.language
    const newLang = currentLang === 'zh-CN' ? 'en-US' : 'zh-CN'
    i18n.changeLanguage(newLang)
  }

  const userMenuProps: MenuProps = {
    items: [
      {
        key: '1',
        icon: <SettingOutlined />,
        label: t('header.settings'),
      },
      {
        key: '2',
        icon: <LogoutOutlined />,
        label: t('header.logout'),
        onClick: onLogout,
      },
    ],
  }

  return (
    <Header
      className='bg-white dark:bg-gray-800 px-4 flex justify-between items-center border-b border-gray-200 dark:border-gray-700'
      style={{
        height: '64px',
        position: 'sticky',
        top: 0,
        zIndex: 1,
        width: '100%',
        padding: '0 16px',
      }}
    >
      <div className='flex items-center'>
        <Button type='text' icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />} onClick={toggle} className='mr-3' />
        <Text strong className='text-lg hidden md:block'>
          {t('dashboard.title')}
        </Text>
      </div>

      <Space size='middle'>
        <Button type='text' icon={<TranslationOutlined />} onClick={changeLanguage} className='flex items-center'>
          <span className='ml-1 hidden sm:inline'>{i18n.language === 'zh-CN' ? 'EN' : '中'}</span>
        </Button>

        <Button type='text' icon={<BulbOutlined />} onClick={toggleTheme} className='flex items-center'>
          <span className='ml-1 hidden sm:inline'>{isDark ? t('theme.light') : t('theme.dark')}</span>
        </Button>

        <ThemeSettings>
          <Button type='text' icon={<SettingOutlined />} className='flex items-center'>
            <span className='ml-1 hidden sm:inline'>{t('theme.settings')}</span>
          </Button>
        </ThemeSettings>

        <Dropdown menu={userMenuProps} placement='bottomRight'>
          <div className='cursor-pointer flex items-center'>
            <Avatar icon={<UserOutlined />} />
            <span className='ml-2 hidden md:inline'>{t('header.profile')}</span>
          </div>
        </Dropdown>
      </Space>
    </Header>
  )
}

export default AppHeader
