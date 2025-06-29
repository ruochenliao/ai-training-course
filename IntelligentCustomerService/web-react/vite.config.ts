import {defineConfig} from 'vite';
import react from '@vitejs/plugin-react';
import {resolve} from 'path';
import UnoCSS from 'unocss/vite';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react(), UnoCSS()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
      '@/components': resolve(__dirname, 'src/components'),
      '@/pages': resolve(__dirname, 'src/pages'),
      '@/hooks': resolve(__dirname, 'src/hooks'),
      '@/utils': resolve(__dirname, 'src/utils'),
      '@/types': resolve(__dirname, 'src/types'),
      '@/api': resolve(__dirname, 'src/api'),
      '@/store': resolve(__dirname, 'src/store'),
      '@/contexts': resolve(__dirname, 'src/contexts'),
      '@/router': resolve(__dirname, 'src/router'),
      '@/i18n': resolve(__dirname, 'src/i18n'),
      '@/assets': resolve(__dirname, 'src/assets'),
      '@/styles': resolve(__dirname, 'src/styles'),
    },
  },
  server: {
    port: 5173,
    host: true,
    open: true,
    cors: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:9999',
        changeOrigin: true,
        secure: false,
      },
      '/ws': {
        target: 'ws://127.0.0.1:9999',
        ws: true,
        changeOrigin: true,
      },
    },
  },
  build: {
    target: 'es2015',
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: true,
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true,
      },
    },
    rollupOptions: {
      output: {
        chunkFileNames: 'js/[name]-[hash].js',
        entryFileNames: 'js/[name]-[hash].js',
        assetFileNames: '[ext]/[name]-[hash].[ext]',
        manualChunks: {
          vendor: ['react', 'react-dom'],
          antd: ['antd'],
          router: ['react-router-dom'],
          query: ['@tanstack/react-query'],
          i18n: ['react-i18next', 'i18next'],
        },
      },
    },
    chunkSizeWarningLimit: 1000,
  },
  preview: {
    port: 4173,
    host: true,
    cors: true,
  },
  define: {
    __APP_VERSION__: JSON.stringify(process.env.npm_package_version),
  },
  css: {
    preprocessorOptions: {
      less: {
        javascriptEnabled: true,
        additionalData: '@root-entry-name: default;',
      },
    },
  },
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'antd',
      'react-router-dom',
      '@tanstack/react-query',
      'react-i18next',
      'i18next',
      'zustand',
      'axios',
      'dayjs',
    ],
  },
});