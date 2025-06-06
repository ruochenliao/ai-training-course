import {create} from 'zustand'
import {persist} from 'zustand/middleware'

interface AppState {
  loading: boolean
  reloading: boolean
  keepAliveList: string[]
  language: string
  collapsed: boolean
  theme: 'light' | 'dark'
  fullscreen: boolean
  setLoading: (loading: boolean) => void
  setReloading: (reloading: boolean) => void
  addKeepAlive: (name: string) => void
  removeKeepAlive: (name: string) => void
  clearKeepAlive: () => void
  setLanguage: (language: string) => void
  setCollapsed: (collapsed: boolean) => void
  toggleCollapsed: () => void
  setTheme: (theme: 'light' | 'dark') => void
  toggleTheme: () => void
  setFullscreen: (fullscreen: boolean) => void
  toggleFullscreen: () => void
}

export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      loading: false,
      reloading: false,
      keepAliveList: [],
      language: 'zh-CN',
      collapsed: false,
      theme: 'light',
      fullscreen: false,

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
        set({ keepAliveList: keepAliveList.filter(item => item !== name) })
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

      setTheme: (theme: 'light' | 'dark') => {
        set({ theme })
        // 更新HTML根元素的class
        if (theme === 'dark') {
          document.documentElement.classList.add('dark')
        } else {
          document.documentElement.classList.remove('dark')
        }
      },

      toggleTheme: () => {
        const { theme } = get()
        const newTheme = theme === 'light' ? 'dark' : 'light'
        get().setTheme(newTheme)
      },

      setFullscreen: (fullscreen: boolean) => {
        set({ fullscreen })
      },

      toggleFullscreen: () => {
        const { fullscreen } = get()
        set({ fullscreen: !fullscreen })
      },
    }),
    {
      name: 'app-storage',
      partialize: (state) => ({
        keepAliveList: state.keepAliveList,
        language: state.language,
        collapsed: state.collapsed,
        theme: state.theme,
      }),
    }
  )
)