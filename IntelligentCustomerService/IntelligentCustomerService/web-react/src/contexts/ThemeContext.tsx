import React, {createContext, ReactNode, useContext, useEffect} from 'react'
import {ConfigProvider, theme} from 'antd'
import {defaultThemePresets, ThemePreset, useThemeStore} from '../store/theme'

interface ThemeContextType {
  isDark: boolean
  toggleTheme: () => void
  primaryColor: string
  secondaryColor: string
  successColor: string
  warningColor: string
  errorColor: string
  infoColor: string
  setPrimaryColor: (color: string) => void
  setThemeColor: (colorKey: string, color: string) => void
  activePreset: string
  setActivePreset: (presetName: string) => void
  applyPreset: (presetName: string) => void
  presets: ThemePreset[]
  customPresets: ThemePreset[]
  addCustomPreset: (preset: ThemePreset) => void
  removeCustomPreset: (presetName: string) => void
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

interface ThemeProviderProps {
  children: ReactNode
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({ children }) => {
  const {
    isDark,
    primaryColor,
    secondaryColor,
    successColor,
    warningColor,
    errorColor,
    infoColor,
    toggleTheme,
    setPrimaryColor,
    setThemeColor,
    activePreset,
    setActivePreset,
    applyPreset,
    customPresets,
    addCustomPreset,
    removeCustomPreset,
  } = useThemeStore()

  // 处理深色模式切换时的类名
  useEffect(() => {
    if (isDark) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [isDark])

  const value: ThemeContextType = {
    isDark,
    toggleTheme,
    primaryColor,
    secondaryColor,
    successColor,
    warningColor,
    errorColor,
    infoColor,
    setPrimaryColor,
    setThemeColor,
    activePreset,
    setActivePreset,
    applyPreset,
    presets: defaultThemePresets,
    customPresets,
    addCustomPreset,
    removeCustomPreset,
  }

  const antdTheme = {
    algorithm: isDark ? theme.darkAlgorithm : theme.defaultAlgorithm,
    token: {
      colorPrimary: primaryColor,
      colorSuccess: successColor,
      colorWarning: warningColor,
      colorError: errorColor,
      colorInfo: infoColor,
      borderRadius: 6,
      wireframe: false,
    },
    components: {
      Layout: {
        bodyBg: isDark ? '#141414' : '#f5f5f5',
        headerBg: isDark ? '#001529' : '#ffffff',
        siderBg: isDark ? '#001529' : '#ffffff',
      },
      Menu: {
        itemBg: 'transparent',
        subMenuItemBg: 'transparent',
      },
      Card: {
        colorBgContainer: isDark ? '#1f1f1f' : '#ffffff',
      },
      Table: {
        colorBgContainer: isDark ? '#1f1f1f' : '#ffffff',
      },
      Modal: {
        contentBg: isDark ? '#1f1f1f' : '#ffffff',
      },
      Drawer: {
        colorBgContainer: isDark ? '#1f1f1f' : '#ffffff',
      },
    },
  }

  return (
    <ThemeContext.Provider value={value}>
      <ConfigProvider theme={antdTheme}>{children}</ConfigProvider>
    </ThemeContext.Provider>
  )
}

export const useTheme = (): ThemeContextType => {
  const context = useContext(ThemeContext)
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider')
  }
  return context
}

export default ThemeContext
