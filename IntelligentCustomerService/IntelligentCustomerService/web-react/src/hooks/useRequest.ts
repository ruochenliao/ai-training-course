import { useCallback, useEffect, useState } from 'react'

export interface RequestOptions<T = any, P = any> {
  manual?: boolean
  defaultParams?: P
  defaultData?: T
  onSuccess?: (data: T, params: P) => void
  onError?: (error: Error, params: P) => void
  onFinally?: (params: P) => void
  formatResult?: (res: any) => T
  pollingInterval?: number
  pollingWhenHidden?: boolean
  refreshDeps?: any[]
}

export interface RequestResult<T = any, P = any> {
  data: T
  loading: boolean
  error: Error | null
  params: P | undefined
  run: (params?: P) => Promise<T>
  refresh: () => Promise<T>
  mutate: (data: T | ((oldData: T) => T)) => void
  cancel: () => void
}

/**
 * 通用请求Hook
 * @param service 请求函数
 * @param options 配置选项
 */
function useRequest<T = any, P = any>(service: (params?: P) => Promise<T>, options: RequestOptions<T, P> = {}): RequestResult<T, P> {
  const {
    manual = false,
    defaultParams,
    defaultData,
    onSuccess,
    onError,
    onFinally,
    formatResult = (res: any) => res,
    pollingInterval = 0,
    pollingWhenHidden = true,
    refreshDeps = [],
  } = options

  const [data, setData] = useState<T>(defaultData as T)
  const [loading, setLoading] = useState(!manual)
  const [error, setError] = useState<Error | null>(null)
  const [params, setParams] = useState<P | undefined>(defaultParams)
  const [pollingTimer, setPollingTimer] = useState<NodeJS.Timeout | null>(null)

  // 取消轮询
  const clearPollingTimer = useCallback(() => {
    if (pollingTimer) {
      clearTimeout(pollingTimer)
      setPollingTimer(null)
    }
  }, [pollingTimer])

  // 取消请求（实际上只是取消轮询和loading状态）
  const cancel = useCallback(() => {
    clearPollingTimer()
    setLoading(false)
  }, [clearPollingTimer])

  // 执行请求
  const run = useCallback(
    async (runParams?: P): Promise<T> => {
      setLoading(true)
      setError(null)

      const finalParams = runParams !== undefined ? runParams : params
      setParams(finalParams)

      try {
        const res = await service(finalParams)
        const formattedResult = formatResult(res) as T
        setData(formattedResult)
        onSuccess?.(formattedResult, finalParams as P)

        // 设置轮询
        if (pollingInterval > 0) {
          clearPollingTimer()
          const timer = setTimeout(() => {
            // 如果配置了pollingWhenHidden为false且页面隐藏，则不执行轮询
            if (!pollingWhenHidden && document.visibilityState === 'hidden') {
              return
            }
            run(finalParams)
          }, pollingInterval)

          setPollingTimer(timer)
        }

        return formattedResult
      } catch (err) {
        const error = err instanceof Error ? err : new Error(String(err))
        setError(error)
        onError?.(error, finalParams as P)
        throw error
      } finally {
        setLoading(false)
        onFinally?.(finalParams as P)
      }
    },
    [params, service, formatResult, onSuccess, onError, onFinally, pollingInterval, pollingWhenHidden, clearPollingTimer],
  )

  // 刷新请求（使用上一次的参数）
  const refresh = useCallback(() => {
    return run(params)
  }, [run, params])

  // 直接修改数据
  const mutate = useCallback((mutateData: T | ((oldData: T) => T)) => {
    if (typeof mutateData === 'function') {
      setData((oldData) => (mutateData as (oldData: T) => T)(oldData))
    } else {
      setData(mutateData)
    }
  }, [])

  // 初始化请求
  useEffect(() => {
    if (!manual) {
      run(defaultParams)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // 根据依赖项刷新
  useEffect(() => {
    if (!manual && refreshDeps.length > 0) {
      refresh()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...refreshDeps])

  // 组件卸载时清除轮询
  useEffect(() => {
    return () => {
      clearPollingTimer()
    }
  }, [clearPollingTimer])

  return {
    data,
    loading,
    error,
    params,
    run,
    refresh,
    mutate,
    cancel,
  }
}

export default useRequest
