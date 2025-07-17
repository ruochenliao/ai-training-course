import { request } from '@/utils'

// 上传文件到知识库
export function uploadFile(data, config = {}) {
  return request({
    url: '/knowledge/upload',
    method: 'post',
    data,
    // 增加超时时间到 5 分钟，适合大文件上传
    timeout: 5 * 60 * 1000, // 5分钟
    headers: {
      'Content-Type': 'multipart/form-data'
    },
    ...config
  })
}