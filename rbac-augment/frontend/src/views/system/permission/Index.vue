<template>
  <div class="permission-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <h2 class="page-title">权限管理</h2>
      <p class="page-description">管理系统中的所有权限，包括权限的创建、编辑、删除和分组管理。</p>
    </div>

    <!-- 工具栏 -->
    <div class="table-toolbar">
      <div class="toolbar-left">
        <el-button
          v-permission="['permission:create']"
          type="primary"
          @click="handleAdd"
        >
          <el-icon><Plus /></el-icon>
          新增权限
        </el-button>
        <el-button
          type="success"
          @click="handleRefreshTree"
        >
          <el-icon><Refresh /></el-icon>
          刷新权限树
        </el-button>
      </div>
      <div class="toolbar-right">
        <el-radio-group v-model="viewMode" @change="handleViewModeChange">
          <el-radio-button label="tree">树形视图</el-radio-button>
          <el-radio-button label="table">表格视图</el-radio-button>
          <el-radio-button label="group">分组视图</el-radio-button>
        </el-radio-group>
      </div>
    </div>

    <!-- 权限树视图 -->
    <div v-if="viewMode === 'tree'" class="permission-tree">
      <el-card>
        <template #header>
          <span>权限树结构</span>
        </template>
        <el-tree
          v-loading="loading"
          :data="permissionTree"
          :props="treeProps"
          node-key="id"
          default-expand-all
          :expand-on-click-node="false"
        >
          <template #default="{ node, data }">
            <div class="tree-node">
              <span class="node-label">{{ data.name }}</span>
              <span class="node-code">{{ data.code }}</span>
              <div class="node-actions">
                <el-button
                  v-permission="['permission:read']"
                  type="primary"
                  size="small"
                  @click="handleView(data)"
                >
                  查看
                </el-button>
                <el-button
                  v-permission="['permission:update']"
                  type="warning"
                  size="small"
                  @click="handleEdit(data)"
                >
                  编辑
                </el-button>
                <el-button
                  v-permission="['permission:delete']"
                  type="danger"
                  size="small"
                  @click="handleDelete(data)"
                >
                  删除
                </el-button>
              </div>
            </div>
          </template>
        </el-tree>
      </el-card>
    </div>

    <!-- 权限分组视图 -->
    <div v-else-if="viewMode === 'group'" class="permission-groups">
      <el-row :gutter="16">
        <el-col
          v-for="group in permissionGroups"
          :key="group.resource"
          :span="8"
        >
          <el-card class="group-card">
            <template #header>
              <div class="group-header">
                <span class="group-title">{{ group.resource }}</span>
                <el-tag size="small">{{ group.permissions.length }} 个权限</el-tag>
              </div>
            </template>
            <div class="permission-list">
              <div
                v-for="permission in group.permissions"
                :key="permission.id"
                class="permission-item"
              >
                <div class="permission-info">
                  <div class="permission-name">{{ permission.name }}</div>
                  <div class="permission-action">{{ permission.action }}</div>
                </div>
                <div class="permission-actions">
                  <el-button
                    v-permission="['permission:update']"
                    type="text"
                    size="small"
                    @click="handleEdit(permission)"
                  >
                    编辑
                  </el-button>
                  <el-button
                    v-permission="['permission:delete']"
                    type="text"
                    size="small"
                    @click="handleDelete(permission)"
                  >
                    删除
                  </el-button>
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 权限表格视图 -->
    <div v-else class="permission-table">
      <el-card>
        <el-table
          v-loading="loading"
          :data="permissionList"
          stripe
          border
        >
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="name" label="权限名称" min-width="150" />
          <el-table-column prop="code" label="权限代码" min-width="150" />
          <el-table-column prop="resource" label="资源" width="120" />
          <el-table-column prop="action" label="操作" width="100" />
          <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
          <el-table-column prop="sort_order" label="排序" width="80" />
          <el-table-column prop="created_at" label="创建时间" width="160">
            <template #default="{ row }">
              {{ formatDateTime(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="180" fixed="right">
            <template #default="{ row }">
              <div class="action-buttons">
                <el-button
                  v-permission="['permission:read']"
                  type="primary"
                  size="small"
                  @click="handleView(row)"
                >
                  查看
                </el-button>
                <el-button
                  v-permission="['permission:update']"
                  type="warning"
                  size="small"
                  @click="handleEdit(row)"
                >
                  编辑
                </el-button>
                <el-button
                  v-permission="['permission:delete']"
                  type="danger"
                  size="small"
                  @click="handleDelete(row)"
                >
                  删除
                </el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  getPermissionList, 
  getPermissionTree, 
  getPermissionGroups,
  deletePermission 
} from '@/api/permission'
import { formatDateTime } from '@/utils'
import type { PermissionListItem, PermissionTreeNode, PermissionGroup } from '@/types'

// 视图模式
const viewMode = ref<'tree' | 'table' | 'group'>('tree')

// 加载状态
const loading = ref(false)

// 数据
const permissionList = ref<PermissionListItem[]>([])
const permissionTree = ref<PermissionTreeNode[]>([])
const permissionGroups = ref<PermissionGroup[]>([])

// 树形组件配置
const treeProps = {
  children: 'children',
  label: 'name'
}

/**
 * 获取权限列表
 */
const fetchPermissionList = async () => {
  try {
    loading.value = true
    const response = await getPermissionList({ page: 1, page_size: 1000 })
    permissionList.value = response.data.items
  } catch (error) {
    console.error('Failed to fetch permission list:', error)
    ElMessage.error('获取权限列表失败')
  } finally {
    loading.value = false
  }
}

/**
 * 获取权限树
 */
const fetchPermissionTree = async () => {
  try {
    loading.value = true
    const response = await getPermissionTree()
    permissionTree.value = response.data
  } catch (error) {
    console.error('Failed to fetch permission tree:', error)
    ElMessage.error('获取权限树失败')
  } finally {
    loading.value = false
  }
}

/**
 * 获取权限分组
 */
const fetchPermissionGroups = async () => {
  try {
    loading.value = true
    const response = await getPermissionGroups()
    permissionGroups.value = response.data
  } catch (error) {
    console.error('Failed to fetch permission groups:', error)
    ElMessage.error('获取权限分组失败')
  } finally {
    loading.value = false
  }
}

/**
 * 处理视图模式变化
 */
const handleViewModeChange = (mode: string) => {
  switch (mode) {
    case 'tree':
      fetchPermissionTree()
      break
    case 'table':
      fetchPermissionList()
      break
    case 'group':
      fetchPermissionGroups()
      break
  }
}

/**
 * 处理新增
 */
const handleAdd = () => {
  ElMessage.info('权限新增功能开发中...')
}

/**
 * 处理查看
 */
const handleView = (row: any) => {
  ElMessage.info('权限详情功能开发中...')
}

/**
 * 处理编辑
 */
const handleEdit = (row: any) => {
  ElMessage.info('权限编辑功能开发中...')
}

/**
 * 处理删除
 */
const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除权限 "${row.name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await deletePermission(row.id)
    ElMessage.success('删除成功')
    
    // 刷新当前视图
    handleViewModeChange(viewMode.value)
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to delete permission:', error)
      ElMessage.error('删除失败')
    }
  }
}

/**
 * 处理刷新权限树
 */
const handleRefreshTree = () => {
  handleViewModeChange(viewMode.value)
}

onMounted(() => {
  fetchPermissionTree()
})
</script>

<style lang="scss" scoped>
.permission-page {
  .page-header {
    margin-bottom: 24px;

    .page-title {
      font-size: 24px;
      font-weight: 600;
      color: #303133;
      margin-bottom: 8px;
    }

    .page-description {
      color: #606266;
      font-size: 14px;
    }
  }

  .table-toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    padding: 16px 20px;
    background-color: #fff;
    border-radius: 8px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);

    .toolbar-left {
      display: flex;
      gap: 8px;
    }
  }

  .permission-tree {
    .tree-node {
      display: flex;
      align-items: center;
      justify-content: space-between;
      width: 100%;
      padding-right: 16px;

      .node-label {
        font-weight: 500;
      }

      .node-code {
        color: #909399;
        font-size: 12px;
        margin-left: 8px;
      }

      .node-actions {
        display: flex;
        gap: 4px;
      }
    }
  }

  .permission-groups {
    .group-card {
      margin-bottom: 16px;

      .group-header {
        display: flex;
        justify-content: space-between;
        align-items: center;

        .group-title {
          font-weight: 600;
          color: #303133;
        }
      }

      .permission-list {
        .permission-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 8px 0;
          border-bottom: 1px solid #f0f0f0;

          &:last-child {
            border-bottom: none;
          }

          .permission-info {
            .permission-name {
              font-weight: 500;
              color: #303133;
            }

            .permission-action {
              font-size: 12px;
              color: #909399;
            }
          }

          .permission-actions {
            display: flex;
            gap: 4px;
          }
        }
      }
    }
  }

  .permission-table {
    .action-buttons {
      display: flex;
      gap: 4px;
    }
  }
}

// 暗色主题
.dark {
  .permission-page {
    .page-header {
      .page-title {
        color: #e5eaf3;
      }

      .page-description {
        color: #a3a6ad;
      }
    }

    .table-toolbar {
      background-color: #2b2b2b;
      color: #e5eaf3;
    }

    .group-card {
      .group-title {
        color: #e5eaf3;
      }

      .permission-item {
        border-bottom-color: #4c4d4f;

        .permission-name {
          color: #e5eaf3;
        }
      }
    }
  }
}
</style>
