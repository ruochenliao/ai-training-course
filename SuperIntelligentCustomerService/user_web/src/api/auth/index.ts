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

// 邮箱验证码
export const emailCode = (data: EmailCodeDTO) => post('/api/v1/base/email/code', data);

// 验证邮箱验证码
export const verifyEmailCode = (email: string, code: string) =>
  post(`/api/v1/base/email/verify?email=${encodeURIComponent(email)}&code=${encodeURIComponent(code)}`);

// 注册账号
export const register = (data: RegisterDTO) => post('/api/v1/base/register', data);

// 获取邮件服务状态
export const getEmailStatus = () => post('/api/v1/base/email/status');

// 获取缓存统计（调试用）
export const getCacheStats = () => post('/api/v1/base/cache/stats');
