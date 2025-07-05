// 企业级表单验证工具函数

import type { FormRules, FormItemRule } from 'element-plus'

/**
 * 验证邮箱格式
 */
export const validateEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

/**
 * 验证手机号格式（中国大陆）
 */
export const validatePhone = (phone: string): boolean => {
  const phoneRegex = /^1[3-9]\d{9}$/
  return phoneRegex.test(phone)
}

/**
 * 验证身份证号格式
 */
export const validateIdCard = (idCard: string): boolean => {
  // 18位身份证号正则
  const idCard18Regex = /^[1-9]\d{5}(18|19|20)\d{2}((0[1-9])|(1[0-2]))(([0-2][1-9])|10|20|30|31)\d{3}[0-9Xx]$/
  // 15位身份证号正则
  const idCard15Regex = /^[1-9]\d{5}\d{2}((0[1-9])|(1[0-2]))(([0-2][1-9])|10|20|30|31)\d{3}$/
  
  return idCard18Regex.test(idCard) || idCard15Regex.test(idCard)
}

/**
 * 验证密码强度
 */
export const validatePassword = (password: string): { isValid: boolean; strength: 'weak' | 'medium' | 'strong'; message: string } => {
  if (password.length < 6) {
    return { isValid: false, strength: 'weak', message: '密码长度至少6位' }
  }
  
  if (password.length < 8) {
    return { isValid: true, strength: 'weak', message: '密码强度较弱，建议至少8位' }
  }
  
  const hasLower = /[a-z]/.test(password)
  const hasUpper = /[A-Z]/.test(password)
  const hasNumber = /\d/.test(password)
  const hasSpecial = /[!@#$%^&*(),.?":{}|<>]/.test(password)
  
  const score = [hasLower, hasUpper, hasNumber, hasSpecial].filter(Boolean).length
  
  if (score >= 3) {
    return { isValid: true, strength: 'strong', message: '密码强度很强' }
  } else if (score >= 2) {
    return { isValid: true, strength: 'medium', message: '密码强度中等' }
  } else {
    return { isValid: true, strength: 'weak', message: '密码强度较弱，建议包含大小写字母、数字和特殊字符' }
  }
}

/**
 * 验证用户名格式
 */
export const validateUsername = (username: string): boolean => {
  // 用户名：3-20位，字母、数字、下划线，不能以数字开头
  const usernameRegex = /^[a-zA-Z_][a-zA-Z0-9_]{2,19}$/
  return usernameRegex.test(username)
}

/**
 * 验证URL格式
 */
export const validateUrl = (url: string): boolean => {
  try {
    new URL(url)
    return true
  } catch {
    return false
  }
}

/**
 * 验证IP地址格式
 */
export const validateIP = (ip: string): boolean => {
  const ipRegex = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/
  return ipRegex.test(ip)
}

/**
 * 验证端口号
 */
export const validatePort = (port: string | number): boolean => {
  const portNum = typeof port === 'string' ? parseInt(port, 10) : port
  return !isNaN(portNum) && portNum >= 1 && portNum <= 65535
}

/**
 * 验证中文姓名
 */
export const validateChineseName = (name: string): boolean => {
  const chineseNameRegex = /^[\u4e00-\u9fa5]{2,10}$/
  return chineseNameRegex.test(name)
}

/**
 * 验证银行卡号
 */
export const validateBankCard = (cardNumber: string): boolean => {
  // 移除空格和连字符
  const cleanNumber = cardNumber.replace(/[\s-]/g, '')
  
  // 检查是否为纯数字且长度在13-19位之间
  if (!/^\d{13,19}$/.test(cleanNumber)) {
    return false
  }
  
  // Luhn算法验证
  let sum = 0
  let isEven = false
  
  for (let i = cleanNumber.length - 1; i >= 0; i--) {
    let digit = parseInt(cleanNumber.charAt(i), 10)
    
    if (isEven) {
      digit *= 2
      if (digit > 9) {
        digit -= 9
      }
    }
    
    sum += digit
    isEven = !isEven
  }
  
  return sum % 10 === 0
}

/**
 * 通用验证器
 */
export const createValidator = (
  rules: Array<{
    test: (value: any) => boolean
    message: string
  }>
) => {
  return (value: any): { isValid: boolean; errors: string[] } => {
    const errors: string[] = []

    for (const rule of rules) {
      if (!rule.test(value)) {
        errors.push(rule.message)
      }
    }

    return {
      isValid: errors.length === 0,
      errors,
    }
  }
}

/**
 * 表单验证器
 */
export const validateForm = (
  data: Record<string, any>,
  rules: Record<
    string,
    Array<{
      test: (value: any) => boolean
      message: string
    }>
  >
): { isValid: boolean; errors: Record<string, string[]> } => {
  const errors: Record<string, string[]> = {}

  for (const [field, fieldRules] of Object.entries(rules)) {
    const value = data[field]
    const fieldErrors: string[] = []

    for (const rule of fieldRules) {
      if (!rule.test(value)) {
        fieldErrors.push(rule.message)
      }
    }

    if (fieldErrors.length > 0) {
      errors[field] = fieldErrors
    }
  }

  return {
    isValid: Object.keys(errors).length === 0,
    errors,
  }
}

// ==================== Element Plus 验证规则库 ====================

/**
 * 必填验证规则
 */
export const requiredRule = (message: string = '此字段为必填项'): FormItemRule => ({
  required: true,
  message,
  trigger: 'blur'
})

/**
 * 邮箱验证规则
 */
export const emailRule = (required: boolean = true): FormItemRule[] => {
  const rules: FormItemRule[] = []
  
  if (required) {
    rules.push(requiredRule('请输入邮箱地址'))
  }
  
  rules.push({
    validator: (rule, value, callback) => {
      if (!value && !required) {
        callback()
        return
      }
      if (!validateEmail(value)) {
        callback(new Error('请输入正确的邮箱格式'))
      } else {
        callback()
      }
    },
    trigger: 'blur'
  })
  
  return rules
}

/**
 * 手机号验证规则
 */
export const phoneRule = (required: boolean = true): FormItemRule[] => {
  const rules: FormItemRule[] = []
  
  if (required) {
    rules.push(requiredRule('请输入手机号'))
  }
  
  rules.push({
    validator: (rule, value, callback) => {
      if (!value && !required) {
        callback()
        return
      }
      if (!validatePhone(value)) {
        callback(new Error('请输入正确的手机号格式'))
      } else {
        callback()
      }
    },
    trigger: 'blur'
  })
  
  return rules
}

/**
 * 密码验证规则
 */
export const passwordRule = (minLength: number = 6, maxLength: number = 50): FormItemRule[] => [
  requiredRule('请输入密码'),
  {
    min: minLength,
    max: maxLength,
    message: `密码长度在 ${minLength} 到 ${maxLength} 个字符`,
    trigger: 'blur'
  },
  {
    validator: (rule, value, callback) => {
      const result = validatePassword(value)
      if (!result.isValid) {
        callback(new Error(result.message))
      } else {
        callback()
      }
    },
    trigger: 'blur'
  }
]

/**
 * 用户名验证规则
 */
export const usernameRule = (minLength: number = 3, maxLength: number = 20): FormItemRule[] => [
  requiredRule('请输入用户名'),
  {
    min: minLength,
    max: maxLength,
    message: `用户名长度在 ${minLength} 到 ${maxLength} 个字符`,
    trigger: 'blur'
  },
  {
    validator: (rule, value, callback) => {
      if (!validateUsername(value)) {
        callback(new Error('用户名只能包含字母、数字和下划线，且不能以数字开头'))
      } else {
        callback()
      }
    },
    trigger: 'blur'
  }
]

/**
 * URL验证规则
 */
export const urlRule = (required: boolean = true): FormItemRule[] => {
  const rules: FormItemRule[] = []
  
  if (required) {
    rules.push(requiredRule('请输入URL地址'))
  }
  
  rules.push({
    validator: (rule, value, callback) => {
      if (!value && !required) {
        callback()
        return
      }
      if (!validateUrl(value)) {
        callback(new Error('请输入正确的URL格式'))
      } else {
        callback()
      }
    },
    trigger: 'blur'
  })
  
  return rules
}

/**
 * 长度验证规则
 */
export const lengthRule = (min: number, max: number, message?: string): FormItemRule => ({
  min,
  max,
  message: message || `长度在 ${min} 到 ${max} 个字符`,
  trigger: 'blur'
})

/**
 * 数字验证规则
 */
export const numberRule = (min?: number, max?: number): FormItemRule[] => {
  const rules: FormItemRule[] = [
    {
      type: 'number',
      message: '请输入数字',
      trigger: 'blur'
    }
  ]
  
  if (min !== undefined || max !== undefined) {
    rules.push({
      validator: (rule, value, callback) => {
        if (min !== undefined && value < min) {
          callback(new Error(`数值不能小于 ${min}`))
        } else if (max !== undefined && value > max) {
          callback(new Error(`数值不能大于 ${max}`))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    })
  }
  
  return rules
}

/**
 * 常用表单验证规则集合
 */
export const commonRules = {
  required: requiredRule,
  email: emailRule,
  phone: phoneRule,
  password: passwordRule,
  username: usernameRule,
  url: urlRule,
  length: lengthRule,
  number: numberRule
}
