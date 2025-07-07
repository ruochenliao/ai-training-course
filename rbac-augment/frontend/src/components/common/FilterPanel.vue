<template>
  <div class="filter-panel" :class="{ collapsed: isCollapsed }">
    <!-- 面板头部 -->
    <div class="panel-header" @click="toggleCollapse">
      <div class="header-left">
        <el-icon class="header-icon">
          <Filter />
        </el-icon>
        <span class="header-title">{{ title }}</span>
        <el-badge v-if="activeFilterCount > 0" :value="activeFilterCount" class="filter-badge" />
      </div>
      <div class="header-right">
        <el-button
          v-if="showClearAll && activeFilterCount > 0"
          type="link"
          size="small"
          @click.stop="handleClearAll"
        >
          清空筛选
        </el-button>
        <el-icon class="collapse-icon" :class="{ rotated: !isCollapsed }">
          <ArrowDown />
        </el-icon>
      </div>
    </div>

    <!-- 面板内容 -->
    <el-collapse-transition>
      <div v-show="!isCollapsed" class="panel-content">
        <!-- 快速筛选标签 -->
        <div v-if="quickFilters.length > 0" class="quick-filters">
          <div class="filter-group">
            <span class="group-label">快速筛选：</span>
            <div class="filter-tags">
              <el-tag
                v-for="filter in quickFilters"
                :key="filter.key"
                :type="isQuickFilterActive(filter) ? 'primary' : 'info'"
                :effect="isQuickFilterActive(filter) ? 'dark' : 'plain'"
                class="filter-tag"
                @click="handleQuickFilter(filter)"
              >
                {{ filter.label }}
              </el-tag>
            </div>
          </div>
        </div>

        <!-- 高级筛选表单 -->
        <div v-if="advancedFilters.length > 0" class="advanced-filters">
          <el-form :model="filterValues" label-position="top" size="small">
            <el-row :gutter="16">
              <el-col
                v-for="filter in advancedFilters"
                :key="filter.prop"
                :span="filter.span || 8"
                :xs="filter.xs || 24"
                :sm="filter.sm || 12"
                :md="filter.md || 8"
                :lg="filter.lg || 6"
              >
                <el-form-item :label="filter.label">
                  <!-- 输入框 -->
                  <el-input
                    v-if="filter.type === 'input'"
                    v-model="filterValues[filter.prop]"
                    :placeholder="filter.placeholder"
                    :prefix-icon="filter.prefixIcon"
                    clearable
                    @change="handleFilterChange"
                  />

                  <!-- 选择器 -->
                  <el-select
                    v-else-if="filter.type === 'select'"
                    v-model="filterValues[filter.prop]"
                    :placeholder="filter.placeholder"
                    :multiple="filter.multiple"
                    :collapse-tags="filter.collapseTags"
                    clearable
                    style="width: 100%"
                    @change="handleFilterChange"
                  >
                    <el-option
                      v-for="option in filter.options"
                      :key="option.value"
                      :label="option.label"
                      :value="option.value"
                    />
                  </el-select>

                  <!-- 日期选择器 -->
                  <el-date-picker
                    v-else-if="filter.type === 'date'"
                    v-model="filterValues[filter.prop]"
                    :type="filter.dateType || 'date'"
                    :placeholder="filter.placeholder"
                    :format="filter.format"
                    :value-format="filter.valueFormat"
                    clearable
                    style="width: 100%"
                    @change="handleFilterChange"
                  />

                  <!-- 日期范围选择器 -->
                  <el-date-picker
                    v-else-if="filter.type === 'daterange'"
                    v-model="filterValues[filter.prop]"
                    type="daterange"
                    :start-placeholder="filter.startPlaceholder || '开始日期'"
                    :end-placeholder="filter.endPlaceholder || '结束日期'"
                    :format="filter.format"
                    :value-format="filter.valueFormat"
                    clearable
                    style="width: 100%"
                    @change="handleFilterChange"
                  />

                  <!-- 数字输入框 -->
                  <el-input-number
                    v-else-if="filter.type === 'number'"
                    v-model="filterValues[filter.prop]"
                    :min="filter.min"
                    :max="filter.max"
                    :step="filter.step"
                    :placeholder="filter.placeholder"
                    style="width: 100%"
                    @change="handleFilterChange"
                  />

                  <!-- 数字范围 -->
                  <div v-else-if="filter.type === 'numberRange'" class="number-range">
                    <el-input-number
                      v-model="filterValues[filter.prop + '_min']"
                      :min="filter.min"
                      :max="filter.max"
                      :step="filter.step"
                      :placeholder="filter.minPlaceholder || '最小值'"
                      style="width: 48%"
                      @change="handleFilterChange"
                    />
                    <span class="range-separator">-</span>
                    <el-input-number
                      v-model="filterValues[filter.prop + '_max']"
                      :min="filter.min"
                      :max="filter.max"
                      :step="filter.step"
                      :placeholder="filter.maxPlaceholder || '最大值'"
                      style="width: 48%"
                      @change="handleFilterChange"
                    />
                  </div>

                  <!-- 开关 -->
                  <el-switch
                    v-else-if="filter.type === 'switch'"
                    v-model="filterValues[filter.prop]"
                    :active-text="filter.activeText"
                    :inactive-text="filter.inactiveText"
                    @change="handleFilterChange"
                  />

                  <!-- 级联选择器 -->
                  <el-cascader
                    v-else-if="filter.type === 'cascader'"
                    v-model="filterValues[filter.prop]"
                    :options="filter.options"
                    :props="filter.props"
                    :placeholder="filter.placeholder"
                    clearable
                    style="width: 100%"
                    @change="handleFilterChange"
                  />

                  <!-- 树形选择器 -->
                  <el-tree-select
                    v-else-if="filter.type === 'tree'"
                    v-model="filterValues[filter.prop]"
                    :data="filter.data"
                    :props="filter.props"
                    :placeholder="filter.placeholder"
                    :multiple="filter.multiple"
                    clearable
                    style="width: 100%"
                    @change="handleFilterChange"
                  />
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
        </div>

        <!-- 自定义筛选内容 -->
        <div v-if="$slots.custom" class="custom-filters">
          <slot name="custom" :values="filterValues" :onChange="handleFilterChange" />
        </div>

        <!-- 操作按钮 -->
        <div v-if="showActions" class="filter-actions">
          <el-button type="primary" :icon="Search" @click="handleApply">
            应用筛选
          </el-button>
          <el-button :icon="Refresh" @click="handleReset">
            重置
          </el-button>
          <el-button v-if="showSave" :icon="Collection" @click="handleSave">
            保存方案
          </el-button>
        </div>

        <!-- 已应用的筛选条件 -->
        <div v-if="showAppliedFilters && appliedFilters.length > 0" class="applied-filters">
          <div class="applied-header">
            <span class="applied-label">已应用筛选：</span>
            <el-button type="link" size="small" @click="handleClearAll">
              清空全部
            </el-button>
          </div>
          <div class="applied-tags">
            <el-tag
              v-for="(filter, index) in appliedFilters"
              :key="index"
              type="success"
              closable
              @close="handleRemoveFilter(filter)"
            >
              {{ filter.label }}: {{ filter.value }}
            </el-tag>
          </div>
        </div>
      </div>
    </el-collapse-transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { Filter, ArrowDown, Search, Refresh, Collection } from '@element-plus/icons-vue'

export interface QuickFilter {
  key: string
  label: string
  value: any
  condition?: Record<string, any>
}

export interface AdvancedFilter {
  prop: string
  label: string
  type: 'input' | 'select' | 'date' | 'daterange' | 'number' | 'numberRange' | 'switch' | 'cascader' | 'tree'
  placeholder?: string
  span?: number
  xs?: number
  sm?: number
  md?: number
  lg?: number
  // 输入框相关
  prefixIcon?: any
  // 选择器相关
  options?: Array<{ label: string; value: any }>
  multiple?: boolean
  collapseTags?: boolean
  // 日期相关
  dateType?: string
  format?: string
  valueFormat?: string
  startPlaceholder?: string
  endPlaceholder?: string
  // 数字相关
  min?: number
  max?: number
  step?: number
  minPlaceholder?: string
  maxPlaceholder?: string
  // 开关相关
  activeText?: string
  inactiveText?: string
  // 级联/树形相关
  props?: any
  data?: any[]
}

export interface AppliedFilter {
  prop: string
  label: string
  value: string
  originalValue: any
}

interface Props {
  title?: string
  collapsed?: boolean
  quickFilters?: QuickFilter[]
  advancedFilters?: AdvancedFilter[]
  modelValue?: Record<string, any>
  showActions?: boolean
  showSave?: boolean
  showClearAll?: boolean
  showAppliedFilters?: boolean
  autoApply?: boolean
  debounceTime?: number
}

const props = withDefaults(defineProps<Props>(), {
  title: '筛选面板',
  collapsed: false,
  quickFilters: () => [],
  advancedFilters: () => [],
  modelValue: () => ({}),
  showActions: true,
  showSave: false,
  showClearAll: true,
  showAppliedFilters: true,
  autoApply: false,
  debounceTime: 300
})

const emit = defineEmits<{
  'update:modelValue': [value: Record<string, any>]
  'update:collapsed': [collapsed: boolean]
  apply: [filters: Record<string, any>]
  reset: []
  save: [filters: Record<string, any>]
  quickFilter: [filter: QuickFilter]
}>()

const isCollapsed = ref(props.collapsed)
const filterValues = ref<Record<string, any>>({ ...props.modelValue })
const debounceTimer = ref<NodeJS.Timeout>()

// 计算活跃筛选条件数量
const activeFilterCount = computed(() => {
  return Object.values(filterValues.value).filter(value => {
    if (Array.isArray(value)) return value.length > 0
    return value !== null && value !== undefined && value !== ''
  }).length
})

// 计算已应用的筛选条件
const appliedFilters = computed((): AppliedFilter[] => {
  const filters: AppliedFilter[] = []
  
  for (const [prop, value] of Object.entries(filterValues.value)) {
    if (value === null || value === undefined || value === '') continue
    
    const filter = props.advancedFilters.find(f => f.prop === prop)
    if (!filter) continue
    
    let displayValue = String(value)
    
    // 处理不同类型的显示值
    if (filter.type === 'select' && filter.options) {
      if (Array.isArray(value)) {
        displayValue = value.map(v => {
          const option = filter.options!.find(opt => opt.value === v)
          return option?.label || v
        }).join(', ')
      } else {
        const option = filter.options.find(opt => opt.value === value)
        displayValue = option?.label || value
      }
    } else if (filter.type === 'daterange' && Array.isArray(value)) {
      displayValue = `${value[0]} ~ ${value[1]}`
    } else if (filter.type === 'switch') {
      displayValue = value ? (filter.activeText || '是') : (filter.inactiveText || '否')
    }
    
    filters.push({
      prop,
      label: filter.label,
      value: displayValue,
      originalValue: value
    })
  }
  
  return filters
})

// 监听外部值变化
watch(() => props.modelValue, (newValue) => {
  filterValues.value = { ...newValue }
}, { deep: true })

// 监听折叠状态变化
watch(() => props.collapsed, (newValue) => {
  isCollapsed.value = newValue
})

watch(isCollapsed, (newValue) => {
  emit('update:collapsed', newValue)
})

// 切换折叠状态
const toggleCollapse = () => {
  isCollapsed.value = !isCollapsed.value
}

// 检查快速筛选是否激活
const isQuickFilterActive = (filter: QuickFilter) => {
  if (filter.condition) {
    return Object.entries(filter.condition).every(([key, value]) => {
      return filterValues.value[key] === value
    })
  }
  return false
}

// 处理快速筛选
const handleQuickFilter = (filter: QuickFilter) => {
  if (filter.condition) {
    if (isQuickFilterActive(filter)) {
      // 取消筛选
      Object.keys(filter.condition).forEach(key => {
        filterValues.value[key] = null
      })
    } else {
      // 应用筛选
      Object.assign(filterValues.value, filter.condition)
    }
  }
  
  emit('quickFilter', filter)
  handleFilterChange()
}

// 处理筛选条件变化
const handleFilterChange = () => {
  emit('update:modelValue', { ...filterValues.value })
  
  if (props.autoApply) {
    if (debounceTimer.value) {
      clearTimeout(debounceTimer.value)
    }
    debounceTimer.value = setTimeout(() => {
      emit('apply', { ...filterValues.value })
    }, props.debounceTime)
  }
}

// 应用筛选
const handleApply = () => {
  emit('apply', { ...filterValues.value })
}

// 重置筛选
const handleReset = () => {
  filterValues.value = {}
  emit('update:modelValue', {})
  emit('reset')
}

// 清空所有筛选
const handleClearAll = () => {
  handleReset()
}

// 保存筛选方案
const handleSave = () => {
  emit('save', { ...filterValues.value })
}

// 移除单个筛选条件
const handleRemoveFilter = (filter: AppliedFilter) => {
  filterValues.value[filter.prop] = null
  handleFilterChange()
}

onMounted(() => {
  if (props.autoApply) {
    emit('apply', { ...filterValues.value })
  }
})
</script>

<style lang="scss" scoped>
.filter-panel {
  border: 1px solid var(--el-border-color);
  border-radius: 6px;
  background-color: var(--el-bg-color);
  transition: all 0.3s ease;

  &.collapsed {
    .panel-header {
      border-bottom: none;
    }
  }

  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    border-bottom: 1px solid var(--el-border-color-lighter);
    cursor: pointer;
    user-select: none;
    transition: all 0.2s ease;

    &:hover {
      background-color: var(--el-bg-color-page);
    }

    .header-left {
      display: flex;
      align-items: center;
      gap: 8px;

      .header-icon {
        font-size: 16px;
        color: var(--el-color-primary);
      }

      .header-title {
        font-weight: 500;
        color: var(--el-text-color-primary);
      }

      .filter-badge {
        :deep(.el-badge__content) {
          font-size: 10px;
          height: 16px;
          line-height: 16px;
          padding: 0 4px;
        }
      }
    }

    .header-right {
      display: flex;
      align-items: center;
      gap: 8px;

      .collapse-icon {
        font-size: 14px;
        color: var(--el-text-color-regular);
        transition: transform 0.3s ease;

        &.rotated {
          transform: rotate(180deg);
        }
      }
    }
  }

  .panel-content {
    padding: 16px;

    .quick-filters {
      margin-bottom: 16px;

      .filter-group {
        display: flex;
        align-items: center;
        gap: 12px;
        flex-wrap: wrap;

        .group-label {
          font-size: 14px;
          color: var(--el-text-color-regular);
          white-space: nowrap;
        }

        .filter-tags {
          display: flex;
          gap: 8px;
          flex-wrap: wrap;

          .filter-tag {
            cursor: pointer;
            transition: all 0.2s ease;

            &:hover {
              transform: translateY(-1px);
            }
          }
        }
      }
    }

    .advanced-filters {
      margin-bottom: 16px;

      .number-range {
        display: flex;
        align-items: center;
        gap: 8px;

        .range-separator {
          color: var(--el-text-color-regular);
          font-size: 14px;
        }
      }
    }

    .custom-filters {
      margin-bottom: 16px;
    }

    .filter-actions {
      display: flex;
      gap: 8px;
      padding-top: 16px;
      border-top: 1px solid var(--el-border-color-lighter);
    }

    .applied-filters {
      margin-top: 16px;
      padding-top: 16px;
      border-top: 1px solid var(--el-border-color-lighter);

      .applied-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;

        .applied-label {
          font-size: 14px;
          color: var(--el-text-color-regular);
        }
      }

      .applied-tags {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
      }
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .filter-panel {
    .panel-content {
      .quick-filters {
        .filter-group {
          flex-direction: column;
          align-items: flex-start;
          gap: 8px;
        }
      }

      .filter-actions {
        flex-direction: column;

        .el-button {
          width: 100%;
        }
      }

      .applied-filters {
        .applied-header {
          flex-direction: column;
          align-items: flex-start;
          gap: 8px;
        }
      }
    }
  }
}

// 暗色主题适配
.dark {
  .filter-panel {
    background-color: var(--el-bg-color-page);
    border-color: var(--el-border-color);

    .panel-header {
      border-bottom-color: var(--el-border-color);

      &:hover {
        background-color: var(--el-bg-color-overlay);
      }
    }

    .panel-content {
      .filter-actions,
      .applied-filters {
        border-top-color: var(--el-border-color);
      }
    }
  }
}
</style>
