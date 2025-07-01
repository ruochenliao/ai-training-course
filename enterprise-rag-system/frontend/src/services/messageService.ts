// 消息服务 - 解决在非组件中使用 message 的问题

import type { MessageInstance } from 'antd/es/message/interface'

class MessageService {
  private messageApi: MessageInstance | null = null

  // 设置 message API 实例
  setMessageApi(api: MessageInstance) {
    this.messageApi = api
  }

  // 成功消息
  success(content: string, duration?: number) {
    if (this.messageApi) {
      this.messageApi.success(content, duration)
    } else {
      console.log('Success:', content)
    }
  }

  // 错误消息
  error(content: string, duration?: number) {
    if (this.messageApi) {
      this.messageApi.error(content, duration)
    } else {
      console.error('Error:', content)
    }
  }

  // 警告消息
  warning(content: string, duration?: number) {
    if (this.messageApi) {
      this.messageApi.warning(content, duration)
    } else {
      console.warn('Warning:', content)
    }
  }

  // 信息消息
  info(content: string, duration?: number) {
    if (this.messageApi) {
      this.messageApi.info(content, duration)
    } else {
      console.info('Info:', content)
    }
  }

  // 加载消息
  loading(content: string, duration?: number) {
    if (this.messageApi) {
      return this.messageApi.loading(content, duration)
    } else {
      console.log('Loading:', content)
      return () => {}
    }
  }

  // 销毁所有消息
  destroy() {
    if (this.messageApi) {
      this.messageApi.destroy()
    }
  }
}

// 导出单例实例
export const messageService = new MessageService()
