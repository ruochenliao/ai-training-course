import React from 'react'
import {Button} from 'antd'
import {Icon} from '@iconify/react'

/**
 * GitHub链接组件 - 对应Vue版本的GithubSite.vue
 *
 * 功能特性：
 * 1. GitHub链接按钮
 * 2. 新窗口打开
 * 3. GitHub图标显示
 */
const GithubSite: React.FC = () => {
  const handleGithubClick = () => {
    window.open('https://github.com', '_blank')
  }

  return (
    <Button
      type='text'
      icon={<Icon icon='mdi:github' style={{ fontSize: '16px' }} />}
      onClick={handleGithubClick}
      className='flex-center'
      title='GitHub'
    />
  )
}

export default GithubSite
