import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import * as path from 'path'

// https://vite.dev/config/
export default defineConfig({
  base: './',
  publicDir: 'public',
  resolve: {
    // 路径别名
    alias: [
      { find: '@', replacement: path.resolve(__dirname, 'src') },
      { find: '@/components', replacement: path.resolve(__dirname, 'src/components') },
      { find: '@/pages', replacement: path.resolve(__dirname, 'src/pages') },
      { find: '@/hooks', replacement: path.resolve(__dirname, 'src/hooks') },
      { find: '@/utils', replacement: path.resolve(__dirname, 'src/utils') },
      { find: '@/api', replacement: path.resolve(__dirname, 'src/api') },
      { find: '@/store', replacement: path.resolve(__dirname, 'src/store') },
      { find: '@/assets', replacement: path.resolve(__dirname, 'src/assets') },
      { find: '@/types', replacement: path.resolve(__dirname, 'src/types') },
    ],
  },
  build: {
    target: 'modules', // 浏览器兼容目标
    outDir: 'dist', // 打包输出路径
    assetsDir: 'assets', // 静态资源存放路径
    cssCodeSplit: true, // 允许 css 代码拆分
    sourcemap: false, // 不生成 sourceMap 文件
    minify: 'terser', // 缩小文件体积
    terserOptions: {
      compress: {
        drop_console: true, // 取消 console
        drop_debugger: true, // 取消 debugger
      },
    },
  },
  server: {
    host: 'localhost',
    port: 3001, // 指定服务器端口
    open: true, // 启动开发服务器时，自动在浏览器打开应用
    strictPort: false, // 若端口被占用，尝试下一个可用端口
    https: false, // 不开启 https 服务
    cors: true, // 允许跨域
    // 配置代理
    proxy: {
      '/api': {
        target: 'http://localhost:8000', // 接口地址
        changeOrigin: true, // 接口跨域
        secure: false, // 启用 https 服务时需要配置
      },
    },
  },
  plugins: [react()],
})
