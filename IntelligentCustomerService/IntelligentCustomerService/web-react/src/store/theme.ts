import {create} from 'zustand'
import {persist} from 'zustand/middleware'

interface ThemeState {
  isDark: boolean
  primaryColor: string
  sidebarCollapsed: boolean
  toggleTheme: () => void
  setPrimaryColor: (color: string) => void
  toggleSidebar: () => void
  setSidebarCollapsed: (collapsed: boolean) => void
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set) => ({
      isDark: false,
      primaryColor: '#1890ff',
      sidebarCollapsed: false,

      toggleTheme: () => {
        set((state) => ({ isDark: !state.isDark }))
      },

      setPrimaryColor: (color: string) => {
        set({ primaryColor: color })
      },

      toggleSidebar: () => {
        set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed }))
      },

      setSidebarCollapsed: (collapsed: boolean) => {
        set({ sidebarCollapsed: collapsed })
      },
    }),
    {
      name: 'theme-storage',
    }
  )
)