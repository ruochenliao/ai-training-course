import {create} from 'zustand'
import {persist} from 'zustand/middleware'

interface AppState {
  loading: boolean
  reloading: boolean
  keepAliveList: string[]
  language: string
  collapsed: boolean
  fullscreen: boolean
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
      }),
    }
  )
)