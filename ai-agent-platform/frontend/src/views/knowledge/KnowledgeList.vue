<template>
  <div class="knowledge-list">
    <div class="page-header">
      <div class="header-left">
        <h1>知识库管理</h1>
        <p>管理您的知识库和文档</p>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="createKnowledge">
          <el-icon><Plus /></el-icon>
          创建知识库
        </el-button>
      </div>
    </div>

    <div class="filter-bar">
      <el-row :gutter="16">
        <el-col :span="6">
          <el-input
            v-model="searchQuery"
            placeholder="搜索知识库..."
            clearable
            @input="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
        <el-col :span="4">
          <el-select v-model="filterPublic" placeholder="可见性" clearable @change="handleFilter">
            <el-option label="全部" value="" />
            <el-option label="公开" :value="true" />
            <el-option label="私有" :value="false" />
          </el-select>
        </el-col>
      </el-row>
    </div>

    <div class="knowledge-grid">
      <el-row :gutter="20">
        <el-col :span="8" v-for="kb in knowledgeBases" :key="kb.id">
          <el-card class="knowledge-card" @click="viewKnowledge(kb.id)">
            <div class="knowledge-header">
              <div class="knowledge-icon">
                <el-icon size="40" color="#409eff"><FolderOpened /></el-icon>
              </div>
              <div class="knowledge-actions" @click.stop>
                <el-dropdown @command="handleCommand">
                  <el-button type="text" size="small">
                    <el-icon><MoreFilled /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item :command="`edit-${kb.id}`">编辑</el-dropdown-item>
                      <el-dropdown-item :command="`upload-${kb.id}`">上传文档</el-dropdown-item>
                      <el-dropdown-item :command="`search-${kb.id}`">搜索测试</el-dropdown-item>
                      <el-dropdown-item :command="`delete-${kb.id}`" divided>删除</el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </div>
            
            <div class="knowledge-info">
              <h3>{{ kb.name }}</h3>
              <p class="knowledge-description">{{ kb.description || '暂无描述' }}</p>
              
              <div class="knowledge-meta">
                <el-tag v-if="kb.is_public" type="success" size="small">公开</el-tag>
                <el-tag v-else type="info" size="small">私有</el-tag>
              </div>
              
              <div class="knowledge-stats">
                <div class="stat-item">
                  <el-icon><Document /></el-icon>
                  <span>{{ kb.document_count || 0 }} 个文档</span>
                </div>
                <div class="stat-item">
                  <el-icon><DataBoard /></el-icon>
                  <span>{{ formatSize(kb.total_size || 0) }}</span>
                </div>
                <div class="stat-item">
                  <el-icon><Calendar /></el-icon>
                  <span>{{ formatDate(kb.created_at) }}</span>
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <div class="pagination-wrapper" v-if="total > 0">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[9, 18, 36]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>

    <div v-if="loading" class="loading-wrapper">
      <el-skeleton :rows="6" animated />
    </div>

    <el-empty v-if="!loading && knowledgeBases.length === 0" description="暂无知识库" />

    <!-- 上传文档对话框 -->
    <el-dialog v-model="uploadDialogVisible" title="上传文档" width="600px">
      <div class="upload-area">
        <el-upload
          ref="uploadRef"
          :action="uploadAction"
          :headers="uploadHeaders"
          :data="uploadData"
          :file-list="fileList"
          :auto-upload="false"
          multiple
          drag
          @change="handleFileChange"
        >
          <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
          <div class="el-upload__text">
            将文件拖到此处，或<em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              支持 PDF、Word、TXT、Markdown 等格式，单个文件不超过 50MB
            </div>
          </template>
        </el-upload>
      </div>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="uploadDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitUpload" :loading="uploading">
            上传
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Plus, Search, FolderOpened, MoreFilled, Document, DataBoard, 
  Calendar, UploadFilled 
} from '@element-plus/icons-vue'
import { knowledgeApi } from '@/api/knowledge'
import { useUserStore } from '@/stores/user'
import { formatTime } from '@/utils'

const router = useRouter()
const userStore = useUserStore()

// 响应式数据
const knowledgeBases = ref([])
const loading = ref(false)
const searchQuery = ref('')
const filterPublic = ref('')
const currentPage = ref(1)
const pageSize = ref(9)
const total = ref(0)

// 上传相关
const uploadDialogVisible = ref(false)
const uploading = ref(false)
const fileList = ref([])
const currentKbId = ref(null)
const uploadRef = ref()

// 计算属性
const searchParams = computed(() => ({
  skip: (currentPage.value - 1) * pageSize.value,
  limit: pageSize.value,
  search: searchQuery.value || undefined,
  is_public: filterPublic.value !== '' ? filterPublic.value : undefined
}))

const uploadAction = computed(() => {
  return `/api/v1/knowledge-bases/${currentKbId.value}/upload`
})

const uploadHeaders = computed(() => ({
  'Authorization': `Bearer ${userStore.token}`
}))

const uploadData = computed(() => ({}))

// 方法
const fetchKnowledgeBases = async () => {
  loading.value = true
  try {
    const response = await knowledgeApi.getKnowledgeBases(searchParams.value)
    knowledgeBases.value = response.data
    total.value = response.total || response.data.length
  } catch (error) {
    console.error('获取知识库列表失败:', error)
    ElMessage.error('获取知识库列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
  fetchKnowledgeBases()
}

const handleFilter = () => {
  currentPage.value = 1
  fetchKnowledgeBases()
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  fetchKnowledgeBases()
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
  fetchKnowledgeBases()
}

const createKnowledge = () => {
  router.push('/knowledge/create')
}

const viewKnowledge = (id: number) => {
  router.push(`/knowledge/${id}`)
}

const handleCommand = async (command: string) => {
  const [action, id] = command.split('-')
  const kbId = parseInt(id)
  
  switch (action) {
    case 'edit':
      router.push(`/knowledge/${kbId}/edit`)
      break
    case 'upload':
      openUploadDialog(kbId)
      break
    case 'search':
      router.push(`/knowledge/${kbId}/search`)
      break
    case 'delete':
      await deleteKnowledge(kbId)
      break
  }
}

const openUploadDialog = (kbId: number) => {
  currentKbId.value = kbId
  uploadDialogVisible.value = true
  fileList.value = []
}

const handleFileChange = (file, fileList) => {
  // 文件变化处理
}

const submitUpload = async () => {
  if (fileList.value.length === 0) {
    ElMessage.warning('请选择要上传的文件')
    return
  }
  
  uploading.value = true
  try {
    await uploadRef.value.submit()
    ElMessage.success('文档上传成功')
    uploadDialogVisible.value = false
    fetchKnowledgeBases()
  } catch (error) {
    console.error('上传失败:', error)
    ElMessage.error('上传失败')
  } finally {
    uploading.value = false
  }
}

const deleteKnowledge = async (id: number) => {
  try {
    await ElMessageBox.confirm('确定要删除这个知识库吗？', '确认删除', {
      type: 'warning'
    })
    
    await knowledgeApi.deleteKnowledgeBase(id)
    ElMessage.success('知识库删除成功')
    fetchKnowledgeBases()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除知识库失败:', error)
      ElMessage.error('删除知识库失败')
    }
  }
}

const formatDate = (dateString: string) => {
  return formatTime(new Date(dateString), 'YYYY-MM-DD')
}

const formatSize = (size: string | number) => {
  const bytes = typeof size === 'string' ? parseInt(size) : size
  if (bytes === 0) return '0 B'
  
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

onMounted(() => {
  fetchKnowledgeBases()
})
</script>

<style lang="scss" scoped>
.knowledge-list {
  padding: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  
  .header-left {
    h1 {
      font-size: 24px;
      font-weight: 600;
      color: #303133;
      margin-bottom: 8px;
    }
    
    p {
      color: #606266;
      margin: 0;
    }
  }
}

.filter-bar {
  margin-bottom: 24px;
}

.knowledge-grid {
  margin-bottom: 24px;
}

.knowledge-card {
  cursor: pointer;
  transition: all 0.3s ease;
  height: 280px;
  
  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  }
  
  :deep(.el-card__body) {
    padding: 20px;
    height: 100%;
    display: flex;
    flex-direction: column;
  }
}

.knowledge-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.knowledge-info {
  flex: 1;
  
  h3 {
    font-size: 16px;
    font-weight: 600;
    color: #303133;
    margin-bottom: 8px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  
  .knowledge-description {
    font-size: 14px;
    color: #606266;
    line-height: 1.5;
    margin-bottom: 12px;
    height: 42px;
    overflow: hidden;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
  }
  
  .knowledge-meta {
    margin-bottom: 16px;
  }
  
  .knowledge-stats {
    .stat-item {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 12px;
      color: #909399;
      margin-bottom: 6px;
      
      &:last-child {
        margin-bottom: 0;
      }
    }
  }
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}

.loading-wrapper {
  padding: 24px;
}

.upload-area {
  margin-bottom: 20px;
  
  :deep(.el-upload-dragger) {
    width: 100%;
  }
}

// 响应式设计
@media (max-width: 1200px) {
  .knowledge-grid {
    :deep(.el-col) {
      width: 50%;
    }
  }
}

@media (max-width: 768px) {
  .knowledge-list {
    padding: 16px;
  }
  
  .page-header {
    flex-direction: column;
    gap: 16px;
    
    .header-right {
      width: 100%;
    }
  }
  
  .filter-bar {
    :deep(.el-col) {
      margin-bottom: 12px;
    }
  }
  
  .knowledge-grid {
    :deep(.el-col) {
      width: 100%;
    }
  }
}
</style>
