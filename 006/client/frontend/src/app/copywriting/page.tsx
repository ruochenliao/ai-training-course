'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import Link from 'next/link'

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
      <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" />
      <polyline points="14 2 14 8 20 8" />
      <line x1="16" y1="13" x2="8" y2="13" />
      <line x1="16" y1="17" x2="8" y2="17" />
      <line x1="10" y1="9" x2="8" y2="9" />
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

function Download(props: React.SVGProps<SVGSVGElement>) {
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
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="7 10 12 15 17 10" />
      <line x1="12" y1="15" x2="12" y2="3" />
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
      <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z" />
      <path d="M5 3v4" />
      <path d="M19 17v4" />
      <path d="M3 5h4" />
      <path d="M17 19h4" />
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

function BookOpen(props: React.SVGProps<SVGSVGElement>) {
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
      <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" />
      <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
    </svg>
  )
}

// 添加系统架构图组件
const ArchitectureDiagram = () => (
  <svg className="w-full h-full" viewBox="0 0 800 400" fill="none" xmlns="http://www.w3.org/2000/svg">
    {/* 渐变定义 */}
    <defs>
      <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" style={{ stopColor: '#3B82F6', stopOpacity: 0.8 }} />
        <stop offset="100%" style={{ stopColor: '#60A5FA', stopOpacity: 0.8 }} />
      </linearGradient>
      <linearGradient id="grad2" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" style={{ stopColor: '#8B5CF6', stopOpacity: 0.8 }} />
        <stop offset="100%" style={{ stopColor: '#A78BFA', stopOpacity: 0.8 }} />
      </linearGradient>
      <linearGradient id="grad3" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" style={{ stopColor: '#F59E0B', stopOpacity: 0.8 }} />
        <stop offset="100%" style={{ stopColor: '#FCD34D', stopOpacity: 0.8 }} />
      </linearGradient>
    </defs>

    {/* 用户输入层 */}
    <g className="user-input">
      <rect x="300" y="20" width="200" height="60" rx="8" fill="url(#grad1)" />
      <text x="400" y="55" textAnchor="middle" fill="white" fontSize="14">用户需求输入</text>
      <line x1="400" y1="80" x2="400" y2="120" stroke="#3B82F6" strokeWidth="2" strokeDasharray="4" />
    </g>

    {/* 智能处理层 */}
    <g className="processing-layer">
      <rect x="150" y="120" width="500" height="160" rx="8" fill="url(#grad2)" />
      <text x="400" y="145" textAnchor="middle" fill="white" fontSize="14">智能处理层</text>

      {/* 左侧模块 */}
      <rect x="170" y="170" width="140" height="90" rx="4" fill="white" fillOpacity="0.9" />
      <text x="240" y="195" textAnchor="middle" fill="#4C1D95" fontSize="12">模板匹配</text>
      <text x="240" y="215" textAnchor="middle" fill="#4C1D95" fontSize="12">风格识别</text>
      <text x="240" y="235" textAnchor="middle" fill="#4C1D95" fontSize="12">意图理解</text>

      {/* 中间模块 */}
      <rect x="330" y="170" width="140" height="90" rx="4" fill="white" fillOpacity="0.9" />
      <text x="400" y="195" textAnchor="middle" fill="#4C1D95" fontSize="12">RAG 检索增强</text>
      <text x="400" y="215" textAnchor="middle" fill="#4C1D95" fontSize="12">知识库集成</text>
      <text x="400" y="235" textAnchor="middle" fill="#4C1D95" fontSize="12">联网搜索</text>

      {/* 右侧模块 */}
      <rect x="490" y="170" width="140" height="90" rx="4" fill="white" fillOpacity="0.9" />
      <text x="560" y="195" textAnchor="middle" fill="#4C1D95" fontSize="12">LLM 生成</text>
      <text x="560" y="215" textAnchor="middle" fill="#4C1D95" fontSize="12">内容优化</text>
      <text x="560" y="235" textAnchor="middle" fill="#4C1D95" fontSize="12">质量控制</text>
    </g>

    {/* 输出层 */}
    <g className="output-layer">
      <rect x="150" y="320" width="500" height="60" rx="8" fill="url(#grad3)" />
      <text x="400" y="355" textAnchor="middle" fill="white" fontSize="14">文案输出与优化</text>
      <line x1="400" y1="280" x2="400" y2="320" stroke="#F59E0B" strokeWidth="2" strokeDasharray="4" />
    </g>

    {/* 连接线 */}
    <g className="connections" stroke="#CBD5E1" strokeWidth="1" strokeDasharray="4">
      <path d="M240 260 L240 320" />
      <path d="M400 260 L400 320" />
      <path d="M560 260 L560 320" />
    </g>
  </svg>
);

// 添加科技感背景组件
const TechBackground = () => (
  <div className="absolute inset-0 -z-10 overflow-hidden">
    <div className="wave-bg"></div>
    <div className="tech-grid absolute inset-0 opacity-10"></div>
    <div className="absolute top-0 right-0 h-[500px] w-[500px] -translate-y-1/2 translate-x-1/2 rounded-full bg-gradient-to-br from-blue-600 to-purple-600 opacity-20 blur-3xl"></div>
    <div className="absolute bottom-0 left-0 h-[500px] w-[500px] translate-y-1/2 -translate-x-1/2 rounded-full bg-gradient-to-tr from-blue-400 to-teal-500 opacity-20 blur-3xl"></div>
  </div>
);

// 添加浮动粒子效果组件
const FloatingParticles = () => (
  <div className="absolute inset-0 -z-5 overflow-hidden">
    <div className="gemini-bg-dots absolute inset-0 opacity-10 z-0"></div>
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

export default function Copywriting() {
  const [query, setQuery] = useState('')
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null)
  const [generatedContent, setGeneratedContent] = useState<string | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)

  const templates = [
    {
      id: 'product-intro',
      title: '产品介绍',
      description: '突出产品特性、优势和价值主张',
      icon: <FileText className="h-6 w-6" />,
    },
    {
      id: 'company-profile',
      title: '企业简介',
      description: '展示企业历史、文化和业务布局',
      icon: <Brain className="h-6 w-6" />,
    },
    {
      id: 'marketing-email',
      title: '营销邮件',
      description: '设计吸引人的促销和活动邮件',
      icon: <Sparkles className="h-6 w-6" />,
    },
    {
      id: 'press-release',
      title: '新闻稿',
      description: '发布企业重要动态和成就',
      icon: <Globe className="h-6 w-6" />,
    },
    {
      id: 'case-study',
      title: '案例研究',
      description: '详细分析成功项目和解决方案',
      icon: <BookOpen className="h-6 w-6" />,
    },
    {
      id: 'social-media',
      title: '社媒内容',
      description: '创作吸引人的社交媒体帖子',
      icon: <Globe className="h-6 w-6" />,
    },
    {
      id: 'white-paper',
      title: '白皮书',
      description: '深度技术或行业研究报告',
      icon: <FileText className="h-6 w-6" />,
    },
    {
      id: 'user-guide',
      title: '用户指南',
      description: '编写清晰的产品使用说明',
      icon: <BookOpen className="h-6 w-6" />,
    },
    {
      id: 'proposal',
      title: '商业提案',
      description: '制作专业的项目或合作提案',
      icon: <FileText className="h-6 w-6" />,
    }
  ]

  const handleGenerateContent = () => {
    if (!query || !selectedTemplate) return

    // 模拟生成过程，添加加载状态
    setIsGenerating(true)
    setTimeout(() => {
      const sampleContents = {
        'product-intro': `# 智能办公解决方案

## 产品概述

我们的智能办公解决方案融合了最新的人工智能技术，为企业提供一站式办公自动化体验。该系统能够显著提升团队协作效率，减少重复性工作，让您的团队专注于更具价值的创造性任务。

## 核心功能

- **智能文档管理**：自动分类、标记和检索文档，告别繁琐的文件管理
- **会议助手**：自动记录会议内容，生成会议纪要，跟踪行动项
- **工作流自动化**：定制化工作流程，实现审批流程自动化
- **数据分析报表**：自动收集数据并生成可视化报表，辅助决策

## 产品优势

1. **效率提升**：减少40%的文档处理时间
2. **成本节约**：降低30%的管理成本
3. **协作增强**：团队协作效率提高50%
4. **数据安全**：企业级安全保障，数据加密存储

欢迎联系我们，为您的企业定制智能办公解决方案。`,
        'company-profile': `# 关于我们

## 公司简介

成立于2010年，但问科技是一家专注于人工智能技术创新与应用的高科技企业。我们致力于为各行业客户提供先进的智能化解决方案，帮助企业实现数字化转型，提升核心竞争力。

## 发展历程

- **2010年**：公司成立，专注于基础AI算法研究
- **2013年**：推出首款智能客服产品，服务金融行业
- **2016年**：完成B轮融资，扩展业务至制造、零售等多个领域
- **2019年**：获得国家高新技术企业认证，技术专利达30项
- **2022年**：推出新一代智能体产品矩阵，全面赋能企业智能化升级

## 企业使命与愿景

**使命**：用AI技术创造价值，推动行业智能化升级
**愿景**：成为全球领先的企业智能化解决方案提供商

## 核心团队

我们拥有一支由AI领域资深专家、工程师和行业顾问组成的精英团队，90%以上的技术人员拥有硕士及以上学历，核心成员来自清华、北大、斯坦福等顶尖学府，平均行业经验超过10年。`,
        'marketing-email': `主题：【限时优惠】升级至但问智能体企业版，释放生产力新高度！

尊敬的客户：

希望这封邮件能为您的工作日增添一抹亮色！

## 智能化升级，效率翻倍

我们很高兴地宣布，全新的但问智能体企业版现已推出，并提供限时**30%折扣**优惠！作为我们的老用户，您将获得**优先升级权**及额外的专属福利。

### 新版本亮点功能：

- 🚀 **多模态理解**：支持文字、图像、语音等多种输入方式
- 💼 **企业知识库私有化部署**：确保数据安全的同时提供精准问答
- 🔄 **工作流自动化**：减少80%重复性工作，释放团队创造力
- 🌐 **多语言支持**：新增10种语言，助力全球业务拓展

### 限时优惠：

- 企业标准版：~~¥19,800/年~~ 现仅需 ¥13,860/年
- 企业高级版：~~¥39,600/年~~ 现仅需 ¥27,720/年

**优惠截止日期**：2023年6月30日

立即联系您的专属客户经理或回复此邮件，了解更多详情并获取免费演示服务。

期待与您一起，开启智能化办公新篇章！

祝商祺，
但问智能体团队`,
        'press-release': `# 新闻稿：但问科技完成C轮5亿融资，加速智能体技术商业化落地

**2023年6月15日，北京** — 国内领先的企业智能化解决方案提供商但问科技今日宣布完成5亿元人民币C轮融资。本轮融资由顶级科技投资机构领投，多家知名产业基金跟投。

## 资金用途

但问科技表示，新一轮融资将主要用于三大方向：

1. 加大对智能体核心技术的研发投入，特别是在大规模语言模型微调、多模态理解和工具调用方面的突破
2. 扩展行业解决方案矩阵，聚焦金融、制造、医疗等高价值垂直领域
3. 加速全球市场布局，计划年内在新加坡、日本设立分支机构

## 创新成果与市场领先地位

但问科技CEO张明表示："此轮融资是投资者对我们技术创新能力和商业模式的高度认可。过去一年，我们的企业级智能体产品已服务超过500家大中型企业客户，帮助客户平均提升30%的运营效率，节约20%的人力成本。"

数据显示，但问科技近两年营收增长超过200%，产品覆盖金融、制造、零售等十余个行业，并在企业智能助手、知识库管理等细分领域市场份额位居前三。

## 行业影响与未来展望

资深产业分析师李华认为："但问科技在智能体技术的落地能力令人印象深刻。他们不仅拥有领先的技术，更重要的是深刻理解企业用户的实际需求，这使他们在竞争激烈的AI赛道中脱颖而出。"

但问科技表示，公司将继续秉持"AI赋能实体经济"的使命，推动智能体技术在更多行业场景的创新应用，助力传统企业数字化转型升级。

**媒体联系人**：
王梦琪 | 公关总监 | wangmq@danwen.ai | 13901234567`,
        'case-study': `# 案例研究：某大型制造企业智能体应用实践

## 客户背景

客户是一家年营收超过50亿元的大型制造企业，拥有15000名员工，多个生产基地分布全国各地。企业面临知识管理效率低下、技术支持响应慢、员工培训成本高等挑战。

## 面临的挑战

1. **知识碎片化**：技术文档、操作手册、故障案例分散在各个系统中，检索困难
2. **专家资源稀缺**：核心技术专家数量有限，无法及时响应全国各基地的技术咨询
3. **培训效率低**：新员工培训周期长，学习曲线陡峭
4. **决策支持不足**：缺乏对生产数据的实时分析和预警能力

## 解决方案

我们为客户定制了一套集成但问智能体技术的企业知识管理与决策支持系统：

1. **企业知识库智能体**：整合全部技术文档、操作规程、故障案例，构建统一知识库
2. **生产辅助决策智能体**：连接生产数据系统，提供实时数据分析和异常预警
3. **员工培训智能体**：为新员工提供个性化学习路径和实时问答支持

## 实施过程

项目分三个阶段实施：

1. **数据整合与知识库构建**（2个月）：收集、清洗、结构化处理企业各类文档
2. **智能体开发与定制**（3个月）：根据企业特定需求开发和训练智能体
3. **系统集成与上线**（1个月）：与企业现有系统集成并分批次推广上线

## 成果与收益

项目上线6个月后的关键成果：

- **技术支持效率提升85%**：90%的常见问题可由智能体直接解答
- **培训周期缩短40%**：新员工入职培训时间从平均4周缩短至2.5周
- **故障处理时间减少50%**：现场工程师能快速获取解决方案
- **专家资源释放**：核心技术专家工作重心从日常咨询转向创新研发
- **ROI显著**：项目投资在8个月内实现完全回报

## 客户评价

"但问智能体系统彻底改变了我们企业的知识管理方式，不仅提高了运营效率，更重要的是让我们的专家团队能够专注于更具价值的创新工作。"
—— 客户CTO 李总

## 经验与启示

本案例的成功实施提供了几点关键启示：

1. 智能体实施前的知识库构建是基础，数据质量直接影响最终效果
2. 分阶段实施策略有助于降低风险，获得组织内部认可
3. 充分结合企业业务流程的定制化开发是智能体落地的关键`
      }

      setGeneratedContent(sampleContents[selectedTemplate as keyof typeof sampleContents])
      setIsGenerating(false)
    }, 1500)
  }

  return (
    <div className="flex min-h-screen flex-col relative">
      {/* 添加科技感背景 */}
      <TechBackground />
      <FloatingParticles />

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
            <Link
              href="/customer-service"
              className="text-sm font-medium text-neutral-600 hover:text-blue-600 dark:text-neutral-300 dark:hover:text-blue-400 transition-colors"
            >
              智能客服
            </Link>
            <Link
              href="/text2sql"
              className="text-sm font-medium text-neutral-600 hover:text-blue-600 dark:text-neutral-300 dark:hover:text-blue-400 transition-colors"
            >
              Text2SQL
            </Link>
            <Link
              href="/knowledge-base"
              className="text-sm font-medium text-neutral-600 hover:text-blue-600 dark:text-neutral-300 dark:hover:text-blue-400 transition-colors"
            >
              知识库问答
            </Link>
            <Link
              href="/copywriting"
              className="text-sm font-medium text-blue-600 dark:text-blue-400 relative after:content-[''] after:absolute after:left-0 after:bottom-[-4px] after:w-full after:h-[2px] after:bg-blue-600 dark:after:bg-blue-400"
            >
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
              <span className="mr-2">✨</span> AI驱动的高效文案创作工具
            </motion.div>
            <motion.h1
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-4 text-3xl font-bold md:text-4xl bg-clip-text text-transparent bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600"
            >
              企业文案创作智能体
            </motion.h1>
            <motion.p
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="mx-auto mb-8 max-w-2xl text-lg text-gray-600 dark:text-gray-300"
            >
              基于 Agent + RAG 技术，结合企业知识库、行业数据和大语言模型，为企业提供专业的文案创作服务。支持多种文案类型，确保输出符合企业调性与行业标准。
            </motion.p>
          </div>

          {/* 核心功能介绍 */}
          <div className="mb-16">
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
                whileHover={{ y: -5, transition: { duration: 0.2 } }}
                className="rounded-lg border bg-card p-6 shadow-sm"
              >
                <div className="mb-4 inline-flex rounded-lg bg-blue-500/10 p-3">
                  <Brain className="h-6 w-6 text-blue-600" />
                </div>
                <h3 className="mb-2 text-lg font-semibold">智能模板匹配</h3>
                <ul className="space-y-2 text-sm text-muted-foreground">
                  <li className="flex items-center">
                    <span className="inline-block h-1.5 w-1.5 rounded-full bg-blue-500 mr-2"></span>
                    自动识别文案类型
                  </li>
                  <li className="flex items-center">
                    <span className="inline-block h-1.5 w-1.5 rounded-full bg-blue-500 mr-2"></span>
                    智能推荐最佳模板
                  </li>
                  <li className="flex items-center">
                    <span className="inline-block h-1.5 w-1.5 rounded-full bg-blue-500 mr-2"></span>
                    个性化模板调整
                  </li>
                </ul>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                whileHover={{ y: -5, transition: { duration: 0.2 } }}
                className="rounded-lg border bg-card p-6 shadow-sm"
              >
                <div className="mb-4 inline-flex rounded-lg bg-purple-500/10 p-3">
                  <Globe className="h-6 w-6 text-purple-600" />
                </div>
                <h3 className="mb-2 text-lg font-semibold">知识增强生成</h3>
                <ul className="space-y-2 text-sm text-muted-foreground">
                  <li className="flex items-center">
                    <span className="inline-block h-1.5 w-1.5 rounded-full bg-purple-500 mr-2"></span>
                    RAG 技术支持
                  </li>
                  <li className="flex items-center">
                    <span className="inline-block h-1.5 w-1.5 rounded-full bg-purple-500 mr-2"></span>
                    多源信息融合
                  </li>
                  <li className="flex items-center">
                    <span className="inline-block h-1.5 w-1.5 rounded-full bg-purple-500 mr-2"></span>
                    实时数据更新
                  </li>
                </ul>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                whileHover={{ y: -5, transition: { duration: 0.2 } }}
                className="rounded-lg border bg-card p-6 shadow-sm"
              >
                <div className="mb-4 inline-flex rounded-lg bg-cyan-500/10 p-3">
                  <Sparkles className="h-6 w-6 text-cyan-600" />
                </div>
                <h3 className="mb-2 text-lg font-semibold">风格定制化</h3>
                <ul className="space-y-2 text-sm text-muted-foreground">
                  <li className="flex items-center">
                    <span className="inline-block h-1.5 w-1.5 rounded-full bg-cyan-500 mr-2"></span>
                    企业调性适配
                  </li>
                  <li className="flex items-center">
                    <span className="inline-block h-1.5 w-1.5 rounded-full bg-cyan-500 mr-2"></span>
                    多样风格模板
                  </li>
                  <li className="flex items-center">
                    <span className="inline-block h-1.5 w-1.5 rounded-full bg-cyan-500 mr-2"></span>
                    个性化调整
                  </li>
                </ul>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 }}
                whileHover={{ y: -5, transition: { duration: 0.2 } }}
                className="rounded-lg border bg-card p-6 shadow-sm"
              >
                <div className="mb-4 inline-flex rounded-lg bg-teal-500/10 p-3">
                  <FileText className="h-6 w-6 text-teal-600" />
                </div>
                <h3 className="mb-2 text-lg font-semibold">质量保证</h3>
                <ul className="space-y-2 text-sm text-muted-foreground">
                  <li className="flex items-center">
                    <span className="inline-block h-1.5 w-1.5 rounded-full bg-teal-500 mr-2"></span>
                    多轮优化
                  </li>
                  <li className="flex items-center">
                    <span className="inline-block h-1.5 w-1.5 rounded-full bg-teal-500 mr-2"></span>
                    准确性检查
                  </li>
                  <li className="flex items-center">
                    <span className="inline-block h-1.5 w-1.5 rounded-full bg-teal-500 mr-2"></span>
                    规范性审核
                  </li>
                </ul>
              </motion.div>
            </div>
          </div>

          {/* 文案生成主体部分 */}
          <div className="mx-auto mb-16 max-w-4xl relative">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="rounded-xl border border-[var(--border)] p-8 bg-white/90 backdrop-blur-sm shadow-md dark:bg-neutral-900/90 dark:border-neutral-800 overflow-hidden relative"
            >
              <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 via-indigo-500/5 to-purple-500/5"></div>
              <div className="relative z-10">
                <h2 className="mb-6 text-2xl font-semibold text-center bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-purple-600">创建高质量文案</h2>

                {/* 第一步：选择模板 */}
                <div className="mb-8">
                  <h3 className="mb-4 text-lg font-medium text-blue-600 dark:text-blue-400 flex items-center">
                    <div className="flex items-center justify-center w-6 h-6 rounded-full bg-blue-500/30 text-blue-600 dark:text-blue-400 mr-2 text-sm">1</div>
                    选择文案模板
                  </h3>
                  <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                    {templates.map((template) => (
                      <motion.div
                        key={template.id}
                        onClick={() => setSelectedTemplate(template.id)}
                        whileHover={{ scale: 1.03 }}
                        className={`cursor-pointer rounded-lg border p-4 transition-all ${
                          selectedTemplate === template.id
                            ? 'border-blue-500/50 bg-blue-500/10 shadow-md'
                            : 'border-[var(--border)] hover:border-blue-500/30 bg-white dark:bg-[var(--card)]'
                        }`}
                      >
                        <div className="mb-2 flex items-center space-x-2">
                          <div className={`rounded-full ${selectedTemplate === template.id ? 'bg-blue-500/30 text-blue-600 dark:text-blue-400' : 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400'} p-2`}>
                            {template.icon}
                          </div>
                          <h4 className="font-medium">{template.title}</h4>
                        </div>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          {template.description}
                        </p>
                      </motion.div>
                    ))}
                  </div>
                </div>

                {/* 第二步：输入需求 */}
                {selectedTemplate && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    transition={{ duration: 0.3 }}
                    className="mb-8 overflow-hidden"
                  >
                    <h3 className="mb-4 text-lg font-medium text-blue-600 dark:text-blue-400 flex items-center">
                      <div className="flex items-center justify-center w-6 h-6 rounded-full bg-blue-500/30 text-blue-600 dark:text-blue-400 mr-2 text-sm">2</div>
                      描述您的需求
                    </h3>
                    <div className="space-y-4">
                      <div className="relative">
                        <Search className="absolute left-3 top-3 h-5 w-5 text-blue-600/60 dark:text-blue-400/60" />
                        <textarea
                          value={query}
                          onChange={(e) => setQuery(e.target.value)}
                          placeholder="详细描述您的需求，例如：写一份关于我们公司新推出的智能办公软件的产品介绍..."
                          className="min-h-[120px] w-full rounded-lg border border-[var(--border)] bg-white dark:bg-[var(--card)] py-2 pl-10 pr-4 focus:outline-none focus:ring-2 focus:ring-blue-500/50 text-neutral-700 dark:text-neutral-200"
                          rows={4}
                        />
                      </div>
                      <button
                        onClick={handleGenerateContent}
                        disabled={!query.trim() || isGenerating}
                        className="gemini-button-primary w-full"
                      >
                        <span className="relative z-10">
                          {isGenerating ? (
                            <span className="flex items-center justify-center">
                              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                              </svg>
                              正在生成文案...
                            </span>
                          ) : "生成文案"}
                        </span>
                      </button>
                    </div>
                  </motion.div>
                )}

                {/* 第三步：生成结果 */}
                {generatedContent && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mb-6"
                  >
                    <div className="mb-4 flex items-center justify-between">
                      <h3 className="text-lg font-medium text-blue-600 dark:text-blue-400 flex items-center">
                        <div className="flex items-center justify-center w-6 h-6 rounded-full bg-blue-500/30 text-blue-600 dark:text-blue-400 mr-2 text-sm">3</div>
                        生成结果
                      </h3>
                      <button className="flex items-center rounded-lg border border-blue-500/30 bg-blue-500/10 px-4 py-2 text-sm font-medium text-blue-600 dark:text-blue-400 hover:bg-blue-500/20 transition-colors">
                        <Download className="mr-2 h-4 w-4" />
                        下载文档
                      </button>
                    </div>
                    <div className="rounded-lg border border-[var(--border)] bg-white dark:bg-[var(--card)] p-6">
                      <pre className="whitespace-pre-wrap text-sm text-neutral-700 dark:text-neutral-200 md-content">
                        {generatedContent}
                      </pre>
                    </div>
                  </motion.div>
                )}
              </div>
            </motion.div>
          </div>

          {/* 技术亮点说明部分 */}
          <div className="mb-16">
            <h2 className="mb-8 text-center text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-purple-600">核心技术亮点</h2>
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              <motion.div
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: 0.1 }}
                whileHover={{ y: -5, transition: { duration: 0.2 } }}
                className="rounded-lg border bg-card p-6 shadow-sm relative overflow-hidden group"
              >
                <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-500 to-blue-300"></div>
                <div className="absolute inset-0 bg-gradient-to-b from-blue-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>

                <div className="mb-4 inline-flex rounded-lg bg-blue-500/10 p-3">
                  <Brain className="h-6 w-6 text-blue-600" />
                </div>
                <h3 className="mb-2 text-xl font-semibold">Agent 智能调度</h3>
                <p className="text-muted-foreground">
                  采用智能体技术，协调多个专业模块，实现文案创作全流程的智能化管理
                </p>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: 0.2 }}
                whileHover={{ y: -5, transition: { duration: 0.2 } }}
                className="rounded-lg border bg-card p-6 shadow-sm relative overflow-hidden group"
              >
                <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-purple-500 to-purple-300"></div>
                <div className="absolute inset-0 bg-gradient-to-b from-purple-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>

                <div className="mb-4 inline-flex rounded-lg bg-purple-500/10 p-3">
                  <Globe className="h-6 w-6 text-purple-600" />
                </div>
                <h3 className="mb-2 text-xl font-semibold">RAG 知识增强</h3>
                <p className="text-muted-foreground">
                  结合检索增强生成技术，融合企业知识库、行业数据，确保文案的专业性和准确性
                </p>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: 0.3 }}
                whileHover={{ y: -5, transition: { duration: 0.2 } }}
                className="rounded-lg border bg-card p-6 shadow-sm relative overflow-hidden group"
              >
                <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-cyan-500 to-cyan-300"></div>
                <div className="absolute inset-0 bg-gradient-to-b from-cyan-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>

                <div className="mb-4 inline-flex rounded-lg bg-cyan-500/10 p-3">
                  <Sparkles className="h-6 w-6 text-cyan-600" />
                </div>
                <h3 className="mb-2 text-xl font-semibold">LLM 能力增强</h3>
                <p className="text-muted-foreground">
                  集成多个大语言模型，通过模型协同提升文案创作的质量和效率
                </p>
              </motion.div>
            </div>
          </div>

          {/* 系统架构图 */}
          <div className="mb-20">
            <h2 className="mb-8 text-center text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-purple-600">系统实现架构</h2>
            <div className="mx-auto max-w-4xl rounded-xl border border-[var(--border)] bg-white/90 backdrop-blur-sm shadow-md dark:bg-neutral-900/90 dark:border-neutral-800 overflow-hidden">
              <div className="relative h-96 p-6 bg-gradient-to-br from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20">
                <div className="absolute inset-0 bg-grid-pattern opacity-30 dark:opacity-10"></div>
                <motion.div
                  initial={{ opacity: 0 }}
                  whileInView={{ opacity: 1 }}
                  viewport={{ once: true }}
                  transition={{ delay: 0.2 }}
                  className="h-full w-full"
                >
                  <ArchitectureDiagram />
                </motion.div>
              </div>
              <div className="grid gap-6 p-6 md:grid-cols-3 border-t border-[var(--border)]">
                <div className="space-y-2">
                  <div className="flex items-center space-x-2">
                    <div className="w-3 h-3 rounded-full bg-blue-500"></div>
                    <span className="text-sm font-medium text-blue-600 dark:text-blue-400">需求理解层</span>
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">智能分析用户需求，匹配最佳文案模板</p>
                </div>
                <div className="space-y-2">
                  <div className="flex items-center space-x-2">
                    <div className="w-3 h-3 rounded-full bg-purple-500"></div>
                    <span className="text-sm font-medium text-purple-600 dark:text-purple-400">智能处理层</span>
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">多模块协同处理，确保文案质量</p>
                </div>
                <div className="space-y-2">
                  <div className="flex items-center space-x-2">
                    <div className="w-3 h-3 rounded-full bg-amber-500"></div>
                    <span className="text-sm font-medium text-amber-600 dark:text-amber-400">输出优化层</span>
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">多轮优化和质量控制</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* 页脚 */}
      <footer className="border-t border-[var(--border)] py-8">
        <div className="container mx-auto px-4 text-center">
          <p className="text-sm text-gray-500 dark:text-gray-400">
            © {new Date().getFullYear()} 但问智能体综合应用平台. 保留所有权利.
          </p>
        </div>
      </footer>

      {/* 添加全局样式 */}
      <style jsx global>{`
        .tech-grid {
          background-image: linear-gradient(to right, rgba(59, 130, 246, 0.1) 1px, transparent 1px),
                            linear-gradient(to bottom, rgba(59, 130, 246, 0.1) 1px, transparent 1px);
          background-size: 30px 30px;
        }

        .wave-bg {
          position: absolute;
          width: 100%;
          height: 100%;
          background: linear-gradient(180deg, rgba(59, 130, 246, 0.03) 0%, rgba(147, 197, 253, 0.02) 100%);
        }

        .bg-grid-pattern {
          background-size: 50px 50px;
          background-image:
            linear-gradient(to right, rgba(59, 130, 246, 0.1) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(59, 130, 246, 0.1) 1px, transparent 1px);
        }

        .shadow-glow-blue {
          box-shadow: 0 0 15px rgba(59, 130, 246, 0.3);
        }

        .particle {
          animation: float 10s infinite ease-in-out;
        }

        @keyframes float {
          0%, 100% {
            transform: translateY(0) translateX(0);
          }
          25% {
            transform: translateY(-30px) translateX(30px);
          }
          50% {
            transform: translateY(-15px) translateX(-15px);
          }
          75% {
            transform: translateY(30px) translateX(15px);
          }
        }

        .md-content {
          line-height: 1.6;
        }

        .md-content h1, .md-content h2, .md-content h3 {
          color: var(--foreground);
          margin-bottom: 0.75rem;
          margin-top: 1.5rem;
        }

        .md-content h1 {
          font-size: 1.5rem;
          font-weight: 700;
        }

        .md-content h2 {
          font-size: 1.25rem;
          font-weight: 600;
        }

        .md-content h3 {
          font-size: 1.125rem;
          font-weight: 600;
        }

        .md-content ul, .md-content ol {
          margin-left: 1.5rem;
          margin-bottom: 1rem;
        }

        .md-content ul {
          list-style-type: disc;
        }

        .md-content ol {
          list-style-type: decimal;
          counter-reset: item;
        }

        .md-content ol > li {
          display: block;
          position: relative;
        }

        .md-content ol > li::before {
          content: counters(item, ".") ". ";
          counter-increment: item;
          position: absolute;
          left: -1.5em;
        }

        .md-content p {
          margin-bottom: 0.75rem;
        }

        .md-content strong {
          color: var(--foreground);
          font-weight: 600;
        }
      `}</style>
    </div>
  )
}