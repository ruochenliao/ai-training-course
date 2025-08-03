<template>
  <div class="profile-page">
    <div class="page-header">
      <h2>个人资料</h2>
      <p>查看和编辑个人信息</p>
    </div>

    <el-row :gutter="24">
      <!-- 左侧：头像和基本信息 -->
      <el-col :span="8">
        <el-card class="profile-card">
          <div class="avatar-section">
            <div class="avatar-container">
              <el-avatar
                :size="120"
                :src="userInfo?.avatar_url"
                class="user-avatar"
              >
                <el-icon size="60"><User /></el-icon>
              </el-avatar>
              <el-button
                type="primary"
                size="small"
                class="change-avatar-btn"
                @click="handleChangeAvatar"
              >
                <el-icon><Camera /></el-icon>
                更换头像
              </el-button>
            </div>

            <div class="user-basic-info">
              <h3>{{ userInfo?.full_name || userInfo?.username }}</h3>
              <p class="user-email">{{ userInfo?.email }}</p>
              <div class="user-badges">
                <el-tag v-if="userInfo?.is_superuser" type="danger" size="small">
                  <el-icon><Medal /></el-icon>
                  超级管理员
                </el-tag>
                <el-tag v-if="userInfo?.is_active" type="success" size="small">
                  <el-icon><Check /></el-icon>
                  已激活
                </el-tag>
              </div>
            </div>
          </div>

          <el-divider />

          <div class="stats-section">
            <div class="stat-item">
              <div class="stat-value">{{ stats.agentCount }}</div>
              <div class="stat-label">智能体数量</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ stats.knowledgeCount }}</div>
              <div class="stat-label">知识库数量</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ stats.chatCount }}</div>
              <div class="stat-label">对话次数</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：详细信息编辑 -->
      <el-col :span="16">
        <el-card class="info-card">
          <template #header>
            <div class="card-header">
              <span>个人信息</span>
              <el-button
                v-if="!isEditing"
                type="primary"
                @click="startEdit"
              >
                <el-icon><Edit /></el-icon>
                编辑
              </el-button>
              <div v-else class="edit-actions">
                <el-button @click="cancelEdit">取消</el-button>
                <el-button
                  type="primary"
                  @click="saveProfile"
                  :loading="saving"
                >
                  保存
                </el-button>
              </div>
            </div>
          </template>

          <el-form
            ref="profileFormRef"
            :model="profileForm"
            :rules="formRules"
            label-width="120px"
            class="profile-form"
          >
            <el-form-item label="用户名" prop="username">
              <el-input
                v-model="profileForm.username"
                :disabled="!isEditing"
                placeholder="请输入用户名"
              />
            </el-form-item>

            <el-form-item label="邮箱" prop="email">
              <el-input
                v-model="profileForm.email"
                :disabled="!isEditing"
                placeholder="请输入邮箱"
              />
            </el-form-item>

            <el-form-item label="姓名" prop="full_name">
              <el-input
                v-model="profileForm.full_name"
                :disabled="!isEditing"
                placeholder="请输入真实姓名"
              />
            </el-form-item>

            <el-form-item label="手机号" prop="phone">
              <el-input
                v-model="profileForm.phone"
                :disabled="!isEditing"
                placeholder="请输入手机号"
              />
            </el-form-item>

            <el-form-item label="个人简介" prop="bio">
              <el-input
                v-model="profileForm.bio"
                :disabled="!isEditing"
                type="textarea"
                :rows="4"
                placeholder="请输入个人简介"
              />
            </el-form-item>

            <el-form-item label="注册时间">
              <el-input
                :value="formatTime(userInfo?.created_at)"
                disabled
              />
            </el-form-item>

            <el-form-item label="最后登录">
              <el-input
                :value="formatTime(userInfo?.last_login_at)"
                disabled
              />
            </el-form-item>
          </el-form>
        </el-card>

        <!-- 密码修改卡片 -->
        <el-card class="password-card" style="margin-top: 24px;">
          <template #header>
            <span>修改密码</span>
          </template>

          <el-form
            ref="passwordFormRef"
            :model="passwordForm"
            :rules="passwordRules"
            label-width="120px"
            class="password-form"
          >
            <el-form-item label="当前密码" prop="current_password">
              <el-input
                v-model="passwordForm.current_password"
                type="password"
                placeholder="请输入当前密码"
                show-password
              />
            </el-form-item>

            <el-form-item label="新密码" prop="new_password">
              <el-input
                v-model="passwordForm.new_password"
                type="password"
                placeholder="请输入新密码"
                show-password
              />
            </el-form-item>

            <el-form-item label="确认密码" prop="confirm_password">
              <el-input
                v-model="passwordForm.confirm_password"
                type="password"
                placeholder="请再次输入新密码"
                show-password
              />
            </el-form-item>

            <el-form-item>
              <el-button
                type="primary"
                @click="changePassword"
                :loading="changingPassword"
              >
                修改密码
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>

    <!-- 头像上传对话框 -->
    <el-dialog
      v-model="avatarDialogVisible"
      title="更换头像"
      width="400px"
    >
      <el-upload
        class="avatar-uploader"
        action="#"
        :show-file-list="false"
        :before-upload="beforeAvatarUpload"
        :http-request="uploadAvatar"
      >
        <img v-if="previewAvatar" :src="previewAvatar" class="avatar-preview" />
        <el-icon v-else class="avatar-uploader-icon"><Plus /></el-icon>
      </el-upload>
      <div class="upload-tips">
        <p>支持 JPG、PNG 格式，文件大小不超过 2MB</p>
      </div>

      <template #footer>
        <el-button @click="avatarDialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          @click="confirmAvatar"
          :disabled="!previewAvatar"
        >
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules, UploadRequestOptions } from 'element-plus'
import {
  User, Camera, Medal, Check, Edit, Plus
} from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { userApi } from '@/api/user'
import type { User as UserType } from '@/types/user'
import { formatTime } from '@/utils'

const userStore = useUserStore()

// 响应式数据
const userInfo = ref<UserType | null>(null)
const isEditing = ref(false)
const saving = ref(false)
const changingPassword = ref(false)
const avatarDialogVisible = ref(false)
const previewAvatar = ref('')

// 统计数据
const stats = reactive({
  agentCount: 0,
  knowledgeCount: 0,
  chatCount: 0
})

// 个人信息表单
const profileFormRef = ref<FormInstance>()
const profileForm = reactive({
  username: '',
  email: '',
  full_name: '',
  phone: '',
  bio: ''
})

// 密码修改表单
const passwordFormRef = ref<FormInstance>()
const passwordForm = reactive({
  current_password: '',
  new_password: '',
  confirm_password: ''
})

// 表单验证规则
const formRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  full_name: [
    { max: 50, message: '姓名长度不能超过 50 个字符', trigger: 'blur' }
  ],
  phone: [
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' }
  ],
  bio: [
    { max: 200, message: '个人简介不能超过 200 个字符', trigger: 'blur' }
  ]
}

const passwordRules: FormRules = {
  current_password: [
    { required: true, message: '请输入当前密码', trigger: 'blur' }
  ],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度在 6 到 20 个字符', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== passwordForm.new_password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

// 获取用户信息
const fetchUserInfo = async () => {
  try {
    userInfo.value = userStore.userInfo
    if (userInfo.value) {
      // 填充表单数据
      Object.assign(profileForm, {
        username: userInfo.value.username || '',
        email: userInfo.value.email || '',
        full_name: userInfo.value.full_name || '',
        phone: userInfo.value.phone || '',
        bio: userInfo.value.bio || ''
      })
    }
  } catch (error) {
    console.error('获取用户信息失败:', error)
    ElMessage.error('获取用户信息失败')
  }
}

// 获取统计数据
const fetchStats = async () => {
  try {
    // TODO: 调用API获取统计数据
    // const response = await userApi.getStats()
    // Object.assign(stats, response.data)

    // 模拟数据
    stats.agentCount = 5
    stats.knowledgeCount = 3
    stats.chatCount = 128
  } catch (error) {
    console.error('获取统计数据失败:', error)
  }
}

// 开始编辑
const startEdit = () => {
  isEditing.value = true
}

// 取消编辑
const cancelEdit = () => {
  isEditing.value = false
  // 重置表单数据
  if (userInfo.value) {
    Object.assign(profileForm, {
      username: userInfo.value.username || '',
      email: userInfo.value.email || '',
      full_name: userInfo.value.full_name || '',
      phone: userInfo.value.phone || '',
      bio: userInfo.value.bio || ''
    })
  }
}

// 保存个人信息
const saveProfile = async () => {
  if (!profileFormRef.value) return

  try {
    await profileFormRef.value.validate()
    saving.value = true

    // TODO: 调用API保存用户信息
    // const response = await userApi.updateProfile(profileForm)
    // userInfo.value = response.data
    // userStore.setUserInfo(response.data)

    // 模拟保存成功
    Object.assign(userInfo.value, profileForm)
    userStore.setUserInfo(userInfo.value)

    isEditing.value = false
    ElMessage.success('个人信息保存成功')
  } catch (error) {
    console.error('保存个人信息失败:', error)
    ElMessage.error('保存个人信息失败')
  } finally {
    saving.value = false
  }
}

// 修改密码
const changePassword = async () => {
  if (!passwordFormRef.value) return

  try {
    await passwordFormRef.value.validate()
    changingPassword.value = true

    // TODO: 调用API修改密码
    // await userApi.changePassword(passwordForm)

    // 重置表单
    Object.assign(passwordForm, {
      current_password: '',
      new_password: '',
      confirm_password: ''
    })

    ElMessage.success('密码修改成功')
  } catch (error) {
    console.error('修改密码失败:', error)
    ElMessage.error('修改密码失败')
  } finally {
    changingPassword.value = false
  }
}

// 更换头像
const handleChangeAvatar = () => {
  avatarDialogVisible.value = true
  previewAvatar.value = ''
}

// 头像上传前检查
const beforeAvatarUpload = (file: File) => {
  const isImage = file.type.startsWith('image/')
  const isLt2M = file.size / 1024 / 1024 < 2

  if (!isImage) {
    ElMessage.error('只能上传图片文件!')
    return false
  }
  if (!isLt2M) {
    ElMessage.error('图片大小不能超过 2MB!')
    return false
  }

  // 预览图片
  const reader = new FileReader()
  reader.onload = (e) => {
    previewAvatar.value = e.target?.result as string
  }
  reader.readAsDataURL(file)

  return false // 阻止自动上传
}

// 上传头像
const uploadAvatar = (options: UploadRequestOptions) => {
  // 这里处理头像上传逻辑
  console.log('上传头像:', options.file)
}

// 确认头像
const confirmAvatar = async () => {
  try {
    // TODO: 调用API上传头像
    // const response = await userApi.uploadAvatar(avatarFile)
    // userInfo.value.avatar_url = response.data.avatar_url

    // 模拟上传成功
    if (userInfo.value) {
      userInfo.value.avatar_url = previewAvatar.value
    }

    avatarDialogVisible.value = false
    ElMessage.success('头像更新成功')
  } catch (error) {
    console.error('头像上传失败:', error)
    ElMessage.error('头像上传失败')
  }
}

onMounted(() => {
  fetchUserInfo()
  fetchStats()
})
</script>

<style lang="scss" scoped>
.profile-page {
  padding: 24px;
}

.page-header {
  margin-bottom: 24px;

  h2 {
    font-size: 24px;
    font-weight: 600;
    color: #303133;
    margin-bottom: 8px;
  }

  p {
    color: #606266;
    font-size: 14px;
  }
}

// 个人资料卡片
.profile-card {
  .avatar-section {
    text-align: center;

    .avatar-container {
      position: relative;
      display: inline-block;
      margin-bottom: 20px;

      .user-avatar {
        border: 4px solid #f0f0f0;
        box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
      }

      .change-avatar-btn {
        position: absolute;
        bottom: -10px;
        left: 50%;
        transform: translateX(-50%);
        font-size: 12px;
        padding: 4px 8px;
      }
    }

    .user-basic-info {
      h3 {
        font-size: 20px;
        font-weight: 600;
        color: #303133;
        margin-bottom: 8px;
      }

      .user-email {
        color: #606266;
        font-size: 14px;
        margin-bottom: 12px;
      }

      .user-badges {
        display: flex;
        justify-content: center;
        gap: 8px;
        flex-wrap: wrap;

        .el-tag {
          display: flex;
          align-items: center;
          gap: 4px;
        }
      }
    }
  }

  .stats-section {
    display: flex;
    justify-content: space-around;

    .stat-item {
      text-align: center;

      .stat-value {
        font-size: 24px;
        font-weight: 600;
        color: #409eff;
        margin-bottom: 4px;
      }

      .stat-label {
        font-size: 12px;
        color: #909399;
      }
    }
  }
}

// 信息卡片
.info-card, .password-card {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .edit-actions {
      display: flex;
      gap: 8px;
    }
  }

  .profile-form, .password-form {
    .el-form-item {
      margin-bottom: 20px;
    }
  }
}

// 头像上传
.avatar-uploader {
  display: flex;
  justify-content: center;

  :deep(.el-upload) {
    border: 1px dashed #d9d9d9;
    border-radius: 6px;
    cursor: pointer;
    position: relative;
    overflow: hidden;
    transition: all 0.3s;
    width: 200px;
    height: 200px;
    display: flex;
    align-items: center;
    justify-content: center;

    &:hover {
      border-color: #409eff;
    }
  }

  .avatar-uploader-icon {
    font-size: 28px;
    color: #8c939d;
  }

  .avatar-preview {
    width: 200px;
    height: 200px;
    object-fit: cover;
    border-radius: 6px;
  }
}

.upload-tips {
  text-align: center;
  margin-top: 16px;

  p {
    color: #909399;
    font-size: 12px;
    margin: 0;
  }
}

// 响应式设计
@media (max-width: 768px) {
  .profile-page {
    padding: 16px;

    .el-col {
      margin-bottom: 24px;
    }
  }

  .stats-section {
    .stat-item {
      .stat-value {
        font-size: 20px;
      }
    }
  }
}
</style>
