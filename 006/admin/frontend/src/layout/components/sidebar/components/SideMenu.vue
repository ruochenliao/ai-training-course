<template>
  <n-menu
    ref="menu"
    class="side-menu"
    accordion
    :indent="18"
    :collapsed-icon-size="22"
    :collapsed-width="64"
    :options="menuOptions"
    :value="activeKey"
    @update:value="handleMenuSelect"
  />
</template>

<script setup>
import { usePermissionStore, useAppStore } from '@/store'
import { renderCustomIcon, renderIcon, isExternal } from '@/utils'

const router = useRouter()
const curRoute = useRoute()
const permissionStore = usePermissionStore()
const appStore = useAppStore()

const activeKey = computed(() => curRoute.meta?.activeMenu || curRoute.name)

const menuOptions = computed(() => {
  return permissionStore.menus.map((item) => getMenuItem(item)).sort((a, b) => a.order - b.order)
})

const menu = ref(null)
watch(curRoute, async () => {
  await nextTick()
  menu.value?.showOption()
})

function resolvePath(basePath, path) {
  if (isExternal(path)) return path
  return (
    '/' +
    [basePath, path]
      .filter((path) => !!path && path !== '/')
      .map((path) => path.replace(/(^\/)|(\/$)/g, ''))
      .join('/')
  )
}

function getMenuItem(route, basePath = '') {
  let menuItem = {
    label: (route.meta && route.meta.title) || route.name,
    key: route.name,
    path: resolvePath(basePath, route.path),
    icon: getIcon(route.meta),
    order: route.meta?.order || 0,
  }

  const visibleChildren = route.children
    ? route.children.filter((item) => item.name && !item.isHidden)
    : []

  if (!visibleChildren.length) return menuItem

  if (visibleChildren.length === 1) {
    // 单个子路由处理
    const singleRoute = visibleChildren[0]
    menuItem = {
      ...menuItem,
      label: singleRoute.meta?.title || singleRoute.name,
      key: singleRoute.name,
      path: resolvePath(menuItem.path, singleRoute.path),
      icon: getIcon(singleRoute.meta),
    }
    const visibleItems = singleRoute.children
      ? singleRoute.children.filter((item) => item.name && !item.isHidden)
      : []

    if (visibleItems.length === 1) {
      menuItem = getMenuItem(visibleItems[0], menuItem.path)
    } else if (visibleItems.length > 1) {
      menuItem.children = visibleItems
        .map((item) => getMenuItem(item, menuItem.path))
        .sort((a, b) => a.order - b.order)
    }
  } else {
    menuItem.children = visibleChildren
      .map((item) => getMenuItem(item, menuItem.path))
      .sort((a, b) => a.order - b.order)
  }
  return menuItem
}

function getIcon(meta) {
  if (meta?.customIcon) return renderCustomIcon(meta.customIcon, { size: 18 })
  if (meta?.icon) return renderIcon(meta.icon, { size: 18 })
  return null
}

function handleMenuSelect(key, item) {
  if (isExternal(item.path)) {
    window.open(item.path)
  } else {
    if (item.path === curRoute.path) {
      appStore.reloadPage()
    } else {
      router.push(item.path)
    }
  }
}
</script>

<style lang="scss">
.side-menu {
  background-color: transparent !important;

  .n-menu-item-content {
    margin: 4px 8px;
    border-radius: 6px;
    transition: all 0.2s ease;
    position: relative;
    overflow: hidden;
    color: #333333 !important; /* 深色文字在浅色背景上 */
    font-weight: 500;

    &::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      width: 3px;
      height: 100%;
      background: transparent;
      transition: all 0.2s ease;
    }

    &.n-menu-item-content--selected {
      background-color: rgba(var(--primary-color-rgb), 0.1) !important; /* 半透明主题色背景 */
      color: var(--primary-color) !important; /* 主题色文字 */
      font-weight: 600;

      &::before {
        background: var(--primary-color);
      }

      .n-menu-item-content__icon {
        color: var(--primary-color) !important;
      }
    }

    &:hover:not(.n-menu-item-content--selected) {
      background-color: rgba(0, 0, 0, 0.05);
      color: var(--primary-color) !important;

      &::before {
        background: rgba(var(--primary-color-rgb), 0.5);
      }

      .n-menu-item-content__icon {
        color: var(--primary-color) !important;
      }
    }

    .n-menu-item-content__icon {
      transition: all 0.2s ease;
      font-size: 16px !important;
      margin-right: 10px !important;
      color: #666666; /* 图标颜色 */
    }

    .n-menu-item-content-header {
      font-size: 14px !important;
    }
  }

  // 暗色模式下的样式
  html.dark & {
    .n-menu-item-content {
      color: rgba(255, 255, 255, 0.85) !important;

      &.n-menu-item-content--selected {
        background-color: rgba(var(--primary-color-rgb), 0.2) !important;
      }

      &:hover:not(.n-menu-item-content--selected) {
        background-color: rgba(255, 255, 255, 0.08);
      }

      .n-menu-item-content__icon {
        color: rgba(255, 255, 255, 0.65);
      }
    }
  }

  // 折叠状态下的菜单样式
  &.n-menu--collapsed {
    .n-menu-item-content {
      margin: 4px 8px;
      justify-content: center;

      .n-menu-item-content__icon {
        margin-right: 0;
        font-size: 18px !important;
      }
    }
  }

  // 子菜单样式
  .n-submenu-children {
    padding-left: 12px;

    &::before {
      content: '';
      position: absolute;
      left: 24px;
      top: 0;
      height: 100%;
      width: 1px;
      background: rgba(0, 0, 0, 0.1); /* 浅色背景上的深色连接线 */
    }

    // 子菜单项特殊样式
    .n-menu-item-content {
      margin-left: 12px;

      &.n-menu-item-content--selected {
        background-color: rgba(var(--primary-color-rgb), 0.1) !important;
      }
    }
  }

  // 子菜单标题样式
  .n-submenu-trigger {
    margin: 4px 8px;
    border-radius: 6px;
    color: #333333 !important; /* 深色文字 */
    font-weight: 500;

    &:hover {
      background-color: rgba(0, 0, 0, 0.05) !important;
      color: var(--primary-color) !important;
    }

    &.n-submenu-trigger--active {
      color: var(--primary-color) !important;
      font-weight: 600;

      .n-submenu-trigger__icon {
        color: var(--primary-color) !important;
      }

      .n-submenu-trigger__prefix {
        color: var(--primary-color) !important;
      }
    }

    .n-submenu-trigger__prefix {
      margin-right: 10px !important;
      font-size: 16px !important;
      color: #666666; /* 图标颜色 */
    }
  }

  // 暗色模式下的子菜单样式
  html.dark & {
    .n-submenu-children::before {
      background: rgba(255, 255, 255, 0.1);
    }

    .n-submenu-trigger {
      color: rgba(255, 255, 255, 0.85) !important;

      &:hover {
        background-color: rgba(255, 255, 255, 0.08) !important;
      }

      .n-submenu-trigger__prefix {
        color: rgba(255, 255, 255, 0.65);
      }
    }
  }
}


</style>
