'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import Link from 'next/link'
import ContactDialog from '../components/ContactDialog'

// 技术背景组件
const TechBackground = () => (
  <div className="absolute inset-0 -z-10 overflow-hidden">
    <div className="wave-bg"></div>
    <div className="tech-grid absolute inset-0 opacity-10"></div>
    <div className="gemini-bg-dots absolute inset-0 opacity-10 z-0"></div>
    <div className="absolute top-0 right-0 h-[500px] w-[500px] -translate-y-1/2 translate-x-1/2 rounded-full bg-gradient-to-br from-blue-600 to-purple-600 opacity-20 blur-3xl"></div>
    <div className="absolute bottom-0 left-0 h-[500px] w-[500px] translate-y-1/2 -translate-x-1/2 rounded-full bg-gradient-to-tr from-indigo-400 to-cyan-500 opacity-20 blur-3xl"></div>
  </div>
);

// 浮动粒子效果组件
const FloatingParticles = () => (
  <div className="absolute inset-0 -z-5 overflow-hidden pointer-events-none">
    {Array.from({ length: 20 }).map((_, i) => (
      <div 
        key={i}
        className="particle absolute h-1 w-1 rounded-full bg-blue-500/40"
        style={{
          top: `${Math.random() * 100}%`,
          left: `${Math.random() * 100}%`,
          animationDelay: `${Math.random() * 5}s`,
          animationDuration: `${5 + Math.random() * 10}s`
        }}
      />
    ))}
  </div>
);

// 系统卡片数据
const systems = [
  {
    title: '智能客服系统',
    description: '基于 Agent + RAG 技术的新一代智能客服系统，提供多模态交互、知识增强和智能编排能力',
    icon: (
      <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
      </svg>
    ),
    href: '/customer-service',
    color: 'from-blue-500 to-cyan-500'
  },
  {
    title: '文案创作系统',
    description: '智能文案创作助手，支持多场景模板、知识增强生成、风格定制和质量保证',
    icon: (
      <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
      </svg>
    ),
    href: '/copywriting',
    color: 'from-purple-500 to-pink-500'
  },
  {
    title: '知识库系统',
    description: '企业级知识库系统，提供文档管理、知识图谱、混合检索和 MCP 集成能力',
    icon: (
      <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
      </svg>
    ),
    href: '/knowledge-base',
    color: 'from-orange-500 to-red-500'
  },
  {
    title: 'Text2SQL 系统',
    description: '自然语言到 SQL 转换系统，支持复杂查询理解、模板生成和结果可视化',
    icon: (
      <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
      </svg>
    ),
    href: '/text2sql',
    color: 'from-green-500 to-teal-500'
  }
]

// 系统状态数据
const stats = [
  { 
    name: 'API 请求成功率', 
    value: '99.9%', 
    icon: (
      <svg className="h-5 w-5 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    trend: 'up' as const,
    color: 'text-green-500'
  },
  { 
    name: '平均响应时间', 
    value: '238ms',
    icon: (
      <svg className="h-5 w-5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    trend: 'down' as const,
    color: 'text-blue-500'
  },
  { 
    name: '模型运行状态', 
    value: '正常',
    icon: (
      <svg className="h-5 w-5 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
      </svg>
    ),
    trend: 'stable' as const,
    color: 'text-green-500'
  },
  { 
    name: '在线用户数', 
    value: '128',
    icon: (
      <svg className="h-5 w-5 text-purple-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
      </svg>
    ),
    trend: 'up' as const,
    color: 'text-purple-500'
  }
]

// 趋势图标组件
const TrendIcon = ({ trend }: { trend: 'up' | 'down' | 'stable' }) => {
  if (trend === 'up') {
    return (
      <svg className="h-4 w-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
      </svg>
    );
  } else if (trend === 'down') {
    return (
      <svg className="h-4 w-4 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 17h8m0 0v-8m0 8l-8-8-4 4-6-6" />
      </svg>
    );
  }
  return (
    <svg className="h-4 w-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14" />
    </svg>
  );
};

export default function Dashboard() {
  const [showContact, setShowContact] = useState(false)
  const [currentTime, setCurrentTime] = useState('')
  
  // 实时时间更新
  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setCurrentTime(now.toLocaleTimeString('zh-CN', { hour12: false }));
    };
    
    updateTime();
    const timer = setInterval(updateTime, 1000);
    
    return () => clearInterval(timer);
  }, []);
  
  return (
    <div className="min-h-screen relative">
      <TechBackground />
      <FloatingParticles />
      
      {/* 导航栏 */}
      <nav className="gemini-navbar">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="h-9 w-9 relative overflow-hidden rounded-full bg-gradient-to-r from-blue-500 to-purple-600 p-2 shadow-md">
                <svg className="h-full w-full text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </div>
              <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600">
                智能体控制台
              </span>
            </div>
            <div className="flex items-center space-x-4">
              <div className="hidden md:flex items-center text-sm text-gray-600 dark:text-gray-300 bg-gray-100 dark:bg-gray-800 rounded-full px-3 py-1">
                <span className="inline-block w-2 h-2 rounded-full bg-green-500 mr-2 animate-pulse"></span>
                系统时间: {currentTime}
              </div>
              <button
                onClick={() => setShowContact(true)}
                className="gemini-button-primary"
              >
                获取技术支持
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 pt-24 pb-12 z-10 relative">
        {/* 标题区域 */}
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="py-8"
        >
          <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600">
            欢迎使用智能体控制台
          </h1>
          <p className="mt-1 text-gray-600 dark:text-gray-300">
            在这里您可以管理和使用我们的四大智能系统，为您的业务注入AI能力
          </p>
        </motion.div>

        {/* 系统卡片网格 */}
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4 mb-8">
          {systems.map((system, index) => (
            <Link key={system.title} href={system.href}>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1, duration: 0.5 }}
                whileHover={{ y: -5, transition: { duration: 0.2 } }}
                className="relative h-full overflow-hidden rounded-xl bg-white/90 backdrop-blur-sm shadow-md dark:bg-neutral-900/90 dark:border-neutral-800 border border-[var(--border)] p-6 transition-all duration-300"
              >
                {/* 背景装饰 */}
                <div className={`absolute -right-8 -top-8 h-40 w-40 rounded-full bg-gradient-to-br ${system.color} opacity-10 blur-2xl transition-opacity group-hover:opacity-20`} />
                <div className="shine-effect absolute inset-0"></div>
                
                <div className="relative">
                  {/* 图标 */}
                  <div className={`mb-4 inline-flex rounded-lg bg-gradient-to-br ${system.color} p-3 text-white shadow-lg`}>
                    {system.icon}
                  </div>
                  
                  {/* 标题和描述 */}
                  <h2 className="mb-2 text-xl font-bold text-gray-900 dark:text-white">
                    {system.title}
                  </h2>
                  <p className="text-gray-600 dark:text-gray-400 text-sm mb-4">
                    {system.description}
                  </p>
                  
                  <div className="mt-auto flex justify-end">
                    <span className="text-sm font-medium text-blue-600 dark:text-blue-400 flex items-center group">
                      进入系统
                      <svg className="h-4 w-4 ml-1 transform transition-transform group-hover:translate-x-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                      </svg>
                    </span>
                  </div>
                </div>
              </motion.div>
            </Link>
          ))}
        </div>

        {/* 系统状态面板 */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.5 }}
          className="rounded-xl border border-[var(--border)] bg-white/90 backdrop-blur-sm shadow-md dark:bg-neutral-900/90 dark:border-neutral-800 overflow-hidden"
        >
          <div className="border-b border-[var(--border)] bg-gray-50/50 dark:bg-gray-800/50 px-6 py-4 flex items-center justify-between">
            <h2 className="text-lg font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-purple-600">
              系统实时状态
            </h2>
            <div className="flex items-center text-sm text-gray-500 dark:text-gray-400">
              <span className="inline-block w-2 h-2 rounded-full bg-green-500 mr-2"></span>
              实时监控中
            </div>
          </div>
          <div className="p-6">
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
              {stats.map((stat) => (
                <motion.div
                  key={stat.name}
                  whileHover={{ y: -5, transition: { duration: 0.2 } }}
                  className="rounded-lg bg-gray-50 p-4 dark:bg-gray-800/50 border border-[var(--border)] shadow-sm transition-all duration-300"
                >
                  <div className="flex items-center mb-2">
                    <div className="mr-2">
                      {stat.icon}
                    </div>
                    <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                      {stat.name}
                    </p>
                  </div>
                  <div className="flex justify-between items-end">
                    <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                      {stat.value}
                    </p>
                    <div className="flex items-center">
                      <TrendIcon trend={stat.trend} />
                    </div>
                  </div>
                  <div className="mt-2 w-full h-1 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                    <div className={`h-full ${stat.trend === 'up' ? 'bg-green-500' : stat.trend === 'down' ? 'bg-blue-500' : 'bg-gray-500'}`} style={{ width: stat.trend === 'up' ? '95%' : stat.trend === 'down' ? '75%' : '85%' }}></div>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </motion.div>

        {/* 快速操作面板 */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5, duration: 0.5 }}
          className="mt-8 rounded-xl border border-[var(--border)] bg-white/90 backdrop-blur-sm shadow-md dark:bg-neutral-900/90 dark:border-neutral-800 p-6"
        >
          <h2 className="mb-4 text-lg font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-purple-600">
            快速操作
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <button className="p-4 rounded-lg border border-[var(--border)] bg-gray-50 dark:bg-gray-800/50 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700/50 transition-colors flex flex-col items-center justify-center">
              <svg className="h-6 w-6 mb-2 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              查看文档
            </button>
            <button className="p-4 rounded-lg border border-[var(--border)] bg-gray-50 dark:bg-gray-800/50 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700/50 transition-colors flex flex-col items-center justify-center">
              <svg className="h-6 w-6 mb-2 text-purple-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              系统设置
            </button>
            <button className="p-4 rounded-lg border border-[var(--border)] bg-gray-50 dark:bg-gray-800/50 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700/50 transition-colors flex flex-col items-center justify-center">
              <svg className="h-6 w-6 mb-2 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
              </svg>
              账单管理
            </button>
            <button className="p-4 rounded-lg border border-[var(--border)] bg-gray-50 dark:bg-gray-800/50 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700/50 transition-colors flex flex-col items-center justify-center">
              <svg className="h-6 w-6 mb-2 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              获取帮助
            </button>
          </div>
        </motion.div>
      </main>

      {/* 技术支持弹窗 */}
      <ContactDialog isOpen={showContact} onClose={() => setShowContact(false)} />

      {/* 添加动效样式 */}
      <style jsx global>{`
        .shine-effect {
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          background: linear-gradient(
            to right,
            rgba(255, 255, 255, 0) 0%,
            rgba(255, 255, 255, 0.2) 50%,
            rgba(255, 255, 255, 0) 100%
          );
          transform: skewX(-20deg);
          animation: shine 6s infinite;
          pointer-events: none;
        }
        
        @keyframes shine {
          0% {
            transform: translateX(-100%) skewX(-20deg);
          }
          15%, 100% {
            transform: translateX(200%) skewX(-20deg);
          }
        }
      `}</style>
    </div>
  )
} 