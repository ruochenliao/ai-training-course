import React, { useState, useEffect, useCallback, useImperativeHandle, forwardRef } from 'react';
import { Table, TableProps, Pagination, Spin } from 'antd';
import { useTranslation } from 'react-i18next';
import QueryBar from '../common/QueryBar';

interface CrudTableProps extends Omit<TableProps<any>, 'dataSource' | 'pagination'> {
  // 对应Vue版本的props
  remote?: boolean; // true: 后端分页  false: 前端分页
  isPagination?: boolean; // 是否分页
  scrollX?: number;
  rowKey?: string;
  columns: any[];
  queryItems?: Record<string, any>; // queryBar中的参数
  extraParams?: Record<string, any>; // 补充参数
  getData: (params: any) => Promise<{ data: any[]; total?: number }>; // 获取数据的函数
  
  // 事件回调
  onQueryItemsChange?: (queryItems: Record<string, any>) => void;
  onChecked?: (rowKeys: React.Key[]) => void;
  onDataChange?: (data: any[]) => void;
  
  // 查询栏
  queryBarSlot?: React.ReactNode;
}

export interface CrudTableRef {
  handleSearch: () => void;
  handleReset: () => void;
  tableData: any[];
}

/**
 * CRUD表格组件
 * 对应Vue版本的CrudTable.vue
 */
const CrudTable = forwardRef<CrudTableRef, CrudTableProps>(({
  remote = true,
  isPagination = true,
  scrollX = 450,
  rowKey = 'id',
  columns,
  queryItems = {},
  extraParams = {},
  getData,
  onQueryItemsChange,
  onChecked,
  onDataChange,
  queryBarSlot,
  ...tableProps
}, ref) => {
  const { t } = useTranslation();
  
  // 状态管理
  const [loading, setLoading] = useState(false);
  const [tableData, setTableData] = useState<any[]>([]);
  const [initQuery] = useState({ ...queryItems });
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0,
    pageSizeOptions: ['10', '20', '50', '100'],
    showSizeChanger: true,
    showQuickJumper: true,
    showTotal: (total: number, range: [number, number]) => 
      `共 ${total} 条`,
  });

  // 查询数据
  const handleQuery = useCallback(async () => {
    try {
      setLoading(true);
      let paginationParams = {};
      
      // 如果非分页模式或者使用前端分页,则无需传分页参数
      if (isPagination && remote) {
        paginationParams = { 
          page: pagination.current, 
          page_size: pagination.pageSize 
        };
      }
      
      const response = await getData({
        ...queryItems,
        ...extraParams,
        ...paginationParams,
      });
      
      setTableData(response.data || []);
      setPagination(prev => ({
        ...prev,
        total: response.total || 0,
      }));
      
      onDataChange?.(response.data || []);
    } catch (error) {
      console.error('查询数据失败:', error);
      setTableData([]);
      setPagination(prev => ({ ...prev, total: 0 }));
      onDataChange?.([]);
    } finally {
      setLoading(false);
    }
  }, [queryItems, extraParams, pagination.current, pagination.pageSize, isPagination, remote, getData, onDataChange]);

  // 搜索
  const handleSearch = useCallback(() => {
    setPagination(prev => ({ ...prev, current: 1 }));
    handleQuery();
  }, [handleQuery]);

  // 重置
  const handleReset = useCallback(() => {
    const resetQueryItems = { ...queryItems };
    for (const key in resetQueryItems) {
      resetQueryItems[key] = null;
    }
    onQueryItemsChange?.({ ...resetQueryItems, ...initQuery });
    
    // 等待状态更新后再查询
    setTimeout(() => {
      setPagination(prev => ({ ...prev, current: 1 }));
      handleQuery();
    }, 0);
  }, [queryItems, initQuery, onQueryItemsChange, handleQuery]);

  // 分页变化
  const onPageChange = useCallback((page: number, pageSize?: number) => {
    setPagination(prev => ({
      ...prev,
      current: page,
      pageSize: pageSize || prev.pageSize,
    }));
    
    if (remote) {
      handleQuery();
    }
  }, [remote, handleQuery]);

  // 选择变化
  const onRowSelectionChange = useCallback((selectedRowKeys: React.Key[]) => {
    if (columns.some((item: any) => item.type === 'selection')) {
      onChecked?.(selectedRowKeys);
    }
  }, [columns, onChecked]);

  // 初始化数据
  useEffect(() => {
    handleQuery();
  }, []);

  // 暴露方法给父组件
  useImperativeHandle(ref, () => ({
    handleSearch,
    handleReset,
    tableData,
  }), [handleSearch, handleReset, tableData]);

  return (
    <div>
      {/* 查询栏 */}
      {queryBarSlot && (
        <div className="mb-6">
          <QueryBar onSearch={handleSearch} onReset={handleReset}>
            {queryBarSlot}
          </QueryBar>
        </div>
      )}

      {/* 数据表格 */}
      <Spin spinning={loading}>
        <Table
          {...tableProps}
          columns={columns}
          dataSource={tableData}
          rowKey={rowKey}
          scroll={{ x: scrollX }}
          pagination={isPagination ? {
            ...pagination,
            onChange: onPageChange,
            onShowSizeChange: onPageChange,
          } : false}
          rowSelection={columns.some((item: any) => item.type === 'selection') ? {
            onChange: onRowSelectionChange,
          } : undefined}
        />
      </Spin>
    </div>
  );
});

CrudTable.displayName = 'CrudTable';

export default CrudTable;
