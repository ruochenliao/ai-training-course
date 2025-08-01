import type {ChatSessionVo, CreateSessionDTO, SessionValidateRequest} from './types';
import {del, get, post, put} from '@/utils/request';

// 获取用户会话列表 - 更新为匹配后端接口
export function get_session_list(params: { page?: number; page_size?: number; session_title?: string; user_id?: string }) {
  return get('/api/v1/customer/sessions/list', {
    page: params.page || 1,
    page_size: params.page_size || 20,
    session_title: params.session_title
  });
}

// 创建新会话 - 更新为匹配后端接口
export function create_session(data: CreateSessionDTO) {
  return post('/api/v1/customer/sessions/create', {
    session_title: data.session_title,
    session_content: data.session_content || "",
    remark: data.remark || ""
  });
}

// 更新会话信息
export function update_session(session_id: string, data: { session_title?: string; session_content?: string; remark?: string }) {
  return put('/api/v1/customer/sessions/' + session_id, data);
}

// 获取会话信息 - 更新为匹配后端接口
export function get_session(session_id: string) {
  return get<ChatSessionVo>('/api/v1/customer/sessions/' + session_id);
}

// 删除会话 - 更新为匹配后端接口（单个删除）
export function delete_session(session_id: string) {
  return del('/api/v1/customer/sessions/' + session_id);
}

// 批量删除会话
export function batch_delete_sessions(session_ids: string[]) {
  return del('/api/v1/customer/sessions/batch', { session_ids });
}

// 验证或创建会话 - 新增接口
export function validate_or_create_session(data: SessionValidateRequest) {
  return post('/api/v1/chat/session/validate', data);
}
