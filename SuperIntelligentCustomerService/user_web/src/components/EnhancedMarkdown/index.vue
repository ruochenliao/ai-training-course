<!-- 增强的Markdown渲染组件 -->
<script setup lang="ts">
import {XMarkdown} from 'vue-element-plus-x';
import {computed, nextTick, ref, watch} from 'vue';

interface Props {
  content: string;
  isStreaming?: boolean;
  enableLatex?: boolean;
  enableBreaks?: boolean;
  allowHtml?: boolean;
  showCopyButton?: boolean;
  showLineNumbers?: boolean;
  theme?: 'light' | 'dark' | 'auto';
}

const props = withDefaults(defineProps<Props>(), {
  isStreaming: false,
  enableLatex: true,
  enableBreaks: true,
  allowHtml: true,
  showCopyButton: true,
  showLineNumbers: false,
  theme: 'auto'
});

const markdownRef = ref<InstanceType<typeof XMarkdown>>();
const isRendering = ref(false);
const renderError = ref<string | null>(null);

// 防抖渲染，避免流式输入时频繁重新渲染
const debouncedContent = ref(props.content);
let debounceTimer: NodeJS.Timeout | null = null;

watch(() => props.content, (newContent) => {
  if (debounceTimer) {
    clearTimeout(debounceTimer);
  }
  
  // 如果是流式输入，使用较短的防抖时间
  const debounceTime = props.isStreaming ? 100 : 50;
  
  debounceTimer = setTimeout(() => {
    debouncedContent.value = newContent;
  }, debounceTime);
}, { immediate: true });

// 主题配置
const themeConfig = computed(() => {
  const themes = {
    light: 'vitesse-light',
    dark: 'vitesse-dark'
  };
  
  return {
    light: themes.light,
    dark: themes.dark
  };
});

// 当前主题模式
const currentTheme = computed(() => {
  if (props.theme === 'auto') {
    // 可以根据系统主题或用户设置来决定
    return 'light'; // 默认浅色主题
  }
  return props.theme;
});

// 复制代码功能
const copyCode = async (code: string) => {
  try {
    await navigator.clipboard.writeText(code);
    ElMessage.success('代码已复制到剪贴板');
  } catch (err) {
    console.error('复制失败:', err);
    ElMessage.error('复制失败，请手动复制');
  }
};

// 处理渲染错误
const handleRenderError = (error: any) => {
  console.error('Markdown渲染错误:', error);
  renderError.value = error.message || '渲染出现错误';
};

// 清除错误状态
const clearError = () => {
  renderError.value = null;
};

// 监听内容变化，清除错误状态
watch(debouncedContent, () => {
  clearError();
});

// 暴露方法给父组件
defineExpose({
  copyCode,
  clearError,
  scrollToBottom: () => {
    nextTick(() => {
      const element = markdownRef.value?.$el;
      if (element) {
        element.scrollTop = element.scrollHeight;
      }
    });
  }
});
</script>

<template>
  <div class="enhanced-markdown-container">
    <!-- 错误提示 -->
    <div v-if="renderError" class="error-banner">
      <el-alert
        :title="renderError"
        type="error"
        :closable="true"
        @close="clearError"
      />
    </div>

    <!-- 加载状态 -->
    <div v-if="isRendering" class="loading-indicator">
      <el-skeleton :rows="3" animated />
    </div>

    <!-- Markdown内容 -->
    <div v-show="!renderError && !isRendering" class="markdown-wrapper">
      <XMarkdown
        ref="markdownRef"
        :markdown="debouncedContent"
        :enable-latex="enableLatex"
        :enable-breaks="enableBreaks"
        :allow-html="allowHtml"
        :themes="themeConfig"
        :default-theme-mode="currentTheme"
        :need-view-code-btn="showCopyButton"
        class="enhanced-markdown-content"
        @error="handleRenderError"
      />
    </div>

    <!-- 流式输入指示器 -->
    <div v-if="isStreaming" class="streaming-indicator">
      <div class="typing-cursor">|</div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.enhanced-markdown-container {
  position: relative;
  width: 100%;
  max-width: 100%;
  overflow: hidden;

  .error-banner {
    margin-bottom: 12px;
  }

  .loading-indicator {
    padding: 16px;
  }

  .markdown-wrapper {
    position: relative;
    width: 100%;
    overflow-wrap: break-word;
    word-wrap: break-word;
  }

  .streaming-indicator {
    display: flex;
    align-items: center;
    margin-top: 4px;
    
    .typing-cursor {
      display: inline-block;
      font-weight: bold;
      color: #409eff;
      animation: blink 1s infinite;
      font-size: 16px;
      line-height: 1;
    }
  }
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

// 深度样式优化
.enhanced-markdown-content {
  // 基础样式
  font-size: 14px;
  line-height: 1.6;
  color: #24292f;
  word-wrap: break-word;
  max-width: 100%;
  overflow-wrap: break-word;

  // 图片样式优化
  :deep(img) {
    max-width: 100%;
    height: auto;
    border-radius: 8px;
    margin: 8px 0;
    display: block;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    transition: transform 0.2s ease;

    &:hover {
      transform: scale(1.02);
    }
  }

  // 代码块样式优化
  :deep(.shiki) {
    background-color: #f6f8fa !important;
    border: 1px solid #d0d7de;
    border-radius: 8px;
    padding: 16px;
    margin: 12px 0;
    overflow-x: auto;
    font-size: 13px;
    line-height: 1.45;
    max-width: 100%;
    position: relative;

    // 代码字体
    code {
      background: transparent !important;
      padding: 0;
      border-radius: 0;
      font-family: 'SFMono-Regular', 'Consolas', 'Liberation Mono', 'Menlo', monospace;
    }

    // 行号样式
    .line-numbers {
      position: absolute;
      left: 0;
      top: 16px;
      bottom: 16px;
      width: 40px;
      background: rgba(0, 0, 0, 0.05);
      border-right: 1px solid #d0d7de;
      padding: 0 8px;
      font-size: 12px;
      color: #656d76;
      user-select: none;
    }
  }

  // 行内代码样式
  :deep(code:not(.shiki code)) {
    background-color: rgba(175, 184, 193, 0.2);
    padding: 2px 4px;
    border-radius: 4px;
    font-size: 0.9em;
    font-family: 'SFMono-Regular', 'Consolas', 'Liberation Mono', 'Menlo', monospace;
  }

  // 表格样式优化
  :deep(table) {
    border-collapse: collapse;
    width: 100%;
    margin: 16px 0;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);

    th, td {
      border: 1px solid #d0d7de;
      padding: 8px 12px;
      text-align: left;
    }

    th {
      background-color: #f6f8fa;
      font-weight: 600;
    }

    tr:nth-child(even) {
      background-color: #f6f8fa;
    }
  }

  // 引用块样式
  :deep(blockquote) {
    border-left: 4px solid #409eff;
    padding: 8px 16px;
    margin: 16px 0;
    background-color: #f8f9fa;
    border-radius: 0 4px 4px 0;
    
    p {
      margin: 0;
    }
  }

  // 列表样式
  :deep(ul), :deep(ol) {
    padding-left: 24px;
    margin: 8px 0;

    li {
      margin: 4px 0;
    }
  }

  // 标题样式
  :deep(h1), :deep(h2), :deep(h3), :deep(h4), :deep(h5), :deep(h6) {
    margin: 16px 0 8px 0;
    font-weight: 600;
    line-height: 1.25;

    &:first-child {
      margin-top: 0;
    }
  }

  :deep(h1) { font-size: 1.5em; border-bottom: 1px solid #d0d7de; padding-bottom: 8px; }
  :deep(h2) { font-size: 1.3em; }
  :deep(h3) { font-size: 1.1em; }

  // 分割线样式
  :deep(hr) {
    border: none;
    border-top: 1px solid #d0d7de;
    margin: 24px 0;
  }

  // 链接样式
  :deep(a) {
    color: #0969da;
    text-decoration: none;
    
    &:hover {
      text-decoration: underline;
    }
  }

  // 数学公式样式
  :deep(.katex) {
    font-size: 1.1em;
  }

  :deep(.katex-display) {
    margin: 16px 0;
    text-align: center;
  }
}

// 暗色主题适配
@media (prefers-color-scheme: dark) {
  .enhanced-markdown-content {
    color: #e6edf3;

    :deep(.shiki) {
      background-color: #161b22 !important;
      border-color: #30363d;
    }

    :deep(code:not(.shiki code)) {
      background-color: rgba(110, 118, 129, 0.4);
    }

    :deep(table) {
      th {
        background-color: #21262d;
      }

      th, td {
        border-color: #30363d;
      }

      tr:nth-child(even) {
        background-color: #161b22;
      }
    }

    :deep(blockquote) {
      background-color: #161b22;
      border-left-color: #409eff;
    }

    :deep(h1) {
      border-bottom-color: #30363d;
    }

    :deep(hr) {
      border-top-color: #30363d;
    }

    :deep(a) {
      color: #58a6ff;
    }
  }
}
</style>
