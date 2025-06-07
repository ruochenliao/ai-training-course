import type {ApiResponse} from './index';
import {request} from './index';

// 部门接口 - 根据API文档定义
export interface Dept {
  id: number;
  name: string;
  parent_id: number;
  order: number;
  remark?: string;
  children?: Dept[];
}

// 部门查询参数
export interface DeptQueryParams {
  name?: string;
}

// 部门创建参数
export interface DeptCreate {
  name: string;
  parent_id: number;
  order: number;
  remark?: string;
}

// 部门更新参数
export interface DeptUpdate {
  id: number;
  name?: string;
  parent_id?: number;
  order?: number;
  remark?: string;
}

// 部门API
export const deptApi = {
  // 获取部门列表 - 返回树形结构
  list: (params?: DeptQueryParams): Promise<ApiResponse<Dept[]>> => {
    return request.get('/api/v1/dept/list', { params });
  },

  // 获取单个部门详情
  get: (id: number): Promise<ApiResponse<Dept>> => {
    return request.get('/api/v1/dept/get', { params: { id } });
  },

  // 创建部门
  create: (data: DeptCreate): Promise<ApiResponse<string>> => {
    return request.post('/api/v1/dept/create', { dept_in: data });
  },

  // 更新部门
  update: (data: DeptUpdate): Promise<ApiResponse<string>> => {
    return request.post('/api/v1/dept/update', { dept_in: data });
  },

  // 删除部门
  delete: (deptId: number): Promise<ApiResponse<string>> => {
    return request.delete('/api/v1/dept/delete', { params: { dept_id: deptId } });
  },
};

export default deptApi;