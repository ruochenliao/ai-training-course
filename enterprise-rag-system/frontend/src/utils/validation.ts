// 验证工具函数

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

  if (idCard.length === 18) {
    if (!idCard18Regex.test(idCard)) return false

    // 验证校验码
    const weights = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
    const checkCodes = ['1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2']

    let sum = 0
    for (let i = 0; i < 17; i++) {
      sum += parseInt(idCard[i]) * weights[i]
    }

    const checkCode = checkCodes[sum % 11]
    return idCard[17].toUpperCase() === checkCode
  } else if (idCard.length === 15) {
    return idCard15Regex.test(idCard)
  }

  return false
}

/**
 * 验证密码强度
 */
export const validatePassword = (
  password: string,
  options: {
    minLength?: number
    requireUppercase?: boolean
    requireLowercase?: boolean
    requireNumbers?: boolean
    requireSpecialChars?: boolean
  } = {}
): { isValid: boolean; errors: string[] } => {
  const {
    minLength = 8,
    requireUppercase = true,
    requireLowercase = true,
    requireNumbers = true,
    requireSpecialChars = true,
  } = options

  const errors: string[] = []

  if (password.length < minLength) {
    errors.push(`密码长度至少${minLength}位`)
  }

  if (requireUppercase && !/[A-Z]/.test(password)) {
    errors.push('密码必须包含大写字母')
  }

  if (requireLowercase && !/[a-z]/.test(password)) {
    errors.push('密码必须包含小写字母')
  }

  if (requireNumbers && !/\d/.test(password)) {
    errors.push('密码必须包含数字')
  }

  if (requireSpecialChars && !/[^a-zA-Z\d]/.test(password)) {
    errors.push('密码必须包含特殊字符')
  }

  return {
    isValid: errors.length === 0,
    errors,
  }
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
  const ipv4Regex = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/
  const ipv6Regex = /^(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$/

  return ipv4Regex.test(ip) || ipv6Regex.test(ip)
}

/**
 * 验证银行卡号格式
 */
export const validateBankCard = (cardNumber: string): boolean => {
  const cleaned = cardNumber.replace(/\D/g, '')

  // 银行卡号长度通常在13-19位之间
  if (cleaned.length < 13 || cleaned.length > 19) {
    return false
  }

  // Luhn算法验证
  let sum = 0
  let isEven = false

  for (let i = cleaned.length - 1; i >= 0; i--) {
    let digit = parseInt(cleaned[i])

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
 * 验证中文姓名格式
 */
export const validateChineseName = (name: string): boolean => {
  const chineseNameRegex = /^[\u4e00-\u9fa5]{2,10}$/
  return chineseNameRegex.test(name)
}

/**
 * 验证数字范围
 */
export const validateNumberRange = (value: number, min?: number, max?: number): boolean => {
  if (min !== undefined && value < min) return false
  if (max !== undefined && value > max) return false
  return true
}

/**
 * 验证字符串长度
 */
export const validateStringLength = (str: string, min?: number, max?: number): boolean => {
  if (min !== undefined && str.length < min) return false
  if (max !== undefined && str.length > max) return false
  return true
}

/**
 * 验证文件类型
 */
export const validateFileType = (file: File, allowedTypes: string[]): boolean => {
  return allowedTypes.includes(file.type)
}

/**
 * 验证文件大小
 */
export const validateFileSize = (
  file: File,
  maxSize: number // 字节
): boolean => {
  return file.size <= maxSize
}

/**
 * 验证日期格式
 */
export const validateDate = (dateString: string): boolean => {
  const date = new Date(dateString)
  return !isNaN(date.getTime())
}

/**
 * 验证日期范围
 */
export const validateDateRange = (date: Date, minDate?: Date, maxDate?: Date): boolean => {
  if (minDate && date < minDate) return false
  if (maxDate && date > maxDate) return false
  return true
}

/**
 * 验证JSON格式
 */
export const validateJson = (jsonString: string): boolean => {
  try {
    JSON.parse(jsonString)
    return true
  } catch {
    return false
  }
}

/**
 * 验证正则表达式
 */
export const validateRegex = (pattern: string): boolean => {
  try {
    new RegExp(pattern)
    return true
  } catch {
    return false
  }
}

/**
 * 验证颜色值（hex）
 */
export const validateHexColor = (color: string): boolean => {
  const hexColorRegex = /^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$/
  return hexColorRegex.test(color)
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
 * 验证QQ号格式
 */
export const validateQQ = (qq: string): boolean => {
  const qqRegex = /^[1-9][0-9]{4,10}$/
  return qqRegex.test(qq)
}

/**
 * 验证微信号格式
 */
export const validateWechat = (wechat: string): boolean => {
  // 微信号：6-20位，字母、数字、下划线、减号，字母开头
  const wechatRegex = /^[a-zA-Z][a-zA-Z0-9_-]{5,19}$/
  return wechatRegex.test(wechat)
}

/**
 * 验证车牌号格式
 */
export const validateLicensePlate = (plate: string): boolean => {
  // 普通车牌号
  const normalPlateRegex =
    /^[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼使领][A-Z][A-Z0-9]{4}[A-Z0-9挂学警港澳]$/
  // 新能源车牌号
  const newEnergyPlateRegex = /^[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼使领][A-Z][A-Z0-9]{5}$/

  return normalPlateRegex.test(plate) || newEnergyPlateRegex.test(plate)
}

/**
 * 验证统一社会信用代码
 */
export const validateSocialCreditCode = (code: string): boolean => {
  const socialCreditRegex = /^[0-9A-HJ-NPQRTUWXY]{2}\d{6}[0-9A-HJ-NPQRTUWXY]{10}$/
  return socialCreditRegex.test(code)
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
