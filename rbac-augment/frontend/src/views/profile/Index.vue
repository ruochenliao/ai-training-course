<!--
  个人资料页面
  功能：
  1. 显示用户基本信息
  2. 修改个人资料
  3. 修改密码
  4. 头像上传
-->
<template>
  <div class="profile-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2 class="page-title">个人资料</h2>
      <p class="page-description">管理您的个人信息和账户设置</p>
    </div>

    <!-- 主要内容区域 -->
    <div class="profile-content">
      <!-- 用户信息卡片 -->
      <el-card class="user-info-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span class="card-title">基本信息</span>
          </div>
        </template>
        
        <div class="user-info">
          <!-- 头像区域 -->
          <div class="avatar-section">
            <el-avatar 
              :size="120" 
              :src="userInfo?.avatar || defaultAvatar"
              class="user-avatar"
            >
              <el-icon><User /></el-icon>
            </el-avatar>
            <el-button 
              type="primary" 
              size="small" 
              class="upload-btn"
              @click="handleAvatarUpload"
            >
              更换头像
            </el-button>
          </div>

          <!-- 信息表单 -->
          <div class="info-form">
            <el-form
              ref="profileFormRef"
              :model="profileForm"
              :rules="profileRules"
              label-width="100px"
              label-position="left"
            >
              <el-form-item label="用户名" prop="username">
                <el-input 
                  v-model="profileForm.username" 
                  placeholder="请输入用户名"
                  :disabled="!editMode"
                />
              </el-form-item>

              <el-form-item label="全名" prop="full_name">
                <el-input 
                  v-model="profileForm.full_name" 
                  placeholder="请输入全名"
                  :disabled="!editMode"
                />
              </el-form-item>

              <el-form-item label="邮箱" prop="email">
                <el-input 
                  v-model="profileForm.email" 
                  placeholder="请输入邮箱"
                  :disabled="!editMode"
                />
              </el-form-item>

              <el-form-item label="手机号" prop="phone">
                <el-input 
                  v-model="profileForm.phone" 
                  placeholder="请输入手机号"
                  :disabled="!editMode"
                />
              </el-form-item>

              <el-form-item label="部门">
                <el-input 
                  :value="userInfo?.department?.name || '暂无'"
                  disabled
                />
              </el-form-item>

              <el-form-item label="角色">
                <el-tag 
                  v-for="role in userInfo?.roles" 
                  :key="role"
                  type="primary"
                  class="role-tag"
                >
                  {{ role }}
                </el-tag>
                <span v-if="!userInfo?.roles?.length" class="text-gray-500">暂无角色</span>
              </el-form-item>

              <el-form-item label="注册时间">
                <el-input 
                  :value="formatDate(userInfo?.created_at)"
                  disabled
                />
              </el-form-item>

              <el-form-item label="最后登录">
                <el-input 
                  :value="formatDate(userInfo?.last_login_at)"
                  disabled
                />
              </el-form-item>

              <!-- 操作按钮 -->
              <el-form-item>
                <div class="form-actions">
                  <el-button 
                    v-if="!editMode"
                    type="primary" 
                    @click="enableEdit"
                  >
                    编辑资料
                  </el-button>
                  <template v-else>
                    <el-button 
                      type="primary" 
                      :loading="saving"
                      @click="saveProfile"
                    >
                      保存修改
                    </el-button>
                    <el-button @click="cancelEdit">
                      取消
                    </el-button>
                  </template>
                </div>
              </el-form-item>
            </el-form>
          </div>
        </div>
      </el-card>

      <!-- 修改密码卡片 -->
      <el-card class="password-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span class="card-title">修改密码</span>
          </div>
        </template>

        <el-form
          ref="passwordFormRef"
          :model="passwordForm"
          :rules="passwordRules"
          label-width="100px"
          label-position="left"
        >
          <el-form-item label="当前密码" prop="old_password">
            <el-input 
              v-model="passwordForm.old_password"
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
              :loading="changingPassword"
              @click="changePassword"
            >
              修改密码
            </el-button>
            <el-button @click="resetPasswordForm">
              重置
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </div>

    <!-- 头像上传对话框 -->
    <el-dialog
      v-model="avatarDialogVisible"
      title="更换头像"
      width="400px"
      :before-close="handleAvatarDialogClose"
    >
      <div class="avatar-upload">
        <el-upload
          class="avatar-uploader"
          action="#"
          :show-file-list="false"
          :before-upload="beforeAvatarUpload"
          :http-request="handleAvatarRequest"
        >
          <img v-if="newAvatarUrl" :src="newAvatarUrl" class="avatar-preview" />
          <el-icon v-else class="avatar-uploader-icon"><Plus /></el-icon>
        </el-upload>
        <div class="upload-tips">
          <p>支持 JPG、PNG 格式</p>
          <p>文件大小不超过 2MB</p>
        </div>
      </div>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="avatarDialogVisible = false">取消</el-button>
          <el-button 
            type="primary" 
            :loading="uploadingAvatar"
            @click="confirmAvatarUpload"
          >
            确定
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { User, Plus } from '@element-plus/icons-vue'
import type { FormInstance, UploadRequestOptions } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { updateProfile, changePassword, uploadAvatar } from '@/api'
import { formatDate } from '@/utils'

/**
 * 组件名称：个人资料页面
 * 作用：用户个人信息管理和密码修改
 */

// Store
const authStore = useAuthStore()

// 响应式数据
const profileFormRef = ref<FormInstance>()
const passwordFormRef = ref<FormInstance>()
const editMode = ref(false)
const saving = ref(false)
const changingPassword = ref(false)
const avatarDialogVisible = ref(false)
const uploadingAvatar = ref(false)
const newAvatarUrl = ref('')
const newAvatarFile = ref<File>()

// 用户信息
const userInfo = computed(() => authStore.userInfo)

// 默认头像
const defaultAvatar = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgdmlld0JveD0iMCAwIDEwMCAxMDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIxMDAiIGhlaWdodD0iMTAwIiBmaWxsPSIjRjVGN0ZBIi8+CjxjaXJjbGUgY3g9IjUwIiBjeT0iMzUiIHI9IjE1IiBmaWxsPSIjOTA5Mzk5Ii8+CjxwYXRoIGQ9Ik0yMCA4MEM0MCA2MCA2MCA2MCA4MCA4MEgyMFoiIGZpbGw9IiM5MDkzOTkiLz4KPC9zdmc+'

// 个人资料表单
const profileForm = reactive({
  username: '',
  full_name: '',
  email: '',
  phone: ''
})

// 原始表单数据（用于取消编辑时恢复）
const originalProfileForm = reactive({
  username: '',
  full_name: '',
  email: '',
  phone: ''
})

// 密码表单
const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

// 表单验证规则
const profileRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 20, message: '用户名长度在 2 到 20 个字符', trigger: 'blur' }
  ],
  full_name: [
    { required: true, message: '请输入全名', trigger: 'blur' },
    { min: 2, max: 50, message: '全名长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ],
  phone: [
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号码', trigger: 'blur' }
  ]
}

const passwordRules = {
  old_password: [
    { required: true, message: '请输入当前密码', trigger: 'blur' }
  ],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度在 6 到 20 个字符', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (rule: any, value: string, callback: Function) => {
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

/**
 * 初始化用户信息
 */
const initUserInfo = () => {
  if (userInfo.value) {
    profileForm.username = userInfo.value.username || ''
    profileForm.full_name = userInfo.value.full_name || ''
    profileForm.email = userInfo.value.email || ''
    profileForm.phone = userInfo.value.phone || ''
    
    // 保存原始数据
    Object.assign(originalProfileForm, profileForm)
  }
}

/**
 * 启用编辑模式
 */
const enableEdit = () => {
  editMode.value = true
}

/**
 * 取消编辑
 */
const cancelEdit = () => {
  editMode.value = false
  // 恢复原始数据
  Object.assign(profileForm, originalProfileForm)
  profileFormRef.value?.clearValidate()
}

/**
 * 保存个人资料
 */
const saveProfile = async () => {
  if (!profileFormRef.value) return
  
  try {
    await profileFormRef.value.validate()
    saving.value = true
    
    // 调用API更新用户信息
    await updateProfile(profileForm)
    
    // 更新本地用户信息
    await authStore.fetchUserProfile()
    
    // 更新原始数据
    Object.assign(originalProfileForm, profileForm)
    
    editMode.value = false
    ElMessage.success('个人资料更新成功')
  } catch (error) {
    console.error('更新个人资料失败:', error)
    ElMessage.error('更新失败，请重试')
  } finally {
    saving.value = false
  }
}

/**
 * 修改密码
 */
const changePassword = async () => {
  if (!passwordFormRef.value) return
  
  try {
    await passwordFormRef.value.validate()
    changingPassword.value = true
    
    // 调用API修改密码
    await changePassword({
      old_password: passwordForm.old_password,
      new_password: passwordForm.new_password
    })
    
    ElMessage.success('密码修改成功')
    resetPasswordForm()
  } catch (error) {
    console.error('修改密码失败:', error)
    ElMessage.error('修改密码失败，请检查当前密码是否正确')
  } finally {
    changingPassword.value = false
  }
}

/**
 * 重置密码表单
 */
const resetPasswordForm = () => {
  passwordForm.old_password = ''
  passwordForm.new_password = ''
  passwordForm.confirm_password = ''
  passwordFormRef.value?.clearValidate()
}

/**
 * 处理头像上传
 */
const handleAvatarUpload = () => {
  avatarDialogVisible.value = true
  newAvatarUrl.value = ''
  newAvatarFile.value = undefined
}

/**
 * 头像上传前验证
 */
const beforeAvatarUpload = (file: File) => {
  const isJPGOrPNG = file.type === 'image/jpeg' || file.type === 'image/png'
  const isLt2M = file.size / 1024 / 1024 < 2

  if (!isJPGOrPNG) {
    ElMessage.error('头像只能是 JPG 或 PNG 格式!')
    return false
  }
  if (!isLt2M) {
    ElMessage.error('头像大小不能超过 2MB!')
    return false
  }

  // 预览图片
  const reader = new FileReader()
  reader.onload = (e) => {
    newAvatarUrl.value = e.target?.result as string
  }
  reader.readAsDataURL(file)
  
  newAvatarFile.value = file
  return false // 阻止自动上传
}

/**
 * 自定义头像上传请求
 */
const handleAvatarRequest = (options: UploadRequestOptions) => {
  // 这里不做任何操作，因为我们阻止了自动上传
  return Promise.resolve()
}

/**
 * 确认头像上传
 */
const confirmAvatarUpload = async () => {
  if (!newAvatarFile.value) {
    ElMessage.warning('请选择要上传的头像')
    return
  }

  try {
    uploadingAvatar.value = true
    
    // 创建FormData
    const formData = new FormData()
    formData.append('avatar', newAvatarFile.value)
    
    // 调用API上传头像
    await uploadAvatar(formData)
    
    // 刷新用户信息
    await authStore.fetchUserProfile()
    
    avatarDialogVisible.value = false
    ElMessage.success('头像更新成功')
  } catch (error) {
    console.error('头像上传失败:', error)
    ElMessage.error('头像上传失败，请重试')
  } finally {
    uploadingAvatar.value = false
  }
}

/**
 * 头像对话框关闭处理
 */
const handleAvatarDialogClose = () => {
  newAvatarUrl.value = ''
  newAvatarFile.value = undefined
}

// 组件挂载时初始化
onMounted(() => {
  initUserInfo()
})
</script>

<style scoped lang="scss">
/**
 * 个人资料页面样式
 */

.profile-container {
  padding: 24px;
  background-color: #f5f7fa;
  min-height: calc(100vh - 60px);

  .page-header {
    margin-bottom: 24px;

    .page-title {
      font-size: 24px;
      font-weight: 600;
      color: #303133;
      margin: 0 0 8px 0;
    }

    .page-description {
      font-size: 14px;
      color: #909399;
      margin: 0;
    }
  }

  .profile-content {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 24px;

    @media (max-width: 1200px) {
      grid-template-columns: 1fr;
    }
  }

  .user-info-card {
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;

      .card-title {
        font-size: 16px;
        font-weight: 600;
        color: #303133;
      }
    }

    .user-info {
      display: flex;
      gap: 32px;

      @media (max-width: 768px) {
        flex-direction: column;
        gap: 24px;
      }

      .avatar-section {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 16px;
        min-width: 160px;

        .user-avatar {
          border: 4px solid #f0f2f5;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }

        .upload-btn {
          width: 100px;
        }
      }

      .info-form {
        flex: 1;
        max-width: 500px;

        .role-tag {
          margin-right: 8px;
          margin-bottom: 4px;
        }

        .form-actions {
          display: flex;
          gap: 12px;
          margin-top: 16px;
        }
      }
    }
  }

  .password-card {
    .card-header {
      .card-title {
        font-size: 16px;
        font-weight: 600;
        color: #303133;
      }
    }

    :deep(.el-form) {
      max-width: 400px;
    }
  }
}

// 头像上传对话框样式
.avatar-upload {
  text-align: center;

  .avatar-uploader {
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

    .avatar-preview {
      width: 200px;
      height: 200px;
      object-fit: cover;
      display: block;
    }

    .avatar-uploader-icon {
      font-size: 28px;
      color: #8c939d;
    }
  }

  .upload-tips {
    margin-top: 16px;

    p {
      margin: 4px 0;
      font-size: 12px;
      color: #909399;
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .profile-container {
    padding: 16px;

    .profile-content {
      gap: 16px;
    }
  }
}
</style>
