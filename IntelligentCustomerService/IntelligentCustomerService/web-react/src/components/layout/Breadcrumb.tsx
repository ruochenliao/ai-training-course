import React from 'react'
import {Breadcrumb as AntBreadcrumb} from 'antd'
import {HomeOutlined} from '@ant-design/icons'
import {Link, useLocation} from 'react-router-dom'
import {useAppStore} from '../../store/app'
import {cn} from '../../utils'

interface BreadcrumbItem {
  title: string
  path?: string
  icon?: React.ReactNode
}

const Breadcrumb: React.FC = () => {
  const location = useLocation()
  const { theme } = useAppStore()

  // 路径映射配置
  const pathMap: Record<string, BreadcrumbItem> = {
    '/': { title: '首页', icon: <HomeOutlined /> },
    '/dashboard': { title: '工作台', icon: <HomeOutlined /> },
    '/profile': { title: '个人资料' },
    '/system': { title: '系统管理' },
    '/system/users': { title: '用户管理' },
    '/system/roles': { title: '角色管理' },
    '/system/menus': { title: '菜单管理' },
    '/system/departments': { title: '部门管理' },
    '/system/apis': { title: 'API管理' },
    '/system/audit-logs': { title: '审计日志' },
  }

  // 生成面包屑项目
  const generateBreadcrumbItems = () => {
    const pathSegments = location.pathname.split('/').filter(Boolean)
    const items: any[] = []

    // 添加首页
    items.push({
      title: (
        <Link to="/dashboard" className={cn(
          "flex items-center",
          theme === 'dark' ? "text-gray-300 hover:text-white" : "text-gray-600 hover:text-blue-600"
        )}>
          <HomeOutlined className="mr-1" />
          工作台
        </Link>
      )
    })

    // 构建路径
    let currentPath = ''
    pathSegments.forEach((segment, index) => {
      currentPath += `/${segment}`
      const pathInfo = pathMap[currentPath]
      
      if (pathInfo) {
        const isLast = index === pathSegments.length - 1
        
        items.push({
          title: isLast ? (
            <span className={cn(
              "font-medium",
              theme === 'dark' ? "text-white" : "text-gray-800"
            )}>
              {pathInfo.icon && <span className="mr-1">{pathInfo.icon}</span>}
              {pathInfo.title}
            </span>
          ) : (
            <Link 
              to={currentPath} 
              className={cn(
                "flex items-center",
                theme === 'dark' ? "text-gray-300 hover:text-white" : "text-gray-600 hover:text-blue-600"
              )}
            >
              {pathInfo.icon && <span className="mr-1">{pathInfo.icon}</span>}
              {pathInfo.title}
            </Link>
          )
        })
      }
    })

    return items
  }

  const breadcrumbItems = generateBreadcrumbItems()

  // 如果只有首页，不显示面包屑
  if (breadcrumbItems.length <= 1) {
    return null
  }

  return (
    <AntBreadcrumb
      items={breadcrumbItems}
      className={cn(
        "text-sm",
        theme === 'dark' ? "text-gray-300" : "text-gray-600"
      )}
      separator={<span className={cn(
        theme === 'dark' ? "text-gray-500" : "text-gray-400"
      )}>></span>}
    />
  )
}

export default Breadcrumb