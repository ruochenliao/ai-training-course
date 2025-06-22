#!/usr/bin/env node
/**
 * 修补 oxc-parser 包以解决 availableParallelism 兼容性问题
 */

const fs = require('fs');
const path = require('path');

function patchOxcParser() {
  console.log('🔧 开始修补 oxc-parser 包...');
  
  // 查找 oxc-parser 包的路径
  const possiblePaths = [
    'node_modules/.pnpm/oxc-parser@0.72.3/node_modules/oxc-parser/index.js',
    'node_modules/oxc-parser/index.js'
  ];
  
  let oxcParserPath = null;
  for (const possiblePath of possiblePaths) {
    const fullPath = path.join(__dirname, '..', possiblePath);
    if (fs.existsSync(fullPath)) {
      oxcParserPath = fullPath;
      break;
    }
  }
  
  if (!oxcParserPath) {
    console.log('❌ 未找到 oxc-parser 包');
    return false;
  }
  
  console.log('📍 找到 oxc-parser 包:', oxcParserPath);
  
  try {
    // 读取原始文件
    let content = fs.readFileSync(oxcParserPath, 'utf8');
    
    // 检查是否已经修补过
    if (content.includes('// PATCHED FOR NODE 18 COMPATIBILITY')) {
      console.log('✅ oxc-parser 已经修补过了');
      return true;
    }
    
    // 添加 polyfill 代码到文件开头
    const polyfillCode = `// PATCHED FOR NODE 18 COMPATIBILITY
const os = require('os');
if (!os.availableParallelism) {
  os.availableParallelism = function() {
    try {
      return os.cpus().length;
    } catch (e) {
      return 4; // 默认值
    }
  };
}

`;
    
    // 将 polyfill 代码添加到文件开头
    content = polyfillCode + content;
    
    // 写回文件
    fs.writeFileSync(oxcParserPath, content, 'utf8');
    
    console.log('✅ oxc-parser 修补完成');
    return true;
    
  } catch (error) {
    console.error('❌ 修补 oxc-parser 时出错:', error.message);
    return false;
  }
}

// 如果直接运行此脚本
if (require.main === module) {
  const success = patchOxcParser();
  process.exit(success ? 0 : 1);
}

module.exports = patchOxcParser;
