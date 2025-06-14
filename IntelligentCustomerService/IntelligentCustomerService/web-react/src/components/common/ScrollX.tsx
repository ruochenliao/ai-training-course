import React, {forwardRef, useEffect, useImperativeHandle, useRef} from 'react'
import {useTheme} from '../../contexts/ThemeContext'
import {cn} from '../../utils'

interface ScrollXProps {
  children: React.ReactNode
  className?: string
  style?: React.CSSProperties
  showScrollbar?: boolean
}

export interface ScrollXRef {
  handleScroll: (x: number, width: number) => void
}

/**
 * 水平滚动容器组件
 * 对应Vue版本的ScrollX.vue
 */
const ScrollX = forwardRef<ScrollXRef, ScrollXProps>(({ children, className, style, showScrollbar = true }, ref) => {
  const { isDark } = useTheme()
  const scrollRef = useRef<HTMLDivElement>(null)

  useImperativeHandle(ref, () => ({
    handleScroll: (x: number) => {
      if (scrollRef.current) {
        const container = scrollRef.current
        const containerWidth = container.clientWidth
        const scrollLeft = container.scrollLeft

        // 计算是否需要滚动
        if (x < scrollLeft || x > scrollLeft + containerWidth) {
          container.scrollTo({
            left: x - containerWidth / 2,
            behavior: 'smooth',
          })
        }
      }
    },
  }))

  useEffect(() => {
    const scrollElement = scrollRef.current
    if (!scrollElement) return

    // 鼠标滚轮水平滚动
    const handleWheel = (e: WheelEvent) => {
      if (e.deltaY !== 0) {
        e.preventDefault()
        scrollElement.scrollLeft += e.deltaY
      }
    }

    scrollElement.addEventListener('wheel', handleWheel, { passive: false })

    return () => {
      scrollElement.removeEventListener('wheel', handleWheel)
    }
  }, [])

  return (
    <div
      ref={scrollRef}
      className={cn('overflow-x-auto', !showScrollbar && 'scrollbar-hide', isDark ? 'custom-scroll-dark' : 'custom-scroll-light', className)}
      style={style}
    >
      {children}
    </div>
  )
})

ScrollX.displayName = 'ScrollX'

export default ScrollX
