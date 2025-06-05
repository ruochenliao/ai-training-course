import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

// 导入翻译资源
import zhCN from './locales/zh-CN.json';
import enUS from './locales/en-US.json';

// 配置 i18next
i18n
  
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    // 默认语言
    lng: 'zh-CN',
    
    // 回退语言
    fallbackLng: 'zh-CN',
    
    // 调试模式
    debug: process.env.NODE_ENV === 'development',
    
    // 命名空间
    defaultNS: 'common',
    ns: ['common', 'auth', 'menu', 'form', 'table', 'message'],
    
    // 插值配置
    interpolation: {
      escapeValue: false, // React 已经安全处理了
    },
    
    // 语言检测配置
    detection: {
      order: ['localStorage', 'navigator', 'htmlTag'],
      caches: ['localStorage'],
      lookupLocalStorage: 'i18nextLng',
    },
    
    // 资源配置
    resources: {
      'zh-CN': zhCN,
      'en-US': enUS,
    },
    
    // React 配置
    react: {
      useSuspense: false,
    },
  });

export default i18n;

// 导出语言列表
export const languages = [
  {
    code: 'zh-CN',
    name: '简体中文',
    flag: '🇨🇳',
  },
  {
    code: 'en-US',
    name: 'English',
    flag: '🇺🇸',
  },
];

// 导出语言切换函数
export const changeLanguage = (lng: string) => {
  return i18n.changeLanguage(lng);
};

// 导出当前语言
export const getCurrentLanguage = () => {
  return i18n.language;
};

// 导出翻译函数
export const t = i18n.t.bind(i18n);