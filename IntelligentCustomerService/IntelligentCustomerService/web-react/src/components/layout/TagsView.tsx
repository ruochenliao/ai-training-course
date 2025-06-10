import React, {useEffect, useRef} from 'react'
import {Dropdown} from 'antd'
import {CloseCircleOutlined, CloseOutlined, ReloadOutlined} from '@ant-design/icons'
import {useLocation, useNavigate} from 'react-router-dom'
import {useTagsStore} from '../../store/tags'
import {useAppStore} from '../../store/app'
import {cn} from '../../utils'

const TagsView: React.FC = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const scrollRef = useRef<HTMLDivElement>(null)
  
  const { tags, removeTag, setActiveTag, removeOtherTags, removeAllTags } = useTagsStore()
  const { theme } = useAppStore()

  // 当前激活的标签
  const currentPath = location.pathname

  // 滚动到激活的标签
  useEffect(() => {
    if (scrollRef.current) {
      const activeElement = scrollRef.current.querySelector(`[data-path="${currentPath}"]`) as HTMLElement
      if (activeElement) {
        activeElement.scrollIntoView({
          behavior: 'smooth',
          block: 'nearest',
          inline: 'center'
        })
      }
    }
  }, [currentPath])

  // 处理标签点击
  const handleTagClick = (tag: any) => {
    setActiveTag(tag.key)
    navigate(tag.path)
  }

  // 处理标签关闭
  const handleTagClose = (e: React.MouseEvent, tag: any) => {
    e.stopPropagation()
    
    if (!tag.closable) return
    
    const tagIndex = tags.findIndex(t => t.key === tag.key)
    removeTag(tag.key)
    
    // 如果关闭的是当前激活的标签，需要跳转到其他标签
    if (tag.key === currentPath && tags.length > 1) {
      const nextTag = tags[tagIndex] || tags[tagIndex - 1]
      if (nextTag) {
        navigate(nextTag.path)
      }
    }
  }

  // 右键菜单项
  const getContextMenuItems = (tag: any) => [
    {
      key: 'refresh',
      icon: <ReloadOutlined />,
      label: '刷新',
      onClick: () => {
        // 刷新当前页面
        window.location.reload()
      }
    },
    {
      key: 'close',
      icon: <CloseOutlined />,
      label: '关闭',
      disabled: !tag.closable,
      onClick: () => handleTagClose({} as React.MouseEvent, tag)
    },
    {
      key: 'closeOthers',
      icon: <CloseCircleOutlined />,
      label: '关闭其他',
      onClick: () => {
        removeOtherTags(tag.key)
        if (tag.key !== currentPath) {
          navigate(tag.path)
        }
      }
    },
    {
      key: 'closeAll',
      icon: <CloseCircleOutlined />,
      label: '关闭所有',
      onClick: () => {
        removeAllTags()
        // 跳转到首页
        navigate('/dashboard')
      }
    }
  ]

  if (tags.length === 0) {
    return null
  }

  return (
    <div className={cn(
      "flex items-center px-4 py-2 border-b overflow-x-auto",
      theme === 'dark' 
        ? "bg-gray-800 border-gray-700" 
        : "bg-gray-50 border-gray-200"
    )}>
      <div 
        ref={scrollRef}
        className="flex items-center space-x-2 min-w-0 flex-1"
        style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
      >
        {tags.map((tag) => {
          const isActive = tag.path === currentPath
          
          return (
            <Dropdown
              key={tag.key}
              menu={{
                items: getContextMenuItems(tag)
              }}
              trigger={['contextMenu']}
            >
              <div
                data-path={tag.path}
                className={cn(
                  "flex items-center px-3 py-1 rounded cursor-pointer transition-all duration-200 whitespace-nowrap",
                  "hover:bg-blue-50 dark:hover:bg-blue-900/20",
                  isActive
                    ? "bg-blue-500 text-white shadow-sm"
                    : theme === 'dark'
                    ? "bg-gray-700 text-gray-300 hover:text-white"
                    : "bg-white text-gray-700 shadow-sm border border-gray-200"
                )}
                onClick={() => handleTagClick(tag)}
              >
                <span className="text-sm font-medium mr-1">
                  {tag.title}
                </span>
                {tag.closable && (
                  <CloseOutlined
                    className={cn(
                      "text-xs ml-1 hover:bg-black/10 rounded p-0.5 transition-colors",
                      isActive ? "text-white/80 hover:text-white" : ""
                    )}
                    onClick={(e) => handleTagClose(e, tag)}
                  />
                )}
              </div>
            </Dropdown>
          )
        })}
      </div>
      
      {/* 操作按钮 */}
      <div className="flex items-center ml-4 space-x-2">
        <Dropdown
          menu={{
            items: [
              {
                key: 'refresh',
                icon: <ReloadOutlined />,
                label: '刷新当前页',
                onClick: () => window.location.reload()
              },
              {
                key: 'closeOthers',
                icon: <CloseCircleOutlined />,
                label: '关闭其他标签',
                onClick: () => {
                  const currentTag = tags.find(tag => tag.path === currentPath)
                  if (currentTag) {
                    removeOtherTags(currentTag.key)
                  }
                }
              },
              {
                key: 'closeAll',
                icon: <CloseCircleOutlined />,
                label: '关闭所有标签',
                onClick: () => {
                  removeAllTags()
                  navigate('/dashboard')
                }
              }
            ]
          }}
          placement="bottomRight"
        >
          <div className={cn(
            "p-1 rounded cursor-pointer transition-colors",
            theme === 'dark'
              ? "hover:bg-gray-700 text-gray-400"
              : "hover:bg-gray-200 text-gray-600"
          )}>
            <CloseCircleOutlined className="text-sm" />
          </div>
        </Dropdown>
      </div>
    </div>
  )
}

export default TagsView