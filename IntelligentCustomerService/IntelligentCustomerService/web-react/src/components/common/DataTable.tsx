import React, { useCallback, useState } from 'react'
import { Button, message, Popconfirm, Space, Table, TableColumnType, TableProps } from 'antd'
import { DeleteOutlined, EditOutlined, PlusOutlined, ReloadOutlined } from '@ant-design/icons'
import { useTranslation } from 'react-i18next'

export interface DataTableColumn<T = any> extends Omit<TableColumnType<T>, 'render'> {
  dataIndex: string
  title: string
  render?: (value: any, record: T, index: number) => React.ReactNode
  editable?: boolean
  searchable?: boolean
  sortable?: boolean
}

export interface DataTableProps<T = any> extends Omit<TableProps<T>, 'columns'> {
  columns: DataTableColumn<T>[]
  data: T[]
  loading?: boolean
  showActions?: boolean
  showAdd?: boolean
  showEdit?: boolean
  showDelete?: boolean
  showRefresh?: boolean
  onAdd?: () => void
  onEdit?: (record: T) => void
  onDelete?: (record: T) => Promise<void> | void
  onRefresh?: () => void
  actionWidth?: number
  actionFixed?: 'left' | 'right'
  deleteConfirmTitle?: string
  deleteConfirmContent?: string
}

const DataTable = <T extends Record<string, any>>(props: DataTableProps<T>): React.ReactElement => {
  const {
    columns,
    data,
    loading = false,
    showActions = true,
    showAdd = true,
    showEdit = true,
    showDelete = true,
    showRefresh = true,
    onAdd,
    onEdit,
    onDelete,
    onRefresh,
    actionWidth = 120,
    actionFixed = 'right',
    deleteConfirmTitle,
    deleteConfirmContent,
    ...tableProps
  } = props

  const { t } = useTranslation()
  const [deleteLoading, setDeleteLoading] = useState<string | null>(null)

  const handleDelete = useCallback(
    async (record: T) => {
      if (!onDelete) return

      const recordId = record.id || record.key
      setDeleteLoading(recordId)

      try {
        await onDelete(record)
        message.success(t('common.deleteSuccess'))
      } catch (error) {
        message.error(t('common.deleteFailed'))
        // console.error('Delete failed:', error)
      } finally {
        setDeleteLoading(null)
      }
    },
    [onDelete, t],
  )

  const actionColumn: DataTableColumn<T> = {
    title: t('common.actions'),
    key: 'actions',
    dataIndex: 'actions',
    width: actionWidth,
    fixed: actionFixed,
    render: (_, record) => {
      const recordId = record.id || record.key
      return (
        <Space size='small'>
          {showEdit && onEdit && (
            <Button type='link' size='small' icon={<EditOutlined />} onClick={() => onEdit(record)}>
              {t('common.edit')}
            </Button>
          )}
          {showDelete && onDelete && (
            <Popconfirm
              title={deleteConfirmTitle || t('common.deleteConfirm')}
              description={deleteConfirmContent || t('common.deleteConfirmContent')}
              onConfirm={() => handleDelete(record)}
              okText={t('common.confirm')}
              cancelText={t('common.cancel')}
            >
              <Button type='link' size='small' danger icon={<DeleteOutlined />} loading={deleteLoading === recordId}>
                {t('common.delete')}
              </Button>
            </Popconfirm>
          )}
        </Space>
      )
    },
  }

  const finalColumns = showActions ? [...columns, actionColumn] : columns

  const toolbar = (
    <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <div>
        {showAdd && onAdd && (
          <Button type='primary' icon={<PlusOutlined />} onClick={onAdd}>
            {t('common.add')}
          </Button>
        )}
      </div>
      <div>
        {showRefresh && onRefresh && (
          <Button icon={<ReloadOutlined />} onClick={onRefresh} loading={loading}>
            {t('common.refresh')}
          </Button>
        )}
      </div>
    </div>
  )

  return (
    <div className='data-table'>
      {toolbar}
      <Table<T>
        {...tableProps}
        columns={finalColumns}
        dataSource={data}
        loading={loading}
        rowKey={(record) => record.id || record.key || Math.random().toString()}
        scroll={{ x: 'max-content' }}
        pagination={{
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total, range) =>
            t('common.pagination.total', {
              start: range[0],
              end: range[1],
              total,
            }),
          ...tableProps.pagination,
        }}
      />
    </div>
  )
}

export default DataTable

// 导出类型
export type { DataTableColumn, DataTableProps }
