import React, {forwardRef, useEffect, useImperativeHandle} from 'react'
import {Modal, ModalProps} from 'antd'
import {useTranslation} from 'react-i18next'
import DynamicForm, {DynamicFormProps, DynamicFormRef, FormItemConfig} from './DynamicForm.tsx'

export interface ModalFormProps extends Omit<ModalProps, 'onOk' | 'onCancel'> {
  formItems: FormItemConfig[]
  formProps?: Omit<DynamicFormProps, 'items' | 'onFinish' | 'showSubmit' | 'showReset'>
  initialValues?: Record<string, any>
  onSubmit?: (values: any) => Promise<void> | void
  onCancel?: () => void
  submitText?: string
  cancelText?: string
  loading?: boolean
  destroyOnClose?: boolean
}

export interface ModalFormRef {
  open: (initialValues?: Record<string, any>) => void
  close: () => void
  submit: () => void
  reset: () => void
  getFieldsValue: () => any
  setFieldsValue: (values: any) => void
  validateFields: () => Promise<any>
}

const ModalForm = forwardRef<ModalFormRef, ModalFormProps>(
  (
    { formItems, formProps, initialValues, onSubmit, onCancel, submitText, cancelText, loading = false, destroyOnClose = true, ...modalProps },
    ref,
  ) => {
    const { t } = useTranslation()
    const [visible, setVisible] = React.useState(false)
    const [submitLoading, setSubmitLoading] = React.useState(false)
    const formRef = React.useRef<DynamicFormRef>(null)

    useImperativeHandle(ref, () => ({
      open: (values?: Record<string, any>) => {
        setVisible(true)
        if (values && formRef.current) {
          setTimeout(() => {
            formRef.current?.setFieldsValue(values)
          }, 100)
        }
      },
      close: () => {
        setVisible(false)
        if (destroyOnClose) {
          formRef.current?.reset()
        }
      },
      submit: () => formRef.current?.submit(),
      reset: () => formRef.current?.reset(),
      getFieldsValue: () => formRef.current?.getFieldsValue() || {},
      setFieldsValue: (values) => formRef.current?.setFieldsValue(values),
      validateFields: () => formRef.current?.validateFields() || Promise.resolve({}),
    }))

    useEffect(() => {
      if (visible && initialValues && formRef.current) {
        formRef.current.setFieldsValue(initialValues)
      }
    }, [visible, initialValues])

    const handleSubmit = async (values: any) => {
      if (!onSubmit) return

      setSubmitLoading(true)
      try {
        await onSubmit(values)
        setVisible(false)
        if (destroyOnClose) {
          formRef.current?.reset()
        }
      } catch (error) {
        console.error('Form submit failed:', error)
      } finally {
        setSubmitLoading(false)
      }
    }

    const handleCancel = () => {
      setVisible(false)
      if (destroyOnClose) {
        formRef.current?.reset()
      }
      onCancel?.()
    }

    return (
      <Modal {...modalProps} open={visible} onCancel={handleCancel} footer={null} destroyOnClose={destroyOnClose}>
        <DynamicForm
          {...formProps}
          ref={formRef}
          items={formItems}
          onFinish={handleSubmit}
          submitText={submitText || t('common.submit')}
          resetText={cancelText || t('common.cancel')}
          loading={submitLoading || loading}
          showSubmit={true}
          showReset={true}
        />
      </Modal>
    )
  },
)

ModalForm.displayName = 'ModalForm'

export default ModalForm

// 导出类型
export type { ModalFormProps, ModalFormRef }
