<template>
  <el-dialog
    v-model="dialogVisible"
    title="菜单详情"
    width="600px"
    :close-on-click-modal="false"
    destroy-on-close
  >
    <div v-loading="loading" class="menu-detail">
      <el-descriptions
        v-if="menuData"
        :column="2"
        border
        class="detail-descriptions"
      >
        <el-descriptions-item label="菜单ID">
          <el-tag type="info" size="small">{{ menuData.id }}</el-tag>
        </el-descriptions-item>
        
        <el-descriptions-item label="菜单名称">
          <span class="detail-value">{{ menuData.title }}</span>
        </el-descriptions-item>
        
        <el-descriptions-item label="菜单类型">
          <el-tag :type="getTypeTagType(menuData.type)" size="small">
            {{ menuData.type }}
          </el-tag>
        </el-descriptions-item>
        
        <el-descriptions-item label="路由路径">
          <el-tag type="primary" size="small">{{ menuData.path }}</el-tag>
        </el-descriptions-item>
        
        <el-descriptions-item label="组件路径">
          <span v-if="menuData.component" class="detail-value">{{ menuData.component }}</span>
          <el-text v-else type="info">无</el-text>
        </el-descriptions-item>
        
        <el-descriptions-item label="菜单图标">
          <div v-if="menuData.icon" class="icon-display">
            <el-icon class="menu-icon">
              <component :is="menuData.icon" />
            </el-icon>
            <span>{{ menuData.icon }}</span>
          </div>
          <el-text v-else type="info">无</el-text>
        </el-descriptions-item>
        
        <el-descriptions-item label="权限标识">
          <span v-if="menuData.permission" class="detail-value">{{ menuData.permission }}</span>
          <el-text v-else type="info">无</el-text>
        </el-descriptions-item>
        
        <el-descriptions-item label="排序">
          <span class="detail-value">{{ menuData.sort_order || 0 }}</span>
        </el-descriptions-item>
        
        <el-descriptions-item label="状态">
          <el-tag :type="menuData.is_active ? 'success' : 'danger'" size="small">
            {{ menuData.is_active ? '启用' : '禁用' }}
          </el-tag>
        </el-descriptions-item>
        
        <el-descriptions-item label="显示状态">
          <el-tag :type="menuData.is_hidden ? 'danger' : 'success'" size="small">
            {{ menuData.is_hidden ? '隐藏' : '显示' }}
          </el-tag>
        </el-descriptions-item>
        
        <el-descriptions-item label="缓存状态">
          <el-tag :type="menuData.keep_alive ? 'success' : 'info'" size="small">
            {{ menuData.keep_alive ? '缓存' : '不缓存' }}
          </el-tag>
        </el-descriptions-item>
        
        <el-descriptions-item label="父级菜单">
          <span v-if="menuData.parent_title" class="detail-value">
            {{ menuData.parent_title }}
          </span>
          <el-text v-else type="info">无</el-text>
        </el-descriptions-item>
        
        <el-descriptions-item label="创建时间">
          <span class="detail-value">{{ formatDateTime(menuData.created_at) }}</span>
        </el-descriptions-item>
        
        <el-descriptions-item label="更新时间">
          <span class="detail-value">{{ formatDateTime(menuData.updated_at) }}</span>
        </el-descriptions-item>
        
        <el-descriptions-item label="菜单描述" :span="2">
          <span v-if="menuData.description" class="detail-value">
            {{ menuData.description }}
          </span>
          <el-text v-else type="info">暂无描述</el-text>
        </el-descriptions-item>
      </el-descriptions>

      <!-- 子菜单列表 -->
      <div v-if="childrenMenus.length > 0" class="children-section">
        <el-divider content-position="left">
          <el-icon><Menu /></el-icon>
          子菜单列表
        </el-divider>
        
        <el-table
          :data="childrenMenus"
          size="small"
          class="children-table"
        >
          <el-table-column prop="title" label="菜单名称" min-width="120">
            <template #default="{ row }">
              <div class="menu-title">
                <el-icon v-if="row.icon" class="menu-icon">
                  <component :is="row.icon" />
                </el-icon>
                <span>{{ row.title }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="type" label="类型" width="80">
            <template #default="{ row }">
              <el-tag :type="getTypeTagType(row.type)" size="small">
                {{ row.type }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="path" label="路由路径" min-width="120" />
          <el-table-column prop="is_active" label="状态" width="80" align="center">
            <template #default="{ row }">
              <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
                {{ row.is_active ? '启用' : '禁用' }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <template #footer>
      <el-button @click="handleClose">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Menu } from '@element-plus/icons-vue'
import { getMenuDetail, getMenuChildren } from '@/api/menu'
import { formatDateTime } from '@/utils'
import type { Menu as MenuType } from '@/types'

interface Props {
  visible: boolean
  menuId?: number
}

interface Emits {
  (e: 'update:visible', visible: boolean): void
}

const props = withDefaults(defineProps<Props>(), {
  visible: false
})

const emit = defineEmits<Emits>()

// 数据状态
const loading = ref(false)
const menuData = ref<MenuType | null>(null)
const childrenMenus = ref<MenuType[]>([])

// 对话框显示状态
const dialogVisible = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value)
})

/**
 * 获取类型标签类型
 */
const getTypeTagType = (type: string) => {
  switch (type) {
    case '目录':
      return 'primary'
    case '菜单':
      return 'success'
    case '按钮':
      return 'warning'
    default:
      return 'info'
  }
}

/**
 * 获取菜单详情
 */
const fetchMenuDetail = async () => {
  if (!props.menuId) return

  try {
    loading.value = true
    
    // 获取菜单详情
    const detailResponse = await getMenuDetail(props.menuId)
    menuData.value = detailResponse.data

    // 获取子菜单
    try {
      const childrenResponse = await getMenuChildren(props.menuId)
      childrenMenus.value = childrenResponse.data || []
    } catch (error) {
      // 如果没有子菜单或接口不存在，忽略错误
      childrenMenus.value = []
    }
  } catch (error) {
    console.error('Failed to fetch menu detail:', error)
    ElMessage.error('获取菜单详情失败')
  } finally {
    loading.value = false
  }
}

/**
 * 处理关闭
 */
const handleClose = () => {
  emit('update:visible', false)
}

// 监听菜单ID变化
watch(
  () => props.menuId,
  (newId) => {
    if (newId && props.visible) {
      fetchMenuDetail()
    }
  },
  { immediate: true }
)

// 监听对话框显示状态
watch(
  () => props.visible,
  (visible) => {
    if (visible && props.menuId) {
      fetchMenuDetail()
    } else if (!visible) {
      // 清空数据
      menuData.value = null
      childrenMenus.value = []
    }
  }
)
</script>

<style lang="scss" scoped>
.menu-detail {
  .detail-descriptions {
    margin-bottom: 20px;

    .detail-value {
      font-weight: 500;
      color: var(--el-text-color-primary);
    }

    .icon-display {
      display: flex;
      align-items: center;
      gap: 8px;

      .menu-icon {
        font-size: 16px;
        color: var(--el-color-primary);
      }
    }
  }

  .children-section {
    margin-top: 20px;

    .children-table {
      margin-top: 16px;

      .menu-title {
        display: flex;
        align-items: center;
        gap: 8px;

        .menu-icon {
          font-size: 16px;
          color: var(--el-color-primary);
        }
      }
    }
  }
}

:deep(.el-descriptions__label) {
  font-weight: 600;
  color: var(--el-text-color-regular);
}

:deep(.el-descriptions__content) {
  color: var(--el-text-color-primary);
}
</style>
