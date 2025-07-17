'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import Link from 'next/link'
import Image from 'next/image'

// 内联定义图标组件
function Brain(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      <path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96.44 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 1.98-3A2.5 2.5 0 0 1 9.5 2Z" />
      <path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96.44 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-1.98-3A2.5 2.5 0 0 0 14.5 2Z" />
    </svg>
  )
}

function Search(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      <circle cx="11" cy="11" r="8" />
      <path d="m21 21-4.3-4.3" />
    </svg>
  )
}

function Database(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      <ellipse cx="12" cy="5" rx="9" ry="3" />
      <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" />
      <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
    </svg>
  )
}

function Network(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      <rect x="16" y="16" width="6" height="6" rx="1" />
      <rect x="2" y="16" width="6" height="6" rx="1" />
      <rect x="9" y="2" width="6" height="6" rx="1" />
      <path d="M5 16v-3a1 1 0 0 1 1-1h12a1 1 0 0 1 1 1v3" />
      <path d="M12 12V8" />
    </svg>
  )
}

function ArrowRight(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      <path d="M5 12h14" />
      <path d="m12 5 7 7-7 7" />
    </svg>
  )
}

function FileText(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
      <line x1="16" y1="13" x2="8" y2="13" />
      <line x1="16" y1="17" x2="8" y2="17" />
      <polyline points="10 9 9 9 8 9" />
    </svg>
  )
}

function Code(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      <polyline points="16 18 22 12 16 6" />
      <polyline points="8 6 2 12 8 18" />
    </svg>
  )
}

function Globe(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      <circle cx="12" cy="12" r="10" />
      <line x1="2" y1="12" x2="22" y2="12" />
      <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
    </svg>
  )
}

function Server(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      <rect x="2" y="2" width="20" height="8" rx="2" ry="2" />
      <rect x="2" y="14" width="20" height="8" rx="2" ry="2" />
      <line x1="6" y1="6" x2="6.01" y2="6" />
      <line x1="6" y1="18" x2="6.01" y2="18" />
    </svg>
  )
}

function Layers(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      <polygon points="12 2 2 7 12 12 22 7 12 2" />
      <polyline points="2 17 12 22 22 17" />
      <polyline points="2 12 12 17 22 12" />
    </svg>
  )
}

function Sparkles(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      <path d="M12 3v18" />
      <path d="m9 6 6 12" />
      <path d="m15 6-6 12" />
      <path d="M6 9h12" />
      <path d="M6 15h12" />
    </svg>
  )
}

function Zap(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
    </svg>
  )
}

function Lock(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
      <path d="M7 11V7a5 5 0 0 1 10 0v4" />
    </svg>
  )
}

function Check(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      <path d="M20 6L9 17l-5-5" />
    </svg>
  )
}

function Settings(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      <path d="M12 2.5a9.5 9.5 0 1 0 0 19 9.5 9.5 0 0 0 0-19z" />
      <path d="M12 4v16" />
      <path d="M12 12h16" />
      <path d="M12 8h16" />
    </svg>
  )
}

export default function KnowledgeBase() {
  return (
    <div className="flex min-h-screen flex-col relative">
      <div className="wave-bg"></div>
      <div className="gemini-bg-dots absolute inset-0 opacity-10 z-0"></div>
      
      {/* 导航栏 */}
      <nav className="gemini-navbar">
        <div className="container mx-auto flex items-center justify-between py-3 px-4">
          <Link href="/" className="flex items-center space-x-2">
            <div className="h-9 w-9 relative overflow-hidden rounded-full bg-gradient-to-r from-blue-500 to-purple-600 p-2 shadow-md">
              <Brain className="h-full w-full text-white" />
            </div>
            <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-purple-600">但问智能体平台</h1>
          </Link>
          <div className="hidden md:flex gap-6">
            <Link href="/customer-service" className="text-sm font-medium text-neutral-600 hover:text-blue-600 dark:text-neutral-300 dark:hover:text-blue-400 transition-colors">
              智能客服
            </Link>
            <Link href="/text2sql" className="text-sm font-medium text-neutral-600 hover:text-blue-600 dark:text-neutral-300 dark:hover:text-blue-400 transition-colors">
              Text2SQL
            </Link>
            <Link href="/knowledge-base" className="text-sm font-medium text-blue-600 dark:text-blue-400 relative after:content-[''] after:absolute after:left-0 after:bottom-[-4px] after:w-full after:h-[2px] after:bg-blue-600 dark:after:bg-blue-400">
              知识库问答
            </Link>
            <Link href="/copywriting" className="text-sm font-medium text-neutral-600 hover:text-blue-600 dark:text-neutral-300 dark:hover:text-blue-400 transition-colors">
              文案创作
            </Link>
          </div>
          <Link
            href="/dashboard"
            className="gemini-button-primary"
          >
            控制台
          </Link>
        </div>
      </nav>

      <main className="flex flex-1 flex-col pt-24 z-10">
        <div className="container mx-auto px-4">
          {/* 顶部标题部分 */}
          <div className="mb-12 text-center">
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5 }}
              className="inline-block p-1.5 px-4 mb-6 rounded-full text-sm font-medium bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-300 border border-blue-100 dark:border-blue-800"
            >
              <span className="mr-2">✨</span> 知识库增强生成技术
            </motion.div>
            <motion.h1
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-4 text-3xl font-bold md:text-4xl bg-clip-text text-transparent bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600"
            >
              但问智能体 RAG 系统
            </motion.h1>
            <motion.p
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="mx-auto mb-8 max-w-2xl text-lg text-gray-600 dark:text-gray-300"
            >
              最先进的智能检索系统，搭载代理式检索增强生成（RAG）与REST API
            </motion.p>
          </div>

          {/* 系统概述 */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="mx-auto mb-16 max-w-4xl"
          >
            <div className="rounded-xl border border-[var(--border)] p-8 bg-white/90 backdrop-blur-sm shadow-md dark:bg-neutral-900/90 dark:border-neutral-800 overflow-hidden relative">
              <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 via-indigo-500/5 to-purple-500/5"></div>
              <div className="relative z-10">
                <h2 className="text-2xl font-bold mb-6 text-center bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-purple-600">系统概述</h2>
                <p className="text-lg mb-6 text-gray-700 dark:text-gray-300">
                  但问智能体是集成了AI检索增强生成（RAG）的全功能解决方案，具备生产级特性，包括多模态内容摄取、混合搜索功能、可配置的GraphRAG以及用户/文档管理。
                </p>
                <p className="text-lg mb-6 text-gray-700 dark:text-gray-300">
                  系统同时包含<strong className="text-blue-600 dark:text-blue-400">深度研究API</strong>，这是一个多步骤推理系统，能从您的知识库和/或互联网获取相关数据，为复杂查询提供更丰富、更具上下文感知的答案。
                </p>
                
                {/* 图片占位区 */}
                <div className="relative h-64 rounded-xl overflow-hidden mb-6 shadow-md neon-glow">
                  <div className="absolute inset-0 bg-gradient-to-br from-blue-500/20 to-purple-500/20"></div>
                  <div className="absolute inset-0 overflow-hidden">
                    <svg width="100%" height="100%" viewBox="0 0 800 500" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid meet">
                      {/* 背景 */}
                      <rect width="800" height="500" fill="#EFF6FF" opacity="0.7" rx="15" ry="15" />
                      <text x="400" y="50" fontFamily="Arial" fontSize="24" fontWeight="bold" textAnchor="middle" fill="#4338CA">但问智能体系统概述</text>

                      {/* 用户层 */}
                      <rect x="300" y="100" width="200" height="60" rx="10" ry="10" fill="#F9FAFB" stroke="#3B82F6" strokeWidth="2" />
                      <text x="400" y="135" fontFamily="Arial" fontSize="16" textAnchor="middle" fill="#1E40AF">用户接口层</text>

                      {/* 应用服务层 */}
                      <rect x="150" y="200" width="500" height="80" rx="10" ry="10" fill="#F5F3FF" stroke="#8B5CF6" strokeWidth="2" />
                      <text x="400" y="230" fontFamily="Arial" fontSize="16" fontWeight="bold" textAnchor="middle" fill="#6D28D9">RAG引擎</text>
                      <text x="400" y="260" fontFamily="Arial" fontSize="14" textAnchor="middle" fill="#7C3AED">检索增强生成 + 代理调度</text>

                      {/* 知识处理层 */}
                      <rect x="100" y="320" width="600" height="100" rx="10" ry="10" fill="#EFF6FF" stroke="#3B82F6" strokeWidth="2" />
                      <text x="400" y="345" fontFamily="Arial" fontSize="16" fontWeight="bold" textAnchor="middle" fill="#1E40AF">知识处理层</text>

                      {/* 知识处理层组件 */}
                      <rect x="130" y="365" width="150" height="40" rx="8" ry="8" fill="#DBEAFE" stroke="#3B82F6" strokeWidth="1.5" />
                      <text x="205" y="390" fontFamily="Arial" fontSize="14" textAnchor="middle" fill="#1E40AF">多模态内容摄取</text>

                      <rect x="320" y="365" width="150" height="40" rx="8" ry="8" fill="#DBEAFE" stroke="#3B82F6" strokeWidth="1.5" />
                      <text x="395" y="390" fontFamily="Arial" fontSize="14" textAnchor="middle" fill="#1E40AF">混合搜索引擎</text>

                      <rect x="510" y="365" width="150" height="40" rx="8" ry="8" fill="#DBEAFE" stroke="#3B82F6" strokeWidth="1.5" />
                      <text x="585" y="390" fontFamily="Arial" fontSize="14" textAnchor="middle" fill="#1E40AF">知识图谱构建</text>

                      {/* 连接线 */}
                      <line x1="400" y1="160" x2="400" y2="200" stroke="#A78BFA" strokeWidth="2" strokeDasharray="5,5" />
                      <line x1="400" y1="280" x2="400" y2="320" stroke="#93C5FD" strokeWidth="2" strokeDasharray="5,5" />

                      {/* 底部框架 */}
                      <rect x="200" y="450" width="400" height="30" rx="5" ry="5" fill="#DBEAFE" stroke="#3B82F6" strokeWidth="1.5" />
                      <text x="400" y="470" fontFamily="Arial" fontSize="14" textAnchor="middle" fill="#1E40AF">数据存储 (向量存储 + 图数据库)</text>
                      <line x1="400" y1="420" x2="400" y2="450" stroke="#93C5FD" strokeWidth="2" strokeDasharray="5,5" />
                    </svg>
                  </div>
                  <div className="absolute inset-0 shine-effect"></div>
                </div>
              </div>
            </div>
          </motion.div>

          {/* 系统架构 */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="mx-auto mb-16 max-w-4xl"
          >
            <h2 className="text-2xl font-bold mb-8 text-center bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-purple-600">系统架构</h2>
            <div className="mb-8">
              <div className="relative h-80 rounded-xl overflow-hidden shadow-lg neon-glow">
                <div className="absolute inset-0 bg-gradient-to-br from-blue-500/20 via-indigo-500/10 to-purple-500/20"></div>
                <div className="absolute inset-0 overflow-hidden">
                  <svg width="100%" height="100%" viewBox="0 0 800 600" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid meet">
                    {/* 背景 */}
                    <rect width="800" height="600" fill="#EFF6FF" opacity="0.7" rx="15" ry="15" />
                    <text x="400" y="40" fontFamily="Arial" fontSize="22" fontWeight="bold" textAnchor="middle" fill="#4F46E5">但问智能体系统架构</text>

                    {/* 客户端/应用层 */}
                    <rect x="20" y="80" width="760" height="60" rx="10" ry="10" fill="#F8FAFC" stroke="#3B82F6" strokeWidth="2" />
                    <text x="400" y="115" fontFamily="Arial" fontSize="16" fontWeight="bold" textAnchor="middle" fill="#1E40AF">客户端/应用层</text>
                    <rect x="60" y="95" width="100" height="30" rx="5" ry="5" fill="#DBEAFE" stroke="#3B82F6" strokeWidth="1" />
                    <text x="110" y="115" fontFamily="Arial" fontSize="12" textAnchor="middle" fill="#2563EB">Web应用</text>
                    <rect x="190" y="95" width="100" height="30" rx="5" ry="5" fill="#DBEAFE" stroke="#3B82F6" strokeWidth="1" />
                    <text x="240" y="115" fontFamily="Arial" fontSize="12" textAnchor="middle" fill="#2563EB">移动应用</text>
                    <rect x="320" y="95" width="100" height="30" rx="5" ry="5" fill="#DBEAFE" stroke="#3B82F6" strokeWidth="1" />
                    <text x="370" y="115" fontFamily="Arial" fontSize="12" textAnchor="middle" fill="#2563EB">第三方集成</text>
                    <rect x="450" y="95" width="100" height="30" rx="5" ry="5" fill="#DBEAFE" stroke="#3B82F6" strokeWidth="1" />
                    <text x="500" y="115" fontFamily="Arial" fontSize="12" textAnchor="middle" fill="#2563EB">聊天界面</text>
                    <rect x="580" y="95" width="100" height="30" rx="5" ry="5" fill="#DBEAFE" stroke="#3B82F6" strokeWidth="1" />
                    <text x="630" y="115" fontFamily="Arial" fontSize="12" textAnchor="middle" fill="#2563EB">管理控制台</text>

                    {/* API层 */}
                    <rect x="20" y="160" width="760" height="60" rx="10" ry="10" fill="#F0F9FF" stroke="#0EA5E9" strokeWidth="2" />
                    <text x="400" y="195" fontFamily="Arial" fontSize="16" fontWeight="bold" textAnchor="middle" fill="#0369A1">API层</text>
                    <rect x="60" y="175" width="120" height="30" rx="5" ry="5" fill="#BAE6FD" stroke="#0EA5E9" strokeWidth="1" />
                    <text x="120" y="195" fontFamily="Arial" fontSize="12" textAnchor="middle" fill="#0369A1">REST API服务</text>
                    <rect x="210" y="175" width="120" height="30" rx="5" ry="5" fill="#BAE6FD" stroke="#0EA5E9" strokeWidth="1" />
                    <text x="270" y="195" fontFamily="Arial" fontSize="12" textAnchor="middle" fill="#0369A1">GraphQL API</text>
                    <rect x="360" y="175" width="120" height="30" rx="5" ry="5" fill="#BAE6FD" stroke="#0EA5E9" strokeWidth="1" />
                    <text x="420" y="195" fontFamily="Arial" fontSize="12" textAnchor="middle" fill="#0369A1">鉴权服务</text>
                    <rect x="510" y="175" width="120" height="30" rx="5" ry="5" fill="#BAE6FD" stroke="#0EA5E9" strokeWidth="1" />
                    <text x="570" y="195" fontFamily="Arial" fontSize="12" textAnchor="middle" fill="#0369A1">速率限制</text>
                    <rect x="660" y="175" width="90" height="30" rx="5" ry="5" fill="#BAE6FD" stroke="#0EA5E9" strokeWidth="1" />
                    <text x="705" y="195" fontFamily="Arial" fontSize="12" textAnchor="middle" fill="#0369A1">负载均衡</text>

                    {/* 核心服务层 */}
                    <rect x="20" y="240" width="760" height="150" rx="10" ry="10" fill="#F5F3FF" stroke="#8B5CF6" strokeWidth="2" />
                    <text x="400" y="265" fontFamily="Arial" fontSize="16" fontWeight="bold" textAnchor="middle" fill="#6D28D9">核心服务层</text>

                    {/* 核心服务层组件 */}
                    <rect x="40" y="280" width="130" height="40" rx="5" ry="5" fill="#DDD6FE" stroke="#8B5CF6" strokeWidth="1" />
                    <text x="105" y="305" fontFamily="Arial" fontSize="13" textAnchor="middle" fill="#6D28D9">文档处理服务</text>

                    <rect x="190" y="280" width="130" height="40" rx="5" ry="5" fill="#DDD6FE" stroke="#8B5CF6" strokeWidth="1" />
                    <text x="255" y="305" fontFamily="Arial" fontSize="13" textAnchor="middle" fill="#6D28D9">向量嵌入服务</text>

                    <rect x="340" y="280" width="130" height="40" rx="5" ry="5" fill="#DDD6FE" stroke="#8B5CF6" strokeWidth="1" />
                    <text x="405" y="305" fontFamily="Arial" fontSize="13" textAnchor="middle" fill="#6D28D9">检索服务</text>

                    <rect x="490" y="280" width="130" height="40" rx="5" ry="5" fill="#DDD6FE" stroke="#8B5CF6" strokeWidth="1" />
                    <text x="555" y="305" fontFamily="Arial" fontSize="13" textAnchor="middle" fill="#6D28D9">图谱构建服务</text>

                    <rect x="640" y="280" width="130" height="40" rx="5" ry="5" fill="#DDD6FE" stroke="#8B5CF6" strokeWidth="1" />
                    <text x="705" y="305" fontFamily="Arial" fontSize="13" textAnchor="middle" fill="#6D28D9">用户/租户服务</text>

                    <rect x="40" y="335" width="130" height="40" rx="5" ry="5" fill="#DDD6FE" stroke="#8B5CF6" strokeWidth="1" />
                    <text x="105" y="360" fontFamily="Arial" fontSize="13" textAnchor="middle" fill="#6D28D9">语义搜索服务</text>

                    <rect x="190" y="335" width="130" height="40" rx="5" ry="5" fill="#DDD6FE" stroke="#8B5CF6" strokeWidth="1" />
                    <text x="255" y="360" fontFamily="Arial" fontSize="13" textAnchor="middle" fill="#6D28D9">关键词搜索服务</text>

                    <rect x="340" y="335" width="130" height="40" rx="5" ry="5" fill="#DDD6FE" stroke="#8B5CF6" strokeWidth="1" />
                    <text x="405" y="360" fontFamily="Arial" fontSize="13" textAnchor="middle" fill="#6D28D9">RAG生成服务</text>

                    <rect x="490" y="335" width="130" height="40" rx="5" ry="5" fill="#DDD6FE" stroke="#8B5CF6" strokeWidth="1" />
                    <text x="555" y="360" fontFamily="Arial" fontSize="13" textAnchor="middle" fill="#6D28D9">MCP集成服务</text>

                    <rect x="640" y="335" width="130" height="40" rx="5" ry="5" fill="#DDD6FE" stroke="#8B5CF6" strokeWidth="1" />
                    <text x="705" y="360" fontFamily="Arial" fontSize="13" textAnchor="middle" fill="#6D28D9">分析服务</text>

                    {/* 编排系统 */}
                    <rect x="20" y="410" width="760" height="60" rx="10" ry="10" fill="#ECFDF5" stroke="#10B981" strokeWidth="2" />
                    <text x="400" y="445" fontFamily="Arial" fontSize="16" fontWeight="bold" textAnchor="middle" fill="#047857">编排系统</text>
                    <rect x="100" y="425" width="150" height="30" rx="5" ry="5" fill="#A7F3D0" stroke="#10B981" strokeWidth="1" />
                    <text x="175" y="445" fontFamily="Arial" fontSize="13" textAnchor="middle" fill="#047857">消息队列</text>
                    <rect x="325" y="425" width="150" height="30" rx="5" ry="5" fill="#A7F3D0" stroke="#10B981" strokeWidth="1" />
                    <text x="400" y="445" fontFamily="Arial" fontSize="13" textAnchor="middle" fill="#047857">任务调度器</text>
                    <rect x="550" y="425" width="150" height="30" rx="5" ry="5" fill="#A7F3D0" stroke="#10B981" strokeWidth="1" />
                    <text x="625" y="445" fontFamily="Arial" fontSize="13" textAnchor="middle" fill="#047857">工作流管理</text>

                    {/* 存储层 */}
                    <rect x="20" y="490" width="760" height="90" rx="10" ry="10" fill="#FEF3C7" stroke="#F59E0B" strokeWidth="2" />
                    <text x="400" y="515" fontFamily="Arial" fontSize="16" fontWeight="bold" textAnchor="middle" fill="#B45309">存储层</text>

                    <rect x="50" y="530" width="130" height="35" rx="5" ry="5" fill="#FDE68A" stroke="#F59E0B" strokeWidth="1" />
                    <text x="115" y="552" fontFamily="Arial" fontSize="13" textAnchor="middle" fill="#B45309">文档存储</text>

                    <rect x="210" y="530" width="130" height="35" rx="5" ry="5" fill="#FDE68A" stroke="#F59E0B" strokeWidth="1" />
                    <text x="275" y="552" fontFamily="Arial" fontSize="13" textAnchor="middle" fill="#B45309">向量存储</text>

                    <rect x="370" y="530" width="130" height="35" rx="5" ry="5" fill="#FDE68A" stroke="#F59E0B" strokeWidth="1" />
                    <text x="435" y="552" fontFamily="Arial" fontSize="13" textAnchor="middle" fill="#B45309">图数据库</text>

                    <rect x="530" y="530" width="130" height="35" rx="5" ry="5" fill="#FDE68A" stroke="#F59E0B" strokeWidth="1" />
                    <text x="595" y="552" fontFamily="Arial" fontSize="13" textAnchor="middle" fill="#B45309">关系型数据库</text>

                    <rect x="370" y="570" width="130" height="15" rx="3" ry="3" fill="#FFFBEB" stroke="#F59E0B" strokeWidth="1" />
                    <text x="435" y="582" fontFamily="Arial" fontSize="10" textAnchor="middle" fill="#B45309">Postgres + pgvector</text>

                    {/* 连接线 */}
                    <line x1="400" y1="140" x2="400" y2="160" stroke="#3B82F6" strokeWidth="1.5" />
                    <line x1="400" y1="220" x2="400" y2="240" stroke="#8B5CF6" strokeWidth="1.5" />
                    <line x1="400" y1="390" x2="400" y2="410" stroke="#10B981" strokeWidth="1.5" />
                    <line x1="400" y1="470" x2="400" y2="490" stroke="#F59E0B" strokeWidth="1.5" />
                  </svg>
                </div>
                <div className="absolute inset-0 shine-effect"></div>
              </div>
            </div>
            
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.2 }}
              className="rounded-xl border bg-white/90 backdrop-blur-sm shadow-md dark:bg-neutral-900/90 dark:border-neutral-800 overflow-hidden"
            >
              <div className="p-6">
                <p className="text-lg mb-4 text-gray-700 dark:text-gray-300">
                  但问智能体系统基于模块化、面向服务的架构设计，确保可扩展性和灵活性：
                </p>
                <ol className="list-decimal pl-6 space-y-2">
                  <li className="text-gray-700 dark:text-gray-300"><strong className="text-blue-600 dark:text-blue-400">API层</strong>：REST API集群处理传入请求，将其路由到适当的服务。</li>
                  <li className="text-gray-700 dark:text-gray-300"><strong className="text-indigo-600 dark:text-indigo-400">核心服务</strong>：专用服务用于身份验证、检索、摄取、图构建和应用管理。</li>
                  <li className="text-gray-700 dark:text-gray-300"><strong className="text-purple-600 dark:text-purple-400">编排系统</strong>：使用消息队列系统管理复杂工作流和长时运行任务。</li>
                  <li className="text-gray-700 dark:text-gray-300"><strong className="text-pink-600 dark:text-pink-400">存储</strong>：利用Postgres与pgvector和全文搜索进行向量存储、搜索和图搜索。</li>
                  <li className="text-gray-700 dark:text-gray-300"><strong className="text-green-600 dark:text-green-400">提供程序</strong>：用于解析、嵌入、认证和检索增强生成的可插拔组件。</li>
                  <li className="text-gray-700 dark:text-gray-300"><strong className="text-teal-600 dark:text-teal-400">应用界面</strong>：提供与系统交互的直观用户界面。</li>
                </ol>
              </div>
            </motion.div>
          </motion.div>

          {/* 技术特点 */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2 }}
            className="mx-auto mb-16 max-w-6xl"
          >
            <h2 className="text-2xl font-bold mb-8 text-center bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-purple-600">核心技术特点</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <motion.div 
                initial={{ opacity: 0, scale: 0.9 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ delay: 0.1 }}
                whileHover={{ y: -5 }}
                className="bg-white dark:bg-neutral-900 rounded-xl shadow-lg overflow-hidden border border-gray-200 dark:border-neutral-800"
              >
                <div className="h-2 bg-gradient-to-r from-blue-500 to-purple-500"></div>
                <div className="p-6">
                  <div className="mb-4 bg-blue-100 dark:bg-blue-900/30 w-12 h-12 flex items-center justify-center rounded-lg">
                    <Search className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                  </div>
                  <h3 className="text-lg font-semibold mb-2 text-gray-800 dark:text-gray-200">混合检索</h3>
                  <p className="text-gray-600 dark:text-gray-400 text-sm">
                    结合语义向量与关键词搜索，获得最相关的检索结果。系统根据查询类型动态调整检索策略。
                  </p>
                  <div className="mt-4">
                    <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">检索准确率</div>
                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                      <div className="bg-blue-600 h-2 rounded-full" style={{ width: '92%' }}></div>
                    </div>
                  </div>
                </div>
              </motion.div>
              
              <motion.div 
                initial={{ opacity: 0, scale: 0.9 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ delay: 0.2 }}
                whileHover={{ y: -5 }}
                className="bg-white dark:bg-neutral-900 rounded-xl shadow-lg overflow-hidden border border-gray-200 dark:border-neutral-800"
              >
                <div className="h-2 bg-gradient-to-r from-purple-500 to-pink-500"></div>
                <div className="p-6">
                  <div className="mb-4 bg-purple-100 dark:bg-purple-900/30 w-12 h-12 flex items-center justify-center rounded-lg">
                    <Layers className="w-6 h-6 text-purple-600 dark:text-purple-400" />
                  </div>
                  <h3 className="text-lg font-semibold mb-2 text-gray-800 dark:text-gray-200">多模态内容</h3>
                  <p className="text-gray-600 dark:text-gray-400 text-sm">
                    支持多种格式的文档摄取，包括PDF、Word、Excel、PPT、Markdown、HTML和图像内容，实现跨格式智能理解。
                  </p>
                  <div className="mt-4 grid grid-cols-5 gap-1">
                    {['PDF', 'DOC', 'XLS', 'MD', 'IMG'].map((format, index) => (
                      <div key={index} className="text-center">
                        <div className="text-xs font-medium bg-gray-100 dark:bg-gray-800 rounded py-1 text-gray-600 dark:text-gray-400">{format}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </motion.div>
              
              <motion.div 
                initial={{ opacity: 0, scale: 0.9 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ delay: 0.3 }}
                whileHover={{ y: -5 }}
                className="bg-white dark:bg-neutral-900 rounded-xl shadow-lg overflow-hidden border border-gray-200 dark:border-neutral-800"
              >
                <div className="h-2 bg-gradient-to-r from-pink-500 to-orange-500"></div>
                <div className="p-6">
                  <div className="mb-4 bg-pink-100 dark:bg-pink-900/30 w-12 h-12 flex items-center justify-center rounded-lg">
                    <Sparkles className="w-6 h-6 text-pink-600 dark:text-pink-400" />
                  </div>
                  <h3 className="text-lg font-semibold mb-2 text-gray-800 dark:text-gray-200">知识更新</h3>
                  <p className="text-gray-600 dark:text-gray-400 text-sm">
                    支持增量知识更新和实时索引，确保信息始终最新。自动清除过时内容，减少冗余和矛盾。
                  </p>
                  <div className="mt-4">
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="text-gray-500 dark:text-gray-400">更新周期</span>
                      <span className="text-gray-600 dark:text-gray-300 font-medium">实时/计划</span>
                    </div>
                    <div className="flex items-center">
                      <div className="relative overflow-hidden w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5">
                        <motion.div 
                          initial={{ width: 0 }}
                          animate={{ width: "100%" }}
                          transition={{ 
                            repeat: Infinity, 
                            duration: 2,
                            ease: "linear"
                          }}
                          className="absolute top-0 h-full bg-gradient-to-r from-pink-500 to-orange-500 rounded-full"
                        ></motion.div>
                      </div>
                    </div>
                  </div>
                </div>
              </motion.div>
              
              <motion.div 
                initial={{ opacity: 0, scale: 0.9 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ delay: 0.4 }}
                whileHover={{ y: -5 }}
                className="bg-white dark:bg-neutral-900 rounded-xl shadow-lg overflow-hidden border border-gray-200 dark:border-neutral-800"
              >
                <div className="h-2 bg-gradient-to-r from-green-500 to-teal-500"></div>
                <div className="p-6">
                  <div className="mb-4 bg-green-100 dark:bg-green-900/30 w-12 h-12 flex items-center justify-center rounded-lg">
                    <Zap className="w-6 h-6 text-green-600 dark:text-green-400" />
                  </div>
                  <h3 className="text-lg font-semibold mb-2 text-gray-800 dark:text-gray-200">高性能处理</h3>
                  <p className="text-gray-600 dark:text-gray-400 text-sm">
                    优化的向量索引和缓存机制，确保即使在大型知识库上也能实现毫秒级响应时间，支持高并发访问。
                  </p>
                  <div className="mt-4">
                    <div className="grid grid-cols-2 gap-2">
                      <div className="text-center p-1 bg-gray-50 dark:bg-gray-800 rounded">
                        <div className="text-xs text-gray-500 dark:text-gray-400">平均响应</div>
                        <div className="font-semibold text-green-600 dark:text-green-400">{"<200ms"}</div>
                      </div>
                      <div className="text-center p-1 bg-gray-50 dark:bg-gray-800 rounded">
                        <div className="text-xs text-gray-500 dark:text-gray-400">并发能力</div>
                        <div className="font-semibold text-green-600 dark:text-green-400">1000+</div>
                      </div>
                    </div>
                  </div>
                </div>
              </motion.div>
              
              <motion.div 
                initial={{ opacity: 0, scale: 0.9 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ delay: 0.5 }}
                whileHover={{ y: -5 }}
                className="bg-white dark:bg-neutral-900 rounded-xl shadow-lg overflow-hidden border border-gray-200 dark:border-neutral-800"
              >
                <div className="h-2 bg-gradient-to-r from-teal-500 to-cyan-500"></div>
                <div className="p-6">
                  <div className="mb-4 bg-teal-100 dark:bg-teal-900/30 w-12 h-12 flex items-center justify-center rounded-lg">
                    <Network className="w-6 h-6 text-teal-600 dark:text-teal-400" />
                  </div>
                  <h3 className="text-lg font-semibold mb-2 text-gray-800 dark:text-gray-200">知识图谱</h3>
                  <p className="text-gray-600 dark:text-gray-400 text-sm">
                    自动构建文档间关联，形成知识图谱，揭示隐藏的洞见。支持复杂关系查询和可视化探索。
                  </p>
                  <div className="mt-4 relative h-8">
                    <div className="absolute inset-0 flex items-center justify-center">
                      <div className="w-2 h-2 bg-teal-500 rounded-full opacity-75 pulse-animation"></div>
                      <div className="absolute w-6 h-0.5 bg-teal-300 rotate-45 translate-x-3"></div>
                      <div className="absolute w-6 h-0.5 bg-teal-300 -rotate-45 -translate-x-3"></div>
                      <div className="absolute w-6 h-0.5 bg-teal-300 rotate-[125deg] translate-y-3"></div>
                      <div className="absolute w-2 h-2 bg-teal-500 rounded-full opacity-75 translate-x-6"></div>
                      <div className="absolute w-2 h-2 bg-teal-500 rounded-full opacity-75 -translate-x-6"></div>
                      <div className="absolute w-2 h-2 bg-teal-500 rounded-full opacity-75 translate-y-6"></div>
                    </div>
                  </div>
                </div>
              </motion.div>
              
              <motion.div 
                initial={{ opacity: 0, scale: 0.9 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ delay: 0.6 }}
                whileHover={{ y: -5 }}
                className="bg-white dark:bg-neutral-900 rounded-xl shadow-lg overflow-hidden border border-gray-200 dark:border-neutral-800"
              >
                <div className="h-2 bg-gradient-to-r from-cyan-500 to-blue-500"></div>
                <div className="p-6">
                  <div className="mb-4 bg-cyan-100 dark:bg-cyan-900/30 w-12 h-12 flex items-center justify-center rounded-lg">
                    <Lock className="w-6 h-6 text-cyan-600 dark:text-cyan-400" />
                  </div>
                  <h3 className="text-lg font-semibold mb-2 text-gray-800 dark:text-gray-200">访问控制</h3>
                  <p className="text-gray-600 dark:text-gray-400 text-sm">
                    细粒度的权限管理，确保关键信息安全。支持基于角色、部门和文档级别的访问控制。
                  </p>
                  <div className="mt-4">
                    <div className="space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-gray-500 dark:text-gray-400">访问控制粒度</span>
                        <div className="flex space-x-1">
                          {[1, 2, 3, 4, 5].map((i) => (
                            <div 
                              key={i} 
                              className={`w-2 h-2 rounded-full ${i <= 5 ? 'bg-cyan-500' : 'bg-gray-300 dark:bg-gray-600'}`}
                            ></div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </motion.div>
            </div>
          </motion.div>

          {/* 核心功能详解 */}
          <div className="mb-16">
            <h2 className="mb-8 text-center text-2xl font-bold">核心功能详解</h2>
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              <motion.div
                whileHover={{ y: -5 }}
                className="rounded-lg border bg-card p-6 shadow-sm"
              >
                <div className="mb-4 inline-flex rounded-lg bg-primary/10 p-3">
                  <FileText className="h-6 w-6 text-primary" />
                </div>
                <h3 className="mb-2 text-xl font-semibold">多模态摄取</h3>
                <p className="text-muted-foreground">
                  解析、处理多种格式文件（.txt、.pdf、.json、.png、.mp3等），将非结构化内容转换为结构化数据。
                </p>
              </motion.div>
              
              <motion.div
                whileHover={{ y: -5 }}
                className="rounded-lg border bg-card p-6 shadow-sm"
              >
                <div className="mb-4 inline-flex rounded-lg bg-purple-500/10 p-3">
                  <Search className="h-6 w-6 text-purple-500" />
                </div>
                <h3 className="mb-2 text-xl font-semibold">混合搜索</h3>
                <p className="text-muted-foreground">
                  结合语义搜索和关键词搜索，通过倒数排序融合实现增强相关性，提供更准确的搜索结果。
                </p>
              </motion.div>
              
              <motion.div
                whileHover={{ y: -5 }}
                className="rounded-lg border bg-card p-6 shadow-sm"
              >
                <div className="mb-4 inline-flex rounded-lg bg-blue-500/10 p-3">
                  <Network className="h-6 w-6 text-blue-500" />
                </div>
                <h3 className="mb-2 text-xl font-semibold">知识图谱</h3>
                <p className="text-muted-foreground">
                  自动提取实体和关系，构建知识图谱，捕捉信息之间的复杂联系，支持图形化查询和推理。
                </p>
              </motion.div>
              
              <motion.div
                whileHover={{ y: -5 }}
                className="rounded-lg border bg-card p-6 shadow-sm"
              >
                <div className="mb-4 inline-flex rounded-lg bg-green-500/10 p-3">
                  <Brain className="h-6 w-6 text-green-500" />
                </div>
                <h3 className="mb-2 text-xl font-semibold">代理式RAG</h3>
                <p className="text-muted-foreground">
                  强大的深度研究代理与RAG集成，智能调度检索策略，基于知识库提供精准、连贯的信息。
                </p>
              </motion.div>
              
              <motion.div
                whileHover={{ y: -5 }}
                className="rounded-lg border bg-card p-6 shadow-sm"
              >
                <div className="mb-4 inline-flex rounded-lg bg-amber-500/10 p-3">
                  <Code className="h-6 w-6 text-amber-500" />
                </div>
                <h3 className="mb-2 text-xl font-semibold">MCP支持</h3>
                <p className="text-muted-foreground">
                  集成Model Context Protocol，增强大型语言模型检索和搜索能力，实现更智能的交互和信息获取。
                </p>
              </motion.div>
              
              <motion.div
                whileHover={{ y: -5 }}
                className="rounded-lg border bg-card p-6 shadow-sm"
              >
                <div className="mb-4 inline-flex rounded-lg bg-rose-500/10 p-3">
                  <Server className="h-6 w-6 text-rose-500" />
                </div>
                <h3 className="mb-2 text-xl font-semibold">自托管支持</h3>
                <p className="text-muted-foreground">
                  提供Docker部署方案，便于本地环境搭建完整但问智能体系统，支持直观的配置文件定制。
                </p>
              </motion.div>
            </div>
          </div>

          {/* MCP功能特性 */}
          <div className="mx-auto mb-16 max-w-4xl">
            <div className="rounded-xl border-2 border-amber-500 p-8 bg-amber-50/5">
              <h2 className="text-2xl font-bold mb-6 text-center">MCP功能特性</h2>
              
              <div className="mb-8">
                <div className="relative h-48 rounded-lg overflow-hidden">
                  <div className="absolute inset-0 bg-gradient-to-br from-amber-500/20 to-orange-500/20"></div>
                  <div className="absolute inset-0 overflow-hidden">
                    <svg width="100%" height="100%" viewBox="0 0 800 500" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid meet">
                      {/* 背景 */}
                      <rect width="800" height="500" fill="#FFFBEB" opacity="0.7" rx="15" ry="15" />
                      <text x="400" y="40" fontFamily="Arial" fontSize="22" fontWeight="bold" textAnchor="middle" fill="#92400E">MCP集成架构</text>
                      <text x="400" y="70" fontFamily="Arial" fontSize="14" textAnchor="middle" fill="#B45309">Model Context Protocol与但问智能体系统的集成</text>

                      {/* LLM区域 */}
                      <rect x="50" y="100" width="200" height="120" rx="10" ry="10" fill="#FFFFFF" stroke="#F59E0B" strokeWidth="2" />
                      <text x="150" y="125" fontFamily="Arial" fontSize="16" fontWeight="bold" textAnchor="middle" fill="#B45309">大型语言模型</text>
                      <rect x="70" y="140" width="160" height="30" rx="5" ry="5" fill="#FDE68A" stroke="#F59E0B" strokeWidth="1" />
                      <text x="150" y="160" fontFamily="Arial" fontSize="13" textAnchor="middle" fill="#B45309">Claude</text>
                      <rect x="70" y="180" width="75" height="25" rx="5" ry="5" fill="#FDE68A" stroke="#F59E0B" strokeWidth="1" />
                      <text x="107" y="197" fontFamily="Arial" fontSize="12" textAnchor="middle" fill="#B45309">GPT</text>
                      <rect x="155" y="180" width="75" height="25" rx="5" ry="5" fill="#FDE68A" stroke="#F59E0B" strokeWidth="1" />
                      <text x="192" y="197" fontFamily="Arial" fontSize="12" textAnchor="middle" fill="#B45309">其他LLM</text>

                      {/* MCP服务器 */}
                      <rect x="300" y="80" width="200" height="300" rx="10" ry="10" fill="#FFFBEB" stroke="#F59E0B" strokeWidth="3" />
                      <text x="400" y="110" fontFamily="Arial" fontSize="18" fontWeight="bold" textAnchor="middle" fill="#92400E">MCP服务器</text>
                      
                      {/* MCP内部组件 */}
                      <rect x="320" y="135" width="160" height="40" rx="5" ry="5" fill="#FDE68A" stroke="#F59E0B" strokeWidth="1.5" />
                      <text x="400" y="160" fontFamily="Arial" fontSize="14" textAnchor="middle" fill="#B45309">工具管理器</text>
                      
                      <rect x="320" y="185" width="160" height="40" rx="5" ry="5" fill="#FDE68A" stroke="#F59E0B" strokeWidth="1.5" />
                      <text x="400" y="210" fontFamily="Arial" fontSize="14" textAnchor="middle" fill="#B45309">搜索工具包</text>

                      <rect x="320" y="235" width="160" height="40" rx="5" ry="5" fill="#FDE68A" stroke="#F59E0B" strokeWidth="1.5" />
                      <text x="400" y="260" fontFamily="Arial" fontSize="14" textAnchor="middle" fill="#B45309">RAG工具包</text>

                      <rect x="320" y="285" width="160" height="40" rx="5" ry="5" fill="#FDE68A" stroke="#F59E0B" strokeWidth="1.5" />
                      <text x="400" y="310" fontFamily="Arial" fontSize="14" textAnchor="middle" fill="#B45309">上下文管理器</text>

                      <rect x="320" y="335" width="160" height="30" rx="5" ry="5" fill="#FDE68A" stroke="#F59E0B" strokeWidth="1" />
                      <text x="400" y="355" fontFamily="Arial" fontSize="12" textAnchor="middle" fill="#B45309">API适配器</text>

                      {/* 但问智能体系统 */}
                      <rect x="550" y="100" width="200" height="250" rx="10" ry="10" fill="#FFFFFF" stroke="#3B82F6" strokeWidth="2" />
                      <text x="650" y="125" fontFamily="Arial" fontSize="16" fontWeight="bold" textAnchor="middle" fill="#1E40AF">但问智能体系统</text>

                      {/* 但问智能体系统组件 */}
                      <rect x="570" y="145" width="160" height="30" rx="5" ry="5" fill="#DBEAFE" stroke="#3B82F6" strokeWidth="1" />
                      <text x="650" y="165" fontFamily="Arial" fontSize="13" textAnchor="middle" fill="#2563EB">API接口</text>
                      
                      <rect x="570" y="185" width="160" height="30" rx="5" ry="5" fill="#DBEAFE" stroke="#3B82F6" strokeWidth="1" />
                      <text x="650" y="205" fontFamily="Arial" fontSize="13" textAnchor="middle" fill="#2563EB">向量搜索服务</text>
                      
                      <rect x="570" y="225" width="160" height="30" rx="5" ry="5" fill="#DBEAFE" stroke="#3B82F6" strokeWidth="1" />
                      <text x="650" y="245" fontFamily="Arial" fontSize="13" textAnchor="middle" fill="#2563EB">图谱搜索服务</text>
                      
                      <rect x="570" y="265" width="160" height="30" rx="5" ry="5" fill="#DBEAFE" stroke="#3B82F6" strokeWidth="1" />
                      <text x="650" y="285" fontFamily="Arial" fontSize="13" textAnchor="middle" fill="#2563EB">知识库管理</text>
                      
                      <rect x="570" y="305" width="160" height="30" rx="5" ry="5" fill="#DBEAFE" stroke="#3B82F6" strokeWidth="1" />
                      <text x="650" y="325" fontFamily="Arial" fontSize="13" textAnchor="middle" fill="#2563EB">文档索引服务</text>

                      {/* 连接线 */}
                      <line x1="250" y1="150" x2="300" y2="150" stroke="#F59E0B" strokeWidth="2" strokeDasharray="5,2" />
                      <text x="275" y="140" fontFamily="Arial" fontSize="10" textAnchor="middle" fill="#92400E">API调用</text>
                      
                      <line x1="500" y1="200" x2="550" y2="200" stroke="#3B82F6" strokeWidth="2" />
                      <text x="525" y="190" fontFamily="Arial" fontSize="10" textAnchor="middle" fill="#1E40AF">搜索请求</text>
                      
                      <line x1="500" y1="250" x2="550" y2="250" stroke="#3B82F6" strokeWidth="2" />
                      <text x="525" y="240" fontFamily="Arial" fontSize="10" textAnchor="middle" fill="#1E40AF">RAG请求</text>
                      
                      <line x1="550" y1="300" x2="500" y2="300" stroke="#3B82F6" strokeWidth="2" strokeDasharray="5,2" />
                      <text x="525" y="290" fontFamily="Arial" fontSize="10" textAnchor="middle" fill="#1E40AF">搜索结果</text>

                      {/* 用户请求流 */}
                      <path d="M150,50 Q150,30 170,30 L630,30 Q650,30 650,50 L650,100" fill="none" stroke="#D97706" strokeWidth="2" strokeDasharray="5,3" />
                      <text x="400" y="20" fontFamily="Arial" fontSize="12" textAnchor="middle" fill="#92400E">用户问题 →</text>
                      
                      {/* 响应流 */}
                      <path d="M150,220 Q150,400 400,400 L400,380" fill="none" stroke="#3B82F6" strokeWidth="2" strokeDasharray="5,3" />
                      <text x="200" y="390" fontFamily="Arial" fontSize="12" textAnchor="middle" fill="#2563EB">← 增强回复</text>
                    </svg>
                  </div>
                  <div className="absolute bottom-3 right-3 bg-white/80 dark:bg-black/40 text-amber-600 text-xs px-2 py-1 rounded-full backdrop-blur-sm">
                    MCP服务模式
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* 应用场景 */}
          <div className="mb-16">
            <h2 className="mb-8 text-center text-2xl font-bold">适用场景</h2>
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
              <div className="rounded-lg border bg-card p-6 shadow-sm">
                <h3 className="mb-2 text-lg font-semibold">企业知识库</h3>
                <p className="text-sm text-muted-foreground">
                  整合企业内部文档、流程和知识，打造智能检索系统，提升信息获取效率
                </p>
              </div>
              
              <div className="rounded-lg border bg-card p-6 shadow-sm">
                <h3 className="mb-2 text-lg font-semibold">智能客服</h3>
                <p className="text-sm text-muted-foreground">
                  构建基于知识库的智能客服系统，提供准确一致的自动化回复和服务支持
                </p>
              </div>
              
              <div className="rounded-lg border bg-card p-6 shadow-sm">
                <h3 className="mb-2 text-lg font-semibold">研究助手</h3>
                <p className="text-sm text-muted-foreground">
                  支持科研人员高效检索和分析大量文献资料，辅助研究过程和决策
                </p>
              </div>
              
              <div className="rounded-lg border bg-card p-6 shadow-sm">
                <h3 className="mb-2 text-lg font-semibold">内容创作</h3>
                <p className="text-sm text-muted-foreground">
                  为内容创作者提供资料检索、事实核查和创意支持，提升创作质量和效率
                </p>
              </div>
            </div>
          </div>

          {/* 快速开始 */}
          <div className="mx-auto mb-16 max-w-4xl">
            <div className="rounded-xl border-2 border-green-500 p-8 bg-green-50/5">
              <h2 className="text-2xl font-bold mb-6 text-center">快速开始</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="flex flex-col items-center text-center">
                  <div className="mb-4 rounded-full bg-green-100 p-3">
                    <Server className="h-6 w-6 text-green-600" />
                  </div>
                  <h3 className="mb-2 font-semibold">1. 部署系统</h3>
                  <p className="text-sm text-muted-foreground">
                    通过Docker容器快速部署但问智能体系统到您的本地或云环境
                  </p>
                </div>
                
                <div className="flex flex-col items-center text-center">
                  <div className="mb-4 rounded-full bg-green-100 p-3">
                    <Database className="h-6 w-6 text-green-600" />
                  </div>
                  <h3 className="mb-2 font-semibold">2. 构建知识库</h3>
                  <p className="text-sm text-muted-foreground">
                    上传文档，自动处理和索引内容，构建智能知识库和知识图谱
                  </p>
                </div>
                
                <div className="flex flex-col items-center text-center">
                  <div className="mb-4 rounded-full bg-green-100 p-3">
                    <Code className="h-6 w-6 text-green-600" />
                  </div>
                  <h3 className="mb-2 font-semibold">3. 接入应用</h3>
                  <p className="text-sm text-muted-foreground">
                    通过API或MCP集成将智能体接入您的应用，实现强大的检索功能
                  </p>
                </div>
              </div>
              
              <div className="mt-8 flex justify-center">
                <Link
                  href="/dashboard"
                  className="rounded-md bg-green-600 px-6 py-3 text-base font-medium text-white hover:bg-green-700 inline-flex items-center"
                >
                  开始使用
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Link>
              </div>
            </div>
          </div>

          {/* 联系我们 */}
          <div className="mx-auto mb-16 max-w-3xl rounded-xl border p-8 shadow-sm">
            <h2 className="text-2xl font-bold mb-6 text-center">联系我们</h2>
            <p className="text-center mb-6">
              如果您对但问智能体系统有任何疑问或需要定制解决方案，请随时与我们联系
            </p>
            <div className="flex justify-center">
              <Link
                href="/contact"
                className="rounded-md bg-primary px-6 py-3 text-base font-medium text-white hover:bg-primary/90"
              >
                获取技术支持
              </Link>
            </div>
          </div>

          {/* 用户界面 */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1 }}
            className="mx-auto mb-16 max-w-5xl"
          >
            <h2 className="text-2xl font-bold mb-8 text-center bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-purple-600">用户界面与交互</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
              <motion.div 
                whileHover={{ scale: 1.02 }}
                className="rounded-xl overflow-hidden shadow-lg border dark:border-neutral-800 bg-white dark:bg-neutral-900"
              >
                <div className="p-1 bg-gradient-to-r from-blue-500 to-purple-500"></div>
                <div className="p-6">
                  <h3 className="text-xl font-semibold mb-3 flex items-center text-gray-800 dark:text-gray-200">
                    <Search className="w-5 h-5 mr-2 text-blue-500" />
                    问答界面
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400 mb-4">
                    直观的问答界面，支持自然语言查询，并提供上下文相关的回答和引用来源。
                  </p>
                  <ul className="space-y-2">
                    <li className="flex items-start">
                      <Check className="w-4 h-4 text-green-500 mt-1 mr-2 flex-shrink-0" />
                      <span className="text-sm text-gray-600 dark:text-gray-400">实时打字效果和思考指示器</span>
                    </li>
                    <li className="flex items-start">
                      <Check className="w-4 h-4 text-green-500 mt-1 mr-2 flex-shrink-0" />
                      <span className="text-sm text-gray-600 dark:text-gray-400">支持引用文档和源链接</span>
                    </li>
                    <li className="flex items-start">
                      <Check className="w-4 h-4 text-green-500 mt-1 mr-2 flex-shrink-0" />
                      <span className="text-sm text-gray-600 dark:text-gray-400">对话历史管理和上下文保持</span>
                    </li>
                  </ul>
                </div>
              </motion.div>
              
              <motion.div 
                whileHover={{ scale: 1.02 }}
                className="rounded-xl overflow-hidden shadow-lg border dark:border-neutral-800 bg-white dark:bg-neutral-900"
              >
                <div className="p-1 bg-gradient-to-r from-purple-500 to-pink-500"></div>
                <div className="p-6">
                  <h3 className="text-xl font-semibold mb-3 flex items-center text-gray-800 dark:text-gray-200">
                    <Settings className="w-5 h-5 mr-2 text-purple-500" />
                    管理控制台
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400 mb-4">
                    强大的管理界面，用于上传、组织和管理知识库内容，提供详细的分析和见解。
                  </p>
                  <ul className="space-y-2">
                    <li className="flex items-start">
                      <Check className="w-4 h-4 text-green-500 mt-1 mr-2 flex-shrink-0" />
                      <span className="text-sm text-gray-600 dark:text-gray-400">批量文档上传和进度跟踪</span>
                    </li>
                    <li className="flex items-start">
                      <Check className="w-4 h-4 text-green-500 mt-1 mr-2 flex-shrink-0" />
                      <span className="text-sm text-gray-600 dark:text-gray-400">知识分类和标签管理系统</span>
                    </li>
                    <li className="flex items-start">
                      <Check className="w-4 h-4 text-green-500 mt-1 mr-2 flex-shrink-0" />
                      <span className="text-sm text-gray-600 dark:text-gray-400">使用分析和热门问题洞察</span>
                    </li>
                  </ul>
                </div>
              </motion.div>
            </div>
            
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.3 }}
              className="relative rounded-xl overflow-hidden shadow-lg"
            >
              <div className="p-6 bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-gray-900 dark:to-gray-800 border border-blue-100 dark:border-gray-700">
                <div className="flex flex-col md:flex-row items-center justify-between gap-6">
                  <div className="flex-1">
                    <h3 className="text-xl font-semibold mb-3 text-gray-800 dark:text-gray-200">交互演示</h3>
                    <p className="text-gray-600 dark:text-gray-400 mb-4">
                      通过实际示例体验但问智能体的强大功能，测试各种查询场景和复杂问题。
                    </p>
                    <div className="space-y-2">
                      <div className="p-3 rounded-lg bg-white/80 dark:bg-gray-800/80 shadow-sm border border-gray-200 dark:border-gray-700">
                        <p className="text-sm text-gray-800 dark:text-gray-300">
                          <span className="font-medium text-blue-600 dark:text-blue-400">示例问题 1:</span> "如何设置向量检索的相似度阈值？"
                        </p>
                      </div>
                      <div className="p-3 rounded-lg bg-white/80 dark:bg-gray-800/80 shadow-sm border border-gray-200 dark:border-gray-700">
                        <p className="text-sm text-gray-800 dark:text-gray-300">
                          <span className="font-medium text-blue-600 dark:text-blue-400">示例问题 2:</span> "但问智能体支持哪些文件格式？"
                        </p>
                      </div>
                    </div>
                    <button className="mt-4 px-4 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-md shadow-md hover:shadow-lg transition-all">
                      尝试演示
                    </button>
                  </div>
                  <div className="flex-1 relative">
                    <div className="absolute -top-12 -right-12 w-64 h-64 bg-blue-400/10 dark:bg-blue-500/10 rounded-full blur-3xl"></div>
                    <div className="relative p-4 rounded-xl bg-white/70 dark:bg-gray-800/70 backdrop-blur-sm border border-gray-200 dark:border-gray-700 floating-effect">
                      <div className="flex items-center mb-3">
                        <div className="w-3 h-3 rounded-full bg-red-500 mr-2"></div>
                        <div className="w-3 h-3 rounded-full bg-yellow-500 mr-2"></div>
                        <div className="w-3 h-3 rounded-full bg-green-500"></div>
                        <div className="ml-auto text-sm text-gray-500 dark:text-gray-400">知识库问答</div>
                      </div>
                      <div className="chat-container h-32 overflow-hidden">
                        <div className="user-message p-2 mb-2 bg-gray-100 dark:bg-gray-700 rounded-lg text-xs">
                          请问但问智能体如何处理多语言文档？
                        </div>
                        <div className="system-message p-2 bg-blue-50 dark:bg-blue-900/20 rounded-lg text-xs">
                          <div className="typing-indicator">
                            <span className="dot"></span>
                            <span className="dot"></span>
                            <span className="dot"></span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          </motion.div>

          {/* 调用行动 */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.3 }}
            className="mx-auto mb-16 max-w-4xl"
          >
            <div className="relative rounded-2xl overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-br from-blue-600 to-purple-700"></div>
              <div className="absolute inset-0 opacity-30 bg-pattern-grid"></div>
              <div className="absolute top-0 left-0 right-0 h-1/3 bg-gradient-to-b from-white/10 to-transparent"></div>
              <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-white/50 to-transparent"></div>
              
              {/* 圆点装饰 */}
              <div className="absolute top-12 left-12 w-24 h-24 rounded-full bg-purple-500/20 blur-xl"></div>
              <div className="absolute bottom-12 right-12 w-32 h-32 rounded-full bg-blue-500/20 blur-xl"></div>
              
              <div className="relative px-8 py-12 text-center text-white">
                <h2 className="text-3xl font-bold mb-4">立即体验但问智能体</h2>
                <p className="text-lg mb-8 max-w-2xl mx-auto text-blue-100">
                  将您的文档转化为智能知识库，获得精准答案，提升团队效率和客户满意度
                </p>
                <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                  <button className="px-6 py-3 bg-white text-blue-700 rounded-full font-medium hover:shadow-lg transition-shadow duration-300 min-w-[160px]">
                    免费试用
                  </button>
                  <button className="px-6 py-3 bg-blue-900/30 text-white border border-blue-400/30 rounded-full font-medium backdrop-blur-sm hover:bg-blue-900/40 transition-colors duration-300 min-w-[160px]">
                    预约演示
                  </button>
                </div>
                
                <div className="mt-8 text-sm text-blue-200/80">
                  <p>无需信用卡 · 14天免费试用 · 企业级支持</p>
                </div>
              </div>
            </div>
          </motion.div>
          
          {/* 页脚装饰 */}
          <div className="relative">
            <div className="absolute inset-x-0 bottom-0 h-px bg-gradient-to-r from-transparent via-gray-300 dark:via-gray-700 to-transparent"></div>
          </div>
        </div>
      </main>

      {/* 页脚 */}
      <footer className="border-t py-8">
        <div className="container mx-auto px-4 text-center">
          <p className="text-sm text-muted-foreground">
            © {new Date().getFullYear()} 但问智能体系统平台. 保留所有权利.
          </p>
        </div>
      </footer>
    </div>
  )
} 