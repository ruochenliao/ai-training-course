import type {EmailCodeDTO, LoginDTO, LoginVO, RegisterDTO} from './types';
import {post} from '@/utils/request';

// 用户登录 - 更新为匹配后端接口
export const login = (data: LoginDTO) => post<LoginVO>('/api/v1/auth/login', data);

// 邮箱验证码 - 更新为匹配后端接口
export const emailCode = (data: EmailCodeDTO) => post('/api/v1/resource/email/code', data);

// 注册账号 - 更新为匹配后端接口
export const register = (data: RegisterDTO) => post('/api/v1/auth/register', data);
