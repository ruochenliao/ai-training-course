import { isNullOrUndef } from '@/utils'

export function setupMessage(NMessage) {
  let loadingMessage = null
  class Message {
    /**
     * 规则：
     * * loading message只显示一个，新的message会替换正在显示的loading message
     * * loading message不会自动清除，除非被替换成非loading message，非loading message默认2秒后自动清除
     */

    removeMessage(message = loadingMessage, duration = 2000) {
      setTimeout(() => {
        if (message) {
          message.destroy()
          message = null
        }
      }, duration)
    }

    showMessage(type, content, option = {}) {
      // 处理传入的内容是对象的情况
      let messageContent = content;
      let messageOption = option;

      // 如果content是对象且包含content属性，则将其分解为内容和选项
      if (typeof content === 'object' && content !== null && 'content' in content) {
        messageContent = content.content;
        // 合并content中的其他选项到option中
        messageOption = { ...option, ...content };
        // 避免重复的content属性
        delete messageOption.content;
      }

      if (loadingMessage && loadingMessage.type === 'loading') {
        // 如果存在则替换正在显示的loading message
        loadingMessage.type = type;
        loadingMessage.content = messageContent;

        if (type !== 'loading') {
          // 非loading message需设置自动清除
          this.removeMessage(loadingMessage, messageOption.duration);
        }
      } else {
        // 不存在正在显示的loading则新建一个message,如果新建的message是loading message则将message赋值存储下来
        let message = NMessage[type](messageContent, messageOption);
        if (type === 'loading') {
          loadingMessage = message;
        }
      }
    }

    loading(content) {
      this.showMessage('loading', content, { duration: 0 })
    }

    success(content, option = {}) {
      this.showMessage('success', content, option)
    }

    error(content, option = {}) {
      this.showMessage('error', content, option)
    }

    info(content, option = {}) {
      this.showMessage('info', content, option)
    }

    warning(content, option = {}) {
      this.showMessage('warning', content, option)
    }
  }

  return new Message()
}

export function setupDialog(NDialog) {
  NDialog.confirm = function (option = {}) {
    const showIcon = !isNullOrUndef(option.title)
    return NDialog[option.type || 'warning']({
      showIcon,
      positiveText: '确定',
      negativeText: '取消',
      onPositiveClick: option.confirm,
      onNegativeClick: option.cancel,
      onMaskClick: option.cancel,
      ...option,
    })
  }

  return NDialog
}
