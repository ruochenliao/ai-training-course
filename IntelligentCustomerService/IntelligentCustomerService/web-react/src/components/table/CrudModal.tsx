import React from 'react'
import type {FormInstance} from 'antd'
import {Button, Modal, Spin} from 'antd'
import {useTheme} from '../../contexts/ThemeContext'
import {cn} from '../../utils'

interface CrudModalProps {
  visible: boolean
  title: string
  loading?: boolean
  width?: number | string
  children: React.ReactNode
  onCancel: () => void
  onOk?: () => void
  formRef?: React.MutableRefObject<FormInstance | null>
  footer?: React.ReactNode | null
  readonly?: boolean // 是否只读模式（查看模式）
}

/**
 * CRUD模态框组件
 * 对应Vue版本的CrudModal.vue
 */
const CrudModal: React.FC<CrudModalProps> = ({
  visible,
  title,
  loading = false,
  width = 600,
  children,
  onCancel,
  onOk,
  footer,
  readonly = false,
}) => {
  const { isDark } = useTheme()

  // 默认底部按钮
  const defaultFooter = readonly
    ? [
        <Button key='cancel' onClick={onCancel}>
          关闭
        </Button>,
      ]
    : [
        <Button key='cancel' onClick={onCancel}>
          取消
        </Button>,
        <Button key='submit' type='primary' loading={loading} onClick={onOk}>
          确定
        </Button>,
      ]

  return (
    <Modal
      title={title}
      open={visible}
      onCancel={onCancel}
      width={width}
      footer={footer !== undefined ? footer : defaultFooter}
      destroyOnClose
      maskClosable={false}
      className={cn(isDark ? 'dark-modal' : '')}
    >
      <Spin spinning={loading}>
        <div className='py-4'>{children}</div>
      </Spin>
    </Modal>
  )
}

export default CrudModal
