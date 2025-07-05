<template>
  <div class="tree-table-container">
    <el-table
      ref="tableRef"
      v-loading="loading"
      :data="data"
      :row-key="rowKey"
      :tree-props="treeProps"
      :default-expand-all="defaultExpandAll"
      :expand-row-keys="expandRowKeys"
      :stripe="stripe"
      :border="border"
      :size="size"
      :height="height"
      :max-height="maxHeight"
      :show-header="showHeader"
      :highlight-current-row="highlightCurrentRow"
      :row-class-name="rowClassName"
      :cell-class-name="cellClassName"
      :header-row-class-name="headerRowClassName"
      :header-cell-class-name="headerCellClassName"
      :empty-text="emptyText"
      :tooltip-effect="tooltipEffect"
      @select="handleSelect"
      @select-all="handleSelectAll"
      @selection-change="handleSelectionChange"
      @cell-mouse-enter="handleCellMouseEnter"
      @cell-mouse-leave="handleCellMouseLeave"
      @cell-click="handleCellClick"
      @cell-dblclick="handleCellDblclick"
      @row-click="handleRowClick"
      @row-contextmenu="handleRowContextmenu"
      @row-dblclick="handleRowDblclick"
      @header-click="handleHeaderClick"
      @header-contextmenu="handleHeaderContextmenu"
      @sort-change="handleSortChange"
      @filter-change="handleFilterChange"
      @current-change="handleCurrentChange"
      @header-dragend="handleHeaderDragend"
      @expand-change="handleExpandChange"
    >
      <!-- 选择列 -->
      <el-table-column
        v-if="showSelection"
        type="selection"
        :width="selectionWidth"
        :fixed="selectionFixed"
        :selectable="selectable"
        :reserve-selection="reserveSelection"
      />

      <!-- 索引列 -->
      <el-table-column
        v-if="showIndex"
        type="index"
        :label="indexLabel"
        :width="indexWidth"
        :fixed="indexFixed"
        :index="indexMethod"
      />

      <!-- 动态列 -->
      <template v-for="column in columns" :key="column.prop || column.type">
        <el-table-column
          :prop="column.prop"
          :label="column.label"
          :width="column.width"
          :min-width="column.minWidth"
          :fixed="column.fixed"
          :render-header="column.renderHeader"
          :sortable="column.sortable"
          :sort-method="column.sortMethod"
          :sort-by="column.sortBy"
          :sort-orders="column.sortOrders"
          :resizable="column.resizable"
          :formatter="column.formatter"
          :show-overflow-tooltip="column.showOverflowTooltip"
          :align="column.align"
          :header-align="column.headerAlign"
          :class-name="column.className"
          :label-class-name="column.labelClassName"
          :filters="column.filters"
          :filter-placement="column.filterPlacement"
          :filter-multiple="column.filterMultiple"
          :filter-method="column.filterMethod"
          :filtered-value="column.filteredValue"
        >
          <template v-if="column.slot" #default="scope">
            <slot :name="column.slot" v-bind="scope" />
          </template>
          <template v-else-if="column.render" #default="scope">
            <component :is="column.render" v-bind="scope" />
          </template>
          <template v-else-if="column.formatter" #default="scope">
            {{ column.formatter(scope.row, scope.column, scope.row[column.prop], scope.$index) }}
          </template>
          <template v-else #default="scope">
            {{ scope.row[column.prop] }}
          </template>

          <!-- 表头插槽 -->
          <template v-if="column.headerSlot" #header="scope">
            <slot :name="column.headerSlot" v-bind="scope" />
          </template>
        </el-table-column>
      </template>

      <!-- 操作列 -->
      <el-table-column
        v-if="showActions"
        :label="actionsLabel"
        :width="actionsWidth"
        :min-width="actionsMinWidth"
        :fixed="actionsFixed"
        :align="actionsAlign"
        class-name="tree-table-actions"
      >
        <template #default="scope">
          <slot name="actions" v-bind="scope">
            <div class="default-actions">
              <el-button
                v-for="action in getRowActions(scope.row)"
                :key="action.key"
                :type="action.type"
                :size="action.size || 'small'"
                :icon="action.icon"
                :disabled="action.disabled"
                :loading="action.loading"
                @click="handleActionClick(action, scope.row, scope.$index)"
              >
                {{ action.label }}
              </el-button>
            </div>
          </slot>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div v-if="showPagination" class="tree-table-pagination">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="pageSizes"
        :layout="paginationLayout"
        :background="paginationBackground"
        :small="paginationSmall"
        :disabled="paginationDisabled"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { TableColumnCtx } from 'element-plus'

export interface TreeTableColumn {
  prop?: string
  label?: string
  width?: string | number
  minWidth?: string | number
  fixed?: boolean | string
  renderHeader?: Function
  sortable?: boolean | string
  sortMethod?: Function
  sortBy?: string | string[] | Function
  sortOrders?: string[]
  resizable?: boolean
  formatter?: Function
  showOverflowTooltip?: boolean
  align?: string
  headerAlign?: string
  className?: string
  labelClassName?: string
  filters?: Array<{ text: string; value: any }>
  filterPlacement?: string
  filterMultiple?: boolean
  filterMethod?: Function
  filteredValue?: any[]
  slot?: string
  headerSlot?: string
  render?: any
}

export interface TreeTableAction {
  key: string
  label: string
  type?: string
  size?: string
  icon?: any
  disabled?: boolean
  loading?: boolean
  permission?: string | string[]
  visible?: boolean | Function
}

interface Props {
  data: any[]
  columns: TreeTableColumn[]
  loading?: boolean
  rowKey?: string
  treeProps?: {
    children?: string
    hasChildren?: string
  }
  defaultExpandAll?: boolean
  expandRowKeys?: any[]
  stripe?: boolean
  border?: boolean
  size?: string
  height?: string | number
  maxHeight?: string | number
  showHeader?: boolean
  highlightCurrentRow?: boolean
  rowClassName?: string | Function
  cellClassName?: string | Function
  headerRowClassName?: string | Function
  headerCellClassName?: string | Function
  emptyText?: string
  tooltipEffect?: string
  // 选择列
  showSelection?: boolean
  selectionWidth?: number
  selectionFixed?: boolean | string
  selectable?: Function
  reserveSelection?: boolean
  // 索引列
  showIndex?: boolean
  indexLabel?: string
  indexWidth?: number
  indexFixed?: boolean | string
  indexMethod?: Function
  // 操作列
  showActions?: boolean
  actionsLabel?: string
  actionsWidth?: number
  actionsMinWidth?: number
  actionsFixed?: boolean | string
  actionsAlign?: string
  actions?: TreeTableAction[]
  // 分页
  showPagination?: boolean
  total?: number
  currentPage?: number
  pageSize?: number
  pageSizes?: number[]
  paginationLayout?: string
  paginationBackground?: boolean
  paginationSmall?: boolean
  paginationDisabled?: boolean
  // 权限
  permissions?: string[]
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  rowKey: 'id',
  treeProps: () => ({ children: 'children', hasChildren: 'hasChildren' }),
  defaultExpandAll: false,
  stripe: true,
  border: true,
  size: 'default',
  showHeader: true,
  highlightCurrentRow: false,
  emptyText: '暂无数据',
  tooltipEffect: 'dark',
  showSelection: false,
  selectionWidth: 55,
  selectionFixed: false,
  reserveSelection: false,
  showIndex: false,
  indexLabel: '#',
  indexWidth: 50,
  indexFixed: false,
  showActions: false,
  actionsLabel: '操作',
  actionsWidth: 200,
  actionsFixed: 'right',
  actionsAlign: 'center',
  actions: () => [],
  showPagination: false,
  total: 0,
  currentPage: 1,
  pageSize: 10,
  pageSizes: () => [10, 20, 50, 100],
  paginationLayout: 'total, sizes, prev, pager, next, jumper',
  paginationBackground: true,
  paginationSmall: false,
  paginationDisabled: false,
  permissions: () => []
})

const emit = defineEmits<{
  select: [selection: any[], row: any]
  selectAll: [selection: any[]]
  selectionChange: [selection: any[]]
  cellMouseEnter: [row: any, column: TableColumnCtx<any>, cell: HTMLElement, event: Event]
  cellMouseLeave: [row: any, column: TableColumnCtx<any>, cell: HTMLElement, event: Event]
  cellClick: [row: any, column: TableColumnCtx<any>, cell: HTMLElement, event: Event]
  cellDblclick: [row: any, column: TableColumnCtx<any>, cell: HTMLElement, event: Event]
  rowClick: [row: any, column: TableColumnCtx<any>, event: Event]
  rowContextmenu: [row: any, column: TableColumnCtx<any>, event: Event]
  rowDblclick: [row: any, column: TableColumnCtx<any>, event: Event]
  headerClick: [column: TableColumnCtx<any>, event: Event]
  headerContextmenu: [column: TableColumnCtx<any>, event: Event]
  sortChange: [data: { column: TableColumnCtx<any>; prop: string; order: string }]
  filterChange: [filters: any]
  currentChange: [currentRow: any, oldCurrentRow: any]
  headerDragend: [newWidth: number, oldWidth: number, column: TableColumnCtx<any>, event: Event]
  expandChange: [row: any, expandedRows: any[]]
  actionClick: [action: TreeTableAction, row: any, index: number]
  sizeChange: [size: number]
  pageChange: [page: number]
}>()

const tableRef = ref()

// 检查权限
const hasPermission = (permission?: string | string[]) => {
  if (!permission) return true
  if (typeof permission === 'string') {
    return props.permissions.includes(permission)
  }
  return permission.some(p => props.permissions.includes(p))
}

// 获取行操作
const getRowActions = (row: any) => {
  return props.actions.filter(action => {
    // 检查权限
    if (!hasPermission(action.permission)) return false
    // 检查可见性
    if (typeof action.visible === 'function') {
      return action.visible(row)
    }
    return action.visible !== false
  })
}

// 事件处理
const handleSelect = (selection: any[], row: any) => emit('select', selection, row)
const handleSelectAll = (selection: any[]) => emit('selectAll', selection)
const handleSelectionChange = (selection: any[]) => emit('selectionChange', selection)
const handleCellMouseEnter = (row: any, column: TableColumnCtx<any>, cell: HTMLElement, event: Event) => 
  emit('cellMouseEnter', row, column, cell, event)
const handleCellMouseLeave = (row: any, column: TableColumnCtx<any>, cell: HTMLElement, event: Event) => 
  emit('cellMouseLeave', row, column, cell, event)
const handleCellClick = (row: any, column: TableColumnCtx<any>, cell: HTMLElement, event: Event) => 
  emit('cellClick', row, column, cell, event)
const handleCellDblclick = (row: any, column: TableColumnCtx<any>, cell: HTMLElement, event: Event) => 
  emit('cellDblclick', row, column, cell, event)
const handleRowClick = (row: any, column: TableColumnCtx<any>, event: Event) => 
  emit('rowClick', row, column, event)
const handleRowContextmenu = (row: any, column: TableColumnCtx<any>, event: Event) => 
  emit('rowContextmenu', row, column, event)
const handleRowDblclick = (row: any, column: TableColumnCtx<any>, event: Event) => 
  emit('rowDblclick', row, column, event)
const handleHeaderClick = (column: TableColumnCtx<any>, event: Event) => 
  emit('headerClick', column, event)
const handleHeaderContextmenu = (column: TableColumnCtx<any>, event: Event) => 
  emit('headerContextmenu', column, event)
const handleSortChange = (data: { column: TableColumnCtx<any>; prop: string; order: string }) => 
  emit('sortChange', data)
const handleFilterChange = (filters: any) => emit('filterChange', filters)
const handleCurrentChange = (currentRow: any, oldCurrentRow: any) => 
  emit('currentChange', currentRow, oldCurrentRow)
const handleHeaderDragend = (newWidth: number, oldWidth: number, column: TableColumnCtx<any>, event: Event) => 
  emit('headerDragend', newWidth, oldWidth, column, event)
const handleExpandChange = (row: any, expandedRows: any[]) => 
  emit('expandChange', row, expandedRows)

const handleActionClick = (action: TreeTableAction, row: any, index: number) => {
  emit('actionClick', action, row, index)
}

const handleSizeChange = (size: number) => emit('sizeChange', size)
const handlePageChange = (page: number) => emit('pageChange', page)

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
.tree-table-container {
  .tree-table-actions {
    .default-actions {
      display: flex;
      gap: 4px;
      justify-content: center;
      flex-wrap: wrap;
    }
  }

  .tree-table-pagination {
    margin-top: 16px;
    text-align: right;
  }
}

// 响应式设计
@media (max-width: 768px) {
  .tree-table-container {
    .tree-table-actions {
      .default-actions {
        flex-direction: column;
        gap: 2px;

        .el-button {
          font-size: 12px;
          padding: 4px 8px;
        }
      }
    }

    .tree-table-pagination {
      text-align: center;

      :deep(.el-pagination) {
        justify-content: center;
      }
    }
  }
}
</style>
