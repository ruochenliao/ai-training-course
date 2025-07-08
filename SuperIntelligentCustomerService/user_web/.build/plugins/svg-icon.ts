import { resolve } from 'node:path';
import { createSvgIconsPlugin } from 'vite-plugin-svg-icons';

const root = resolve(import.meta.dirname, '../../');

export default function createSvgIcon(isBuild: boolean) {
  return createSvgIconsPlugin({
    iconDirs: [
      resolve(root, 'src/assets/icons/svg'),
      resolve(root, 'src/assets/icons/Buildings'),
      resolve(root, 'src/assets/icons/Business'),
      resolve(root, 'src/assets/icons/Device'),
      resolve(root, 'src/assets/icons/Document'),
      resolve(root, 'src/assets/icons/Others'),
      resolve(root, 'src/assets/icons/System'),
      resolve(root, 'src/assets/icons/User'),
    ],
    symbolId: 'icon-[dir]-[name]',
    svgoOptions: isBuild,
  });
}
