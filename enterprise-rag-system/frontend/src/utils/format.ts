// 格式化工具函数

import { format, formatDistanceToNow, isValid, parseISO } from 'date-fns'
import { zhCN } from 'date-fns/locale'

/**
 * 格式化日期时间
 */
export const formatDateTime = (date: string | Date | number, pattern = 'yyyy-MM-dd HH:mm:ss'): string => {
  try {
    let dateObj: Date
    if (typeof date === 'string') {
      dateObj = parseISO(date)
    } else if (typeof date === 'number') {
      dateObj = new Date(date)
    } else {
      dateObj = date
    }

    if (!isValid(dateObj)) {
      return '无效日期'
    }

    return format(dateObj, pattern, { locale: zhCN })
  } catch {
    return '无效日期'
  }
}

/**
 * 格式化相对时间
 */
export const formatRelativeTime = (date: string | Date | number): string => {
  try {
    let dateObj: Date
    if (typeof date === 'string') {
      dateObj = parseISO(date)
    } else if (typeof date === 'number') {
      dateObj = new Date(date)
    } else {
      dateObj = date
    }

    if (!isValid(dateObj)) {
      return '无效日期'
    }

    return formatDistanceToNow(dateObj, { addSuffix: true, locale: zhCN })
  } catch {
    return '无效日期'
  }
}

/**
 * 格式化文件大小
 */
export const formatFileSize = (bytes: number, decimals = 2): string => {
  if (bytes === 0) return '0 B'

  const k = 1024
  const dm = decimals < 0 ? 0 : decimals
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']

  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i]
}

/**
 * 格式化数字
 */
export const formatNumber = (
  num: number,
  options: {
    precision?: number
    useGrouping?: boolean
    currency?: string
    percentage?: boolean
  } = {}
): string => {
  const { precision = 2, useGrouping = true, currency, percentage = false } = options

  if (percentage) {
    return (num * 100).toFixed(precision) + '%'
  }

  if (currency) {
    return new Intl.NumberFormat('zh-CN', {
      style: 'currency',
      currency,
      minimumFractionDigits: precision,
      maximumFractionDigits: precision,
    }).format(num)
  }

  return new Intl.NumberFormat('zh-CN', {
    useGrouping,
    minimumFractionDigits: precision,
    maximumFractionDigits: precision,
  }).format(num)
}

/**
 * 格式化大数字（K, M, B）
 */
export const formatLargeNumber = (num: number, precision = 1): string => {
  if (num >= 1e9) {
    return (num / 1e9).toFixed(precision) + 'B'
  }
  if (num >= 1e6) {
    return (num / 1e6).toFixed(precision) + 'M'
  }
  if (num >= 1e3) {
    return (num / 1e3).toFixed(precision) + 'K'
  }
  return num.toString()
}

/**
 * 格式化手机号
 */
export const formatPhone = (phone: string): string => {
  const cleaned = phone.replace(/\D/g, '')
  if (cleaned.length === 11) {
    return cleaned.replace(/(\d{3})(\d{4})(\d{4})/, '$1 $2 $3')
  }
  return phone
}

/**
 * 格式化身份证号
 */
export const formatIdCard = (idCard: string): string => {
  if (idCard.length === 18) {
    return idCard.replace(/(\d{6})(\d{8})(\d{4})/, '$1 $2 $3')
  }
  if (idCard.length === 15) {
    return idCard.replace(/(\d{6})(\d{6})(\d{3})/, '$1 $2 $3')
  }
  return idCard
}

/**
 * 格式化银行卡号
 */
export const formatBankCard = (cardNumber: string): string => {
  const cleaned = cardNumber.replace(/\D/g, '')
  return cleaned.replace(/(\d{4})(?=\d)/g, '$1 ')
}

/**
 * 格式化文本省略
 */
export const formatEllipsis = (text: string, maxLength: number): string => {
  if (text.length <= maxLength) return text
  return text.slice(0, maxLength) + '...'
}

/**
 * 格式化首字母大写
 */
export const formatCapitalize = (text: string): string => {
  return text.charAt(0).toUpperCase() + text.slice(1).toLowerCase()
}

/**
 * 格式化驼峰命名
 */
export const formatCamelCase = (text: string): string => {
  return text
    .replace(/[-_\s]+(.)?/g, (_, char) => (char ? char.toUpperCase() : ''))
    .replace(/^[A-Z]/, char => char.toLowerCase())
}

/**
 * 格式化短横线命名
 */
export const formatKebabCase = (text: string): string => {
  return text
    .replace(/([a-z])([A-Z])/g, '$1-$2')
    .replace(/[\s_]+/g, '-')
    .toLowerCase()
}

/**
 * 格式化下划线命名
 */
export const formatSnakeCase = (text: string): string => {
  return text
    .replace(/([a-z])([A-Z])/g, '$1_$2')
    .replace(/[\s-]+/g, '_')
    .toLowerCase()
}

/**
 * 格式化JSON
 */
export const formatJson = (obj: any, indent = 2): string => {
  try {
    return JSON.stringify(obj, null, indent)
  } catch {
    return '无效的JSON对象'
  }
}

/**
 * 格式化URL
 */
export const formatUrl = (url: string, baseUrl?: string): string => {
  try {
    if (url.startsWith('http://') || url.startsWith('https://')) {
      return url
    }
    if (baseUrl) {
      return new URL(url, baseUrl).toString()
    }
    return url
  } catch {
    return url
  }
}

/**
 * 格式化颜色值
 */
export const formatColor = (color: string): string => {
  // 移除空格并转换为小写
  const cleaned = color.replace(/\s/g, '').toLowerCase()

  // 如果是3位hex，转换为6位
  if (/^#[0-9a-f]{3}$/i.test(cleaned)) {
    return '#' + cleaned[1] + cleaned[1] + cleaned[2] + cleaned[2] + cleaned[3] + cleaned[3]
  }

  return cleaned
}

/**
 * 格式化CSS类名
 */
export const formatClassName = (...classes: (string | undefined | null | false)[]): string => {
  return classes.filter(Boolean).join(' ')
}

/**
 * 格式化查询参数
 */
export const formatQueryParams = (params: Record<string, any>): string => {
  const searchParams = new URLSearchParams()

  Object.entries(params).forEach(([key, value]) => {
    if (value !== null && value !== undefined && value !== '') {
      searchParams.append(key, String(value))
    }
  })

  const queryString = searchParams.toString()
  return queryString ? `?${queryString}` : ''
}

/**
 * 格式化HTML标签移除
 */
export const formatStripHtml = (html: string): string => {
  const div = document.createElement('div')
  div.innerHTML = html
  return div.textContent || div.innerText || ''
}

/**
 * 格式化高亮文本
 */
export const formatHighlight = (text: string, keyword: string): string => {
  if (!keyword) return text

  const regex = new RegExp(`(${keyword})`, 'gi')
  return text.replace(regex, '<mark>$1</mark>')
}

/**
 * 格式化密码强度
 */
export const formatPasswordStrength = (
  password: string
): {
  score: number
  level: 'weak' | 'medium' | 'strong' | 'very-strong'
  feedback: string[]
} => {
  let score = 0
  const feedback: string[] = []

  if (password.length >= 8) {
    score += 1
  } else {
    feedback.push('密码长度至少8位')
  }

  if (/[a-z]/.test(password)) score += 1
  else feedback.push('包含小写字母')

  if (/[A-Z]/.test(password)) score += 1
  else feedback.push('包含大写字母')

  if (/\d/.test(password)) score += 1
  else feedback.push('包含数字')

  if (/[^a-zA-Z\d]/.test(password)) score += 1
  else feedback.push('包含特殊字符')

  let level: 'weak' | 'medium' | 'strong' | 'very-strong'
  if (score <= 2) level = 'weak'
  else if (score === 3) level = 'medium'
  else if (score === 4) level = 'strong'
  else level = 'very-strong'

  return { score, level, feedback }
}
