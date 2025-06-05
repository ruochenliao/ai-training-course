import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AppState {
  loading: boolean
  reloading: boolean
  keepAliveList: string[]
  language: string
  setLoading: (loading: boolean) => void
  setReloading: (reloading: boolean) => void
  addKeepAlive: (name: string) => void
  removeKeepAlive: (name: string) => void
  clearKeepAlive: () => void
  setLanguage: (language: string) => void
}

export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      loading: false,
      reloading: false,
      keepAliveList: [],
      language: 'zh-CN',

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
    }),
    {
      name: 'app-storage',
      partialize: (state) => ({
        keepAliveList: state.keepAliveList,
        language: state.language,
      }),
    }
  )
)