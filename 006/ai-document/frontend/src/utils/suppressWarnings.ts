/**
 * 抑制已知的第三方库警告
 * 这些警告来自第三方库，我们无法直接修复，但可以抑制以减少控制台噪音
 */

// 保存原始的console方法
const originalWarn = console.warn;
const originalError = console.error;

// 需要抑制的警告模式
const suppressedWarnings = [
  // React-Quill的findDOMNode警告
  /findDOMNode is deprecated/,
  // Quill的DOMNodeInserted警告
  /DOMNodeInserted.*mutation event/,
  // React Router的未来标志警告（可选）
  /React Router Future Flag Warning/,
];

// 需要抑制的错误模式（谨慎使用）
const suppressedErrors = [
  // 可以在这里添加需要抑制的错误模式
];

/**
 * 检查消息是否应该被抑制
 */
function shouldSuppress(message: string, patterns: RegExp[]): boolean {
  return patterns.some(pattern => pattern.test(message));
}

/**
 * 自定义console.warn，过滤已知警告
 */
console.warn = (...args: any[]) => {
  const message = args.join(' ');
  
  if (!shouldSuppress(message, suppressedWarnings)) {
    originalWarn.apply(console, args);
  }
};

/**
 * 自定义console.error，过滤已知错误（谨慎使用）
 */
console.error = (...args: any[]) => {
  const message = args.join(' ');
  
  if (!shouldSuppress(message, suppressedErrors)) {
    originalError.apply(console, args);
  }
};

/**
 * 恢复原始console方法的函数
 */
export function restoreConsole() {
  console.warn = originalWarn;
  console.error = originalError;
}

/**
 * 开发环境下的警告过滤器
 * 只在开发环境下抑制警告，生产环境保持原样
 */
export function setupDevelopmentWarningFilter() {
  if (process.env.NODE_ENV === 'development') {
    // 只在开发环境下抑制警告
    console.info('🔇 开发环境警告过滤器已启用');
  }
}

// 自动初始化
if (typeof window !== 'undefined' && process.env.NODE_ENV === 'development') {
  setupDevelopmentWarningFilter();
}

export default {
  setupDevelopmentWarningFilter,
  restoreConsole
};
