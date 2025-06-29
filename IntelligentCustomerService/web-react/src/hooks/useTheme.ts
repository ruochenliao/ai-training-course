import {useCallback, useEffect} from 'react'
import {useAppStore} from '@/store/app.ts'
import useLocalStorage from './useLocalStorage.ts'

export type ThemeMode = 'light' | 'dark' | 'system'

/**
 * 主题Hook
 */
function useTheme() {
  const { theme, setTheme } = useAppStore()
  const [themeMode, setThemeMode] = useLocalStorage<ThemeMode>('theme-mode', 'system')

  // 检测系统主题
  const detectSystemTheme = useCallback((): 'light' | 'dark' => {
    if (typeof window === 'undefined') return 'light'
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  }, [])

  // 应用主题
  const applyTheme = useCallback(
    (mode: ThemeMode) => {
      const finalTheme = mode === 'system' ? detectSystemTheme() : mode

      // 更新store中的主题
      setTheme(finalTheme)

      // 更新HTML根元素的class
      if (finalTheme === 'dark') {
        document.documentElement.classList.add('dark')
        document.documentElement.setAttribute('data-theme', 'dark')
      } else {
        document.documentElement.classList.remove('dark')
        document.documentElement.setAttribute('data-theme', 'light')
      }
    },
    [detectSystemTheme, setTheme],
  )

  // 切换主题
  const toggleTheme = useCallback(() => {
    const newMode: ThemeMode = themeMode === 'light' ? 'dark' : themeMode === 'dark' ? 'system' : 'light'
    setThemeMode(newMode)
    applyTheme(newMode)
  }, [themeMode, setThemeMode, applyTheme])

  // 设置主题
  const changeTheme = useCallback(
    (mode: ThemeMode) => {
      setThemeMode(mode)
      applyTheme(mode)
    },
    [setThemeMode, applyTheme],
  )

  // 监听系统主题变化
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')

    const handleChange = () => {
      if (themeMode === 'system') {
        applyTheme('system')
      }
    }

    mediaQuery.addEventListener('change', handleChange)

    return () => {
      mediaQuery.removeEventListener('change', handleChange)
    }
  }, [themeMode, applyTheme])

  // 初始化主题
  useEffect(() => {
    applyTheme(themeMode)
  }, [themeMode, applyTheme])

  return {
    theme,
    themeMode,
    isDark: theme === 'dark',
    isLight: theme === 'light',
    isSystem: themeMode === 'system',
    toggleTheme,
    changeTheme,
  }
}

export default useTheme
