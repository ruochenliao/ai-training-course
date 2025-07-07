<template>
  <el-card class="search-form-container" shadow="never">
    <el-form
      ref="formRef"
      :model="modelValue"
      :inline="inline"
      :label-width="labelWidth"
      class="search-form"
      @submit.prevent="handleSearch"
    >
      <el-row :gutter="gutter">
        <el-col
          v-for="(field, index) in fields"
          :key="field.prop"
          :span="field.span || defaultSpan"
          :xs="field.xs || 24"
          :sm="field.sm || 12"
          :md="field.md || 8"
          :lg="field.lg || 6"
        >
          <el-form-item :label="field.label" :prop="field.prop">
            <!-- 输入框 -->
            <el-input
              v-if="field.type === 'input'"
              v-model="modelValue[field.prop]"
              :placeholder="field.placeholder"
              :clearable="field.clearable !== false"
              :prefix-icon="field.prefixIcon"
              :suffix-icon="field.suffixIcon"
              @keyup.enter="handleSearch"
              @clear="handleFieldChange(field.prop, '')"
            />
            
            <!-- 选择器 -->
            <el-select
              v-else-if="field.type === 'select'"
              v-model="modelValue[field.prop]"
              :placeholder="field.placeholder"
              :clearable="field.clearable !== false"
              :multiple="field.multiple"
              :filterable="field.filterable"
              @change="handleFieldChange(field.prop, $event)"
            >
              <el-option
                v-for="option in field.options"
                :key="option.value"
                :label="option.label"
                :value="option.value"
                :disabled="option.disabled"
              />
            </el-select>
            
            <!-- 日期选择器 -->
            <el-date-picker
              v-else-if="field.type === 'date'"
              v-model="modelValue[field.prop]"
              :type="field.dateType || 'date'"
              :placeholder="field.placeholder"
              :clearable="field.clearable !== false"
              :format="field.format"
              :value-format="field.valueFormat"
              @change="handleFieldChange(field.prop, $event)"
            />
            
            <!-- 日期范围选择器 -->
            <el-date-picker
              v-else-if="field.type === 'daterange'"
              v-model="modelValue[field.prop]"
              type="daterange"
              :range-separator="field.rangeSeparator || '至'"
              :start-placeholder="field.startPlaceholder || '开始日期'"
              :end-placeholder="field.endPlaceholder || '结束日期'"
              :clearable="field.clearable !== false"
              :format="field.format"
              :value-format="field.valueFormat"
              @change="handleFieldChange(field.prop, $event)"
            />
            
            <!-- 数字输入框 -->
            <el-input-number
              v-else-if="field.type === 'number'"
              v-model="modelValue[field.prop]"
              :placeholder="field.placeholder"
              :min="field.min"
              :max="field.max"
              :step="field.step"
              :precision="field.precision"
              @change="handleFieldChange(field.prop, $event)"
            />
          </el-form-item>
        </el-col>
        
        <!-- 操作按钮 -->
        <el-col :span="actionSpan" class="search-actions">
          <el-form-item>
            <el-button
              type="primary"
              :icon="Search"
              :loading="loading"
              @click="handleSearch"
            >
              {{ searchText }}
            </el-button>
            <el-button
              :icon="Refresh"
              @click="handleReset"
            >
              {{ resetText }}
            </el-button>
            <el-button
              v-if="showAdvanced && hasAdvancedFields"
              type="link"
              :icon="isAdvancedVisible ? ArrowUp : ArrowDown"
              @click="toggleAdvanced"
            >
              {{ isAdvancedVisible ? '收起' : '展开' }}
            </el-button>
          </el-form-item>
        </el-col>
      </el-row>
      
      <!-- 高级搜索区域 -->
      <el-collapse-transition>
        <div v-show="isAdvancedVisible && hasAdvancedFields">
          <el-divider content-position="left">高级搜索</el-divider>
          <el-row :gutter="gutter">
            <el-col
              v-for="field in advancedFields"
              :key="field.prop"
              :span="field.span || defaultSpan"
              :xs="field.xs || 24"
              :sm="field.sm || 12"
              :md="field.md || 8"
              :lg="field.lg || 6"
            >
              <el-form-item :label="field.label" :prop="field.prop">
                <!-- 这里可以复用上面的字段类型组件 -->
                <component
                  :is="getFieldComponent(field.type)"
                  v-model="modelValue[field.prop]"
                  v-bind="getFieldProps(field)"
                  @change="handleFieldChange(field.prop, $event)"
                />
              </el-form-item>
            </el-col>
          </el-row>
        </div>
      </el-collapse-transition>
    </el-form>
  </el-card>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Search, Refresh, ArrowUp, ArrowDown } from '@element-plus/icons-vue'
import type { FormInstance } from 'element-plus'

export interface SearchField {
  prop: string
  label: string
  type: 'input' | 'select' | 'date' | 'daterange' | 'number'
  placeholder?: string
  clearable?: boolean
  span?: number
  xs?: number
  sm?: number
  md?: number
  lg?: number
  // 输入框特有属性
  prefixIcon?: any
  suffixIcon?: any
  // 选择器特有属性
  options?: Array<{ label: string; value: any; disabled?: boolean }>
  multiple?: boolean
  filterable?: boolean
  // 日期选择器特有属性
  dateType?: string
  format?: string
  valueFormat?: string
  rangeSeparator?: string
  startPlaceholder?: string
  endPlaceholder?: string
  // 数字输入框特有属性
  min?: number
  max?: number
  step?: number
  precision?: number
  // 高级搜索
  advanced?: boolean
}

interface Props {
  modelValue: Record<string, any>
  fields: SearchField[]
  inline?: boolean
  labelWidth?: string | number
  gutter?: number
  defaultSpan?: number
  actionSpan?: number
  loading?: boolean
  searchText?: string
  resetText?: string
  showAdvanced?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  inline: true,
  labelWidth: 'auto',
  gutter: 16,
  defaultSpan: 6,
  actionSpan: 6,
  loading: false,
  searchText: '搜索',
  resetText: '重置',
  showAdvanced: true
})

const emit = defineEmits<{
  'update:modelValue': [value: Record<string, any>]
  search: [value: Record<string, any>]
  reset: []
  fieldChange: [prop: string, value: any]
}>()

const formRef = ref<FormInstance>()
const isAdvancedVisible = ref(false)

// 计算基础字段和高级字段
const basicFields = computed(() => props.fields.filter(field => !field.advanced))
const advancedFields = computed(() => props.fields.filter(field => field.advanced))
const hasAdvancedFields = computed(() => advancedFields.value.length > 0)

// 搜索处理
const handleSearch = () => {
  emit('search', props.modelValue)
}

// 重置处理
const handleReset = () => {
  formRef.value?.resetFields()
  const resetData: Record<string, any> = {}
  props.fields.forEach(field => {
    resetData[field.prop] = field.type === 'daterange' ? [] : ''
  })
  emit('update:modelValue', resetData)
  emit('reset')
}

// 字段变化处理
const handleFieldChange = (prop: string, value: any) => {
  emit('update:modelValue', { ...props.modelValue, [prop]: value })
  emit('fieldChange', prop, value)
}

// 切换高级搜索
const toggleAdvanced = () => {
  isAdvancedVisible.value = !isAdvancedVisible.value
}

// 获取字段组件
const getFieldComponent = (type: string) => {
  const componentMap = {
    input: 'el-input',
    select: 'el-select',
    date: 'el-date-picker',
    daterange: 'el-date-picker',
    number: 'el-input-number'
  }
  return componentMap[type as keyof typeof componentMap] || 'el-input'
}

// 获取字段属性
const getFieldProps = (field: SearchField) => {
  const baseProps = {
    placeholder: field.placeholder,
    clearable: field.clearable !== false
  }
  
  if (field.type === 'select') {
    return {
      ...baseProps,
      multiple: field.multiple,
      filterable: field.filterable
    }
  }
  
  if (field.type === 'date' || field.type === 'daterange') {
    return {
      ...baseProps,
      type: field.type === 'daterange' ? 'daterange' : field.dateType || 'date',
      format: field.format,
      valueFormat: field.valueFormat
    }
  }
  
  if (field.type === 'number') {
    return {
      ...baseProps,
      min: field.min,
      max: field.max,
      step: field.step,
      precision: field.precision
    }
  }
  
  return baseProps
}
</script>

<style lang="scss" scoped>
.search-form-container {
  margin-bottom: 16px;
  
  :deep(.el-card__body) {
    padding: 16px;
  }
}

.search-form {
  .search-actions {
    display: flex;
    align-items: center;
    
    .el-form-item {
      margin-bottom: 0;
    }
  }
}

@media (max-width: 768px) {
  .search-actions {
    margin-top: 16px;
  }
}
</style>
