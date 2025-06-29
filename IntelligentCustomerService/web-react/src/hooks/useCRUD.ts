import {useCallback, useRef, useState} from 'react'
import type {FormInstance} from 'antd'
import {message} from 'antd'

// 操作类型定义
type ActionType = 'view' | 'edit' | 'add'

// 操作标题映射
const ACTIONS: Record<ActionType, string> = {
  view: '查看',
  edit: '编辑',
  add: '新增',
}

// useCRUD Hook 参数类型
interface UseCRUDOptions<T = any> {
  name: string
  initForm?: T
  doCreate?: (data: T) => Promise<any>
  doDelete?: (params: any) => Promise<any>
  doUpdate?: (data: T) => Promise<any>
  refresh?: (data?: any) => void
}

// useCRUD Hook 返回类型
interface UseCRUDReturn<T = any> {
  modalVisible: boolean
  modalAction: ActionType | ''
  modalTitle: string
  modalLoading: boolean
  modalForm: T
  modalFormRef: React.MutableRefObject<FormInstance | null>
  handleAdd: () => void
  handleEdit: (row: T) => void
  handleView: (row: T) => void
  handleSave: (...callbacks: Array<() => void>) => Promise<void>
  handleDelete: (params?: any) => Promise<void>
  setModalVisible: (visible: boolean) => void
  setModalForm: (form: T) => void
}

/**
 * CRUD操作的通用Hook
 * 对应Vue版本的useCRUD组合式函数
 */
export function useCRUD<T = any>(options: UseCRUDOptions<T>): UseCRUDReturn<T> {
  const { name, initForm = {} as T, doCreate, doDelete, doUpdate, refresh } = options

  // 状态管理
  const [modalVisible, setModalVisible] = useState(false)
  const [modalAction, setModalAction] = useState<ActionType | ''>('')
  const [modalLoading, setModalLoading] = useState(false)
  const [modalForm, setModalForm] = useState<T>({ ...initForm })
  const modalFormRef = useRef<FormInstance | null>(null)

  // 计算模态框标题
  const modalTitle = modalAction ? `${ACTIONS[modalAction as ActionType]}${name}` : ''

  // 新增操作
  const handleAdd = useCallback(() => {
    setModalAction('add')
    setModalVisible(true)
    setModalForm({ ...initForm })
  }, [initForm])

  // 编辑操作
  const handleEdit = useCallback((row: T) => {
    setModalAction('edit')
    setModalVisible(true)
    setModalForm({ ...row })
  }, [])

  // 查看操作
  const handleView = useCallback((row: T) => {
    setModalAction('view')
    setModalVisible(true)
    setModalForm({ ...row })
  }, [])

  // 保存操作
  const handleSave = useCallback(
    async (...callbacks: Array<() => void>) => {
      if (!['edit', 'add'].includes(modalAction)) {
        setModalVisible(false)
        return
      }

      if (!modalFormRef.current) {
        return
      }

      try {
        // 表单验证
        await modalFormRef.current.validateFields()

        const actions = {
          add: {
            api: () => doCreate?.(modalForm),
            cb: () => {
              callbacks.forEach((callback) => callback && callback())
            },
            msg: () => message.success('新增成功'),
          },
          edit: {
            api: () => doUpdate?.(modalForm),
            cb: () => {
              callbacks.forEach((callback) => callback && callback())
            },
            msg: () => message.success('编辑成功'),
          },
        }

        const action = actions[modalAction as 'add' | 'edit']

        try {
          setModalLoading(true)
          const data = await action.api()
          action.cb()
          action.msg()
          setModalLoading(false)
          setModalVisible(false)
          data && refresh?.(data)
        } catch (error) {
          setModalLoading(false)
          throw error
        }
      } catch (error) {
        // 表单验证失败或API调用失败
        console.error('保存失败:', error)
      }
    },
    [modalAction, modalForm, doCreate, doUpdate, refresh],
  )

  // 删除操作
  const handleDelete = useCallback(
    async (params?: any) => {
      if (!params || (typeof params === 'object' && Object.keys(params).length === 0)) {
        return
      }

      try {
        setModalLoading(true)
        const data = await doDelete?.(params)
        message.success('删除成功')
        setModalLoading(false)
        refresh?.(data)
      } catch (error) {
        setModalLoading(false)
        throw error
      }
    },
    [doDelete, refresh],
  )

  return {
    modalVisible,
    modalAction,
    modalTitle,
    modalLoading,
    modalForm,
    modalFormRef,
    handleAdd,
    handleEdit,
    handleView,
    handleSave,
    handleDelete,
    setModalVisible,
    setModalForm,
  }
}

export default useCRUD
