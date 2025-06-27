/**
 * 主题上下文和Provider
 * 支持深色/浅色主题切换和持久化
 */

'use client';

import React, {createContext, useContext, useEffect, useState} from 'react';
import {lightTheme, Theme, ThemeName, themes} from '@/styles/themes';

interface ThemeContextType {
  theme: Theme;
  themeName: ThemeName;
  toggleTheme: () => void;
  setTheme: (themeName: ThemeName) => void;
  isDark: boolean;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

interface ThemeProviderProps {
  children: React.ReactNode;
  defaultTheme?: ThemeName;
}

export function ThemeProvider({ children, defaultTheme = 'light' }: ThemeProviderProps) {
  const [themeName, setThemeName] = useState<ThemeName>(defaultTheme);
  const [mounted, setMounted] = useState(false);

  // 从localStorage读取主题设置
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') as ThemeName;
    if (savedTheme && themes[savedTheme]) {
      setThemeName(savedTheme);
    } else {
      // 检测系统主题偏好
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      setThemeName(prefersDark ? 'dark' : 'light');
    }
    setMounted(true);
  }, []);

  // 保存主题设置到localStorage
  useEffect(() => {
    if (mounted) {
      localStorage.setItem('theme', themeName);
      
      // 更新HTML根元素的data-theme属性
      document.documentElement.setAttribute('data-theme', themeName);
      
      // 更新CSS变量
      const theme = themes[themeName];
      const root = document.documentElement;
      
      // 设置颜色变量
      Object.entries(theme.colors).forEach(([key, value]) => {
        if (Array.isArray(value)) {
          value.forEach((color, index) => {
            root.style.setProperty(`--color-${key}-${index}`, color);
          });
        } else {
          root.style.setProperty(`--color-${key}`, value);
        }
      });
      
      // 设置字体变量
      root.style.setProperty('--font-family', theme.typography.fontFamily);
      Object.entries(theme.typography.fontSize).forEach(([key, value]) => {
        root.style.setProperty(`--font-size-${key}`, value);
      });
      
      // 设置间距变量
      Object.entries(theme.spacing).forEach(([key, value]) => {
        root.style.setProperty(`--spacing-${key}`, value);
      });
      
      // 设置圆角变量
      Object.entries(theme.borderRadius).forEach(([key, value]) => {
        root.style.setProperty(`--border-radius-${key}`, value);
      });
      
      // 设置阴影变量
      Object.entries(theme.shadows).forEach(([key, value]) => {
        root.style.setProperty(`--shadow-${key}`, value);
      });
    }
  }, [themeName, mounted]);

  const toggleTheme = () => {
    setThemeName(prev => prev === 'light' ? 'dark' : 'light');
  };

  const setTheme = (newTheme: ThemeName) => {
    setThemeName(newTheme);
  };

  const theme = themes[themeName];
  const isDark = themeName === 'dark';

  // 防止服务端渲染不匹配
  if (!mounted) {
    return (
      <ThemeContext.Provider value={{
        theme: lightTheme,
        themeName: 'light',
        toggleTheme: () => {},
        setTheme: () => {},
        isDark: false
      }}>
        {children}
      </ThemeContext.Provider>
    );
  }

  return (
    <ThemeContext.Provider value={{
      theme,
      themeName,
      toggleTheme,
      setTheme,
      isDark
    }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}

// 主题切换Hook
export function useThemeToggle() {
  const { toggleTheme, isDark } = useTheme();
  return { toggleTheme, isDark };
}

// 获取当前主题颜色的Hook
export function useThemeColors() {
  const { theme } = useTheme();
  return theme.colors;
}

// 获取当前主题排版的Hook
export function useThemeTypography() {
  const { theme } = useTheme();
  return theme.typography;
}

// 获取当前主题间距的Hook
export function useThemeSpacing() {
  const { theme } = useTheme();
  return theme.spacing;
}

// 监听系统主题变化的Hook
export function useSystemTheme() {
  const { setTheme } = useTheme();
  
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    
    const handleChange = (e: MediaQueryListEvent) => {
      // 只有在用户没有手动设置主题时才跟随系统
      const savedTheme = localStorage.getItem('theme');
      if (!savedTheme) {
        setTheme(e.matches ? 'dark' : 'light');
      }
    };
    
    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, [setTheme]);
}
