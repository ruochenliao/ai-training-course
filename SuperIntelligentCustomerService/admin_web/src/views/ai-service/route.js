/**
 * 智能客服路由配置
 */
const Layout = () => import('@/layout/index.vue')

export default {
  name: '智能客服',
  path: '/ai-service',
  component: Layout,
  meta: {
    title: '智能客服',
    icon: 'material-symbols:smart-toy-outline',
    order: 1,
  },
  children: [
    {
      path: 'model',
      name: 'AiServiceModel',
      component: () => import('./model/index.vue'),
      meta: {
        title: '模型管理',
        icon: 'material-symbols:model-training',
      },
    },
    {
      path: 'knowledge',
      name: 'AiServiceKnowledge',
      component: () => import('./knowledge/index.vue'),
      meta: {
        title: '知识库管理',
        icon: 'material-symbols:library-books-outline',
      },
    },
    {
      path: 'knowledge/files/:kbId',
      name: 'AiServiceKnowledgeFiles',
      component: () => import('./knowledge/files.vue'),
      meta: {
        title: '文件管理',
        icon: 'mdi:file-multiple',
        hideInMenu: true, // 不在菜单中显示
      },
    },
  ],
}
