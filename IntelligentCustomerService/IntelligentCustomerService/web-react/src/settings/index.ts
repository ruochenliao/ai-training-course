// 主题配置导出 - 对应Vue版本的settings/index.js
import themeConfig from './theme.json';

export { themeConfig };

// 布局设置 - 对应Vue版本的 header, tags 配置
export const layoutSettings = {
  header: {
    height: themeConfig.layout.header.height,
  },
  tags: {
    visible: themeConfig.layout.tags.visible,
    height: themeConfig.layout.tags.height,
  },
};

// Naive UI主题覆盖 - 对应Vue版本的 naiveThemeOverrides
export const naiveThemeOverrides = themeConfig.naiveThemeOverrides;

// 默认导出
export default {
  themeConfig,
  layoutSettings,
  naiveThemeOverrides,
};
