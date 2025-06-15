import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export type ThemePreset = {
  name: string
  primaryColor: string
  secondaryColor?: string
  successColor?: string
  warningColor?: string
  errorColor?: string
  infoColor?: string
}

export const defaultThemePresets: ThemePreset[] = [
  {
    name: 'Vue版本主题',
    primaryColor: '#F4511E',
    secondaryColor: '#2080F0',
    successColor: '#18A058',
    warningColor: '#F0A020',
    errorColor: '#D03050',
    infoColor: '#2080F0',
  },
  {
    name: '默认蓝',
    primaryColor: '#1890ff',
    secondaryColor: '#722ed1',
    successColor: '#52c41a',
    warningColor: '#faad14',
    errorColor: '#f5222d',
    infoColor: '#1890ff',
  },
  {
    name: '科技紫',
    primaryColor: '#722ed1',
    secondaryColor: '#1890ff',
    successColor: '#52c41a',
    warningColor: '#faad14',
    errorColor: '#f5222d',
    infoColor: '#1890ff',
  },
  {
    name: '活力橙',
    primaryColor: '#fa8c16',
    secondaryColor: '#1890ff',
    successColor: '#52c41a',
    warningColor: '#faad14',
    errorColor: '#f5222d',
    infoColor: '#1890ff',
  },
  {
    name: '沉稳绿',
    primaryColor: '#13c2c2',
    secondaryColor: '#1890ff',
    successColor: '#52c41a',
    warningColor: '#faad14',
    errorColor: '#f5222d',
    infoColor: '#1890ff',
  },
  {
    name: '商务灰',
    primaryColor: '#5a5a5a',
    secondaryColor: '#1890ff',
    successColor: '#52c41a',
    warningColor: '#faad14',
    errorColor: '#f5222d',
    infoColor: '#1890ff',
  },
]

interface ThemeState {
  isDark: boolean
  primaryColor: string
  secondaryColor: string
  successColor: string
  warningColor: string
  errorColor: string
  infoColor: string
  sidebarCollapsed: boolean
  activePreset: string
  customPresets: ThemePreset[]

  toggleTheme: () => void
  setPrimaryColor: (color: string) => void
  setThemeColor: (colorKey: string, color: string) => void
  toggleSidebar: () => void
  setSidebarCollapsed: (collapsed: boolean) => void
  setActivePreset: (presetName: string) => void
  addCustomPreset: (preset: ThemePreset) => void
  removeCustomPreset: (presetName: string) => void
  applyPreset: (presetName: string) => void
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set, get) => ({
      isDark: false,
      // 使用Vue版本的默认主题色
      primaryColor: '#F4511E',
      secondaryColor: '#2080F0',
      successColor: '#18A058',
      warningColor: '#F0A020',
      errorColor: '#D03050',
      infoColor: '#2080F0',
      sidebarCollapsed: false,
      activePreset: 'Vue版本主题',
      customPresets: [],

      toggleTheme: () => {
        set((state) => ({ isDark: !state.isDark }))
      },

      setPrimaryColor: (color: string) => {
        set({ primaryColor: color })
      },

      setThemeColor: (colorKey: string, color: string) => {
        set({ [colorKey]: color } as any)
      },

      toggleSidebar: () => {
        set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed }))
      },

      setSidebarCollapsed: (collapsed: boolean) => {
        set({ sidebarCollapsed: collapsed })
      },

      setActivePreset: (presetName: string) => {
        set({ activePreset: presetName })
      },

      addCustomPreset: (preset: ThemePreset) => {
        const { customPresets } = get()
        // 检查是否已存在同名预设
        const exists = customPresets.some((p) => p.name === preset.name)
        if (!exists) {
          set({ customPresets: [...customPresets, preset] })
        }
      },

      removeCustomPreset: (presetName: string) => {
        const { customPresets } = get()
        set({
          customPresets: customPresets.filter((p) => p.name !== presetName),
        })
      },

      applyPreset: (presetName: string) => {
        const { customPresets } = get()
        // 查找系统预设
        const systemPreset = defaultThemePresets.find((p) => p.name === presetName)
        // 查找自定义预设
        const customPreset = customPresets.find((p) => p.name === presetName)

        const preset = systemPreset || customPreset

        if (preset) {
          set({
            activePreset: presetName,
            primaryColor: preset.primaryColor,
            secondaryColor: preset.secondaryColor || '#722ed1',
            successColor: preset.successColor || '#52c41a',
            warningColor: preset.warningColor || '#faad14',
            errorColor: preset.errorColor || '#f5222d',
            infoColor: preset.infoColor || '#1890ff',
          })
        }
      },
    }),
    {
      name: 'theme-storage',
    },
  ),
)
