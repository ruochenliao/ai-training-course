// 登录表单状态管理
import {defineStore} from 'pinia';

type LoginFormType = 'AccountPassword' | 'VerificationCode' | 'RegistrationForm';

export const useLoginFormStore = defineStore('loginForm', () => {
  const LoginFormType = ref<LoginFormType>('AccountPassword');
  const prefilledUsername = ref<string>('');

  // 设置登录表单类型
  const setLoginFormType = (type: LoginFormType) => {
    LoginFormType.value = type;
  };

  // 设置预填的用户名（注册成功后使用）
  const setPrefilledUsername = (username: string) => {
    prefilledUsername.value = username;
  };

  // 清除预填的用户名
  const clearPrefilledUsername = () => {
    prefilledUsername.value = '';
  };

  return {
    LoginFormType,
    setLoginFormType,
    prefilledUsername,
    setPrefilledUsername,
    clearPrefilledUsername,
  };
});
