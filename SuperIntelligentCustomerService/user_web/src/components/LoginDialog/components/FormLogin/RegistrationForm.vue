<!-- 注册表单 -->
<script lang="ts" setup>
import type {FormInstance, FormRules} from 'element-plus';
import {ElMessage} from 'element-plus';
import {Bell, Message, Unlock} from '@element-plus/icons-vue';
import type {RegisterDTO} from '@/api/auth/types';
import {useCountdown} from '@vueuse/core';
import {reactive, ref, shallowRef} from 'vue';
import {emailCode, register} from '@/api/auth';
import {useLoginFormStore} from '@/stores/modules/loginForm';

const loginFromStore = useLoginFormStore();
const countdown = shallowRef(60);
const { start, stop, resume } = useCountdown(countdown, {
  onComplete() {
    resume();
  },
  onTick() {
    countdown.value--;
  },
});

const formRef = ref<FormInstance>();

const formModel = ref<RegisterDTO>({
  username: '',
  password: '',
  code: '',
  confirmPassword: '',
});

const rules = reactive<FormRules<RegisterDTO>>({
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  confirmPassword: [
    { required: true, message: '请输入确认密码', trigger: 'blur' },
    {
      validator: (_, value) => {
        if (value !== formModel.value.password) {
          return new Error('两次输入的密码不一致');
        }
        return true;
      },
      trigger: 'change',
    },
  ],
  username: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    {
      validator: (_, value) => {
        if (!isEmail(value)) {
          return new Error('请输入正确的邮箱');
        }
        return true;
      },
      trigger: 'blur',
    },
  ],
});

function isEmail(email: string) {
  const emailRegex = /^[\w.-]+@[a-z0-9.-]+\.[a-z]{2,4}$/i;
  return emailRegex.test(email);
}
async function handleSubmit() {
  try {
    await formRef.value?.validate();
    const params: RegisterDTO = {
      username: formModel.value.username,
      password: formModel.value.password,
      code: formModel.value.code,
      confirmPassword: formModel.value.confirmPassword,
    };
    await register(params);
    ElMessage.success('注册成功！请使用新账号登录');

    // 保存注册的邮箱地址，用于登录表单预填
    const registeredEmail = formModel.value.username;

    formRef.value?.resetFields();
    resume();

    // 注册成功后切换到登录表单并预填邮箱
    setTimeout(() => {
      loginFromStore.setPrefilledUsername(registeredEmail);
      loginFromStore.setLoginFormType('AccountPassword');
    }, 1500); // 1.5秒后切换，让用户看到成功提示
  }
  catch (error: any) {
    console.error('请求错误:', error);
    ElMessage.error(error?.response?.data?.detail || '注册失败，请重试');
  }
}

// 获取验证码
async function getEmailCode() {
  if (formModel.value.username === '') {
    ElMessage.error('请输入邮箱');
    return;
  }
  if (!isEmail(formModel.value.username)) {
    ElMessage.error('请输入正确的邮箱格式');
    return;
  }
  if (countdown.value > 0 && countdown.value < 60) {
    return;
  }
  try {
    start();
    await emailCode({ username: formModel.value.username });
    ElMessage.success('验证码发送成功');
  }
  catch (error: any) {
    console.error('请求错误:', error);
    stop();
    ElMessage.error(error?.response?.data?.detail || '验证码发送失败，请重试');
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
        <el-input v-model="formModel.username" placeholder="请输入邮箱" autocomplete="off">
          <template #prefix>
            <el-icon>
              <Message />
            </el-icon>
          </template>
        </el-input>
      </el-form-item>

      <el-form-item prop="code">
        <el-input v-model="formModel.code" placeholder="请输入验证码" autocomplete="off">
          <template #prefix>
            <el-icon>
              <Bell />
            </el-icon>
          </template>

          <template #suffix>
            <div class="font-size-14px cursor-pointer bg-[var(0,0,0,0.4)]" @click="getEmailCode">
              {{ countdown === 0 || countdown === 60 ? "获取验证码" : `${countdown} s` }}
            </div>
          </template>
        </el-input>
      </el-form-item>

      <el-form-item prop="password">
        <el-input v-model="formModel.password" placeholder="请输入密码" autocomplete="off">
          <template #prefix>
            <el-icon>
              <Unlock />
            </el-icon>
          </template>
        </el-input>
      </el-form-item>

      <el-form-item prop="confirmPassword">
        <el-input v-model="formModel.confirmPassword" placeholder="请确认密码" autocomplete="off">
          <template #prefix>
            <el-icon>
              <Lock />
            </el-icon>
          </template>
        </el-input>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" style="width: 100%" native-type="submit">
          注册
        </el-button>
      </el-form-item>
    </el-form>

    <!-- 返回登录 -->
    <div class="form-tip font-size-12px flex items-center">
      <span>已有账号，</span>
      <span
        class="c-[var(--el-color-primar,#409eff)] cursor-pointer"
        @click="loginFromStore.setLoginFormType('AccountPassword')"
      >
        返回登录
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
