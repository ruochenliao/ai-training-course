import type { ConfigEnv, PluginOption } from 'vite';
import { resolve } from 'node:path';
import vue from '@vitejs/plugin-vue';
import UnoCSS from 'unocss/vite';
import AutoImport from 'unplugin-auto-import/vite';
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers';
import Components from 'unplugin-vue-components/vite';
import envTyped from 'vite-plugin-env-typed';
import createSvgIcon from './svg-icon.js';

const root = resolve(import.meta.dirname, '../../');

function plugins({ mode, command }: ConfigEnv): PluginOption[] {
  return [
    UnoCSS(),
    envTyped({
      mode,
      envDir: root,
      envPrefix: 'VITE_',
      filePath: resolve(root, 'types', 'import_meta.d.ts'),
    }),
    vue(),
    AutoImport({
      imports: ['vue'],
      eslintrc: {
        enabled: true,
      },
      resolvers: [ElementPlusResolver()],
      dts: resolve(root, 'types', 'auto-imports.d.ts'),
    }),
    Components({
      resolvers: [ElementPlusResolver()],
      dts: resolve(root, 'types', 'components.d.ts'),
    }),
    createSvgIcon(command === 'build'),
  ];
}

export default plugins;
