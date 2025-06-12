import React, { useEffect, useRef, useState } from 'react'
import { Tag } from 'antd'
import { useLocation, useNavigate } from 'react-router-dom'
import { useTagsStore } from '../../store/tags'
import { useAppStore } from '../../store/app'
import ScrollX from '../common/ScrollX'
import ContextMenu from './ContextMenu'

/**
 * 标签页组件 - 对应Vue版本的tags/index.vue
 *
 * 功能特性：
 * 1. 基于路由的标签生成
 * 2. 标签可关闭（至少保留一个）
 * 3. 水平滚动支持
 * 4. 右键菜单操作
 * 5. 当前标签高亮
 * 6. 标签点击切换路由
 */

const TagsView: React.FC = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const scrollXRef = useRef<any>(null)
  const tabRefs = useRef<(HTMLElement | null)[]>([])

  const { tags, activeTag, removeTag, setActiveTag } = useTagsStore()
  const { setReloading } = useAppStore()

  // 右键菜单状态 - 对应Vue版本的 contextMenuOption
  const [contextMenuOption, setContextMenuOption] = useState({
    show: false,
    x: 0,
    y: 0,
    currentPath: '',
  })

  // 监听激活标签变化，自动滚动 - 对应Vue版本的 watch(() => tagsStore.activeIndex)
  useEffect(() => {
    const activeIndex = tags.findIndex(tag => tag.path === activeTag)
    if (activeIndex >= 0 && tabRefs.current[activeIndex] && scrollXRef.current) {
      const activeTabElement = tabRefs.current[activeIndex]
      if (activeTabElement) {
        const { offsetLeft: x, offsetWidth: width } = activeTabElement
        scrollXRef.current.handleScroll(x + width, width)
      }
    }
  }, [activeTag, tags])

  // 处理标签点击 - 对应Vue版本的 handleTagClick
  const handleTagClick = (path: string) => {
    setActiveTag(path)
    navigate(path)
  }

  // 处理标签关闭 - 对应Vue版本的 @close.stop
  const handleTagClose = (path: string) => {
    removeTag(path)
  }

  // 右键菜单处理 - 对应Vue版本的 handleContextMenu
  const handleContextMenu = (e: React.MouseEvent, tag: any) => {
    e.preventDefault()
    const { clientX, clientY } = e
    setContextMenuOption({
      show: false,
      x: clientX,
      y: clientY,
      currentPath: tag.path,
    })
    // 使用 setTimeout 确保先隐藏再显示
    setTimeout(() => {
      setContextMenuOption(prev => ({ ...prev, show: true }))
    }, 0)
  }

  return (
    <ScrollX
      ref={scrollXRef}
      className="bg-white dark:bg-dark"
    >
      {tags.map((tag, index) => (
        <Tag
          key={tag.path}
          ref={(el) => (tabRefs.current[index] = el)}
          className="mx-5 cursor-pointer rounded-4 px-15 hover:color-primary"
          color={activeTag === tag.path ? 'blue' : 'default'}
          closable={tags.length > 1}
          onClick={() => handleTagClick(tag.path)}
          onClose={() => handleTagClose(tag.path)}
          onContextMenu={(e) => handleContextMenu(e, tag)}
        >
          {tag.title}
        </Tag>
      ))}

      {/* 右键菜单 - 对应Vue版本的 ContextMenu */}
      {contextMenuOption.show && (
        <ContextMenu
          show={contextMenuOption.show}
          currentPath={contextMenuOption.currentPath}
          x={contextMenuOption.x}
          y={contextMenuOption.y}
          onClose={() => setContextMenuOption(prev => ({ ...prev, show: false }))}
        />
      )}
    </ScrollX>
  )
}

export default TagsView