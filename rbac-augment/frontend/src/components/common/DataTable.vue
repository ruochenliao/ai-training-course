<template>
  <div class="data-table-container">
    <!-- 表格工具栏 -->
    <div v-if="showToolbar" class="table-toolbar">
      <!-- 左侧操作区 -->
      <div class="toolbar-left">
        <slot name="toolbar-left">
          <el-button
            v-if="showRefresh"
            type="default"
            :icon="Refresh"
            @click="handleRefresh"
            :loading="loading"
          >
            刷新
          </el-button>
          <el-button
            v-if="showBatchDelete && selectedRows.length > 0"
            type="danger"
            :icon="Delete"
            @click="handleBatchDelete"
          >
            批量删除 ({{ selectedRows.length }})
          </el-button>
        </slot>
      </div>

      <!-- 右侧工具区 -->
      <div class="toolbar-right">
        <slot name="toolbar-right">
          <!-- 密度切换 -->
          <el-tooltip content="密度" placement="top">
            <el-dropdown @command="handleDensityChange">
              <el-button type="text" :icon="Operation" />
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="default" :class="{ active: density === 'default' }">
                    默认
                  </el-dropdown-item>
                  <el-dropdown-item command="medium" :class="{ active: density === 'medium' }">
                    中等
                  </el-dropdown-item>
                  <el-dropdown-item command="small" :class="{ active: density === 'small' }">
                    紧凑
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </el-tooltip>

          <!-- 列设置 -->
          <el-tooltip content="列设置" placement="top">
            <el-button type="text" :icon="Setting" @click="showColumnSetting = true" />
          </el-tooltip>

          <!-- 全屏 -->
          <el-tooltip content="全屏" placement="top">
            <el-button type="text" :icon="FullScreen" @click="toggleFullscreen" />
          </el-tooltip>
        </slot>
      </div>
    </div>

    <!-- 数据表格 -->
    <div class="table-wrapper" :class="{ 'is-fullscreen': isFullscreen }">
      <el-table
        ref="tableRef"
        v-loading="loading"
        :data="tableData"
        :size="density"
        :height="tableHeight"
        :max-height="maxHeight"
        :stripe="stripe"
        :border="border"
        :show-header="showHeader"
        :highlight-current-row="highlightCurrentRow"
        :row-key="rowKey"
        :tree-props="treeProps"
        :default-expand-all="defaultExpandAll"
        :expand-row-keys="expandRowKeys"
        :selection-change="handleSelectionChange"
        :sort-change="handleSortChange"
        :filter-change="handleFilterChange"
        :current-change="handleCurrentChange"
        :row-click="handleRowClick"
        :row-dblclick="handleRowDblclick"
        :header-cell-style="headerCellStyle"
        :cell-style="cellStyle"
        :row-style="rowStyle"
        :span-method="spanMethod"
        class="enterprise-table"
        @selection-change="handleSelectionChange"
      >
        <!-- 多选列 -->
        <el-table-column
          v-if="showSelection"
          type="selection"
          width="50"
          align="center"
          fixed="left"
        />

        <!-- 序号列 -->
        <el-table-column
          v-if="showIndex"
          type="index"
          label="序号"
          width="60"
          align="center"
          fixed="left"
          :index="getIndex"
        />

        <!-- 动态列 -->
        <template v-for="column in visibleColumns" :key="column.prop">
          <el-table-column
            :prop="column.prop"
            :label="column.label"
            :width="column.width"
            :min-width="column.minWidth"
            :fixed="column.fixed"
            :align="column.align || 'left'"
            :sortable="column.sortable"
            :sort-method="column.sortMethod"
            :sort-by="column.sortBy"
            :sort-orders="column.sortOrders"
            :resizable="column.resizable !== false"
            :show-overflow-tooltip="column.showOverflowTooltip !== false"
            :class-name="column.className"
            :label-class-name="column.labelClassName"
            :filters="column.filters"
            :filter-method="column.filterMethod"
            :filter-multiple="column.filterMultiple"
            :filter-placement="column.filterPlacement"
          >
            <template #default="scope">
              <slot
                v-if="column.slot"
                :name="column.slot"
                :row="scope.row"
                :column="scope.column"
                :$index="scope.$index"
              />
              <span v-else>{{ getColumnValue(scope.row, column) }}</span>
            </template>
            <template v-if="column.headerSlot" #header="scope">
              <slot
                :name="column.headerSlot"
                :column="scope.column"
                :$index="scope.$index"
              />
            </template>
          </el-table-column>
        </template>

        <!-- 操作列 -->
        <el-table-column
          v-if="$slots.actions"
          label="操作"
          :width="actionWidth"
          :min-width="actionMinWidth"
          fixed="right"
          align="center"
          class-name="table-actions"
        >
          <template #default="scope">
            <slot
              name="actions"
              :row="scope.row"
              :column="scope.column"
              :$index="scope.$index"
            />
          </template>
        </el-table-column>

        <!-- 空数据 -->
        <template #empty>
          <slot name="empty">
            <div class="table-empty">
              <el-empty :description="emptyText" />
            </div>
          </slot>
        </template>
      </el-table>
    </div>

    <!-- 分页器 -->
    <div v-if="showPagination && pagination" class="table-pagination">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :page-sizes="pageSizes"
        :layout="paginationLayout"
        :background="true"
        :small="false"
        @size-change="handleSizeChange"
        @current-change="handleCurrentPageChange"
      />
    </div>

    <!-- 列设置对话框 -->
    <el-dialog
      v-model="showColumnSetting"
      title="列设置"
      width="400px"
      :close-on-click-modal="false"
    >
      <div class="column-setting">
        <el-checkbox
          v-model="checkAll"
          :indeterminate="isIndeterminate"
          @change="handleCheckAllChange"
        >
          全选
        </el-checkbox>
        <el-divider />
        <el-checkbox-group v-model="checkedColumns" @change="handleCheckedColumnsChange">
          <draggable
            v-model="columnSettings"
            item-key="prop"
            handle=".drag-handle"
            @end="handleColumnSort"
          >
            <template #item="{ element }">
              <div class="column-item">
                <el-icon class="drag-handle"><Rank /></el-icon>
                <el-checkbox :label="element.prop">{{ element.label }}</el-checkbox>
              </div>
            </template>
          </draggable>
        </el-checkbox-group>
      </div>
      <template #footer>
        <el-button @click="resetColumns">重置</el-button>
        <el-button type="primary" @click="showColumnSetting = false">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Refresh,
  Delete,
  Operation,
  Setting,
  FullScreen,
  Rank
} from '@element-plus/icons-vue'
// import draggable from 'vuedraggable' // 暂时移除拖拽功能

// 类型定义
interface TableColumn {
  prop: string
  label: string
  width?: number | string
  minWidth?: number | string
  fixed?: boolean | 'left' | 'right'
  align?: 'left' | 'center' | 'right'
  sortable?: boolean | 'custom'
  sortMethod?: Function
  sortBy?: string | string[] | Function
  sortOrders?: string[]
  resizable?: boolean
  showOverflowTooltip?: boolean
  className?: string
  labelClassName?: string
  filters?: Array<{ text: string; value: any }>
  filterMethod?: Function
  filterMultiple?: boolean
  filterPlacement?: string
  slot?: string
  headerSlot?: string
  visible?: boolean
}

interface Pagination {
  page: number
  pageSize: number
  total: number
}

interface Props {
  data: any[]
  columns: TableColumn[]
  loading?: boolean
  pagination?: Pagination
  showToolbar?: boolean
  showRefresh?: boolean
  showBatchDelete?: boolean
  showSelection?: boolean
  showIndex?: boolean
  showPagination?: boolean
  stripe?: boolean
  border?: boolean
  showHeader?: boolean
  highlightCurrentRow?: boolean
  rowKey?: string
  treeProps?: object
  defaultExpandAll?: boolean
  expandRowKeys?: any[]
  tableHeight?: number | string
  maxHeight?: number | string
  density?: 'default' | 'medium' | 'small'
  actionWidth?: number | string
  actionMinWidth?: number | string
  emptyText?: string
  pageSizes?: number[]
  paginationLayout?: string
  headerCellStyle?: object | Function
  cellStyle?: object | Function
  rowStyle?: object | Function
  spanMethod?: Function
}

const props = withDefaults(defineProps<Props>(), {
  data: () => [],
  columns: () => [],
  loading: false,
  showToolbar: true,
  showRefresh: true,
  showBatchDelete: false,
  showSelection: false,
  showIndex: false,
  showPagination: true,
  stripe: true,
  border: true,
  showHeader: true,
  highlightCurrentRow: false,
  defaultExpandAll: false,
  density: 'default',
  actionWidth: 150,
  actionMinWidth: 100,
  emptyText: '暂无数据',
  pageSizes: () => [10, 20, 50, 100],
  paginationLayout: 'total, sizes, prev, pager, next, jumper'
})

const emit = defineEmits([
  'refresh',
  'batch-delete',
  'selection-change',
  'sort-change',
  'filter-change',
  'current-change',
  'row-click',
  'row-dblclick',
  'size-change',
  'current-page-change'
])

// 响应式数据
const tableRef = ref()
const selectedRows = ref<any[]>([])
const isFullscreen = ref(false)
const showColumnSetting = ref(false)
const columnSettings = ref<TableColumn[]>([])
const checkedColumns = ref<string[]>([])

// 初始化列设置
const initColumnSettings = () => {
  columnSettings.value = props.columns.map(col => ({ ...col, visible: col.visible !== false }))
  checkedColumns.value = columnSettings.value.filter(col => col.visible).map(col => col.prop)
}

// 监听列变化
watch(() => props.columns, initColumnSettings, { immediate: true })

// 计算属性
const tableData = computed(() => props.data)

const visibleColumns = computed(() => {
  return columnSettings.value.filter(col => checkedColumns.value.includes(col.prop))
})

const checkAll = computed({
  get: () => checkedColumns.value.length === columnSettings.value.length,
  set: (val: boolean) => {
    checkedColumns.value = val ? columnSettings.value.map(col => col.prop) : []
  }
})

const isIndeterminate = computed(() => {
  const checkedCount = checkedColumns.value.length
  return checkedCount > 0 && checkedCount < columnSettings.value.length
})

// 方法定义
const handleRefresh = () => {
  emit('refresh')
}

const handleBatchDelete = async () => {
  try {
    await ElMessageBox.confirm('确定要删除选中的数据吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    emit('batch-delete', selectedRows.value)
  } catch {
    // 用户取消
  }
}

const handleSelectionChange = (selection: any[]) => {
  selectedRows.value = selection
  emit('selection-change', selection)
}

const handleDensityChange = (density: string) => {
  // 这里可以通过 emit 传递给父组件或者直接修改本地状态
}

const toggleFullscreen = () => {
  isFullscreen.value = !isFullscreen.value
}

const getIndex = (index: number) => {
  if (props.pagination) {
    return (props.pagination.page - 1) * props.pagination.pageSize + index + 1
  }
  return index + 1
}

const getColumnValue = (row: any, column: TableColumn) => {
  const keys = column.prop.split('.')
  let value = row
  for (const key of keys) {
    value = value?.[key]
  }
  return value
}

const handleSortChange = (sort: any) => {
  emit('sort-change', sort)
}

const handleFilterChange = (filters: any) => {
  emit('filter-change', filters)
}

const handleCurrentChange = (currentRow: any) => {
  emit('current-change', currentRow)
}

const handleRowClick = (row: any, column: any, event: Event) => {
  emit('row-click', row, column, event)
}

const handleRowDblclick = (row: any, column: any, event: Event) => {
  emit('row-dblclick', row, column, event)
}

const handleSizeChange = (size: number) => {
  emit('size-change', size)
}

const handleCurrentPageChange = (page: number) => {
  emit('current-page-change', page)
}

const handleCheckAllChange = (val: boolean) => {
  checkedColumns.value = val ? columnSettings.value.map(col => col.prop) : []
}

const handleCheckedColumnsChange = (value: string[]) => {
  checkedColumns.value = value
}

const handleColumnSort = () => {
  // 列排序后的处理
}

const resetColumns = () => {
  initColumnSettings()
}

// 暴露方法
defineExpose({
  tableRef,
  clearSelection: () => tableRef.value?.clearSelection(),
  toggleRowSelection: (row: any, selected?: boolean) => tableRef.value?.toggleRowSelection(row, selected),
  toggleAllSelection: () => tableRef.value?.toggleAllSelection(),
  toggleRowExpansion: (row: any, expanded?: boolean) => tableRef.value?.toggleRowExpansion(row, expanded),
  setCurrentRow: (row: any) => tableRef.value?.setCurrentRow(row),
  clearSort: () => tableRef.value?.clearSort(),
  clearFilter: (columnKeys?: string[]) => tableRef.value?.clearFilter(columnKeys),
  doLayout: () => tableRef.value?.doLayout(),
  sort: (prop: string, order: string) => tableRef.value?.sort(prop, order)
})
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.data-table-container {
  background: $card-color;
  border-radius: $border-radius-lg;
  box-shadow: $box-shadow-sm;
  overflow: hidden;
}

.table-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: $spacing-md $spacing-lg;
  border-bottom: 1px solid $border-color-light;
  background: $bg-color-page;

  .toolbar-left,
  .toolbar-right {
    display: flex;
    align-items: center;
    gap: $spacing-sm;
  }
}

.table-wrapper {
  &.is-fullscreen {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: $z-index-modal;
    background: $card-color;
  }
}

:deep(.enterprise-table) {
  .el-table__header {
    th {
      background: $bg-color-page;
      color: $text-color-1;
      font-weight: $font-weight-medium;
    }
  }

  .table-actions {
    .el-button + .el-button {
      margin-left: $spacing-xs;
    }
  }
}

.table-pagination {
  display: flex;
  justify-content: flex-end;
  padding: $spacing-md $spacing-lg;
  border-top: 1px solid $border-color-light;
  background: $bg-color-page;
}

.table-empty {
  padding: $spacing-xl 0;
}

.column-setting {
  .column-item {
    display: flex;
    align-items: center;
    gap: $spacing-sm;
    padding: $spacing-xs 0;

    .drag-handle {
      cursor: move;
      color: $text-color-3;
    }
  }
}

// 暗色主题
.dark {
  .data-table-container {
    background: $dark-card-color;
  }

  .table-toolbar,
  .table-pagination {
    background: $dark-bg-color-page;
    border-color: $dark-border-color;
  }

  :deep(.enterprise-table) {
    .el-table__header th {
      background: $dark-bg-color-page;
      color: $dark-text-color-1;
    }
  }
}
</style>
