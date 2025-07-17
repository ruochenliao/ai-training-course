'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import Link from 'next/link'
import Image from 'next/image'

// 导入图标
import { ArrowRight, Brain, Database, MessageSquare, FileText } from '@/components/ui/icons'

export default function Home() {
  const [hoveredCard, setHoveredCard] = useState<number | null>(null)
  
  const features = [
    {
      id: 1,
      title: '智能客服系统',
      description: '对接公司现有业务系统回答用户问题，基于智能体调用工具完成业务处理',
      icon: <MessageSquare className="h-6 w-6" />,
      link: '/customer-service',
      color: 'from-emerald-600 to-teal-600',
    },
    {
      id: 2,
      title: 'Text2SQL数据分析智能体',
      description: '将自然语言问题转换为SQL语句并执行，返回命令、解释、结果及图形化报表',
      icon: <Database className="h-6 w-6" />,
      link: '/text2sql',
      color: 'from-purple-600 to-pink-600',
    },
    {
      id: 3,
      title: '企业级知识库问答智能体',
      description: '结合传统RAG、NanoGraphRAG、多模态RAG等技术为用户提供精确的知识召回并加工',
      icon: <Brain className="h-6 w-6" />,
      link: '/knowledge-base',
      color: 'from-blue-600 to-indigo-600',
    },
    {
      id: 4,
      title: '企业内部文案创作智能体',
      description: '根据用户意图选择合适文案模板，借助RAG与LLM完成高质量文案生成',
      icon: <FileText className="h-6 w-6" />,
      link: '/copywriting',
      color: 'from-orange-600 to-amber-600',
    }
  ]

  return (
    <main className="flex min-h-screen flex-col bg-[var(--background)]">
      {/* 导航栏 */}
      <nav className="gemini-navbar">
        <div className="container mx-auto flex items-center justify-between px-4 py-3">
          <div className="flex items-center space-x-2">
            <Brain className="h-8 w-8 text-google-blue" />
            <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-google-blue to-google-purple">但问智能体</h1>
          </div>
          <div className="hidden md:flex space-x-8">
            {features.map((feature) => (
              <Link 
                key={feature.id}
                href={feature.link}
                className="text-sm font-medium text-[var(--foreground)] transition-colors hover:text-[var(--primary)]"
              >
                {feature.title}
              </Link>
            ))}
          </div>
          <div className="flex items-center space-x-4">
            <Link
              href="/login"
              className="gemini-button-text"
            >
              登录
            </Link>
            <Link
              href="/register"
              className="gemini-button-primary"
            >
              免费注册
            </Link>
          </div>
        </div>
      </nav>

      {/* 主页横幅 */}
      <section className="relative isolate overflow-hidden pt-24 lg:pt-32 wave-background">
        <div className="container mx-auto px-4 py-16 md:py-24">
          <div className="grid items-center gap-12 lg:grid-cols-2">
            <div>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
              >
                <h1 className="mb-6 text-4xl font-extrabold tracking-tight md:text-5xl lg:text-6xl text-[var(--foreground)]">
                  让<span className="gemini-gradient-text font-extrabold">AI智能体</span><br />
                  为企业创造新价值
                </h1>
                <p className="mb-8 text-lg text-[var(--muted)]">
                  但问智能体综合应用平台整合多种先进AI技术，提供企业级知识管理、数据分析、客户服务和创意支持，让您的企业实现智能化转型。
                </p>
                <div className="flex flex-wrap gap-4">
                  <Link href="/register" className="gemini-button-primary">
                    免费开始使用
                  </Link>
                  <Link href="/demo" className="gemini-button-secondary">
                    查看演示
                  </Link>
                </div>
              </motion.div>
            </div>
            <div className="relative">
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.6, delay: 0.2 }}
                className="relative"
              >
                <div className="relative overflow-hidden rounded-2xl shadow-2xl">
                  <div className="bg-gradient-to-br from-google-blue via-google-purple to-google-red p-1">
                    <div className="bg-white dark:bg-gray-900 rounded-xl p-4">
                      <div className="flex items-center space-x-2 mb-4">
                        <div className="h-3 w-3 rounded-full bg-red-500"></div>
                        <div className="h-3 w-3 rounded-full bg-yellow-500"></div>
                        <div className="h-3 w-3 rounded-full bg-green-500"></div>
                      </div>
                      <div className="space-y-4 p-2">
                        <div className="flex items-start space-x-3">
                          <div className="h-8 w-8 flex-shrink-0 rounded-full bg-gray-200 flex items-center justify-center text-gray-500">
                            U
                          </div>
                          <div className="rounded-2xl rounded-tl-none bg-gray-100 dark:bg-gray-800 p-3">
                            <p className="text-[var(--foreground)]">如何使用但问智能体平台分析我的销售数据？</p>
                          </div>
                        </div>
                        <div className="flex items-start space-x-3">
                          <div className="h-8 w-8 flex-shrink-0 rounded-full bg-google-blue flex items-center justify-center text-white">
                            <Brain className="h-5 w-5" />
                          </div>
                          <div className="rounded-2xl rounded-tl-none bg-blue-50 dark:bg-gray-700 p-3">
                            <p className="text-[var(--foreground)]">您可以使用我们的Text2SQL智能体功能，只需用自然语言描述您的分析需求，系统将自动转换为SQL查询并生成可视化报表。例如，您可以输入"显示过去6个月各地区的销售增长趋势"，系统会自动生成相应的数据分析结果。</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="absolute -z-10 top-1/2 left-1/2 h-40 w-80 -translate-x-1/2 -translate-y-1/2 rounded-full bg-google-blue/20 blur-3xl"></div>
              </motion.div>
            </div>
          </div>
        </div>

        {/* 分隔波浪 */}
        <div className="absolute bottom-0 left-0 w-full overflow-hidden leading-none">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 120" preserveAspectRatio="none" className="h-12 w-full text-[var(--background)]">
            <path d="M0,0V46.29c47.79,22.2,103.59,32.17,158,28,70.36-5.37,136.33-33.31,206.8-37.5C438.64,32.43,512.34,53.67,583,72.05c69.27,18,138.3,24.88,209.4,13.08,36.15-6,69.85-17.84,104.45-29.34C989.49,25,1113-14.29,1200,52.47V0Z" fill="currentColor" opacity=".25" />
            <path d="M0,0V15.81C13,36.92,27.64,56.86,47.69,72.05,99.41,111.27,165,111,224.58,91.58c31.15-10.15,60.09-26.07,89.67-39.8,40.92-19,84.73-46,130.83-49.67,36.26-2.85,70.9,9.42,98.6,31.56,31.77,25.39,62.32,62,103.63,73,40.44,10.79,81.35-6.69,119.13-24.28s75.16-39,116.92-43.05c59.73-5.85,113.28,22.88,168.9,38.84,30.2,8.66,59,6.17,87.09-7.5,22.43-10.89,48-26.93,60.65-49.24V0Z" fill="currentColor" opacity=".5" />
            <path d="M0,0V5.63C149.93,59,314.09,71.32,475.83,42.57c43-7.64,84.23-20.12,127.61-26.46,59-8.63,112.48,12.24,165.56,35.4C827.93,77.22,886,95.24,951.2,90c86.53-7,172.46-45.71,248.8-84.81V0Z" fill="currentColor" />
          </svg>
        </div>
      </section>

      {/* 特色功能部分 */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <div className="mb-16 text-center">
            <h2 className="mb-4 text-3xl font-bold sm:text-4xl text-[var(--foreground)]">强大的智能体功能</h2>
            <p className="mx-auto max-w-3xl text-lg text-[var(--muted)]">
              探索我们集成的智能体解决方案，为您的企业带来智能化转型
            </p>
          </div>
          <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-4">
            {features.map((feature, index) => (
              <motion.div
                key={feature.id}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="group"
              >
                <Link href={feature.link}>
                  <div className="h-full overflow-hidden rounded-2xl border border-[var(--border)] bg-[var(--card)] p-6 transition-all duration-300 hover:shadow-lg">
                    <div className={`mb-4 inline-flex rounded-xl bg-gradient-to-r ${feature.color} p-3 text-white`}>
                      {feature.icon}
                    </div>
                    <h3 className="mb-2 text-xl font-bold text-[var(--foreground)] group-hover:text-[var(--primary)]">{feature.title}</h3>
                    <p className="mb-4 text-[var(--muted)]">{feature.description}</p>
                    <div className="flex items-center text-sm font-medium text-[var(--primary)] opacity-0 transition-opacity group-hover:opacity-100">
                      立即探索
                      <ArrowRight className="ml-1 h-4 w-4" />
                    </div>
                  </div>
                </Link>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* 技术优势部分 */}
      <section className="py-20 bg-gradient-to-b from-white to-blue-50 dark:from-gray-900 dark:to-gray-800">
        <div className="container mx-auto px-4">
          <div className="mb-16 text-center">
            <h2 className="mb-4 text-3xl font-bold sm:text-4xl text-[var(--foreground)]">技术优势</h2>
            <p className="mx-auto max-w-3xl text-lg text-[var(--muted)]">
              基于前沿AI技术，打造高效、精准的企业智能解决方案
            </p>
          </div>
          <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
            {[
              {
                title: "传统RAG与NanoGraphRAG",
                description: "融合传统检索增强和基于知识图谱的语义检索，提供更准确的知识问答体验",
                icon: <svg className="h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" /></svg>,
                color: "text-google-blue"
              },
              {
                title: "智能体开发框架",
                description: "基于最新的大模型智能体框架，实现复杂任务推理和规划能力",
                icon: <svg className="h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" /></svg>,
                color: "text-google-purple"
              },
              {
                title: "多模态感知能力",
                description: "支持图像、文本等多种数据类型的处理和理解，实现全方位信息获取",
                icon: <svg className="h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2" /></svg>,
                color: "text-google-red"
              },
              {
                title: "工具调用能力",
                description: "智能体可调用各种API和工具，实现业务流程自动化和系统集成",
                icon: <svg className="h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>,
                color: "text-google-yellow"
              },
              {
                title: "企业知识安全",
                description: "严格的数据隐私保护和访问控制机制，保障企业知识资产安全",
                icon: <svg className="h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>,
                color: "text-google-green"
              },
              {
                title: "高级嵌入模型",
                description: "采用先进的嵌入技术，实现精准的语义理解和相似度匹配",
                icon: <svg className="h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 4a2 2 0 114 0v1a1 1 0 001 1h3a1 1 0 011 1v3a1 1 0 01-1 1h-1a2 2 0 100 4h1a1 1 0 011 1v3a1 1 0 01-1 1h-3a1 1 0 01-1-1v-1a2 2 0 10-4 0v1a1 1 0 01-1 1H7a1 1 0 01-1-1v-3a1 1 0 00-1-1H4a2 2 0 110-4h1a1 1 0 001-1V7a1 1 0 011-1h3a1 1 0 001-1V4z" /></svg>,
                color: "text-google-blue"
              }
            ].map((tech, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: i * 0.1 }}
                className="gemini-card"
              >
                <div className={`mb-4 inline-flex items-center justify-center rounded-full p-3 ${tech.color} bg-opacity-10`}>
                  <div className={tech.color}>{tech.icon}</div>
                </div>
                <h3 className="mb-2 text-xl font-bold text-[var(--foreground)]">{tech.title}</h3>
                <p className="text-[var(--muted)]">{tech.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA部分 */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <div className="mx-auto max-w-4xl rounded-2xl bg-gradient-to-r from-google-blue to-google-purple p-[2px]">
            <div className="rounded-2xl bg-white p-10 dark:bg-gray-800">
              <div className="text-center">
                <h2 className="mb-4 text-3xl font-bold text-[var(--foreground)]">准备好开始使用了吗？</h2>
                <p className="mb-8 text-lg text-[var(--muted)]">
                  立即加入但问智能体平台，体验AI为企业带来的变革力量
                </p>
                <div className="flex flex-wrap justify-center gap-4">
                  <Link href="/register" className="gemini-button-primary">
                    免费注册
                  </Link>
                  <Link href="/contact" className="gemini-button-secondary">
                    联系我们
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 页脚 */}
      <footer className="bg-[var(--card)] py-10">
        <div className="container mx-auto px-4">
          <div className="flex flex-wrap justify-between">
            <div className="mb-8 w-full md:mb-0 md:w-1/3">
              <div className="flex items-center space-x-2 mb-4">
                <Brain className="h-6 w-6 text-google-blue" />
                <span className="text-xl font-bold text-[var(--foreground)]">但问智能体</span>
              </div>
              <p className="max-w-xs text-sm text-[var(--muted)]">
                企业级智能体解决方案提供商，致力于用AI为企业创造价值
              </p>
              <div className="mt-4 flex space-x-4">
                {['twitter', 'facebook', 'linkedin', 'github'].map((social) => (
                  <a key={social} href={`#${social}`} className="text-[var(--muted)] hover:text-[var(--primary)]">
                    <span className="sr-only">{social}</span>
                    <div className="h-6 w-6 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
                      <span className="text-xs">{social[0].toUpperCase()}</span>
                    </div>
                  </a>
                ))}
              </div>
            </div>
            <div className="grid grid-cols-2 gap-8 sm:grid-cols-3 md:w-2/3">
              <div>
                <h4 className="mb-4 text-sm font-semibold uppercase tracking-wider text-[var(--foreground)]">解决方案</h4>
                <ul className="space-y-2 text-sm">
                  {features.map((feature) => (
                    <li key={feature.id}>
                      <Link href={feature.link} className="text-[var(--muted)] hover:text-[var(--primary)]">
                        {feature.title}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <h4 className="mb-4 text-sm font-semibold uppercase tracking-wider text-[var(--foreground)]">资源</h4>
                <ul className="space-y-2 text-sm">
                  <li><Link href="/docs" className="text-[var(--muted)] hover:text-[var(--primary)]">文档</Link></li>
                  <li><Link href="/blog" className="text-[var(--muted)] hover:text-[var(--primary)]">博客</Link></li>
                  <li><Link href="/case-studies" className="text-[var(--muted)] hover:text-[var(--primary)]">案例研究</Link></li>
                </ul>
              </div>
              <div>
                <h4 className="mb-4 text-sm font-semibold uppercase tracking-wider text-[var(--foreground)]">关于</h4>
                <ul className="space-y-2 text-sm">
                  <li><Link href="/about" className="text-[var(--muted)] hover:text-[var(--primary)]">关于我们</Link></li>
                  <li><Link href="/contact" className="text-[var(--muted)] hover:text-[var(--primary)]">联系我们</Link></li>
                  <li><Link href="/careers" className="text-[var(--muted)] hover:text-[var(--primary)]">加入我们</Link></li>
                </ul>
              </div>
            </div>
          </div>
          <div className="mt-10 border-t border-[var(--border)] pt-6">
            <p className="text-center text-sm text-[var(--muted)]">
              &copy; {new Date().getFullYear()} 但问智能体综合应用平台. 保留所有权利.
            </p>
          </div>
        </div>
      </footer>
    </main>
  )
} 