<script setup>
import {h, onMounted, ref, resolveDirective, withDirectives} from 'vue'
import {NButton, NForm, NFormItem, NInput, NInputNumber, NSelect, NSwitch, NTag, useMessage, useDialog} from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CrudTable from '@/components/table/CrudTable.vue'

import {formatDate, renderIcon} from '@/utils'
import {useCRUD} from '@/composables'
import api from '@/api'
import TheIcon from '@/components/icon/TheIcon.vue'

defineOptions({ name: '模型管理' })

const $table = ref(null)
const queryItems = ref({})
const vPermission = resolveDirective('permission')
const message = useMessage()
const dialog = useDialog()

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
    provider_name: 'openai',
    provider_display_name: 'OpenAI',
    base_url: 'https://api.openai.com/v1',
    category: 'chat',
    model_name: '',
    display_name: '',
    description: '',
    vision: false,
    function_calling: false,
    json_output: false,
    structured_output: false,
    multiple_system_messages: false,
    model_family: 'unknown',
    max_tokens: 4096,
    temperature: 0.7,
    top_p: 0.9,
    input_price_per_1k: 0,
    output_price_per_1k: 0,
    is_active: true,
    is_default: false,
    sort_order: 0,
  },
  doCreate: api.createModel,
  doUpdate: api.updateModel,
  doDelete: api.deleteModel,
  refresh: () => $table.value?.handleSearch(),
})

// 模型分类选项
const categoryOptions = [
  { label: '对话模型', value: 'chat' },
  { label: '嵌入模型', value: 'embedding' },
  { label: '图像模型', value: 'image' },
  { label: '语音模型', value: 'audio' },
  { label: '多模态模型', value: 'multimodal' },
  { label: '代码模型', value: 'code' },
]

// 提供商选项
const providerOptions = [
  { label: 'OpenAI', value: 'openai' },
  { label: 'Anthropic', value: 'anthropic' },
  { label: 'Google', value: 'google' },
  { label: 'DeepSeek', value: 'deepseek' },
  { label: 'Qwen', value: 'qwen' },
  { label: '智谱AI', value: 'zhipu' },
  { label: '百度', value: 'baidu' },
  { label: '腾讯', value: 'tencent' },
  { label: '其他', value: 'other' },
]

// 模型系列选项
const modelFamilyOptions = [
  { label: 'GPT', value: 'gpt' },
  { label: 'Claude', value: 'claude' },
  { label: 'Gemini', value: 'gemini' },
  { label: 'DeepSeek', value: 'deepseek' },
  { label: 'Qwen', value: 'qwen' },
  { label: 'GLM', value: 'glm' },
  { label: 'ERNIE', value: 'ernie' },
  { label: '其他', value: 'unknown' },
]

onMounted(() => {
  $table.value?.handleSearch()
})

// 处理启用/禁用状态切换
async function handleToggleStatus(row) {
  if (row.publishing) return
  row.publishing = true
  try {
    await api.toggleModelStatus(row.id)
    row.is_active = !row.is_active
    message.success(`${row.is_active ? '启用' : '禁用'}成功`)
    $table.value?.handleSearch()
  } catch (error) {
    message.error(`操作失败: ${error.message}`)
  } finally {
    row.publishing = false
  }
}

// 设置默认模型
async function handleSetDefault(row) {
  if (row.is_default) {
    message.info('该模型已经是默认模型')
    return
  }

  dialog.warning({
    title: '确认设置',
    content: `确定将 "${row.display_name}" 设置为默认模型吗？这将取消当前分类下其他模型的默认状态。`,
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await api.setDefaultModel(row.id, row.category)
        message.success('设置默认模型成功')
        $table.value?.handleSearch()
      } catch (error) {
        message.error(`设置失败: ${error.message}`)
      }
    }
  })
}

// 处理提供商变更
function handleProviderChange(value) {
  const providerDefaults = {
    openai: {
      provider_display_name: 'OpenAI',
      base_url: 'https://api.openai.com/v1'
    },
    anthropic: {
      provider_display_name: 'Anthropic',
      base_url: 'https://api.anthropic.com'
    },
    google: {
      provider_display_name: 'Google',
      base_url: 'https://generativelanguage.googleapis.com/v1beta'
    },
    deepseek: {
      provider_display_name: 'DeepSeek',
      base_url: 'https://api.deepseek.com/v1'
    },
    qwen: {
      provider_display_name: 'Qwen',
      base_url: 'https://dashscope.aliyuncs.com/compatible-mode/v1'
    },
    zhipu: {
      provider_display_name: '智谱AI',
      base_url: 'https://open.bigmodel.cn/api/paas/v4'
    },
    baidu: {
      provider_display_name: '百度',
      base_url: 'https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop'
    },
    tencent: {
      provider_display_name: '腾讯',
      base_url: 'https://hunyuan.tencentcloudapi.com'
    }
  }

  if (providerDefaults[value]) {
    Object.assign(modalForm.value, providerDefaults[value])
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
    title: '提供商',
    key: 'provider_display_name',
    width: 100,
    align: 'center',
    render(row) {
      const tagType = {
        'OpenAI': 'info',
        'Anthropic': 'success',
        'Google': 'warning',
        'DeepSeek': 'error',
        'Qwen': 'primary',
      }
      return h(NTag, { type: tagType[row.provider_display_name] || 'default' }, { default: () => row.provider_display_name })
    },
  },
  {
    title: '模型分类',
    key: 'category',
    width: 100,
    align: 'center',
    render(row) {
      const tagType = {
        'chat': 'info',
        'embedding': 'success',
        'image': 'warning',
        'audio': 'error',
        'multimodal': 'primary',
        'code': 'default',
      }
      const categoryLabels = {
        'chat': '对话',
        'embedding': '嵌入',
        'image': '图像',
        'audio': '语音',
        'multimodal': '多模态',
        'code': '代码',
      }
      return h(NTag, { type: tagType[row.category] || 'default' }, {
        default: () => categoryLabels[row.category] || row.category
      })
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
    key: 'display_name',
    width: 120,
    ellipsis: { tooltip: true },
  },
  {
    title: '模型描述',
    key: 'description',
    width: 200,
    ellipsis: { tooltip: true },
  },
  {
    title: '模型系列',
    key: 'model_family',
    width: 80,
    align: 'center',
  },
  {
    title: '输入价格',
    key: 'input_price_per_1k',
    width: 90,
    align: 'center',
    render(row) {
      return `¥${row.input_price_per_1k || 0}/1K`
    },
  },
  {
    title: '输出价格',
    key: 'output_price_per_1k',
    width: 90,
    align: 'center',
    render(row) {
      return `¥${row.output_price_per_1k || 0}/1K`
    },
  },
  {
    title: '默认',
    key: 'is_default',
    width: 60,
    align: 'center',
    render(row) {
      return row.is_default ? h(NTag, { type: 'success', size: 'small' }, { default: () => '默认' }) : null
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
        onUpdateValue: () => handleToggleStatus(row),
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
    width: 180,
    align: 'center',
    fixed: 'right',
    render(row) {
      return [
        withDirectives(
          h(
            NButton,
            {
              size: 'small',
              type: 'info',
              style: 'margin-right: 4px;',
              onClick: () => handleSetDefault(row),
              disabled: row.is_default,
            },
            {
              default: () => '设为默认',
              icon: renderIcon('material-symbols:star', { size: 14 }),
            }
          ),
          [[vPermission, 'post/api/v1/system/llm/models/set-default']]
        ),
        withDirectives(
          h(
            NButton,
            {
              size: 'small',
              type: 'primary',
              style: 'margin-right: 4px;',
              onClick: () => handleEdit(row),
            },
            {
              default: () => '编辑',
              icon: renderIcon('material-symbols:edit', { size: 14 }),
            }
          ),
          [[vPermission, 'put/api/v1/system/llm/models']]
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
              icon: renderIcon('material-symbols:delete-outline', { size: 14 }),
            }
          ),
          [[vPermission, 'delete/api/v1/system/llm/models']]
        ),
      ]
    },
  },
]

// 表单验证规则
const rules = {
  provider_name: [{ required: true, message: '请选择提供商', trigger: 'change' }],
  provider_display_name: [{ required: true, message: '请输入提供商显示名称', trigger: 'blur' }],
  base_url: [{ required: true, message: '请输入API基础URL', trigger: 'blur' }],
  category: [{ required: true, message: '请选择模型分类', trigger: 'change' }],
  model_name: [{ required: true, message: '请输入模型名称', trigger: 'blur' }],
  display_name: [{ required: true, message: '请输入显示名称', trigger: 'blur' }],
  model_family: [{ required: true, message: '请选择模型系列', trigger: 'change' }],
  max_tokens: [{ required: true, message: '请输入最大令牌数', trigger: 'blur', type: 'number' }],
  temperature: [{ required: true, message: '请输入温度值', trigger: 'blur', type: 'number' }],
  top_p: [{ required: true, message: '请输入top_p值', trigger: 'blur', type: 'number' }],
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
        <QueryBarItem label="提供商" :label-width="50">
          <NSelect
            v-model:value="queryItems.provider_name"
            clearable
            placeholder="请选择提供商"
            :options="providerOptions"
            @update:value="$table?.handleSearch()"
          />
        </QueryBarItem>
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
        <QueryBarItem label="状态" :label-width="40">
          <NSelect
            v-model:value="queryItems.is_active"
            clearable
            placeholder="请选择状态"
            :options="[
              { label: '启用', value: true },
              { label: '禁用', value: false }
            ]"
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
        label-width="120px"
        require-mark-placement="right-hanging"
      >
        <!-- 提供商信息 -->
        <NFormItem label="提供商" path="provider_name">
          <NSelect
            v-model:value="modalForm.provider_name"
            placeholder="请选择提供商"
            :options="providerOptions"
            @update:value="handleProviderChange"
          />
        </NFormItem>
        <NFormItem label="提供商显示名称" path="provider_display_name">
          <NInput v-model:value="modalForm.provider_display_name" placeholder="请输入提供商显示名称" />
        </NFormItem>
        <NFormItem label="API基础URL" path="base_url">
          <NInput v-model:value="modalForm.base_url" placeholder="请输入API基础URL" />
        </NFormItem>
        <NFormItem label="API密钥" path="api_key">
          <NInput
            v-model:value="modalForm.api_key"
            type="password"
            placeholder="请输入API密钥"
            show-password-on="click"
          />
        </NFormItem>

        <!-- 基本信息 -->
        <NFormItem label="模型名称" path="model_name">
          <NInput v-model:value="modalForm.model_name" placeholder="请输入模型名称" />
        </NFormItem>
        <NFormItem label="显示名称" path="display_name">
          <NInput v-model:value="modalForm.display_name" placeholder="请输入显示名称" />
        </NFormItem>
        <NFormItem label="模型分类" path="category">
          <NSelect
            v-model:value="modalForm.category"
            placeholder="请选择模型分类"
            :options="categoryOptions"
          />
        </NFormItem>
        <NFormItem label="模型描述" path="description">
          <NInput
            v-model:value="modalForm.description"
            type="textarea"
            placeholder="请输入模型描述"
            :rows="3"
          />
        </NFormItem>
        <NFormItem label="模型系列" path="model_family">
          <NSelect
            v-model:value="modalForm.model_family"
            placeholder="请选择模型系列"
            :options="modelFamilyOptions"
          />
        </NFormItem>

        <!-- 模型能力 -->
        <NFormItem label="支持视觉" path="vision">
          <NSwitch v-model:value="modalForm.vision" />
        </NFormItem>
        <NFormItem label="支持函数调用" path="function_calling">
          <NSwitch v-model:value="modalForm.function_calling" />
        </NFormItem>
        <NFormItem label="支持JSON输出" path="json_output">
          <NSwitch v-model:value="modalForm.json_output" />
        </NFormItem>
        <NFormItem label="支持结构化输出" path="structured_output">
          <NSwitch v-model:value="modalForm.structured_output" />
        </NFormItem>
        <NFormItem label="支持多系统消息" path="multiple_system_messages">
          <NSwitch v-model:value="modalForm.multiple_system_messages" />
        </NFormItem>

        <!-- 技术配置 -->
        <NFormItem label="最大令牌数" path="max_tokens">
          <NInputNumber
            v-model:value="modalForm.max_tokens"
            placeholder="请输入最大令牌数"
            :min="1"
            :max="1000000"
          />
        </NFormItem>
        <NFormItem label="温度" path="temperature">
          <NInputNumber
            v-model:value="modalForm.temperature"
            placeholder="请输入温度值"
            :min="0"
            :max="2"
            :step="0.1"
            :precision="1"
          />
        </NFormItem>
        <NFormItem label="Top P" path="top_p">
          <NInputNumber
            v-model:value="modalForm.top_p"
            placeholder="请输入top_p值"
            :min="0"
            :max="1"
            :step="0.1"
            :precision="1"
          />
        </NFormItem>

        <!-- 定价信息 -->
        <NFormItem label="输入价格/1K" path="input_price_per_1k">
          <NInputNumber
            v-model:value="modalForm.input_price_per_1k"
            placeholder="请输入输入价格"
            :min="0"
            :step="0.001"
            :precision="6"
          />
        </NFormItem>
        <NFormItem label="输出价格/1K" path="output_price_per_1k">
          <NInputNumber
            v-model:value="modalForm.output_price_per_1k"
            placeholder="请输入输出价格"
            :min="0"
            :step="0.001"
            :precision="6"
          />
        </NFormItem>

        <!-- 系统配置 -->
        <NFormItem label="系统提示词" path="system_prompt">
          <NInput
            v-model:value="modalForm.system_prompt"
            type="textarea"
            placeholder="请输入系统提示词"
            :rows="4"
          />
        </NFormItem>

        <!-- 状态管理 -->
        <NFormItem label="是否启用" path="is_active">
          <NSwitch v-model:value="modalForm.is_active" />
        </NFormItem>
        <NFormItem label="设为默认" path="is_default">
          <NSwitch v-model:value="modalForm.is_default" />
        </NFormItem>
        <NFormItem label="排序顺序" path="sort_order">
          <NInputNumber
            v-model:value="modalForm.sort_order"
            placeholder="请输入排序顺序"
            :min="0"
          />
        </NFormItem>
      </NForm>
    </CrudModal>
  </CommonPage>
</template>
