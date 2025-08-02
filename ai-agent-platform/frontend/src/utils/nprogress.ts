// 页面进度条组件封装
import NProgress from 'nprogress'
import 'nprogress/nprogress.css'

NProgress.configure({ 
  showSpinner: false, // 显示右上角螺旋加载提示
  minimum: 0.3, // 更改启动时使用的最小百分比
  speed: 500, // 递增进度条的速度
  trickleSpeed: 200 // 自动递增间隔
})

// 打开进度条
export const NProgressStart = (color: string = '#409eff') => {
  // 动态设置进度条颜色
  const style = document.createElement('style')
  style.innerHTML = `
    #nprogress .bar {
      background: ${color} !important;
    }
    #nprogress .peg {
      box-shadow: 0 0 10px ${color}, 0 0 5px ${color} !important;
    }
  `
  document.head.appendChild(style)
  NProgress.start()
}

// 关闭进度条
export const NProgressDone = () => {
  NProgress.done()
}

// 设置进度
export const NProgressSet = (progress: number) => {
  NProgress.set(progress)
}

// 增加进度
export const NProgressInc = () => {
  NProgress.inc()
}
