import useRequest from './useRequest.ts'
import useTable from './useTable.ts'
import useLocalStorage from './useLocalStorage.ts'
import usePermission from './usePermission.ts'
import useTheme from './useTheme.ts'
import useWindowSize from './useWindowSize.ts'
import useWebSocket from './useWebSocket.ts'
import useCRUD from './useCRUD.ts'

export { useRequest, useTable, useLocalStorage, usePermission, useTheme, useWindowSize, useWebSocket, useCRUD }

// 默认导出
export default {
  useRequest,
  useTable,
  useLocalStorage,
  usePermission,
  useTheme,
  useWindowSize,
  useWebSocket,
  useCRUD,
}
