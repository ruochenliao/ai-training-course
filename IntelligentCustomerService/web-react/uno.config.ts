import {
    defineConfig,
    presetAttributify,
    presetIcons,
    presetTypography,
    presetUno,
    presetWebFonts,
    transformerDirectives,
    transformerVariantGroup
} from 'unocss'

export default defineConfig({
  shortcuts: [
    // flex
    ['flex-center', 'flex justify-center items-center'],
    ['flex-col-center', 'flex flex-col justify-center items-center'],
    ['flex-x-center', 'flex justify-center'],
    ['flex-y-center', 'flex items-center'],
    // position
    ['absolute-center', 'absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2'],
    ['fixed-center', 'fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2'],
    // size
    ['size-full', 'w-full h-full'],
    ['size-screen', 'w-screen h-screen'],
    // text
    ['text-ellipsis', 'truncate'],
    // border
    ['border-base', 'border border-gray-200 dark:border-gray-700'],
    // background
    ['bg-base', 'bg-white dark:bg-gray-900'],
    ['bg-container', 'bg-gray-50 dark:bg-gray-800'],
  ],
  presets: [
    presetUno(),
    presetAttributify(),
    presetIcons({
      scale: 1.2,
      warn: true,
      collections: {
        carbon: () => import('@iconify-json/carbon/icons.json').then(i => i.default),
        mdi: () => import('@iconify-json/mdi/icons.json').then(i => i.default),
        tabler: () => import('@iconify-json/tabler/icons.json').then(i => i.default),
      }
    }),
    presetTypography(),
    presetWebFonts({
      fonts: {
        sans: 'DM Sans',
        serif: 'DM Serif Display',
        mono: 'DM Mono',
      },
    }),
  ],
  transformers: [
    transformerDirectives(),
    transformerVariantGroup(),
  ],
  theme: {
    colors: {
      primary: {
        50: '#eff6ff',
        100: '#dbeafe',
        200: '#bfdbfe',
        300: '#93c5fd',
        400: '#60a5fa',
        500: '#3b82f6',
        600: '#2563eb',
        700: '#1d4ed8',
        800: '#1e40af',
        900: '#1e3a8a',
      },
    },
  },
})