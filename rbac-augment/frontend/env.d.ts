/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
  readonly VITE_APP_TITLE: string
  readonly VITE_APP_VERSION: string
  readonly VITE_USE_MOCK: string
  readonly VITE_USE_PWA: string
  readonly VITE_ROUTER_MODE: string
  readonly VITE_BUILD_GZIP: string
  readonly VITE_DROP_CONSOLE: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
