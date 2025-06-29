import {useCallback, useEffect, useState} from 'react'
import useRequest from './useRequest.ts'
import type {TablePaginationConfig} from 'antd/es/table'
import type {FilterValue, SorterResult} from 'antd/es/table/interface'

export interface TableParams {
  pagination: TablePaginationConfig
  filters: Record<string, FilterValue | null>
  sorter: SorterResult<Record<string, unknown>> | SorterResult<Record<string, unknown>>[]
  [key: string]: unknown
}

export interface UseTableOptions<T = any, P = any> {
  defaultPageSize?: number
  defaultCurrent?: number
  refreshDeps?: any[]
  manual?: boolean
  defaultParams?: Omit<P, 'current' | 'pageSize'>
  onSuccess?: (data: { list: T[]; total: number }, params: P) => void
  onError?: (error: Error, params: P) => void
  formatResult?: (res: any) => { list: T[]; total: number }
}

export interface UseTableResult<T = any, P = any> {
  tableProps: {
    dataSource: T[]
    loading: boolean
    pagination: TablePaginationConfig
    onChange: (
      pagination: TablePaginationConfig,
      filters: Record<string, FilterValue | null>,
      sorter: SorterResult<any> | SorterResult<any>[],
      extra: any,
    ) => void
  }
  refresh: () => Promise<{ list: T[]; total: number }>
  search: (params?: Omit<P, 'current' | 'pageSize'>) => Promise<{ list: T[]; total: number }>
  reset: () => void
  params: P
  setTableData: (data: T[]) => void
  tableData: T[]
  error: Error | null
}

/**
 * 表格数据处理Hook
 * @param service 获取表格数据的请求函数
 * @param options 配置选项
 */
function useTable<T = any, P extends Record<string, any> = any>(
  service: (params: P) => Promise<{ list: T[]; total: number }>,
  options: UseTableOptions<T, P> = {},
): UseTableResult<T, P> {
  const {
    defaultPageSize = 10,
    defaultCurrent = 1,
    refreshDeps = [],
    manual = false,
    defaultParams = {} as Omit<P, 'current' | 'pageSize'>,
    onSuccess,
    onError,
    formatResult,
  } = options

  const [tableData, setTableData] = useState<T[]>([])
  const [total, setTotal] = useState<number>(0)
  const [tableParams, setTableParams] = useState<TableParams>({
    pagination: {
      current: defaultCurrent,
      pageSize: defaultPageSize,
    },
    filters: {},
    sorter: {},
  })

  // 转换参数
  const getParams = useCallback(
    (
      pagination: TablePaginationConfig = tableParams.pagination,
      filters: Record<string, FilterValue | null> = tableParams.filters,
      sorter: SorterResult<any> | SorterResult<any>[] = tableParams.sorter,
      extraParams: Omit<P, 'current' | 'pageSize'> = defaultParams as any,
    ): P => {
      const { current = 1, pageSize = defaultPageSize } = pagination || {}

      // 处理排序参数
      const sortParams: Record<string, string> = {}
      if (sorter && 'field' in sorter && sorter.order) {
        sortParams.sortField = sorter.field as string
        sortParams.sortOrder = sorter.order
      }

      // 处理过滤参数
      const filterParams: Record<string, any> = {}
      if (filters) {
        Object.keys(filters).forEach((key) => {
          const filterValue = filters[key]
          if (filterValue !== null && filterValue !== undefined) {
            filterParams[key] = filterValue
          }
        })
      }

      // 使用类型断言解决类型不匹配问题
      return {
        current,
        pageSize,
        ...sortParams,
        ...filterParams,
        ...extraParams,
      } as unknown as P
    },
    [tableParams, defaultParams, defaultPageSize],
  )

  // 定义错误处理函数，避免undefined类型问题
  const handleError = useCallback(
    (error: Error, params: P) => {
      if (onError) {
        onError(error, params)
      }
    },
    [onError],
  )

  // 定义格式化结果函数，避免undefined类型问题
  const handleFormatResult = useCallback(
    (res: any) => {
      if (formatResult) {
        return formatResult(res)
      }
      return res
    },
    [formatResult],
  )

  // 请求数据
  const {
    data,
    loading,
    error,
    run,
    refresh: refreshRequest,
  } = useRequest<{ list: T[]; total: number }, P>(
    // 使用类型断言解决参数可选性问题
    ((params: P) => service(params)) as (params?: P) => Promise<{ list: T[]; total: number }>,
    {
      manual,
      defaultParams: getParams(),
      formatResult: handleFormatResult,
      refreshDeps,
      onSuccess: (data, params) => {
        setTableData(data.list)
        setTotal(data.total)
        onSuccess?.(data, params)
      },
      onError: handleError,
    },
  )

  // 表格变化处理
  const handleTableChange = (
    pagination: TablePaginationConfig,
    filters: Record<string, FilterValue | null>,
    sorter: SorterResult<any> | SorterResult<any>[],
  ) => {
    setTableParams({
      pagination,
      filters,
      sorter,
    })

    const params = getParams(pagination, filters, sorter)
    run(params)
  }

  // 刷新表格数据
  const refresh = useCallback(() => {
    return refreshRequest()
  }, [refreshRequest])

  // 搜索
  const search = useCallback(
    (params?: Omit<P, 'current' | 'pageSize'>) => {
      const newPagination = { ...tableParams.pagination, current: 1 }
      setTableParams((prev) => ({
        ...prev,
        pagination: newPagination,
      }))

      const searchParams = getParams(newPagination, tableParams.filters, tableParams.sorter, params || (defaultParams as any))

      return run(searchParams)
    },
    [tableParams, run, getParams, defaultParams],
  )

  // 重置表格
  const reset = useCallback(() => {
    const newPagination = {
      ...tableParams.pagination,
      current: defaultCurrent,
      pageSize: defaultPageSize,
    }

    setTableParams({
      pagination: newPagination,
      filters: {},
      sorter: {},
    })

    const params = getParams(newPagination, {}, {}, defaultParams as any)
    run(params)
  }, [tableParams, run, getParams, defaultParams, defaultCurrent, defaultPageSize])

  // 更新数据
  useEffect(() => {
    if (data) {
      setTableData(data.list)
      setTotal(data.total)
    }
  }, [data])

  // 更新分页总数
  useEffect(() => {
    setTableParams((prev) => ({
      ...prev,
      pagination: {
        ...prev.pagination,
        total,
      },
    }))
  }, [total])

  return {
    tableProps: {
      dataSource: tableData,
      loading,
      pagination: {
        ...tableParams.pagination,
        total,
        showSizeChanger: true,
        showQuickJumper: true,
      },
      onChange: handleTableChange,
    },
    refresh,
    search,
    reset,
    params: getParams(),
    setTableData,
    tableData,
    error,
  }
}

export default useTable
