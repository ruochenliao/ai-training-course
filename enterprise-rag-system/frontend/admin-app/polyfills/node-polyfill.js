/**
 * Node.js polyfills for compatibility with older versions
 * 为旧版本 Node.js 提供兼容性 polyfill
 */

// 立即执行，确保在任何模块加载前就设置好 polyfill
(function() {
  const os = require('os');

  // Polyfill for os.availableParallelism() - introduced in Node.js 19.9.0
  // 为 os.availableParallelism() 提供 polyfill - 该函数在 Node.js 19.9.0 中引入
  if (!os.availableParallelism) {
    os.availableParallelism = function() {
      // Fallback to os.cpus().length for older Node.js versions
      // 对于旧版本 Node.js，回退到 os.cpus().length
      try {
        return os.cpus().length;
      } catch (e) {
        // 如果获取 CPU 信息失败，返回默认值
        return 4;
      }
    };

    console.log('[Polyfill] Added os.availableParallelism() for Node.js compatibility');
  }

  // 确保 polyfill 被正确设置
  if (typeof os.availableParallelism === 'function') {
    console.log('[Polyfill] os.availableParallelism() is available, returns:', os.availableParallelism());
  }
})();

module.exports = {};
