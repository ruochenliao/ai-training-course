'use client'

import { useState } from 'react'
import Link from 'next/link'
import Image from 'next/image'
import { motion } from 'framer-motion'

export default function Register() {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [step, setStep] = useState(1)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    
    // 模拟API调用
    setTimeout(() => {
      setIsLoading(false)
      if (step === 1) {
        setStep(2)
      } else {
        // 实际项目中这里应该重定向到用户仪表盘
        window.location.href = '/dashboard'
      }
    }, 1500)
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[var(--background)] p-4">
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-bl from-white via-blue-50 to-purple-50 dark:from-gray-900 dark:via-gray-900 dark:to-purple-950"></div>
        <div className="absolute right-1/4 top-0 h-96 w-96 rounded-full bg-gradient-to-tr from-purple-100 to-purple-50 blur-3xl dark:from-purple-900/30 dark:to-purple-900/10"></div>
        <div className="absolute left-1/4 bottom-0 h-96 w-96 rounded-full bg-gradient-to-tr from-blue-100 to-blue-50 blur-3xl dark:from-blue-900/30 dark:to-blue-900/10"></div>
      </div>
      
      <div className="relative">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="mx-auto w-full max-w-md overflow-hidden rounded-2xl bg-white/80 p-8 shadow-xl backdrop-blur-md dark:bg-gray-800/80"
        >
          <div className="mb-8 text-center">
            <Link href="/" className="inline-block">
              <div className="mb-2 flex items-center justify-center">
                <Image 
                  src="/logo.svg" 
                  alt="但问智能体"
                  width={40}
                  height={40}
                  className="mr-2"
                  onError={(e) => {
                    // 如果图片不存在，显示文本logo
                    e.currentTarget.style.display = 'none'
                  }}
                />
                <span className="text-xl font-bold">但问智能体</span>
              </div>
            </Link>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">创建您的账户</h1>
            <p className="mt-2 text-sm text-gray-600 dark:text-gray-300">
              {step === 1 ? '注册一个新账户，体验AI智能体的强大功能' : '完善您的账户信息，开始使用'}
            </p>
          </div>
          
          {step === 1 ? (
            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700 dark:text-gray-200">
                  电子邮箱
                </label>
                <div className="mt-1">
                  <input
                    id="email"
                    name="email"
                    type="email"
                    autoComplete="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="gemini-input w-full"
                    placeholder="输入您的邮箱"
                  />
                </div>
              </div>

              <div>
                <label htmlFor="password" className="block text-sm font-medium text-gray-700 dark:text-gray-200">
                  密码
                </label>
                <div className="mt-1">
                  <input
                    id="password"
                    name="password"
                    type="password"
                    autoComplete="new-password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="gemini-input w-full"
                    placeholder="设置一个安全的密码"
                  />
                  <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                    密码长度至少为8位，包含字母和数字
                  </p>
                </div>
              </div>

              <div className="flex items-center">
                <input
                  id="terms"
                  name="terms"
                  type="checkbox"
                  required
                  className="h-4 w-4 rounded border-gray-300 text-[var(--primary)] focus:ring-[var(--primary)]"
                />
                <label htmlFor="terms" className="ml-2 block text-sm text-gray-600 dark:text-gray-300">
                  我已阅读并同意{' '}
                  <Link href="/terms" className="font-medium text-[var(--primary)] hover:text-blue-600">
                    使用条款
                  </Link>
                  {' '}和{' '}
                  <Link href="/privacy" className="font-medium text-[var(--primary)] hover:text-blue-600">
                    隐私政策
                  </Link>
                </label>
              </div>

              <div>
                <button
                  type="submit"
                  disabled={isLoading}
                  className="gemini-button-primary w-full"
                >
                  {isLoading ? (
                    <span className="flex items-center justify-center">
                      <svg className="mr-2 h-4 w-4 animate-spin text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      处理中...
                    </span>
                  ) : (
                    '下一步'
                  )}
                </button>
              </div>
            </form>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-gray-700 dark:text-gray-200">
                  姓名
                </label>
                <div className="mt-1">
                  <input
                    id="name"
                    name="name"
                    type="text"
                    autoComplete="name"
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="gemini-input w-full"
                    placeholder="您的姓名"
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-200">
                  选择您感兴趣的领域
                </label>
                <div className="mt-2 grid grid-cols-2 gap-2">
                  {['智能客服', 'Text2SQL', '知识库问答', '文案创作'].map((item) => (
                    <div
                      key={item}
                      className="flex items-center rounded-lg border border-gray-300 p-3 hover:border-[var(--primary)] hover:bg-blue-50 dark:border-gray-600 dark:hover:bg-blue-900/20"
                    >
                      <input
                        type="checkbox"
                        id={`interest-${item}`}
                        name="interests"
                        value={item}
                        className="h-4 w-4 rounded border-gray-300 text-[var(--primary)] focus:ring-[var(--primary)]"
                      />
                      <label
                        htmlFor={`interest-${item}`}
                        className="ml-2 w-full cursor-pointer text-sm font-medium text-gray-700 dark:text-gray-200"
                      >
                        {item}
                      </label>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <button
                  type="submit"
                  disabled={isLoading}
                  className="gemini-button-primary w-full"
                >
                  {isLoading ? (
                    <span className="flex items-center justify-center">
                      <svg className="mr-2 h-4 w-4 animate-spin text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      注册中...
                    </span>
                  ) : (
                    '完成注册'
                  )}
                </button>
                <button
                  type="button"
                  onClick={() => setStep(1)}
                  className="mt-3 w-full text-center text-sm font-medium text-[var(--primary)] hover:text-blue-600"
                >
                  返回上一步
                </button>
              </div>
            </form>
          )}
          
          <p className="mt-8 text-center text-sm text-gray-600 dark:text-gray-400">
            已有账户？{' '}
            <Link href="/login" className="font-medium text-[var(--primary)] hover:text-blue-600">
              登录
            </Link>
          </p>
        </motion.div>
      </div>
    </div>
  )
} 