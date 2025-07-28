<!-- 账号密码登录表单 -->
<script lang="ts" setup>
import type {FormInstance, FormRules} from 'element-plus';
import type {LoginDTO} from '@/api/auth/types';
import {reactive, ref} from 'vue';
import {useRouter} from 'vue-router';
import {login} from '@/api';
import {useUserStore} from '@/stores';
import {useLoginFormStore} from '@/stores/modules/loginForm';
import {useSessionStore} from '@/stores/modules/session';

const userStore = useUserStore();
const sessionStore = useSessionStore();
const loginFromStore = useLoginFormStore();

const formRef = ref<FormInstance>();

const formModel = reactive<LoginDTO>({
  username: '',
  password: '',
});

const rules = reactive<FormRules<LoginDTO>>({
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
});

const router = useRouter();
async function handleSubmit() {
  try {
    await formRef.value?.validate();
    const res = await login(formModel);
    console.log(res, 'res');

    // 适配后端实际返回的数据格式
    // 后端返回: { code: 200, msg: "OK", data: { access_token: "...", username: "admin" } }
    if (res.data && res.data.access_token) {
      userStore.setToken(res.data.access_token);

      // 构建用户信息对象
      const userInfo = {
        username: res.data.username,
        token: res.data.access_token
      };
      userStore.setUserInfo(userInfo);

      ElMessage.success('登录成功');
      userStore.closeLoginDialog();
      // 立刻获取回话列表
      await sessionStore.requestSessionList(1, true);
      router.replace('/');
    } else {
      ElMessage.error('登录失败：返回数据格式错误');
    }
  }
  catch (error) {
    console.error('请求错误:', error);
    ElMessage.error('登录失败，请检查用户名和密码');
  }
}
</script>

<template>
  <div class="custom-form">
    <el-form
      ref="formRef"
      :model="formModel"
      :rules="rules"
      style="width: 230px"
      @submit.prevent="handleSubmit"
    >
      <el-form-item prop="username">
        <el-input v-model="formModel.username" placeholder="请输入用户名">
          <template #prefix>
            <el-icon>
              <User />
            </el-icon>
          </template>
        </el-input>
      </el-form-item>
      <el-form-item prop="password">
        <el-input
          v-model="formModel.password"
          placeholder="请输入密码"
          type="password"
          show-password
        >
          <template #prefix>
            <el-icon>
              <Lock />
            </el-icon>
          </template>
        </el-input>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" style="width: 100%" native-type="submit">
          登录
        </el-button>
      </el-form-item>
    </el-form>

    <!-- 注册登录 -->
    <div class="form-tip font-size-12px flex items-center">
      <span>没有账号？</span>
      <span
        class="c-[var(--el-color-primar,#409eff)] cursor-pointer"
        @click="loginFromStore.setLoginFormType('RegistrationForm')"
      >
        立即注册
      </span>
    </div>
  </div>
</template>

<style scoped lang="scss">
.custom-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.form-group {
  display: flex;
  gap: 8px;
  align-items: center;
}
.login-btn {
  padding: 12px;
  margin-top: 24px;
  color: white;
  cursor: pointer;
  background: #409eff;
  border: none;
  border-radius: 4px;
}
</style>
