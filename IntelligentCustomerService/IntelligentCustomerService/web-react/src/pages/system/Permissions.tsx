import React, { useState, useRef } from 'react';
import {
  Card,
  Button,
  Space,
  Tag,
  Switch,
  Dropdown,
  Modal,
  message,
  Tree,
  Typography,
  Tooltip,
  Row,
  Col,
  Divider,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  MoreOutlined,
  SafetyOutlined,
  ApiOutlined,
  MenuOutlined,
  ControlOutlined,
  EyeOutlined,
  CopyOutlined,
  ExpandAltOutlined,
  CompressOutlined,
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { DataTable } from '../../components/common/DataTable';
import { ModalForm } from '../../components/common/ModalForm';
import { QueryBar } from '../../components/common/QueryBar';
import { useRequest } from '../../hooks/useRequest';
import { permissionApi } from '../../api/permission';
import type { FormField } from '../../components/common/DynamicForm';
import type { ModalFormRef } from '../../components/common/ModalForm';
import type { QueryBarRef } from '../../components/common/QueryBar';
import type { DataNode } from 'antd/es/tree';

const { Text, Title } = Typography;

// 权限接口
interface Permission {
  id: string;
  name: string;
  displayName: string;
  description?: string;
  type: 'menu' | 'button' | 'api';
  path?: string;
  method?: string;
  icon?: string;
  sort: number;
  status: 'active' | 'inactive';
  parentId?: string;
  children?: Permission[];
  level: number;
  isSystem: boolean;
  createdAt: string;
  updatedAt: string;
}

const Permissions: React.FC = () => {
  const { t } = useTranslation();
  const [selectedRowKeys, setSelectedRowKeys] = useState<string[]>([]);
  const [viewMode, setViewMode] = useState<'table' | 'tree'>('table');
  const [expandedKeys, setExpandedKeys] = useState<string[]>([]);
  const [selectedPermission, setSelectedPermission] = useState<Permission | null>(null);
  const modalFormRef = useRef<ModalFormRef>(null);
  const queryBarRef = useRef<QueryBarRef>(null);

  // 获取权限列表
  const {
    data: permissionsData,
    loading: permissionsLoading,
    error: permissionsError,
    run: fetchPermissions,
  } = useRequest(permissionApi.getPermissions, {
    defaultParams: [{ page: 1, pageSize: 10 }],
  });

  // 获取权限树
  const {
    data: permissionTree = [],
    loading: treeLoading,
    run: fetchPermissionTree,
  } = useRequest(permissionApi.getPermissionTree, {
    defaultRun: true,
  });

  // 创建权限
  const { loading: creating, run: createPermission } = useRequest(
    permissionApi.createPermission,
    {
      manual: true,
      onSuccess: () => {
        message.success(t('permissions.createSuccess'));
        modalFormRef.current?.close();
        fetchPermissions();
        fetchPermissionTree();
      },
    }
  );

  // 更新权限
  const { loading: updating, run: updatePermission } = useRequest(
    permissionApi.updatePermission,
    {
      manual: true,
      onSuccess: () => {
        message.success(t('permissions.updateSuccess'));
        modalFormRef.current?.close();
        fetchPermissions();
        fetchPermissionTree();
      },
    }
  );

  // 删除权限
  const { loading: deleting, run: deletePermission } = useRequest(
    permissionApi.deletePermission,
    {
      manual: true,
      onSuccess: () => {
        message.success(t('permissions.deleteSuccess'));
        fetchPermissions();
        fetchPermissionTree();
      },
    }
  );

  // 批量删除权限
  const { loading: batchDeleting, run: batchDeletePermissions } = useRequest(
    permissionApi.batchDeletePermissions,
    {
      manual: true,
      onSuccess: () => {
        message.success(t('permissions.batchDeleteSuccess'));
        setSelectedRowKeys([]);
        fetchPermissions();
        fetchPermissionTree();
      },
    }
  );

  // 切换权限状态
  const { loading: toggling, run: togglePermissionStatus } = useRequest(
    permissionApi.togglePermissionStatus,
    {
      manual: true,
      onSuccess: () => {
        message.success(t('permissions.statusUpdateSuccess'));
        fetchPermissions();
        fetchPermissionTree();
      },
    }
  );

  // 复制权限
  const { loading: copying, run: copyPermission } = useRequest(
    permissionApi.copyPermission,
    {
      manual: true,
      onSuccess: () => {
        message.success(t('permissions.copySuccess'));
        fetchPermissions();
        fetchPermissionTree();
      },
    }
  );

  // 查询字段配置
  const queryFields: FormField[] = [
    {
      name: 'keyword',
      label: t('permissions.keyword'),
      type: 'input',
      placeholder: t('permissions.keywordPlaceholder'),
      colProps: { span: 6 },
    },
    {
      name: 'type',
      label: t('permissions.type'),
      type: 'select',
      options: [
        { label: t('permissions.typeMenu'), value: 'menu' },
        { label: t('permissions.typeButton'), value: 'button' },
        { label: t('permissions.typeApi'), value: 'api' },
      ],
      colProps: { span: 4 },
    },
    {
      name: 'status',
      label: t('permissions.status'),
      type: 'select',
      options: [
        { label: t('permissions.statusActive'), value: 'active' },
        { label: t('permissions.statusInactive'), value: 'inactive' },
      ],
      colProps: { span: 4 },
    },
    {
      name: 'parentId',
      label: t('permissions.parent'),
      type: 'treeSelect',
      treeData: convertToTreeSelectData(permissionTree),
      placeholder: t('permissions.parentPlaceholder'),
      colProps: { span: 6 },
    },
  ];

  // 表单字段配置
  const getFormFields = (mode: string): FormField[] => [
    {
      name: 'name',
      label: t('permissions.name'),
      type: 'input',
      required: true,
      rules: [
        { required: true, message: t('permissions.nameRequired') },
        { min: 2, max: 50, message: t('permissions.nameLength') },
        { pattern: /^[a-zA-Z0-9_:]+$/, message: t('permissions.namePattern') },
      ],
      colProps: { span: 12 },
    },
    {
      name: 'displayName',
      label: t('permissions.displayName'),
      type: 'input',
      required: true,
      rules: [
        { required: true, message: t('permissions.displayNameRequired') },
        { min: 2, max: 50, message: t('permissions.displayNameLength') },
      ],
      colProps: { span: 12 },
    },
    {
      name: 'type',
      label: t('permissions.type'),
      type: 'select',
      required: true,
      options: [
        { label: t('permissions.typeMenu'), value: 'menu' },
        { label: t('permissions.typeButton'), value: 'button' },
        { label: t('permissions.typeApi'), value: 'api' },
      ],
      colProps: { span: 8 },
    },
    {
      name: 'parentId',
      label: t('permissions.parent'),
      type: 'treeSelect',
      treeData: convertToTreeSelectData(permissionTree),
      placeholder: t('permissions.parentPlaceholder'),
      colProps: { span: 8 },
    },
    {
      name: 'sort',
      label: t('permissions.sort'),
      type: 'number',
      defaultValue: 0,
      colProps: { span: 8 },
    },
    {
      name: 'path',
      label: t('permissions.path'),
      type: 'input',
      placeholder: t('permissions.pathPlaceholder'),
      colProps: { span: 12 },
      dependencies: ['type'],
      visible: (values) => values.type === 'menu' || values.type === 'api',
    },
    {
      name: 'method',
      label: t('permissions.method'),
      type: 'select',
      options: [
        { label: 'GET', value: 'GET' },
        { label: 'POST', value: 'POST' },
        { label: 'PUT', value: 'PUT' },
        { label: 'DELETE', value: 'DELETE' },
        { label: 'PATCH', value: 'PATCH' },
      ],
      colProps: { span: 12 },
      dependencies: ['type'],
      visible: (values) => values.type === 'api',
    },
    {
      name: 'icon',
      label: t('permissions.icon'),
      type: 'input',
      placeholder: t('permissions.iconPlaceholder'),
      colProps: { span: 12 },
      dependencies: ['type'],
      visible: (values) => values.type === 'menu',
    },
    {
      name: 'description',
      label: t('permissions.description'),
      type: 'textarea',
      colProps: { span: 24 },
    },
    {
      name: 'status',
      label: t('permissions.status'),
      type: 'select',
      options: [
        { label: t('permissions.statusActive'), value: 'active' },
        { label: t('permissions.statusInactive'), value: 'inactive' },
      ],
      defaultValue: 'active',
      colProps: { span: 12 },
    },
  ];

  // 转换为树选择数据
  function convertToTreeSelectData(permissions: Permission[]): any[] {
    return permissions.map(permission => ({
      title: permission.displayName,
      value: permission.id,
      children: permission.children ? convertToTreeSelectData(permission.children) : undefined,
    }));
  }

  // 转换权限数据为树形结构
  const convertPermissionsToTree = (permissions: Permission[]): DataNode[] => {
    return permissions.map(permission => ({
      key: permission.id,
      title: (
        <Space>
          {getPermissionIcon(permission.type)}
          <Text strong={permission.type === 'menu'}>{permission.displayName}</Text>
          <Tag size="small" color={getPermissionTypeColor(permission.type)}>
            {t(`permissions.type${permission.type.charAt(0).toUpperCase() + permission.type.slice(1)}`)}
          </Tag>
          {permission.status === 'inactive' && (
            <Tag size="small" color="red">
              {t('permissions.statusInactive')}
            </Tag>
          )}
          {permission.isSystem && (
            <Tag size="small" color="orange">
              {t('permissions.system')}
            </Tag>
          )}
        </Space>
      ),
      children: permission.children ? convertPermissionsToTree(permission.children) : undefined,
    }));
  };

  // 获取权限类型图标
  const getPermissionIcon = (type: string) => {
    switch (type) {
      case 'menu':
        return <MenuOutlined style={{ color: '#1890ff' }} />;
      case 'button':
        return <ControlOutlined style={{ color: '#52c41a' }} />;
      case 'api':
        return <ApiOutlined style={{ color: '#fa8c16' }} />;
      default:
        return <SafetyOutlined />;
    }
  };

  // 获取权限类型颜色
  const getPermissionTypeColor = (type: string) => {
    switch (type) {
      case 'menu':
        return 'blue';
      case 'button':
        return 'green';
      case 'api':
        return 'orange';
      default:
        return 'default';
    }
  };

  // 表格列配置
  const columns = [
    {
      title: t('permissions.name'),
      dataIndex: 'name',
      key: 'name',
      sorter: true,
      render: (name: string, record: Permission) => (
        <Space>
          {getPermissionIcon(record.type)}
          <Text code>{name}</Text>
          {record.isSystem && (
            <Tooltip title={t('permissions.systemPermissionTooltip')}>
              <Tag color="orange" size="small">
                {t('permissions.system')}
              </Tag>
            </Tooltip>
          )}
        </Space>
      ),
    },
    {
      title: t('permissions.displayName'),
      dataIndex: 'displayName',
      key: 'displayName',
      sorter: true,
      render: (displayName: string, record: Permission) => (
        <Space>
          <Text strong={record.type === 'menu'}>{displayName}</Text>
          <Text type="secondary">({t(`permissions.level${record.level}`)})</Text>
        </Space>
      ),
    },
    {
      title: t('permissions.type'),
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => (
        <Tag color={getPermissionTypeColor(type)}>
          {t(`permissions.type${type.charAt(0).toUpperCase() + type.slice(1)}`)}
        </Tag>
      ),
    },
    {
      title: t('permissions.path'),
      dataIndex: 'path',
      key: 'path',
      ellipsis: true,
      render: (path: string, record: Permission) => {
        if (!path) return '-';
        return (
          <Space>
            <Text code>{path}</Text>
            {record.method && (
              <Tag size="small" color="purple">
                {record.method}
              </Tag>
            )}
          </Space>
        );
      },
    },
    {
      title: t('permissions.sort'),
      dataIndex: 'sort',
      key: 'sort',
      sorter: true,
      width: 80,
    },
    {
      title: t('permissions.status'),
      dataIndex: 'status',
      key: 'status',
      render: (status: string, record: Permission) => {
        const statusConfig = {
          active: { color: 'green', text: t('permissions.statusActive') },
          inactive: { color: 'red', text: t('permissions.statusInactive') },
        };
        const config = statusConfig[status as keyof typeof statusConfig];
        return (
          <Space>
            <Tag color={config.color}>{config.text}</Tag>
            <Switch
              size="small"
              checked={status === 'active'}
              loading={toggling}
              disabled={record.isSystem}
              onChange={(checked) => togglePermissionStatus(record.id, checked ? 'active' : 'inactive')}
            />
          </Space>
        );
      },
    },
    {
      title: t('permissions.createdAt'),
      dataIndex: 'createdAt',
      key: 'createdAt',
      sorter: true,
    },
    {
      title: t('common.actions'),
      key: 'actions',
      width: 120,
      render: (_, record: Permission) => {
        const menuItems = [
          {
            key: 'edit',
            label: t('common.edit'),
            icon: <EditOutlined />,
            disabled: record.isSystem,
            onClick: () => handleEdit(record),
          },
          {
            key: 'copy',
            label: t('permissions.copy'),
            icon: <CopyOutlined />,
            onClick: () => handleCopy(record),
          },
          {
            key: 'view',
            label: t('common.view'),
            icon: <EyeOutlined />,
            onClick: () => handleView(record),
          },
          {
            key: 'addChild',
            label: t('permissions.addChild'),
            icon: <PlusOutlined />,
            disabled: record.type === 'api' || record.type === 'button',
            onClick: () => handleAddChild(record),
          },
          {
            type: 'divider' as const,
          },
          {
            key: 'delete',
            label: t('common.delete'),
            icon: <DeleteOutlined />,
            danger: true,
            disabled: record.isSystem || (record.children && record.children.length > 0),
            onClick: () => handleDelete(record),
          },
        ];

        return (
          <Space>
            <Button
              type="link"
              size="small"
              icon={<EditOutlined />}
              disabled={record.isSystem}
              onClick={() => handleEdit(record)}
            >
              {t('common.edit')}
            </Button>
            <Dropdown menu={{ items: menuItems }} trigger={['click']}>
              <Button type="link" size="small" icon={<MoreOutlined />} />
            </Dropdown>
          </Space>
        );
      },
    },
  ];

  // 处理查询
  const handleQuery = (values: any) => {
    fetchPermissions({ ...values, page: 1, pageSize: 10 });
  };

  // 处理重置
  const handleReset = () => {
    queryBarRef.current?.resetFields();
    fetchPermissions({ page: 1, pageSize: 10 });
  };

  // 处理添加
  const handleAdd = () => {
    modalFormRef.current?.open({
      title: t('permissions.add'),
      mode: 'create',
    });
  };

  // 处理添加子权限
  const handleAddChild = (parent: Permission) => {
    modalFormRef.current?.open({
      title: t('permissions.addChild'),
      mode: 'create',
      initialValues: {
        parentId: parent.id,
        type: parent.type === 'menu' ? 'button' : 'api',
      },
    });
  };

  // 处理编辑
  const handleEdit = (record: Permission) => {
    modalFormRef.current?.open({
      title: t('permissions.edit'),
      mode: 'edit',
      initialValues: record,
    });
  };

  // 处理查看
  const handleView = (record: Permission) => {
    modalFormRef.current?.open({
      title: t('permissions.view'),
      mode: 'view',
      initialValues: record,
    });
  };

  // 处理删除
  const handleDelete = (record: Permission) => {
    Modal.confirm({
      title: t('permissions.confirmDelete'),
      content: t('permissions.confirmDeleteMessage', { name: record.displayName }),
      onOk: () => deletePermission(record.id),
    });
  };

  // 处理批量删除
  const handleBatchDelete = () => {
    if (selectedRowKeys.length === 0) {
      message.warning(t('permissions.selectPermissionsToDelete'));
      return;
    }

    Modal.confirm({
      title: t('permissions.confirmBatchDelete'),
      content: t('permissions.confirmBatchDeleteMessage', { count: selectedRowKeys.length }),
      onOk: () => batchDeletePermissions(selectedRowKeys),
    });
  };

  // 处理复制
  const handleCopy = (record: Permission) => {
    Modal.confirm({
      title: t('permissions.confirmCopy'),
      content: t('permissions.confirmCopyMessage', { name: record.displayName }),
      onOk: () => copyPermission(record.id),
    });
  };

  // 处理表单提交
  const handleSubmit = (values: any, mode: string) => {
    if (mode === 'create') {
      createPermission(values);
    } else if (mode === 'edit') {
      updatePermission(values.id, values);
    }
  };

  // 处理分页变化
  const handleTableChange = (pagination: any, filters: any, sorter: any) => {
    const params = {
      page: pagination.current,
      pageSize: pagination.pageSize,
      ...filters,
    };

    if (sorter.field) {
      params.sortBy = sorter.field;
      params.sortOrder = sorter.order === 'ascend' ? 'asc' : 'desc';
    }

    fetchPermissions(params);
  };

  // 处理树节点选择
  const handleTreeSelect = (selectedKeys: string[]) => {
    if (selectedKeys.length > 0) {
      const permission = findPermissionById(permissionTree, selectedKeys[0]);
      setSelectedPermission(permission);
    } else {
      setSelectedPermission(null);
    }
  };

  // 根据ID查找权限
  const findPermissionById = (permissions: Permission[], id: string): Permission | null => {
    for (const permission of permissions) {
      if (permission.id === id) {
        return permission;
      }
      if (permission.children) {
        const found = findPermissionById(permission.children, id);
        if (found) return found;
      }
    }
    return null;
  };

  // 展开/收起所有节点
  const handleExpandAll = () => {
    const getAllKeys = (permissions: Permission[]): string[] => {
      let keys: string[] = [];
      permissions.forEach(permission => {
        keys.push(permission.id);
        if (permission.children) {
          keys = keys.concat(getAllKeys(permission.children));
        }
      });
      return keys;
    };

    if (expandedKeys.length === 0) {
      setExpandedKeys(getAllKeys(permissionTree));
    } else {
      setExpandedKeys([]);
    }
  };

  return (
    <div style={{ padding: '24px' }}>
      <Row gutter={[16, 16]}>
        {/* 左侧权限树 */}
        <Col span={viewMode === 'tree' ? 24 : 8}>
          <Card
            title={
              <Space>
                <SafetyOutlined />
                <Text strong>{t('permissions.tree')}</Text>
              </Space>
            }
            extra={
              <Space>
                <Button
                  size="small"
                  icon={expandedKeys.length === 0 ? <ExpandAltOutlined /> : <CompressOutlined />}
                  onClick={handleExpandAll}
                >
                  {expandedKeys.length === 0 ? t('permissions.expandAll') : t('permissions.collapseAll')}
                </Button>
                <Button
                  size="small"
                  type={viewMode === 'tree' ? 'primary' : 'default'}
                  onClick={() => setViewMode(viewMode === 'tree' ? 'table' : 'tree')}
                >
                  {viewMode === 'tree' ? t('permissions.tableView') : t('permissions.treeView')}
                </Button>
              </Space>
            }
            style={{ height: '100%' }}
          >
            <Tree
              treeData={convertPermissionsToTree(permissionTree)}
              expandedKeys={expandedKeys}
              onExpand={setExpandedKeys}
              onSelect={handleTreeSelect}
              showLine
              showIcon={false}
              height={600}
              loading={treeLoading}
            />
          </Card>
        </Col>

        {/* 右侧详情/表格 */}
        {viewMode === 'table' && (
          <Col span={16}>
            <Card>
              {/* 查询栏 */}
              <QueryBar
                ref={queryBarRef}
                fields={queryFields}
                onQuery={handleQuery}
                onReset={handleReset}
              />

              {/* 操作栏 */}
              <div style={{ marginBottom: '16px' }}>
                <Space>
                  <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
                    {t('permissions.add')}
                  </Button>
                  <Button
                    danger
                    icon={<DeleteOutlined />}
                    disabled={selectedRowKeys.length === 0}
                    loading={batchDeleting}
                    onClick={handleBatchDelete}
                  >
                    {t('permissions.batchDelete')}
                  </Button>
                </Space>
              </div>

              {/* 数据表格 */}
              <DataTable
                columns={columns}
                dataSource={permissionsData?.list || []}
                loading={permissionsLoading}
                error={permissionsError}
                rowKey="id"
                rowSelection={{
                  selectedRowKeys,
                  onChange: setSelectedRowKeys,
                  getCheckboxProps: (record: Permission) => ({
                    disabled: record.isSystem,
                  }),
                }}
                pagination={{
                  current: permissionsData?.pagination?.current || 1,
                  pageSize: permissionsData?.pagination?.pageSize || 10,
                  total: permissionsData?.pagination?.total || 0,
                  showSizeChanger: true,
                  showQuickJumper: true,
                  showTotal: (total, range) =>
                    t('common.pagination.total', {
                      start: range[0],
                      end: range[1],
                      total,
                    }),
                }}
                onChange={handleTableChange}
                onRefresh={() => fetchPermissions()}
              />
            </Card>
          </Col>
        )}

        {/* 权限详情 */}
        {viewMode === 'table' && selectedPermission && (
          <Col span={24}>
            <Card title={t('permissions.details')} style={{ marginTop: '16px' }}>
              <Row gutter={[16, 16]}>
                <Col span={8}>
                  <Text strong>{t('permissions.name')}: </Text>
                  <Text code>{selectedPermission.name}</Text>
                </Col>
                <Col span={8}>
                  <Text strong>{t('permissions.displayName')}: </Text>
                  <Text>{selectedPermission.displayName}</Text>
                </Col>
                <Col span={8}>
                  <Text strong>{t('permissions.type')}: </Text>
                  <Tag color={getPermissionTypeColor(selectedPermission.type)}>
                    {t(`permissions.type${selectedPermission.type.charAt(0).toUpperCase() + selectedPermission.type.slice(1)}`)}
                  </Tag>
                </Col>
                {selectedPermission.path && (
                  <Col span={12}>
                    <Text strong>{t('permissions.path')}: </Text>
                    <Text code>{selectedPermission.path}</Text>
                  </Col>
                )}
                {selectedPermission.method && (
                  <Col span={12}>
                    <Text strong>{t('permissions.method')}: </Text>
                    <Tag color="purple">{selectedPermission.method}</Tag>
                  </Col>
                )}
                {selectedPermission.description && (
                  <Col span={24}>
                    <Text strong>{t('permissions.description')}: </Text>
                    <Text>{selectedPermission.description}</Text>
                  </Col>
                )}
              </Row>
            </Card>
          </Col>
        )}
      </Row>

      {/* 权限表单弹窗 */}
      <ModalForm
        ref={modalFormRef}
        fields={getFormFields('create')}
        onSubmit={handleSubmit}
        loading={creating || updating}
        width={800}
      />
    </div>
  );
};

export default Permissions;