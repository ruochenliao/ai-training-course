import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AppState {
  loading: boolean
  reloading: boolean
  keepAliveList: string[]
  language: string
  collapsed: boolean
  fullscreen: boolean
  aliveKeys: Record<string, string>
  setLoading: (loading: boolean) => void
  setReloading: (reloading: boolean) => void
  addKeepAlive: (name: string) => void
  removeKeepAlive: (name: string) => void
  clearKeepAlive: () => void
  setLanguage: (language: string) => void
  setCollapsed: (collapsed: boolean) => void
  toggleCollapsed: () => void
  setFullscreen: (fullscreen: boolean) => void
  toggleFullscreen: () => void
  setFullScreen: (fullscreen: boolean) => void
  setAliveKeys: (key: string, val: string) => void
  reloadPage: () => void
}

export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      loading: false,
      reloading: false,
      keepAliveList: [],
      language: 'zh-CN',
      collapsed: false,
      fullscreen: false,
      aliveKeys: {},

      setLoading: (loading: boolean) => {
        set({ loading })
      },

      setReloading: (reloading: boolean) => {
        set({ reloading })
      },

      addKeepAlive: (name: string) => {
        const { keepAliveList } = get()
        if (!keepAliveList.includes(name)) {
          set({ keepAliveList: [...keepAliveList, name] })
        }
      },

      removeKeepAlive: (name: string) => {
        const { keepAliveList } = get()
        set({ keepAliveList: keepAliveList.filter((item) => item !== name) })
      },

      clearKeepAlive: () => {
        set({ keepAliveList: [] })
      },

      setLanguage: (language: string) => {
        set({ language })
      },

      setCollapsed: (collapsed: boolean) => {
        set({ collapsed })
      },

      toggleCollapsed: () => {
        const { collapsed } = get()
        set({ collapsed: !collapsed })
      },

      setFullscreen: (fullscreen: boolean) => {
        set({ fullscreen })
      },

      toggleFullscreen: () => {
        const { fullscreen } = get()
        set({ fullscreen: !fullscreen })
      },

      // 对应Vue版本的 setFullScreen
      setFullScreen: (fullscreen: boolean) => {
        set({ fullscreen })
      },

      // 对应Vue版本的 setAliveKeys
      setAliveKeys: (key: string, val: string) => {
        const { aliveKeys } = get()
        set({ aliveKeys: { ...aliveKeys, [key]: val } })
      },

      // 对应Vue版本的 reloadPage
      reloadPage: () => {
        set({ reloading: true })
        setTimeout(() => {
          set({ reloading: false })
          document.documentElement.scrollTo({ left: 0, top: 0 })
        }, 100)
      },
    }),
    {
      name: 'app-storage',
      partialize: (state) => ({
        keepAliveList: state.keepAliveList,
        language: state.language,
        collapsed: state.collapsed,
      }),
    },
  ),
)
