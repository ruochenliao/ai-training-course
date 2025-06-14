import React from 'react'
import type {MenuProps} from 'antd'
import {Button, Dropdown} from 'antd'
import {Icon} from '@iconify/react'
import {useTranslation} from 'react-i18next'
import {useAppStore} from '../../store/app'

/**
 * 语言切换组件 - 对应Vue版本的Languages.vue
 *
 * 功能特性：
 * 1. 支持多语言切换
 * 2. 下拉菜单选择语言
 * 3. 国际化支持
 */
const Languages: React.FC = () => {
  const { i18n } = useTranslation()
  const { language, setLanguage } = useAppStore()

  const languageOptions: MenuProps['items'] = [
    {
      key: 'zh-CN',
      label: '简体中文',
      icon: <Icon icon='emojione:flag-for-china' />,
    },
    {
      key: 'en',
      label: 'English',
      icon: <Icon icon='emojione:flag-for-united-states' />,
    },
  ]

  const handleLanguageChange = ({ key }: { key: string }) => {
    setLanguage(key)
    i18n.changeLanguage(key)
  }

  const currentLanguage = languageOptions.find((item) => item?.key === language)

  return (
    <Dropdown
      menu={{
        items: languageOptions,
        onClick: handleLanguageChange,
      }}
      placement='bottomRight'
    >
      <Button type='text' icon={<Icon icon='mdi:translate' style={{ fontSize: '16px' }} />} className='flex-center'>
        {currentLanguage?.label}
      </Button>
    </Dropdown>
  )
}

export default Languages
