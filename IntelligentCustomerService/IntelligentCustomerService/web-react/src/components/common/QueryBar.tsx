import React, {useCallback, useState} from 'react';
import {Button, Collapse, FormInstance} from 'antd';
import {DownOutlined, ReloadOutlined, SearchOutlined, UpOutlined} from '@ant-design/icons';
import {useTranslation} from 'react-i18next';
import DynamicForm, {DynamicFormRef, FormItemConfig} from './DynamicForm';

const { Panel } = Collapse;

export interface QueryBarProps {
  items: FormItemConfig[];
  onSearch?: (values: any) => void;
  onReset?: () => void;
  loading?: boolean;
  defaultCollapsed?: boolean;
  showCollapse?: boolean;
  columns?: number;
  searchText?: string;
  resetText?: string;
  initialValues?: Record<string, any>;
}

export interface QueryBarRef {
  form: FormInstance;
  search: () => void;
  reset: () => void;
  getFieldsValue: () => any;
  setFieldsValue: (values: any) => void;
  validateFields: () => Promise<any>;
}

const QueryBar = React.forwardRef<QueryBarRef, QueryBarProps>(
  (
    {
      items,
      onSearch,
      onReset,
      loading = false,
      defaultCollapsed = false,
      showCollapse = true,
      columns = 3,
      searchText,
      resetText,
      initialValues,
    },
    ref
  ) => {
    const { t } = useTranslation();
    const [collapsed, setCollapsed] = useState(defaultCollapsed);
    const formRef = React.useRef<DynamicFormRef>(null);

    React.useImperativeHandle(ref, () => ({
      form: formRef.current?.form!,
      search: () => handleSearch(),
      reset: () => handleReset(),
      getFieldsValue: () => formRef.current?.getFieldsValue() || {},
      setFieldsValue: (values) => formRef.current?.setFieldsValue(values),
      validateFields: () => formRef.current?.validateFields() || Promise.resolve({}),
    }));

    const handleSearch = useCallback(async () => {
      try {
        const values = await formRef.current?.validateFields();
        // 过滤掉空值
        const filteredValues = Object.keys(values || {}).reduce((acc, key) => {
          const value = values[key];
          if (value !== undefined && value !== null && value !== '') {
            acc[key] = value;
          }
          return acc;
        }, {} as any);
        
        onSearch?.(filteredValues);
      } catch (error) {
        console.error('Search validation failed:', error);
      }
    }, [onSearch]);

    const handleReset = useCallback(() => {
      formRef.current?.reset();
      onReset?.();
    }, [onReset]);

    const handleFinish = (values: any) => {
      handleSearch();
    };

    // 根据折叠状态决定显示的表单项
    const visibleItems = showCollapse && collapsed 
      ? items.slice(0, columns) 
      : items;

    const actionButtons = (
      <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
        <Button
          type="primary"
          icon={<SearchOutlined />}
          onClick={handleSearch}
          loading={loading}
        >
          {searchText || t('common.search')}
        </Button>
        <Button
          icon={<ReloadOutlined />}
          onClick={handleReset}
        >
          {resetText || t('common.reset')}
        </Button>
        {showCollapse && items.length > columns && (
          <Button
            type="link"
            icon={collapsed ? <DownOutlined /> : <UpOutlined />}
            onClick={() => setCollapsed(!collapsed)}
          >
            {collapsed ? t('common.expand') : t('common.collapse')}
          </Button>
        )}
      </div>
    );

    return (
      <div className="query-bar" style={{ 
        padding: '16px', 
        background: '#fafafa', 
        borderRadius: '6px',
        marginBottom: '16px'
      }}>
        <DynamicForm
          ref={formRef}
          items={visibleItems}
          columns={columns}
          onFinish={handleFinish}
          showSubmit={false}
          showReset={false}
          initialValues={initialValues}
        />
        
        <div style={{ 
          marginTop: '16px', 
          display: 'flex', 
          justifyContent: 'flex-end',
          borderTop: '1px solid #f0f0f0',
          paddingTop: '16px'
        }}>
          {actionButtons}
        </div>
      </div>
    );
  }
);

QueryBar.displayName = 'QueryBar';

export default QueryBar;

// 导出类型
export type { QueryBarProps, QueryBarRef };