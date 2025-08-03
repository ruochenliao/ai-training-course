<template>
  <div class="key-value-editor">
    <div 
      v-for="(item, index) in items" 
      :key="index"
      class="kv-item"
    >
      <el-input 
        v-model="item.key" 
        placeholder="键"
        size="small"
        @input="updateItems"
      />
      <el-input 
        v-model="item.value" 
        placeholder="值"
        size="small"
        @input="updateItems"
      />
      <el-button 
        size="small" 
        type="danger" 
        text
        @click="removeItem(index)"
      >
        <el-icon><Delete /></el-icon>
      </el-button>
    </div>
    
    <el-button 
      size="small" 
      type="primary" 
      text
      @click="addItem"
    >
      <el-icon><Plus /></el-icon>
      添加
    </el-button>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { Delete, Plus } from '@element-plus/icons-vue'

// Props
interface Props {
  modelValue: Record<string, any>
}

const props = defineProps<Props>()
const emit = defineEmits(['update:modelValue', 'change'])

// 响应式数据
const items = ref<Array<{ key: string; value: string }>>([])

// 方法
const initItems = () => {
  if (props.modelValue && typeof props.modelValue === 'object') {
    items.value = Object.entries(props.modelValue).map(([key, value]) => ({
      key,
      value: String(value)
    }))
  } else {
    items.value = []
  }
  
  // 确保至少有一个空项
  if (items.value.length === 0) {
    items.value.push({ key: '', value: '' })
  }
}

const updateItems = () => {
  const result: Record<string, any> = {}
  
  items.value.forEach(item => {
    if (item.key.trim()) {
      result[item.key.trim()] = item.value
    }
  })
  
  emit('update:modelValue', result)
  emit('change', result)
  
  // 如果最后一项不为空，添加新的空项
  const lastItem = items.value[items.value.length - 1]
  if (lastItem && (lastItem.key.trim() || lastItem.value.trim())) {
    items.value.push({ key: '', value: '' })
  }
}

const addItem = () => {
  items.value.push({ key: '', value: '' })
}

const removeItem = (index: number) => {
  if (items.value.length > 1) {
    items.value.splice(index, 1)
    updateItems()
  }
}

// 监听props变化
watch(() => props.modelValue, initItems, { immediate: true, deep: true })

// 生命周期
onMounted(() => {
  initItems()
})
</script>

<style scoped>
.key-value-editor {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.kv-item {
  display: flex;
  gap: 8px;
  align-items: center;
}

.kv-item .el-input {
  flex: 1;
}

.kv-item .el-input:first-child {
  max-width: 120px;
}
</style>
