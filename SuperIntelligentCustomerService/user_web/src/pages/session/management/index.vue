<template>
  <div class="session-management">
    <div class="header">
      <h2>会话管理</h2>
      <div class="actions">
        <el-input
          v-model="searchTitle"
          placeholder="搜索会话标题"
          style="width: 200px; margin-right: 10px"
          @input="handleSearch"
        />
        <el-button type="primary" @click="showCreateDialog">
          <el-icon><Plus /></el-icon>
          新建会话
        </el-button>
        <el-button 
          type="danger" 
          :disabled="selectedSessions.length === 0"
          @click="handleBatchDelete"
        >
          <el-icon><Delete /></el-icon>
          批量删除
        </el-button>
      </div>
    </div>

    <div class="table-container">
      <el-table
        :data="sessions"
        v-loading="loading"
        @selection-change="handleSelectionChange"
        style="width: 100%"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="session_id" label="会话ID" width="280" />
        <el-table-column prop="session_title" label="会话标题" min-width="200" />
        <el-table-column prop="session_content" label="会话内容" min-width="200" show-overflow-tooltip />
        <el-table-column prop="message_count" label="消息数量" width="100" />
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column prop="last_active" label="最后活动" width="180" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button size="small" @click="handleView(row)">查看</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </div>

    <!-- 创建/编辑会话对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑会话' : '创建会话'"
      width="600px"
    >
      <el-form :model="sessionForm" :rules="formRules" ref="formRef" label-width="100px">
        <el-form-item label="会话标题" prop="session_title">
          <el-input v-model="sessionForm.session_title" placeholder="请输入会话标题" />
        </el-form-item>
        <el-form-item label="会话内容" prop="session_content">
          <el-input
            v-model="sessionForm.session_content"
            type="textarea"
            :rows="4"
            placeholder="请输入会话内容"
          />
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input v-model="sessionForm.remark" placeholder="请输入备注" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmit">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import {onMounted, reactive, ref} from 'vue'
import {ElMessage, ElMessageBox} from 'element-plus'
import {Delete, Plus} from '@element-plus/icons-vue'
import {useRouter} from 'vue-router'
import {
  batch_delete_sessions,
  create_session,
  delete_session,
  get_session_list,
  update_session
} from '@/api/session'

const router = useRouter()

// 响应式数据
const loading = ref(false)
const sessions = ref([])
const selectedSessions = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const searchTitle = ref('')

// 对话框相关
const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref()
const sessionForm = reactive({
  session_id: '',
  session_title: '',
  session_content: '',
  remark: ''
})

// 表单验证规则
const formRules = {
  session_title: [
    { required: true, message: '请输入会话标题', trigger: 'blur' }
  ]
}

// 获取会话列表
const fetchSessions = async () => {
  loading.value = true
  try {
    const response = await get_session_list({
      page: currentPage.value,
      page_size: pageSize.value,
      session_title: searchTitle.value
    })
    
    if (response.code === 200) {
      sessions.value = response.data
      total.value = response.total || 0
    }
  } catch (error) {
    console.error('获取会话列表失败:', error)
    ElMessage.error('获取会话列表失败')
  } finally {
    loading.value = false
  }
}

// 搜索处理
const handleSearch = () => {
  currentPage.value = 1
  fetchSessions()
}

// 分页处理
const handleSizeChange = (size: number) => {
  pageSize.value = size
  fetchSessions()
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
  fetchSessions()
}

// 选择处理
const handleSelectionChange = (selection: any[]) => {
  selectedSessions.value = selection
}

// 显示创建对话框
const showCreateDialog = () => {
  isEdit.value = false
  Object.assign(sessionForm, {
    session_id: '',
    session_title: '',
    session_content: '',
    remark: ''
  })
  dialogVisible.value = true
}

// 编辑会话
const handleEdit = (row: any) => {
  isEdit.value = true
  Object.assign(sessionForm, {
    session_id: row.session_id,
    session_title: row.session_title,
    session_content: row.session_content,
    remark: row.remark
  })
  dialogVisible.value = true
}

// 查看会话
const handleView = (row: any) => {
  router.push({
    name: 'chatWithId',
    params: { id: row.session_id }
  })
}

// 删除会话
const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除会话 "${row.session_title}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const response = await delete_session(row.session_id)
    if (response.code === 200) {
      ElMessage.success('删除成功')
      fetchSessions()
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除会话失败:', error)
      ElMessage.error('删除会话失败')
    }
  }
}

// 批量删除
const handleBatchDelete = async () => {
  if (selectedSessions.value.length === 0) {
    ElMessage.warning('请选择要删除的会话')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedSessions.value.length} 个会话吗？`,
      '确认批量删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const sessionIds = selectedSessions.value.map((session: any) => session.session_id)
    const response = await batch_delete_sessions(sessionIds)
    
    if (response.code === 200) {
      ElMessage.success('批量删除成功')
      selectedSessions.value = []
      fetchSessions()
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量删除失败:', error)
      ElMessage.error('批量删除失败')
    }
  }
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    
    if (isEdit.value) {
      // 更新会话
      const response = await update_session(sessionForm.session_id, {
        session_title: sessionForm.session_title,
        session_content: sessionForm.session_content,
        remark: sessionForm.remark
      })
      
      if (response.code === 200) {
        ElMessage.success('更新成功')
        dialogVisible.value = false
        fetchSessions()
      }
    } else {
      // 创建会话
      const response = await create_session({
        session_title: sessionForm.session_title,
        session_content: sessionForm.session_content,
        remark: sessionForm.remark
      })
      
      if (response.code === 200) {
        ElMessage.success('创建成功')
        dialogVisible.value = false
        fetchSessions()
      }
    }
  } catch (error) {
    console.error('提交失败:', error)
    ElMessage.error('操作失败')
  }
}

// 初始化
onMounted(() => {
  fetchSessions()
})
</script>

<style scoped>
.session-management {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.actions {
  display: flex;
  align-items: center;
}

.table-container {
  background: white;
  border-radius: 8px;
  padding: 20px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}
</style>
