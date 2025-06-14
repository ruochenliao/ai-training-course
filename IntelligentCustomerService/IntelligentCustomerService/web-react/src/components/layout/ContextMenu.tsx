import React, { useEffect } from 'react'
import { Menu } from 'antd'
import { useNavigate } from 'react-router-dom'
import { useTagsStore } from '../../store/tags'
import { useAppStore } from '../../store/app'

interface ContextMenuProps {
  show: boolean
  currentPath: string
  x: number
  y: number
  onClose: () => void
}

/**
 * 右键菜单组件 - 对应Vue版本的ContextMenu.vue
 *
 * 功能特性：
 * 1. 关闭当前标签
 * 2. 关闭其他标签
 * 3. 关闭左侧标签
 * 4. 关闭右侧标签
 * 5. 关闭所有标签
 */
const ContextMenu: React.FC<ContextMenuProps> = ({ show, currentPath, x, y, onClose }) => {
  const navigate = useNavigate()
  const { tags, removeTag, removeOtherTags, removeLeftTags, removeRightTags, removeAllTags } = useTagsStore()
  const { setReloading } = useAppStore()

  // 点击外部关闭菜单
  useEffect(() => {
    const handleClickOutside = () => {
      onClose()
    }

    if (show) {
      document.addEventListener('click', handleClickOutside)
      return () => {
        document.removeEventListener('click', handleClickOutside)
      }
    }
  }, [show, onClose])

  if (!show) return null

  const currentTag = tags.find((tag) => tag.path === currentPath)
  const currentIndex = tags.findIndex((tag) => tag.path === currentPath)

  const menuItems = [
    {
      key: 'refresh',
      label: '刷新',
      onClick: () => {
        setReloading(true)
        setTimeout(() => setReloading(false), 100)
        onClose()
      },
    },
    {
      key: 'close',
      label: '关闭',
      disabled: !currentTag || tags.length <= 1,
      onClick: () => {
        if (currentTag && tags.length > 1) {
          removeTag(currentPath)
        }
        onClose()
      },
    },
    {
      key: 'closeOthers',
      label: '关闭其他',
      disabled: tags.length <= 1,
      onClick: () => {
        removeOtherTags(currentPath)
        navigate(currentPath)
        onClose()
      },
    },
    {
      key: 'closeLeft',
      label: '关闭左侧',
      disabled: currentIndex <= 0,
      onClick: () => {
        removeLeftTags(currentPath)
        onClose()
      },
    },
    {
      key: 'closeRight',
      label: '关闭右侧',
      disabled: currentIndex >= tags.length - 1,
      onClick: () => {
        removeRightTags(currentPath)
        onClose()
      },
    },
    {
      key: 'closeAll',
      label: '关闭所有',
      onClick: () => {
        removeAllTags()
        navigate('/dashboard')
        onClose()
      },
    },
  ]

  return (
    <div
      className='fixed z-50'
      style={{
        left: x,
        top: y,
      }}
      onClick={(e) => e.stopPropagation()}
    >
      <Menu items={menuItems} className='shadow-lg border rounded' style={{ minWidth: 120 }} />
    </div>
  )
}

export default ContextMenu
