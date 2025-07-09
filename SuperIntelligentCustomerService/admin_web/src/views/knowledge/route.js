/**
 * 知识库管理路由配置
 */
const Layout = () => import('@/layout/index.vue')

export default {
  name: '知识库管理',
  path: '/knowledge',
  component: Layout,
  meta: {
    title: '知识库管理',
    icon: 'mdi:database',
    order: 5,
  },
  children: [
    {
      path: '',
      name: 'Knowledge',
      component: () => import('./index.vue'),
      meta: {
        title: '知识库列表',
        icon: 'mdi:database-outline',
      },
    },
    {
      path: 'files/:kbId',
      name: 'KnowledgeFiles',
      component: () => import('./files.vue'),
      meta: {
        title: '文件管理',
        icon: 'mdi:file-multiple',
        hideInMenu: true, // 不在菜单中显示
      },
    },
  ],
}
