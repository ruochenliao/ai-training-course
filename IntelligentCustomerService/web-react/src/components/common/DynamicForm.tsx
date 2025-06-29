import React, {forwardRef, useImperativeHandle} from 'react'
import {
    Button,
    Checkbox,
    DatePicker,
    Form,
    FormInstance,
    FormProps,
    Input,
    InputNumber,
    Radio,
    Select,
    Switch,
    TimePicker,
    Upload
} from 'antd'
import {UploadOutlined} from '@ant-design/icons'
import {useTranslation} from 'react-i18next'
import {Rule} from 'antd/es/form'

const { TextArea } = Input
const { Option } = Select
const { RangePicker } = DatePicker

export type FormItemType =
  | 'input'
  | 'password'
  | 'textarea'
  | 'number'
  | 'select'
  | 'multiSelect'
  | 'date'
  | 'dateRange'
  | 'time'
  | 'switch'
  | 'radio'
  | 'checkbox'
  | 'upload'
  | 'custom'

export interface FormItemOption {
  label: string
  value: any
  disabled?: boolean
}

export interface FormItemConfig {
  name: string
  label: string
  type: FormItemType
  required?: boolean
  rules?: Rule[]
  placeholder?: string
  options?: FormItemOption[]
  disabled?: boolean
  hidden?: boolean
  span?: number // Grid span (1-24)
  props?: Record<string, any> // Additional props for the form item
  render?: (value: any, form: FormInstance) => React.ReactNode // Custom render function
}

export interface DynamicFormProps extends Omit<FormProps, 'children'> {
  items: FormItemConfig[]
  columns?: number // Number of columns (1-4)
  onFinish?: (values: any) => void
  onFinishFailed?: (errorInfo: any) => void
  submitText?: string
  resetText?: string
  showSubmit?: boolean
  showReset?: boolean
  loading?: boolean
}

export interface DynamicFormRef {
  form: FormInstance
  submit: () => void
  reset: () => void
  getFieldsValue: () => any
  setFieldsValue: (values: any) => void
  validateFields: () => Promise<any>
}

const DynamicForm = forwardRef<DynamicFormRef, DynamicFormProps>(
  (
    { items, columns = 1, onFinish, onFinishFailed, submitText, resetText, showSubmit = true, showReset = true, loading = false, ...formProps },
    ref,
  ) => {
    const { t } = useTranslation()
    const [form] = Form.useForm()

    useImperativeHandle(ref, () => ({
      form,
      submit: () => form.submit(),
      reset: () => form.resetFields(),
      getFieldsValue: () => form.getFieldsValue(),
      setFieldsValue: (values) => form.setFieldsValue(values),
      validateFields: () => form.validateFields(),
    }))

    const getSpan = (itemSpan?: number) => {
      if (itemSpan) return itemSpan
      return Math.floor(24 / columns)
    }

    const renderFormItem = (item: FormItemConfig) => {
      const { type, options = [], props = {} } = item

      switch (type) {
        case 'input':
          return <Input placeholder={item.placeholder} {...props} />

        case 'password':
          return <Input.Password placeholder={item.placeholder} {...props} />

        case 'textarea':
          return <TextArea placeholder={item.placeholder} rows={4} {...props} />

        case 'number':
          return <InputNumber placeholder={item.placeholder} style={{ width: '100%' }} {...props} />

        case 'select':
          return (
            <Select placeholder={item.placeholder} {...props}>
              {options.map((option) => (
                <Option key={option.value} value={option.value} disabled={option.disabled}>
                  {option.label}
                </Option>
              ))}
            </Select>
          )

        case 'multiSelect':
          return (
            <Select mode='multiple' placeholder={item.placeholder} {...props}>
              {options.map((option) => (
                <Option key={option.value} value={option.value} disabled={option.disabled}>
                  {option.label}
                </Option>
              ))}
            </Select>
          )

        case 'date':
          return <DatePicker style={{ width: '100%' }} {...props} />

        case 'dateRange':
          return <RangePicker style={{ width: '100%' }} {...props} />

        case 'time':
          return <TimePicker style={{ width: '100%' }} {...props} />

        case 'switch':
          return <Switch {...props} />

        case 'radio':
          return (
            <Radio.Group {...props}>
              {options.map((option) => (
                <Radio key={option.value} value={option.value} disabled={option.disabled}>
                  {option.label}
                </Radio>
              ))}
            </Radio.Group>
          )

        case 'checkbox':
          return (
            <Checkbox.Group {...props}>
              {options.map((option) => (
                <Checkbox key={option.value} value={option.value} disabled={option.disabled}>
                  {option.label}
                </Checkbox>
              ))}
            </Checkbox.Group>
          )

        case 'upload':
          return (
            <Upload {...props}>
              <Button icon={<UploadOutlined />}>{t('common.upload')}</Button>
            </Upload>
          )

        case 'custom':
          return item.render ? item.render(form.getFieldValue(item.name), form) : null

        default:
          return <Input placeholder={item.placeholder} {...props} />
      }
    }

    const getRules = (item: FormItemConfig): Rule[] => {
      const rules: Rule[] = []

      if (item.required) {
        rules.push({
          required: true,
          message: t('form.required', { field: item.label }),
        })
      }

      if (item.rules) {
        rules.push(...item.rules)
      }

      return rules
    }

    return (
      <Form {...formProps} form={form} layout='vertical' onFinish={onFinish} onFinishFailed={onFinishFailed}>
        <div className='dynamic-form-grid' style={{ display: 'flex', flexWrap: 'wrap', gap: '16px' }}>
          {items
            .filter((item) => !item.hidden)
            .map((item) => (
              <div
                key={item.name}
                style={{
                  flex: `0 0 calc(${(getSpan(item.span) / 24) * 100}% - 8px)`,
                  minWidth: 0,
                }}
              >
                <Form.Item name={item.name} label={item.label} rules={getRules(item)} hidden={item.hidden}>
                  {renderFormItem(item)}
                </Form.Item>
              </div>
            ))}
        </div>

        {(showSubmit || showReset) && (
          <Form.Item style={{ marginTop: 24 }}>
            <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
              {showReset && <Button onClick={() => form.resetFields()}>{resetText || t('common.reset')}</Button>}
              {showSubmit && (
                <Button type='primary' htmlType='submit' loading={loading}>
                  {submitText || t('common.submit')}
                </Button>
              )}
            </div>
          </Form.Item>
        )}
      </Form>
    )
  },
)

DynamicForm.displayName = 'DynamicForm'

export default DynamicForm

// 导出类型
export type { FormItemConfig, FormItemOption, DynamicFormProps, DynamicFormRef }
