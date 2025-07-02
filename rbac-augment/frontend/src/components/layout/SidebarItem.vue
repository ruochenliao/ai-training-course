<template>
  <div v-if="!item.meta?.hidden">
    <!-- 有子菜单的情况 -->
    <el-sub-menu
      v-if="hasChildren"
      :index="item.path"
      :popper-append-to-body="false"
    >
      <template #title>
        <el-icon v-if="item.meta?.icon">
          <component :is="item.meta.icon" />
        </el-icon>
        <span>{{ item.meta?.title }}</span>
      </template>
      
      <sidebar-item
        v-for="child in visibleChildren"
        :key="child.path"
        :item="child"
        :base-path="resolvePath(child.path)"
      />
    </el-sub-menu>

    <!-- 没有子菜单的情况 -->
    <el-menu-item
      v-else
      :index="resolvePath(item.path)"
    >
      <el-icon v-if="item.meta?.icon">
        <component :is="item.meta.icon" />
      </el-icon>
      <template #title>
        <span>{{ item.meta?.title }}</span>
      </template>
    </el-menu-item>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { hasPermission } from '@/utils/permission'

interface MenuItem {
  path: string
  name?: string
  meta?: {
    title?: string
    icon?: string
    hidden?: boolean
    permissions?: string[]
    roles?: string[]
  }
  children?: MenuItem[]
}

interface Props {
  item: MenuItem
  basePath?: string
}

const props = withDefaults(defineProps<Props>(), {
  basePath: ''
})

// 解析完整路径
const resolvePath = (routePath: string) => {
  if (routePath.startsWith('/')) {
    return routePath
  }
  return `${props.basePath}/${routePath}`.replace(/\/+/g, '/')
}

// 可见的子菜单
const visibleChildren = computed(() => {
  if (!props.item.children) return []
  
  return props.item.children.filter(child => {
    // 检查是否隐藏
    if (child.meta?.hidden) return false
    
    // 检查权限
    if (child.meta?.permissions) {
      return hasPermission(child.meta.permissions)
    }
    
    return true
  })
})

// 是否有子菜单
const hasChildren = computed(() => {
  return visibleChildren.value.length > 0
})
</script>
