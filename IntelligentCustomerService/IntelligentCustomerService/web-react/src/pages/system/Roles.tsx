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
  Divider,
  Typography,
  Tooltip,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  MoreOutlined,
  SafetyOutlined,
  TeamOutlined,
  EyeOutlined,
  CopyOutlined,
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { DataTable } from '../../components/common/DataTable';
import { ModalForm } from '../../components/common/ModalForm';
import { QueryBar } from '../../components/common/QueryBar';
import { useRequest } from '../../hooks/useRequest';
import { roleApi } from '../../api/role';
import type { FormField } from '../../components/common/DynamicForm';
import type { ModalFormRef } from '../../components/common/ModalForm';
import type { QueryBarRef } from '../../components/common/QueryBar';
import type { DataNode } from 'antd/es/tree';

const { Text } = Typography;

// 角色接口
interface Role {
  id: string;
  name: string;
  displayName: string;
  description?: string;
  status: 'active' | 'inactive';
  permissions: string[];
  userCount: number;
  isSystem: boolean;
  createdAt: string;
  updatedAt: string;
}

// 权限接口
interface Permission {
  id: string;
  name: string;
  displayName: string;
  description?: string;
  type: 'menu' | 'button' | 'api';
  parentId?: string;
  children?: Permission[];
}

const Roles: React.FC = () => {
  const { t } = useTranslation();
  const [selectedRowKeys, setSelectedRowKeys] = useState<string[]>([]);
  const [permissionModalVisible, setPermissionModalVisible] = useState(false);
  const [selectedRole, setSelectedRole] = useState<Role | null>(null);
  const [checkedPermissions, setCheckedPermissions] = useState<string[]>([]);
  const modalFormRef = useRef<ModalFormRef>(null);
  const queryBarRef = useRef<QueryBarRef>(null);

  // 获取角色列表
  const {
    data: rolesData,
    loading: rolesLoading,
    error: rolesError,
    run: fetchRoles,
  } = useRequest(roleApi.getRoles, {
    defaultParams: [{ page: 1, pageSize: 10 }],
  });

  // 获取权限树
  const {
    data: permissions = [],
    run: fetchPermissions,
  } = useRequest(roleApi.getPermissions, {
    defaultRun: true,
  });

  // 创建角色
  const { loading: creating, run: createRole } = useRequest(roleApi.createRole, {
    manual: true,
    onSuccess: () => {
      message.success(t('roles.createSuccess'));
      modalFormRef.current?.close();
      fetchRoles();
    },
  });

  // 更新角色
  const { loading: updating, run: updateRole } = useRequest(roleApi.updateRole, {
    manual: true,
    onSuccess: () => {
      message.success(t('roles.updateSuccess'));
      modalFormRef.current?.close();
      fetchRoles();
    },
  });

  // 删除角色
  const { loading: deleting, run: deleteRole } = useRequest(roleApi.deleteRole, {
    manual: true,
    onSuccess: () => {
      message.success(t('roles.deleteSuccess'));
      fetchRoles();
    },
  });

  // 批量删除角色
  const { loading: batchDeleting, run: batchDeleteRoles } = useRequest(
    roleApi.batchDeleteRoles,
    {
      manual: true,
      onSuccess: () => {
        message.success(t('roles.batchDeleteSuccess'));
        setSelectedRowKeys([]);
        fetchRoles();
      },
    }
  );

  // 更新角色权限
  const { loading: updatingPermissions, run: updateRolePermissions } = useRequest(
    roleApi.updateRolePermissions,
    {
      manual: true,
      onSuccess: () => {
        message.success(t('roles.permissionsUpdateSuccess'));
        setPermissionModalVisible(false);
        fetchRoles();
      },
    }
  );

  // 切换角色状态
  const { loading: toggling, run: toggleRoleStatus } = useRequest(
    roleApi.toggleRoleStatus,
    {
      manual: true,
      onSuccess: () => {
        message.success(t('roles.statusUpdateSuccess'));
        fetchRoles();
      },
    }
  );

  // 复制角色
  const { loading: copying, run: copyRole } = useRequest(roleApi.copyRole, {
    manual: true,
    onSuccess: () => {
      message.success(t('roles.copySuccess'));
      fetchRoles();
    },
  });

  // 查询字段配置
  const queryFields: FormField[] = [
    {
      name: 'keyword',
      label: t('roles.keyword'),
      type: 'input',
      placeholder: t('roles.keywordPlaceholder'),
      colProps: { span: 6 },
    },
    {
      name: 'status',
      label: t('roles.status'),
      type: 'select',
      options: [
        { label: t('roles.statusActive'), value: 'active' },
        { label: t('roles.statusInactive'), value: 'inactive' },
      ],
      colProps: { span: 4 },
    },
    {
      name: 'isSystem',
      label: t('roles.type'),
      type: 'select',
      options: [
        { label: t('roles.systemRole'), value: true },
        { label: t('roles.customRole'), value: false },
      ],
      colProps: { span: 4 },
    },
  ];

  // 表单字段配置
  const formFields: FormField[] = [
    {
      name: 'name',
      label: t('roles.name'),
      type: 'input',
      required: true,
      rules: [
        { required: true, message: t('roles.nameRequired') },
        { min: 2, max: 50, message: t('roles.nameLength') },
        { pattern: /^[a-zA-Z0-9_]+$/, message: t('roles.namePattern') },
      ],
      colProps: { span: 12 },
    },
    {
      name: 'displayName',
      label: t('roles.displayName'),
      type: 'input',
      required: true,
      rules: [
        { required: true, message: t('roles.displayNameRequired') },
        { min: 2, max: 50, message: t('roles.displayNameLength') },
      ],
      colProps: { span: 12 },
    },
    {
      name: 'description',
      label: t('roles.description'),
      type: 'textarea',
      colProps: { span: 24 },
    },
    {
      name: 'status',
      label: t('roles.status'),
      type: 'select',
      options: [
        { label: t('roles.statusActive'), value: 'active' },
        { label: t('roles.statusInactive'), value: 'inactive' },
      ],
      defaultValue: 'active',
      colProps: { span: 12 },
    },
  ];

  // 转换权限数据为树形结构
  const convertPermissionsToTree = (permissions: Permission[]): DataNode[] => {
    const buildTree = (items: Permission[], parentId?: string): DataNode[] => {
      return items
        .filter(item => item.parentId === parentId)
        .map(item => ({
          key: item.id,
          title: (
            <Space>
              <Text>{item.displayName}</Text>
              <Tag size="small" color={getPermissionTypeColor(item.type)}>
                {t(`roles.permissionType.${item.type}`)}
              </Tag>
            </Space>
          ),
          children: buildTree(items, item.id),
        }));
    };
    return buildTree(permissions);
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
      title: t('roles.name'),
      dataIndex: 'name',
      key: 'name',
      sorter: true,
      render: (name: string, record: Role) => (
        <Space>
          <Text strong>{name}</Text>
          {record.isSystem && (
            <Tooltip title={t('roles.systemRoleTooltip')}>
              <Tag color="red" size="small">
                {t('roles.system')}
              </Tag>
            </Tooltip>
          )}
        </Space>
      ),
    },
    {
      title: t('roles.displayName'),
      dataIndex: 'displayName',
      key: 'displayName',
      sorter: true,
    },
    {
      title: t('roles.description'),
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
      render: (description: string) => description || '-',
    },
    {
      title: t('roles.userCount'),
      dataIndex: 'userCount',
      key: 'userCount',
      sorter: true,
      render: (count: number) => (
        <Space>
          <TeamOutlined />
          <Text>{count}</Text>
        </Space>
      ),
    },
    {
      title: t('roles.permissions'),
      dataIndex: 'permissions',
      key: 'permissions',
      render: (permissions: string[]) => (
        <Space>
          <SafetyOutlined />
          <Text>{permissions.length}</Text>
          <Text type="secondary">{t('roles.permissionsCount')}</Text>
        </Space>
      ),
    },
    {
      title: t('roles.status'),
      dataIndex: 'status',
      key: 'status',
      render: (status: string, record: Role) => {
        const statusConfig = {
          active: { color: 'green', text: t('roles.statusActive') },
          inactive: { color: 'red', text: t('roles.statusInactive') },
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
              onChange={(checked) => toggleRoleStatus(record.id, checked ? 'active' : 'inactive')}
            />
          </Space>
        );
      },
    },
    {
      title: t('roles.createdAt'),
      dataIndex: 'createdAt',
      key: 'createdAt',
      sorter: true,
    },
    {
      title: t('common.actions'),
      key: 'actions',
      width: 120,
      render: (_, record: Role) => {
        const menuItems = [
          {
            key: 'edit',
            label: t('common.edit'),
            icon: <EditOutlined />,
            disabled: record.isSystem,
            onClick: () => handleEdit(record),
          },
          {
            key: 'permissions',
            label: t('roles.managePermissions'),
            icon: <SafetyOutlined />,
            onClick: () => handleManagePermissions(record),
          },
          {
            key: 'copy',
            label: t('roles.copy'),
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
            type: 'divider' as const,
          },
          {
            key: 'delete',
            label: t('common.delete'),
            icon: <DeleteOutlined />,
            danger: true,
            disabled: record.isSystem || record.userCount > 0,
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
    fetchRoles({ ...values, page: 1, pageSize: 10 });
  };

  // 处理重置
  const handleReset = () => {
    queryBarRef.current?.resetFields();
    fetchRoles({ page: 1, pageSize: 10 });
  };

  // 处理添加
  const handleAdd = () => {
    modalFormRef.current?.open({
      title: t('roles.add'),
      mode: 'create',
    });
  };

  // 处理编辑
  const handleEdit = (record: Role) => {
    modalFormRef.current?.open({
      title: t('roles.edit'),
      mode: 'edit',
      initialValues: record,
    });
  };

  // 处理查看
  const handleView = (record: Role) => {
    modalFormRef.current?.open({
      title: t('roles.view'),
      mode: 'view',
      initialValues: record,
    });
  };

  // 处理删除
  const handleDelete = (record: Role) => {
    Modal.confirm({
      title: t('roles.confirmDelete'),
      content: t('roles.confirmDeleteMessage', { name: record.displayName }),
      onOk: () => deleteRole(record.id),
    });
  };

  // 处理批量删除
  const handleBatchDelete = () => {
    if (selectedRowKeys.length === 0) {
      message.warning(t('roles.selectRolesToDelete'));
      return;
    }

    Modal.confirm({
      title: t('roles.confirmBatchDelete'),
      content: t('roles.confirmBatchDeleteMessage', { count: selectedRowKeys.length }),
      onOk: () => batchDeleteRoles(selectedRowKeys),
    });
  };

  // 处理复制
  const handleCopy = (record: Role) => {
    Modal.confirm({
      title: t('roles.confirmCopy'),
      content: t('roles.confirmCopyMessage', { name: record.displayName }),
      onOk: () => copyRole(record.id),
    });
  };

  // 处理权限管理
  const handleManagePermissions = (record: Role) => {
    setSelectedRole(record);
    setCheckedPermissions(record.permissions);
    setPermissionModalVisible(true);
  };

  // 处理权限变化
  const handlePermissionCheck = (checkedKeys: any) => {
    setCheckedPermissions(checkedKeys);
  };

  // 保存权限
  const handleSavePermissions = () => {
    if (!selectedRole) return;
    updateRolePermissions(selectedRole.id, checkedPermissions);
  };

  // 处理表单提交
  const handleSubmit = (values: any, mode: string) => {
    if (mode === 'create') {
      createRole(values);
    } else if (mode === 'edit') {
      updateRole(values.id, values);
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

    fetchRoles(params);
  };

  return (
    <div style={{ padding: '24px' }}>
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
              {t('roles.add')}
            </Button>
            <Button
              danger
              icon={<DeleteOutlined />}
              disabled={selectedRowKeys.length === 0}
              loading={batchDeleting}
              onClick={handleBatchDelete}
            >
              {t('roles.batchDelete')}
            </Button>
          </Space>
        </div>

        {/* 数据表格 */}
        <DataTable
          columns={columns}
          dataSource={rolesData?.list || []}
          loading={rolesLoading}
          error={rolesError}
          rowKey="id"
          rowSelection={{
            selectedRowKeys,
            onChange: setSelectedRowKeys,
            getCheckboxProps: (record: Role) => ({
              disabled: record.isSystem,
            }),
          }}
          pagination={{
            current: rolesData?.pagination?.current || 1,
            pageSize: rolesData?.pagination?.pageSize || 10,
            total: rolesData?.pagination?.total || 0,
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
          onRefresh={() => fetchRoles()}
        />
      </Card>

      {/* 角色表单弹窗 */}
      <ModalForm
        ref={modalFormRef}
        fields={formFields}
        onSubmit={handleSubmit}
        loading={creating || updating}
        width={600}
      />

      {/* 权限管理弹窗 */}
      <Modal
        title={t('roles.managePermissions')}
        open={permissionModalVisible}
        onCancel={() => setPermissionModalVisible(false)}
        onOk={handleSavePermissions}
        confirmLoading={updatingPermissions}
        width={800}
        destroyOnClose
      >
        <div style={{ marginBottom: '16px' }}>
          <Text strong>{t('roles.role')}: </Text>
          <Text>{selectedRole?.displayName}</Text>
        </div>
        <Divider />
        <Tree
          checkable
          checkedKeys={checkedPermissions}
          onCheck={handlePermissionCheck}
          treeData={convertPermissionsToTree(permissions)}
          height={400}
          showLine
          showIcon={false}
        />
      </Modal>
    </div>
  );
};

export default Roles;