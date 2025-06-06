import React, {createContext, ReactNode, useContext} from 'react';
import {ConfigProvider, theme} from 'antd';
import {useThemeStore} from '../store/theme';

interface ThemeContextType {
  isDark: boolean;
  toggleTheme: () => void;
  primaryColor: string;
  setPrimaryColor: (color: string) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

interface ThemeProviderProps {
  children: ReactNode;
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({ children }) => {
  const {
    isDark,
    primaryColor,
    toggleTheme,
    setPrimaryColor,
  } = useThemeStore();

  const value: ThemeContextType = {
    isDark,
    toggleTheme,
    primaryColor,
    setPrimaryColor,
  };

  const antdTheme = {
    algorithm: isDark ? theme.darkAlgorithm : theme.defaultAlgorithm,
    token: {
      colorPrimary: primaryColor,
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
    },
  };

  return (
    <ThemeContext.Provider value={value}>
      <ConfigProvider theme={antdTheme}>
        {children}
      </ConfigProvider>
    </ThemeContext.Provider>
  );
};

export const useTheme = (): ThemeContextType => {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

export default ThemeContext;