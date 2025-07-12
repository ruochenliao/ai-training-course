import type {Component} from 'vue';

export interface GetSessionListParams {
  /**
   * 创建者
   */
  createBy?: number;
  /**
   * 创建部门
   */
  createDept?: number;
  /**
   * 创建时间
   */
  createTime?: Date;
  /**
   * 主键
   */
  id?: number;
  /**
   * 排序的方向desc或者asc
   */
  isAsc?: string;
  /**
   * 排序列
   */
  orderByColumn?: string;
  /**
   * 当前页数
   */
  pageNum?: number;
  /**
   * 分页大小
   */
  pageSize?: number;
  /**
   * 请求参数
   */
  params?: { [key: string]: { [key: string]: any } };
  /**
   * 备注
   */
  remark?: string;
  /**
   * 会话内容
   */
  sessionContent?: string;
  /**
   * 会话标题
   */
  sessionTitle?: string;
  /**
   * 更新者
   */
  updateBy?: number;
  /**
   * 更新时间
   */
  updateTime?: Date;
  /**
   * 用户id
   */
  userId: number;
}

/**
 * ChatSessionVo，会话管理视图对象 chat_session
 */
export interface ChatSessionVo {
  /**
   * 主键
   */
  // id?: number
  id?: string;
  /**
   * 备注
   */
  remark?: string;
  /**
   * 会话内容
   */
  sessionContent?: string;
  /**
   * 会话标题
   */
  sessionTitle?: string;
  /**
   * 用户id
   */
  userId?: number;
  /**
   * 创建时间
   */
  created_at?: string;
  /**
   * 更新时间
   */
  updated_at?: string;
  /**
   * 自定义的消息前缀图标字段
   */
  prefixIcon?: Component;
}

/**
 * ChatSessionBo，会话管理业务对象 chat_session
 */
export interface CreateSessionDTO {
  /**
   * 创建者
   */
  create_by?: number;
  /**
   * 创建部门
   */
  create_dept?: number;
  /**
   * 创建时间
   */
  create_time?: Date;
  /**
   * 主键
   */
  id?: string;
  /**
   * 请求参数
   */
  params?: { [key: string]: { [key: string]: any } };
  /**
   * 备注
   */
  remark?: string;
  /**
   * 会话内容
   */
  session_content?: string;
  /**
   * 会话标题
   */
  session_title: string;
  /**
   * 更新者
   */
  update_by?: number;
  /**
   * 更新时间
   */
  update_time?: Date;
  /**
   * 用户id（可选，使用当前登录用户）
   */
  user_id?: number;
}

/**
 * 会话验证请求 - 匹配后端接口
 */
export interface SessionValidateRequest {
  /**
   * 会话ID（可选）
   */
  session_id?: string;
  /**
   * 默认会话标题（当需要创建新会话时使用）
   */
  default_title?: string;
}

// export interface CreateSessionVO {
//   id: number;
// }
