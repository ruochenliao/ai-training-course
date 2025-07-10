<template>
  <CommonPage show-footer title="知识库管理">
    <template #action>
      <n-space>
        <n-button @click="showStatistics = true">
          <TheIcon icon="material-symbols:analytics" :size="18" class="mr-5" />统计信息
        </n-button>
        <n-button v-permission="'post/api/v1/knowledge/'" type="primary" @click="handleAdd">
          <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />创建知识库
        </n-button>
      </n-space>
    </template>

    <!-- 表格 -->
    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      :columns="columns"
      :get-data="api.getKnowledgeBaseList"
    >
      <template #queryBar>
        <QueryBarItem label="名称" :label-width="40">
          <n-input
            v-model:value="queryItems.search"
            clearable
            type="text"
            placeholder="请输入知识库名称"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
        <QueryBarItem label="类型" :label-width="40">
          <n-select
            v-model:value="queryItems.knowledge_type"
            clearable
            placeholder="请选择类型"
            :options="knowledgeTypeOptions"
            @update:value="$table?.handleSearch()"
          />
        </QueryBarItem>
        <QueryBarItem label="状态" :label-width="40">
          <n-select
            v-model:value="queryItems.is_public"
            clearable
            placeholder="请选择状态"
            :options="publicOptions"
            @update:value="$table?.handleSearch()"
          />
        </QueryBarItem>
      </template>
    </CrudTable>

    <!-- 创建/编辑对话框 -->
    <CrudModal
      v-model:visible="modalVisible"
      :title="modalTitle"
      :loading="modalLoading"
      @save="handleSaveCustom"
    >
      <n-form
        ref="modalFormRef"
        label-placement="left"
        label-width="100px"
        :model="modalForm"
        :rules="rules"
      >
        <n-form-item label="知识库名称" path="name">
          <n-input
            v-model:value="modalForm.name"
            placeholder="请输入知识库名称"
            maxlength="200"
            show-count
          />
        </n-form-item>

        <n-form-item label="知识库类型" path="knowledge_type">
          <n-select
            v-model:value="modalForm.knowledge_type"
            placeholder="请选择知识库类型"
            :options="knowledgeTypeOptions"
          />
        </n-form-item>

        <n-form-item label="访问权限" path="is_public">
          <n-radio-group v-model:value="modalForm.is_public">
            <n-space>
              <n-radio :value="false">私有（仅自己可见）</n-radio>
              <n-radio :value="true">公开（所有人可见）</n-radio>
            </n-space>
          </n-radio-group>
        </n-form-item>

        <n-form-item label="描述信息">
          <n-input
            v-model:value="modalForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入知识库描述"
            maxlength="500"
            show-count
          />
        </n-form-item>

        <!-- 高级配置 -->
        <n-collapse>
          <n-collapse-item title="高级配置" name="advanced">
            <n-form-item label="最大文件大小">
              <n-space align="center">
                <n-input-number
                  v-model:value="modalForm.max_file_size_mb"
                  :min="1"
                  :max="100"
                  :step="1"
                  style="width: 150px"
                />
                <span>MB</span>
              </n-space>
            </n-form-item>

            <n-form-item label="允许文件类型">
              <n-checkbox-group v-model:value="modalForm.allowed_file_types">
                <n-space>
                  <n-checkbox value="pdf" label="PDF" />
                  <n-checkbox value="docx" label="Word文档" />
                  <n-checkbox value="txt" label="文本文件" />
                  <n-checkbox value="md" label="Markdown" />
                  <n-checkbox value="jpg" label="图片(JPG)" />
                  <n-checkbox value="png" label="图片(PNG)" />
                </n-space>
              </n-checkbox-group>
            </n-form-item>

            <n-form-item label="嵌入模型">
              <n-select
                v-model:value="modalForm.embedding_model"
                placeholder="选择嵌入模型"
                :options="embeddingModelOptions"
              />
            </n-form-item>

            <n-grid :cols="2" :x-gap="20">
              <n-grid-item>
                <n-form-item label="分块大小">
                  <n-input-number
                    v-model:value="modalForm.chunk_size"
                    :min="256"
                    :max="4096"
                    :step="256"
                    style="width: 100%"
                  />
                </n-form-item>
              </n-grid-item>
              <n-grid-item>
                <n-form-item label="分块重叠">
                  <n-input-number
                    v-model:value="modalForm.chunk_overlap"
                    :min="0"
                    :max="512"
                    :step="50"
                    style="width: 100%"
                  />
                </n-form-item>
              </n-grid-item>
            </n-grid>
          </n-collapse-item>
        </n-collapse>
      </n-form>
    </CrudModal>

    <!-- 统计信息抽屉 -->
    <n-drawer v-model:show="showStatistics" :width="400" placement="right">
      <n-drawer-content title="知识库统计" closable>
        <KnowledgeStatistics />
      </n-drawer-content>
    </n-drawer>

    <!-- 知识库详情 -->
    <KnowledgeDetail
      v-model:visible="showDetail"
      :knowledge-base-id="selectedKbId"
      @refresh="$table?.handleSearch()"
    />

    <!-- 文件管理弹窗 -->
    <FileManagementModal
      v-model:show="fileModalVisible"
      :knowledge-base="selectedKnowledgeBase"
    />
  </CommonPage>
</template>

<script setup>
import { h, onMounted, ref, resolveDirective, withDirectives } from 'vue'
import {
  NButton,
  NCheckbox,
  NCheckboxGroup,
  NForm,
  NFormItem,
  NImage,
  NInput,
  NSpace,
  NSwitch,
  NTag,
  NPopconfirm,
  NSelect,
  NRadioGroup,
  NRadio,
  NInputNumber,
  NGrid,
  NGridItem,
  NCollapse,
  NCollapseItem,
  NDrawer,
  NDrawerContent,
  useMessage
} from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import KnowledgeStatistics from './components/KnowledgeStatistics.vue'
import KnowledgeDetail from './components/KnowledgeDetail.vue'
import FileManagementModal from './components/FileManagementModal.vue'

import { formatDate, renderIcon } from '@/utils'
import { useCRUD } from '@/composables'
import api from '@/api'
import TheIcon from '@/components/icon/TheIcon.vue'
import { useRouter } from 'vue-router'

defineOptions({ name: '知识库管理' })

const $table = ref(null)
const queryItems = ref({})
const vPermission = resolveDirective('permission')
const router = useRouter()
const message = useMessage()

// 新增状态
const showStatistics = ref(false)
const showDetail = ref(false)
const selectedKbId = ref(null)

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
  name: '知识库',
  initForm: {
    name: '',
    description: '',
    knowledge_type: null,
    is_public: false,
    max_file_size_mb: 50,
    allowed_file_types: ['pdf', 'docx', 'txt', 'md'],
    embedding_model: 'BAAI/bge-small-zh-v1.5',
    chunk_size: 1024,
    chunk_overlap: 100
  },
  doCreate: api.createKnowledgeBase,
  doUpdate: (data) => api.updateKnowledgeBase(data.id, data),
  doDelete: (data) => api.deleteKnowledgeBase(data.id),
  refresh: () => $table.value?.handleSearch(),
})

const knowledgeTypeOptions = ref([])
const publicOptions = [
  { label: '公开', value: true },
  { label: '私有', value: false }
]

const embeddingModelOptions = [
  { label: 'BAAI/bge-small-zh-v1.5', value: 'BAAI/bge-small-zh-v1.5' },
  { label: 'text-embedding-ada-002', value: 'text-embedding-ada-002' }
]

// 表单验证规则
const rules = {
  name: [
    { required: true, message: '请输入知识库名称', trigger: 'blur' },
    { min: 2, max: 200, message: '长度在 2 到 200 个字符', trigger: 'blur' }
  ],
  knowledge_type: [
    { required: true, message: '请选择知识库类型', trigger: 'change' }
  ]
}

// 表格列定义
const columns = [
  {
    title: '知识库名称',
    key: 'name',
    width: 200,
    render(row) {
      return h('div', { class: 'flex items-center' }, [
        h(TheIcon, {
          icon: 'material-symbols:database',
          size: 20,
          style: { marginRight: '8px', color: '#18a058' }
        }),
        h('div', [
          h('div', { class: 'font-medium' }, row.name),
          h('div', { class: 'text-xs text-gray-500' }, row.description || '暂无描述')
        ])
      ])
    }
  },
  {
    title: '类型',
    key: 'knowledge_type',
    width: 100,
    render(row) {
      const typeMap = {
        'technical': { label: '技术文档', type: 'info' },
        'faq': { label: 'FAQ', type: 'success' },
        'policy': { label: '政策制度', type: 'warning' },
        'product': { label: '产品说明', type: 'error' },
        'general': { label: '通用', type: 'default' }
      }
      const typeInfo = typeMap[row.knowledge_type] || { label: row.knowledge_type, type: 'default' }
      return h(NTag, { type: typeInfo.type, size: 'small' }, { default: () => typeInfo.label })
    }
  },
  {
    title: '访问权限',
    key: 'is_public',
    width: 100,
    render(row) {
      return h(NTag, {
        type: row.is_public ? 'success' : 'info',
        size: 'small'
      }, { default: () => row.is_public ? '公开' : '私有' })
    }
  },
  {
    title: '文件统计',
    key: 'file_count',
    width: 120,
    render(row) {
      return h('div', { class: 'text-center' }, [
        h('div', { class: 'font-medium' }, `${row.file_count || 0} 个文件`),
        h('div', { class: 'text-xs text-gray-500' }, formatFileSize(row.total_size || 0))
      ])
    }
  },
  {
    title: '创建时间',
    key: 'created_at',
    width: 150,
    render(row) {
      return formatDate(row.created_at)
    }
  },
  {
    title: '操作',
    key: 'actions',
    width: 280,
    align: 'center',
    fixed: 'right',
    render(row) {
      return [
        withDirectives(
          h(
            NButton,
            {
              size: 'small',
              style: 'margin-right: 8px;',
              onClick: () => viewDetail(row),
            },
            {
              default: () => '详情',
              icon: renderIcon('material-symbols:info', { size: 16 }),
            }
          ),
          [[vPermission, 'get/api/v1/knowledge/']]
        ),
        withDirectives(
          h(
            NButton,
            {
              size: 'small',
              type: 'primary',
              style: 'margin-right: 8px;',
              onClick: () => viewFiles(row),
            },
            {
              default: () => '文件管理',
              icon: renderIcon('material-symbols:folder-open', { size: 16 }),
            }
          ),
          [[vPermission, 'get/api/v1/knowledge/']]
        ),
        withDirectives(
          h(
            NButton,
            {
              size: 'small',
              type: 'info',
              style: 'margin-right: 8px;',
              onClick: () => {
                handleEdit(row)
                // 处理编辑时的特殊字段
                modalForm.value.max_file_size_mb = Math.round((row.max_file_size || 52428800) / 1024 / 1024)
              },
            },
            {
              default: () => '编辑',
              icon: renderIcon('material-symbols:edit', { size: 16 }),
            }
          ),
          [[vPermission, 'put/api/v1/knowledge/']]
        ),
        withDirectives(
          h(
            NPopconfirm,
            {
              onPositiveClick: () => handleDelete({ id: row.id }),
            },
            {
              trigger: () => h(
                NButton,
                {
                  size: 'small',
                  type: 'error',
                },
                {
                  default: () => '删除',
                  icon: renderIcon('material-symbols:delete', { size: 16 }),
                }
              ),
              default: () => `确定要删除知识库"${row.name}"吗？`,
            }
          ),
          [[vPermission, 'delete/api/v1/knowledge/']]
        ),
      ]
    },
  },
]

// 查看详情
const viewDetail = (kb) => {
  selectedKbId.value = kb.id
  showDetail.value = true
}

// 文件管理弹窗相关
const fileModalVisible = ref(false)
const selectedKnowledgeBase = ref(null)

// 查看文件
const viewFiles = (kb) => {
  selectedKnowledgeBase.value = kb
  fileModalVisible.value = true
}





// 格式化文件大小
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

// 自定义保存处理
const handleSaveCustom = async () => {
  // 表单验证
  try {
    await modalFormRef.value?.validate()
  } catch (error) {
    return
  }

  // 准备提交数据
  const submitData = {
    ...modalForm.value,
    max_file_size: modalForm.value.max_file_size_mb * 1024 * 1024 // 转换为字节
  }
  delete submitData.max_file_size_mb

  // 调用原始的保存方法
  modalLoading.value = true
  try {
    if (submitData.id) {
      // 编辑模式
      await api.updateKnowledgeBase(submitData.id, submitData)
      message.success('更新成功')
    } else {
      // 创建模式
      await api.createKnowledgeBase(submitData)
      message.success('创建成功')
    }
    modalVisible.value = false
    // 刷新表格数据
    $table.value?.handleSearch()
  } catch (error) {
    console.error('保存失败:', error)
    message.error('操作失败')
  } finally {
    modalLoading.value = false
  }
}

onMounted(() => {
  $table.value?.handleSearch()
  // 加载知识库类型选项
  api.getKnowledgeTypes().then((res) => {
    if (res.code === 200) {
      knowledgeTypeOptions.value = res.data.map(type => ({
        label: type.label,
        value: type.value
      }))
    }
  }).catch(() => {
    // 如果API不存在，使用默认选项
    knowledgeTypeOptions.value = [
      { label: '技术文档', value: 'technical' },
      { label: 'FAQ', value: 'faq' },
      { label: '政策制度', value: 'policy' },
      { label: '产品说明', value: 'product' },
      { label: '通用', value: 'general' }
    ]
  })
})
</script>

<style scoped>
/* 表格样式优化 */
:deep(.n-data-table-th) {
  background-color: var(--n-th-color);
  font-weight: 600;
}

:deep(.n-data-table-td) {
  border-bottom: 1px solid var(--n-border-color);
}

:deep(.n-data-table-tr:hover .n-data-table-td) {
  background-color: var(--n-th-color-hover);
}

/* 操作按钮样式 */
.action-button {
  margin-right: 8px;
}

.action-button:last-child {
  margin-right: 0;
}

/* 文件信息样式 */
.file-info {
  display: flex;
  align-items: center;
}

.file-details {
  display: flex;
  flex-direction: column;
}

.font-medium {
  font-weight: 500;
}

.text-xs {
  font-size: 12px;
}

.text-gray-500 {
  color: #6b7280;
}

.text-center {
  text-align: center;
}

.flex {
  display: flex;
}

.items-center {
  align-items: center;
}

.mr-5 {
  margin-right: 5px;
}
</style>
