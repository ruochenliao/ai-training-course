/**
 * Gemini风格主题配置
 * 支持深色和浅色主题切换
 */

export interface Theme {
  name: string;
  colors: {
    primary: string;
    secondary: string;
    background: string;
    surface: string;
    surfaceVariant: string;
    onBackground: string;
    onSurface: string;
    onSurfaceVariant: string;
    outline: string;
    outlineVariant: string;
    shadow: string;
    scrim: string;
    inverseSurface: string;
    inverseOnSurface: string;
    inversePrimary: string;
    // 消息气泡颜色
    userMessage: string;
    assistantMessage: string;
    systemMessage: string;
    // 状态颜色
    success: string;
    warning: string;
    error: string;
    info: string;
    // 图表颜色
    chart: string[];
  };
  typography: {
    fontFamily: string;
    fontSize: {
      xs: string;
      sm: string;
      base: string;
      lg: string;
      xl: string;
      '2xl': string;
      '3xl': string;
      '4xl': string;
    };
    fontWeight: {
      normal: number;
      medium: number;
      semibold: number;
      bold: number;
    };
    lineHeight: {
      tight: number;
      normal: number;
      relaxed: number;
    };
  };
  spacing: {
    xs: string;
    sm: string;
    md: string;
    lg: string;
    xl: string;
    '2xl': string;
    '3xl': string;
    '4xl': string;
  };
  borderRadius: {
    sm: string;
    md: string;
    lg: string;
    xl: string;
    full: string;
  };
  shadows: {
    sm: string;
    md: string;
    lg: string;
    xl: string;
  };
  animation: {
    duration: {
      fast: string;
      normal: string;
      slow: string;
    };
    easing: {
      easeIn: string;
      easeOut: string;
      easeInOut: string;
    };
  };
}

// 浅色主题 (Gemini Light)
export const lightTheme: Theme = {
  name: 'light',
  colors: {
    primary: '#1a73e8',
    secondary: '#5f6368',
    background: '#ffffff',
    surface: '#f8f9fa',
    surfaceVariant: '#e8eaed',
    onBackground: '#202124',
    onSurface: '#3c4043',
    onSurfaceVariant: '#5f6368',
    outline: '#dadce0',
    outlineVariant: '#e8eaed',
    shadow: 'rgba(60, 64, 67, 0.3)',
    scrim: 'rgba(60, 64, 67, 0.4)',
    inverseSurface: '#2d3134',
    inverseOnSurface: '#f1f3f4',
    inversePrimary: '#8ab4f8',
    // 消息气泡
    userMessage: '#1a73e8',
    assistantMessage: '#f8f9fa',
    systemMessage: '#e8f0fe',
    // 状态颜色
    success: '#137333',
    warning: '#f29900',
    error: '#d93025',
    info: '#1a73e8',
    // 图表颜色
    chart: [
      '#1a73e8', '#34a853', '#fbbc04', '#ea4335',
      '#9aa0a6', '#ff6d01', '#9c27b0', '#00acc1'
    ]
  },
  typography: {
    fontFamily: '"Google Sans", "Roboto", -apple-system, BlinkMacSystemFont, sans-serif',
    fontSize: {
      xs: '0.75rem',
      sm: '0.875rem',
      base: '1rem',
      lg: '1.125rem',
      xl: '1.25rem',
      '2xl': '1.5rem',
      '3xl': '1.875rem',
      '4xl': '2.25rem'
    },
    fontWeight: {
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700
    },
    lineHeight: {
      tight: 1.25,
      normal: 1.5,
      relaxed: 1.75
    }
  },
  spacing: {
    xs: '0.25rem',
    sm: '0.5rem',
    md: '1rem',
    lg: '1.5rem',
    xl: '2rem',
    '2xl': '3rem',
    '3xl': '4rem',
    '4xl': '6rem'
  },
  borderRadius: {
    sm: '0.25rem',
    md: '0.5rem',
    lg: '0.75rem',
    xl: '1rem',
    full: '9999px'
  },
  shadows: {
    sm: '0 1px 2px 0 rgba(60, 64, 67, 0.3), 0 1px 3px 1px rgba(60, 64, 67, 0.15)',
    md: '0 1px 2px 0 rgba(60, 64, 67, 0.3), 0 2px 6px 2px rgba(60, 64, 67, 0.15)',
    lg: '0 2px 3px 0 rgba(60, 64, 67, 0.3), 0 6px 10px 4px rgba(60, 64, 67, 0.15)',
    xl: '0 4px 4px 0 rgba(60, 64, 67, 0.3), 0 8px 12px 6px rgba(60, 64, 67, 0.15)'
  },
  animation: {
    duration: {
      fast: '150ms',
      normal: '300ms',
      slow: '500ms'
    },
    easing: {
      easeIn: 'cubic-bezier(0.4, 0, 1, 1)',
      easeOut: 'cubic-bezier(0, 0, 0.2, 1)',
      easeInOut: 'cubic-bezier(0.4, 0, 0.2, 1)'
    }
  }
};

// 深色主题 (Gemini Dark)
export const darkTheme: Theme = {
  name: 'dark',
  colors: {
    primary: '#8ab4f8',
    secondary: '#9aa0a6',
    background: '#202124',
    surface: '#303134',
    surfaceVariant: '#3c4043',
    onBackground: '#e8eaed',
    onSurface: '#f1f3f4',
    onSurfaceVariant: '#9aa0a6',
    outline: '#5f6368',
    outlineVariant: '#3c4043',
    shadow: 'rgba(0, 0, 0, 0.3)',
    scrim: 'rgba(0, 0, 0, 0.4)',
    inverseSurface: '#f1f3f4',
    inverseOnSurface: '#3c4043',
    inversePrimary: '#1a73e8',
    // 消息气泡
    userMessage: '#8ab4f8',
    assistantMessage: '#303134',
    systemMessage: '#1e3a8a',
    // 状态颜色
    success: '#81c995',
    warning: '#fdd663',
    error: '#f28b82',
    info: '#8ab4f8',
    // 图表颜色
    chart: [
      '#8ab4f8', '#81c995', '#fdd663', '#f28b82',
      '#9aa0a6', '#ff8a65', '#ba68c8', '#4dd0e1'
    ]
  },
  typography: {
    fontFamily: '"Google Sans", "Roboto", -apple-system, BlinkMacSystemFont, sans-serif',
    fontSize: {
      xs: '0.75rem',
      sm: '0.875rem',
      base: '1rem',
      lg: '1.125rem',
      xl: '1.25rem',
      '2xl': '1.5rem',
      '3xl': '1.875rem',
      '4xl': '2.25rem'
    },
    fontWeight: {
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700
    },
    lineHeight: {
      tight: 1.25,
      normal: 1.5,
      relaxed: 1.75
    }
  },
  spacing: {
    xs: '0.25rem',
    sm: '0.5rem',
    md: '1rem',
    lg: '1.5rem',
    xl: '2rem',
    '2xl': '3rem',
    '3xl': '4rem',
    '4xl': '6rem'
  },
  borderRadius: {
    sm: '0.25rem',
    md: '0.5rem',
    lg: '0.75rem',
    xl: '1rem',
    full: '9999px'
  },
  shadows: {
    sm: '0 1px 2px 0 rgba(0, 0, 0, 0.3), 0 1px 3px 1px rgba(0, 0, 0, 0.15)',
    md: '0 1px 2px 0 rgba(0, 0, 0, 0.3), 0 2px 6px 2px rgba(0, 0, 0, 0.15)',
    lg: '0 2px 3px 0 rgba(0, 0, 0, 0.3), 0 6px 10px 4px rgba(0, 0, 0, 0.15)',
    xl: '0 4px 4px 0 rgba(0, 0, 0, 0.3), 0 8px 12px 6px rgba(0, 0, 0, 0.15)'
  },
  animation: {
    duration: {
      fast: '150ms',
      normal: '300ms',
      slow: '500ms'
    },
    easing: {
      easeIn: 'cubic-bezier(0.4, 0, 1, 1)',
      easeOut: 'cubic-bezier(0, 0, 0.2, 1)',
      easeInOut: 'cubic-bezier(0.4, 0, 0.2, 1)'
    }
  }
};

export const themes = {
  light: lightTheme,
  dark: darkTheme
};

export type ThemeName = keyof typeof themes;
