import { useEffect } from 'react';

/**
 * 工具栏监控组件
 * 专门用于监控和保护Quill编辑器的工具栏显示
 */
const ToolbarMonitor: React.FC = () => {
  useEffect(() => {
    console.log('🔧 工具栏监控器已启动');

    // 强制显示工具栏的函数
    const forceShowToolbar = (toolbar: HTMLElement) => {
      const styles = {
        'display': 'block',
        'visibility': 'visible',
        'opacity': '1',
        'height': 'auto',
        'min-height': '42px',
        'max-height': 'none',
        'overflow': 'visible',
        'position': 'relative',
        'z-index': '1000',
        'background': 'linear-gradient(to bottom, #fafafa, #f0f0f0)',
        'border': 'none',
        'border-bottom': '1px solid #e8e8e8',
        'padding': '12px 16px',
        'box-shadow': '0 1px 3px rgba(0, 0, 0, 0.1)',
        'flex-shrink': '0',
        'transform': 'none',
        'transition': 'none',
        'animation': 'none'
      };

      Object.entries(styles).forEach(([property, value]) => {
        toolbar.style.setProperty(property, value, 'important');
      });

      // 强制显示工具栏内的所有元素
      const elements = toolbar.querySelectorAll('button, .ql-picker, .ql-formats, span, svg');
      elements.forEach(element => {
        const el = element as HTMLElement;
        el.style.setProperty('display', 'inline-block', 'important');
        el.style.setProperty('visibility', 'visible', 'important');
        el.style.setProperty('opacity', '1', 'important');
      });
    };

    // 检查并修复所有工具栏
    const checkAndFixAllToolbars = () => {
      const toolbars = document.querySelectorAll('.ql-toolbar');
      let fixedCount = 0;

      toolbars.forEach(toolbar => {
        const toolbarElement = toolbar as HTMLElement;
        
        // 检查工具栏是否可见
        const computedStyle = window.getComputedStyle(toolbarElement);
        const isHidden = computedStyle.display === 'none' || 
                        computedStyle.visibility === 'hidden' || 
                        computedStyle.opacity === '0' ||
                        toolbarElement.offsetHeight === 0;

        if (isHidden || true) { // 总是强制修复
          forceShowToolbar(toolbarElement);
          fixedCount++;
        }
      });

      return { total: toolbars.length, fixed: fixedCount };
    };

    // 立即检查一次
    const initialCheck = checkAndFixAllToolbars();
    console.log(`🔧 初始检查: 发现 ${initialCheck.total} 个工具栏，修复 ${initialCheck.fixed} 个`);

    // 定期检查（前10秒每100ms检查一次，确保页面加载时工具栏正常）
    let checkCount = 0;
    const maxChecks = 100; // 10秒内检查100次
    
    const intensiveTimer = setInterval(() => {
      checkCount++;
      const result = checkAndFixAllToolbars();
      
      if (result.total > 0 && checkCount % 10 === 0) {
        console.log(`🔧 密集检查 ${checkCount}: 工具栏 ${result.total} 个，修复 ${result.fixed} 个`);
      }
      
      if (checkCount >= maxChecks) {
        clearInterval(intensiveTimer);
        console.log('🔧 密集检查阶段完成，切换到常规监控');
        
        // 切换到常规监控（每2秒检查一次）
        const regularTimer = setInterval(() => {
          const result = checkAndFixAllToolbars();
          if (result.fixed > 0) {
            console.log(`🔧 常规监控: 修复了 ${result.fixed} 个工具栏`);
          }
        }, 2000);

        // 10分钟后停止常规监控
        setTimeout(() => {
          clearInterval(regularTimer);
          console.log('🔧 工具栏监控器已停止常规检查');
        }, 600000);
      }
    }, 100);

    // DOM变化监听器
    const observer = new MutationObserver((mutations) => {
      let shouldCheck = false;
      
      mutations.forEach(mutation => {
        // 检查是否有新的工具栏添加或样式变化
        if (mutation.type === 'childList') {
          const addedNodes = Array.from(mutation.addedNodes);
          const hasToolbar = addedNodes.some(node => {
            if (node.nodeType === Node.ELEMENT_NODE) {
              const element = node as Element;
              return element.classList.contains('ql-toolbar') || 
                     element.querySelector('.ql-toolbar') !== null;
            }
            return false;
          });
          if (hasToolbar) shouldCheck = true;
        }
        
        if (mutation.type === 'attributes' && 
            mutation.target instanceof Element &&
            (mutation.target.classList.contains('ql-toolbar') ||
             mutation.target.closest('.ql-toolbar'))) {
          shouldCheck = true;
        }
      });

      if (shouldCheck) {
        setTimeout(() => {
          const result = checkAndFixAllToolbars();
          if (result.fixed > 0) {
            console.log(`🔧 DOM变化触发: 修复了 ${result.fixed} 个工具栏`);
          }
        }, 50);
      }
    });

    // 开始观察DOM变化
    observer.observe(document.body, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ['style', 'class', 'hidden']
    });

    // 页面可见性变化监听
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        setTimeout(() => {
          const result = checkAndFixAllToolbars();
          if (result.fixed > 0) {
            console.log(`🔧 页面重新可见: 修复了 ${result.fixed} 个工具栏`);
          }
        }, 100);
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);

    // 窗口焦点变化监听
    const handleFocus = () => {
      setTimeout(() => {
        const result = checkAndFixAllToolbars();
        if (result.fixed > 0) {
          console.log(`🔧 窗口获得焦点: 修复了 ${result.fixed} 个工具栏`);
        }
      }, 100);
    };

    window.addEventListener('focus', handleFocus);

    // 清理函数
    return () => {
      clearInterval(intensiveTimer);
      observer.disconnect();
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('focus', handleFocus);
      console.log('🔧 工具栏监控器已清理');
    };
  }, []);

  return null; // 这是一个无UI的监控组件
};

export default ToolbarMonitor;
