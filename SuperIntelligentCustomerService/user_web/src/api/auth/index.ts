import type {EmailCodeDTO, LoginDTO, LoginVO, RegisterDTO} from './types';
import {post} from '@/utils/request';

// 用户登录 - 使用 /api/v1/base/access_token 接口
export const login = (data: LoginDTO) => {
  // 转换为后端期望的格式 (CredentialsSchema)
  const credentials = {
    username: data.username,
    password: data.password
  };
  return post<LoginVO>('/api/v1/base/access_token', credentials);
};

// 邮箱验证码 - API端点已删除，需要使用替代方案
// export const emailCode = (data: EmailCodeDTO) => post('/api/v1/resource/email/code', data);

// 注册账号 - API端点已删除，需要使用替代方案
// export const register = (data: RegisterDTO) => post('/api/v1/auth/register', data);
