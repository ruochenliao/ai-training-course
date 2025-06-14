import React, { useEffect, useRef, useState } from 'react'
import { CloseOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useTagsStore, type TagItem } from '../../store/tags'
import ScrollX, { type ScrollXRef } from '../common/ScrollX'
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
  const scrollXRef = useRef<ScrollXRef>(null)
  const tabRefs = useRef<(HTMLElement | null)[]>([])

  const { tags, activeTag, removeTag, setActiveTag } = useTagsStore()

  // 右键菜单状态 - 对应Vue版本的 contextMenuOption
  const [contextMenuOption, setContextMenuOption] = useState({
    show: false,
    x: 0,
    y: 0,
    currentPath: '',
  })

  // 监听激活标签变化，自动滚动 - 对应Vue版本的 watch(() => tagsStore.activeIndex)
  useEffect(() => {
    const activeIndex = tags.findIndex((tag) => tag.path === activeTag)
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
  const handleTagClose = (e: React.MouseEvent, path: string) => {
    e.stopPropagation()
    removeTag(path)
  }

  // 右键菜单处理 - 对应Vue版本的 handleContextMenu
  const handleContextMenu = (e: React.MouseEvent, tag: TagItem) => {
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
      setContextMenuOption((prev) => ({ ...prev, show: true }))
    }, 0)
  }

  return (
    <div className='app-tags'>
      <ScrollX ref={scrollXRef} className='h-full'>
        {tags.map((tag, index) => (
          <div
            key={tag.path}
            ref={(el) => (tabRefs.current[index] = el)}
            className={`app-tag ${activeTag === tag.path ? 'active' : ''}`}
            onClick={() => handleTagClick(tag.path)}
            onContextMenu={(e) => handleContextMenu(e, tag)}
          >
            <span>{tag.title}</span>
            {tags.length > 1 && tag.closable && (
              <span className='app-tag-close' onClick={(e) => handleTagClose(e, tag.path)}>
                <CloseOutlined style={{ fontSize: '10px' }} />
              </span>
            )}
          </div>
        ))}
      </ScrollX>

      {/* 右键菜单 - 对应Vue版本的 ContextMenu */}
      {contextMenuOption.show && (
        <ContextMenu
          show={contextMenuOption.show}
          currentPath={contextMenuOption.currentPath}
          x={contextMenuOption.x}
          y={contextMenuOption.y}
          onClose={() => setContextMenuOption((prev) => ({ ...prev, show: false }))}
        />
      )}
    </div>
  )
}

export default TagsView
