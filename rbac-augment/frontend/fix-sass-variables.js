const fs = require('fs');
const path = require('path');

// 需要替换的变量列表
const variables = [
  'spacing-lg', 'spacing-md', 'spacing-sm', 'spacing-xs', 'spacing-xl',
  'border-radius-base', 'border-radius-small', 'border-radius-large',
  'box-shadow-base', 'box-shadow-light',
  'header-height', 'sidebar-width', 'sidebar-collapsed-width', 'footer-height',
  'border-color-base', 'border-color-light', 'border-color-lighter', 'border-color-extra-light',
  'text-color-primary', 'text-color-regular', 'text-color-secondary', 'text-color-placeholder',
  'font-size-xs', 'font-size-sm', 'font-size-base', 'font-size-lg', 'font-size-xl',
  'primary-color', 'success-color', 'warning-color', 'danger-color', 'info-color',
  'background-color-base', 'background-color-light',
  'dark-bg-color', 'dark-bg-color-light', 'dark-text-color', 'dark-text-color-light', 'dark-border-color',
  'transition-base', 'transition-fade', 'transition-md-fade',
  'z-index-normal', 'z-index-top', 'z-index-popper'
];

function fixSassFile(filePath) {
  console.log(`修复文件: ${filePath}`);
  
  let content = fs.readFileSync(filePath, 'utf8');
  
  // 替换所有变量引用
  variables.forEach(variable => {
    const oldPattern = new RegExp(`\\$${variable}`, 'g');
    const newPattern = `vars.$${variable}`;
    content = content.replace(oldPattern, newPattern);
  });
  
  fs.writeFileSync(filePath, content, 'utf8');
  console.log(`✅ 已修复: ${filePath}`);
}

// 修复文件列表
const filesToFix = [
  './src/styles/components.scss',
  './src/styles/pages.scss'
];

filesToFix.forEach(file => {
  const fullPath = path.join(__dirname, file);
  if (fs.existsSync(fullPath)) {
    fixSassFile(fullPath);
  } else {
    console.log(`⚠️  文件不存在: ${fullPath}`);
  }
});

console.log('🎉 所有文件修复完成！');
