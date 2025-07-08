<script setup>
import { h, ref, resolveDirective, withDirectives, onMounted } from 'vue'
import {
  NButton,
  NForm,
  NFormItem,
  NInput,
  NInputNumber,
  NSelect,
  NSwitch,
  NTag,
  useMessage,
} from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CrudTable from '@/components/table/CrudTable.vue'

import { formatDate, renderIcon } from '@/utils'
import { useCRUD } from '@/composables'
import api from '@/api'
import TheIcon from '@/components/icon/TheIcon.vue'

defineOptions({ name: '模型管理' })

const $table = ref(null)
const queryItems = ref({})
const vPermission = resolveDirective('permission')
const message = useMessage()

const {
  modalVisible,
  modalTitle,
  modalAction,
  modalLoading,
  handleSave,
  modalForm,
  modalFormRef,
  handleEdit,
  handleDelete,
  handleAdd,
} = useCRUD({
  name: '模型',
  initForm: {
    category: '对话模型',
    model_type: 'chat',
    model_price: 0,
    is_active: true,
  },
  doCreate: api.createModel,
  doUpdate: api.updateModel,
  doDelete: api.deleteModel,
  refresh: () => $table.value?.handleSearch(),
})

// 模型分类选项
const categoryOptions = [
  { label: '对话模型', value: '对话模型' },
  { label: '嵌入模型', value: '嵌入模型' },
  { label: '图像模型', value: '图像模型' },
  { label: '语音模型', value: '语音模型' },
  { label: '本地模型', value: '本地模型' },
]

// 模型类型选项
const typeOptions = [
  { label: 'chat', value: 'chat' },
  { label: 'embedding', value: 'embedding' },
  { label: 'image', value: 'image' },
  { label: 'audio', value: 'audio' },
]

onMounted(() => {
  $table.value?.handleSearch()
})

// 处理启用/禁用状态切换
async function handleUpdateStatus(row) {
  if (row.publishing) return
  row.publishing = true
  try {
    const updateData = {
      id: row.id,
      is_active: !row.is_active,
    }
    await api.updateModel(updateData)
    row.is_active = !row.is_active
    message.success(`${row.is_active ? '启用' : '禁用'}成功`)
    $table.value?.handleSearch()
  } catch (error) {
    message.error(`操作失败: ${error.message}`)
  } finally {
    row.publishing = false
  }
}

// 表格列配置
const columns = [
  {
    title: 'ID',
    key: 'id',
    width: 60,
    align: 'center',
  },
  {
    title: '模型分类',
    key: 'category',
    width: 100,
    align: 'center',
    render(row) {
      const tagType = {
        '对话模型': 'info',
        '嵌入模型': 'success',
        '图像模型': 'warning',
        '语音模型': 'error',
        '本地模型': 'default',
      }
      return h(NTag, { type: tagType[row.category] || 'default' }, { default: () => row.category })
    },
  },
  {
    title: '模型名称',
    key: 'model_name',
    width: 150,
    ellipsis: { tooltip: true },
  },
  {
    title: '显示名称',
    key: 'model_show',
    width: 120,
    ellipsis: { tooltip: true },
  },
  {
    title: '模型描述',
    key: 'model_describe',
    width: 200,
    ellipsis: { tooltip: true },
  },
  {
    title: '模型类型',
    key: 'model_type',
    width: 80,
    align: 'center',
  },
  {
    title: '价格',
    key: 'model_price',
    width: 80,
    align: 'center',
    render(row) {
      return `¥${row.model_price || 0}`
    },
  },
  {
    title: '状态',
    key: 'is_active',
    width: 80,
    align: 'center',
    render(row) {
      return h(NSwitch, {
        size: 'small',
        rubberBand: false,
        value: row.is_active,
        loading: !!row.publishing,
        onUpdateValue: () => handleUpdateStatus(row),
      })
    },
  },
  {
    title: '创建时间',
    key: 'created_at',
    width: 180,
    render(row) {
      return formatDate(row.created_at)
    },
  },
  {
    title: '操作',
    key: 'actions',
    width: 120,
    align: 'center',
    fixed: 'right',
    render(row) {
      return [
        withDirectives(
          h(
            NButton,
            {
              size: 'small',
              type: 'primary',
              style: 'margin-right: 8px;',
              onClick: () => handleEdit(row),
            },
            {
              default: () => '编辑',
              icon: renderIcon('material-symbols:edit', { size: 16 }),
            }
          ),
          [[vPermission, 'post/api/v1/system/model/update']]
        ),
        withDirectives(
          h(
            NButton,
            {
              size: 'small',
              type: 'error',
              onClick: () => handleDelete(row.id),
            },
            {
              default: () => '删除',
              icon: renderIcon('material-symbols:delete-outline', { size: 16 }),
            }
          ),
          [[vPermission, 'delete/api/v1/system/model/delete']]
        ),
      ]
    },
  },
]

// 表单验证规则
const rules = {
  category: [{ required: true, message: '请选择模型分类', trigger: 'change' }],
  model_name: [{ required: true, message: '请输入模型名称', trigger: 'blur' }],
  model_show: [{ required: true, message: '请输入显示名称', trigger: 'blur' }],
  model_type: [{ required: true, message: '请选择模型类型', trigger: 'change' }],
}
</script>

<template>
  <CommonPage show-footer title="模型列表">
    <template #action>
      <NButton v-permission="'post/api/v1/system/model/create'" type="primary" @click="handleAdd">
        <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />新建模型
      </NButton>
    </template>

    <!-- 表格 -->
    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      :columns="columns"
      :get-data="api.getModelList"
    >
      <template #queryBar>
        <QueryBarItem label="分类" :label-width="40">
          <NSelect
            v-model:value="queryItems.category"
            clearable
            placeholder="请选择模型分类"
            :options="categoryOptions"
            @update:value="$table?.handleSearch()"
          />
        </QueryBarItem>
        <QueryBarItem label="名称" :label-width="40">
          <NInput
            v-model:value="queryItems.model_name"
            clearable
            type="text"
            placeholder="请输入模型名称"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
        <QueryBarItem label="类型" :label-width="40">
          <NSelect
            v-model:value="queryItems.model_type"
            clearable
            placeholder="请选择模型类型"
            :options="typeOptions"
            @update:value="$table?.handleSearch()"
          />
        </QueryBarItem>
      </template>
    </CrudTable>

    <!-- 新增/编辑弹窗 -->
    <CrudModal
      v-model:visible="modalVisible"
      :title="modalTitle"
      :loading="modalLoading"
      @save="handleSave"
    >
      <NForm
        ref="modalFormRef"
        :model="modalForm"
        :rules="rules"
        label-placement="left"
        label-width="100px"
        require-mark-placement="right-hanging"
      >
        <NFormItem label="模型分类" path="category">
          <NSelect
            v-model:value="modalForm.category"
            placeholder="请选择模型分类"
            :options="categoryOptions"
          />
        </NFormItem>
        <NFormItem label="模型名称" path="model_name">
          <NInput v-model:value="modalForm.model_name" placeholder="请输入模型名称" />
        </NFormItem>
        <NFormItem label="显示名称" path="model_show">
          <NInput v-model:value="modalForm.model_show" placeholder="请输入显示名称" />
        </NFormItem>
        <NFormItem label="模型类型" path="model_type">
          <NSelect
            v-model:value="modalForm.model_type"
            placeholder="请选择模型类型"
            :options="typeOptions"
          />
        </NFormItem>
        <NFormItem label="模型描述" path="model_describe">
          <NInput
            v-model:value="modalForm.model_describe"
            type="textarea"
            placeholder="请输入模型描述"
            :rows="3"
          />
        </NFormItem>
        <NFormItem label="模型价格" path="model_price">
          <NInputNumber
            v-model:value="modalForm.model_price"
            placeholder="请输入模型价格"
            :min="0"
            :step="0.001"
            :precision="4"
          />
        </NFormItem>
        <NFormItem label="API主机" path="api_host">
          <NInput v-model:value="modalForm.api_host" placeholder="请输入API主机地址" />
        </NFormItem>
        <NFormItem label="API密钥" path="api_key">
          <NInput
            v-model:value="modalForm.api_key"
            type="password"
            placeholder="请输入API密钥"
            show-password-on="click"
          />
        </NFormItem>
        <NFormItem label="系统提示词" path="system_prompt">
          <NInput
            v-model:value="modalForm.system_prompt"
            type="textarea"
            placeholder="请输入系统提示词"
            :rows="4"
          />
        </NFormItem>
        <NFormItem label="是否启用" path="is_active">
          <NSwitch v-model:value="modalForm.is_active" />
        </NFormItem>
        <NFormItem label="备注" path="remark">
          <NInput
            v-model:value="modalForm.remark"
            type="textarea"
            placeholder="请输入备注"
            :rows="2"
          />
        </NFormItem>
      </NForm>
    </CrudModal>
  </CommonPage>
</template>
