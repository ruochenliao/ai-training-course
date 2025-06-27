// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2025-06-22',
  devtools: { enabled: true },
  
  // CSS框架
  css: [
    '@unocss/reset/tailwind.css',
    '~/assets/css/main.css'
  ],
  
  // 模块
  modules: [
    '@nuxtjs/tailwindcss',
    '@unocss/nuxt',
    '@pinia/nuxt',
    '@vueuse/nuxt'
  ],
  
  // 构建配置
  build: {
    transpile: ['naive-ui', 'vueuc', '@css-render/vue3-ssr', '@juggle/resize-observer']
  },
  
  // Vite配置
  vite: {
    optimizeDeps: {
      include: [
        'naive-ui',
        'vueuc',
        'date-fns-tz/esm/formatInTimeZone'
      ]
    }
  },
  
  // 运行时配置
  runtimeConfig: {
    // 私有配置（仅服务端可用）
    apiSecret: '',
    
    // 公共配置（客户端也可用）
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || 'http://localhost:8000/api/v1',
      wsUrl: process.env.NUXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws',
      appName: '企业级RAG知识库管理系统',
      version: '1.0.0'
    }
  },
  
  // 应用配置
  app: {
    head: {
      title: '企业级RAG知识库管理系统',
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        { name: 'description', content: '基于多智能体协作的企业级知识库管理系统' }
      ],
      link: [
        { rel: 'icon', type: 'image/x-icon', href: '/favicon.ico' }
      ]
    }
  },
  
  // 服务端渲染 - 暂时禁用以避免 CSS 渲染问题
  ssr: false,
  
  // TypeScript配置
  typescript: {
    strict: true,
    typeCheck: false
  },
  
  // 开发服务器配置
  devServer: {
    port: 3001,
    host: '0.0.0.0'
  },
  
  // 路由配置
  router: {
    options: {
      strict: false,
      sensitive: false
    }
  },
  
  // 实验性功能
  experimental: {
    payloadExtraction: false,
    inlineSSRStyles: false
  },
  
  // Nitro配置
  nitro: {
    esbuild: {
      options: {
        target: 'es2020'
      }
    }
  }
})
