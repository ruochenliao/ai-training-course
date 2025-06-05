import React, { useState, useRef } from 'react';
import {
  Card,
  Button,
  Space,
  Tag,
  Avatar,
  Switch,
  Dropdown,
  Modal,
  message,
  Upload,
  Image,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  MoreOutlined,
  UserOutlined,
  LockOutlined,
  UnlockOutlined,
  UploadOutlined,
  EyeOutlined,
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { DataTable } from '../../components/common/DataTable';
import { ModalForm } from '../../components/common/ModalForm';
import { QueryBar } from '../../components/common/QueryBar';
import { useRequest } from '../../hooks/useRequest';
import { userApi } from '../../api/user';
import type { FormField } from '../../components/common/DynamicForm';
import type { ModalFormRef } from '../../components/common/ModalForm';
import type { QueryBarRef } from '../../components/common/QueryBar';

// 用户接口
interface User {
  id: string;
  username: string;
  email: string;
  phone?: string;
  realName: string;
  avatar?: string;
  status: 'active' | 'inactive' | 'locked';
  roles: string[];
  department?: string;
  position?: string;
  lastLoginTime?: string;
  createdAt: string;
  updatedAt: string;
}

// 角色接口
interface Role {
  id: string;
  name: string;
  displayName: string;
  description?: string;
}

const Users: React.FC = () => {
  const { t } = useTranslation();
  const [selectedRowKeys, setSelectedRowKeys] = useState<string[]>([]);
  const [previewImage, setPreviewImage] = useState<string>('');
  const [previewVisible, setPreviewVisible] = useState(false);
  const modalFormRef = useRef<ModalFormRef>(null);
  const queryBarRef = useRef<QueryBarRef>(null);

  // 获取用户列表
  const {
    data: usersData,
    loading: usersLoading,
    error: usersError,
    run: fetchUsers,
  } = useRequest(userApi.getUsers, {
    defaultParams: [{ page: 1, pageSize: 10 }],
  });

  // 获取角色列表
  const {
    data: roles = [],
    run: fetchRoles,
  } = useRequest(userApi.getRoles, {
    defaultRun: true,
  });

  // 创建用户
  const { loading: creating, run: createUser } = useRequest(userApi.createUser, {
    manual: true,
    onSuccess: () => {
      message.success(t('users.createSuccess'));
      modalFormRef.current?.close();
      fetchUsers();
    },
  });

  // 更新用户
  const { loading: updating, run: updateUser } = useRequest(userApi.updateUser, {
    manual: true,
    onSuccess: () => {
      message.success(t('users.updateSuccess'));
      modalFormRef.current?.close();
      fetchUsers();
    },
  });

  // 删除用户
  const { loading: deleting, run: deleteUser } = useRequest(userApi.deleteUser, {
    manual: true,
    onSuccess: () => {
      message.success(t('users.deleteSuccess'));
      fetchUsers();
    },
  });

  // 批量删除用户
  const { loading: batchDeleting, run: batchDeleteUsers } = useRequest(
    userApi.batchDeleteUsers,
    {
      manual: true,
      onSuccess: () => {
        message.success(t('users.batchDeleteSuccess'));
        setSelectedRowKeys([]);
        fetchUsers();
      },
    }
  );

  // 重置密码
  const { loading: resettingPassword, run: resetPassword } = useRequest(
    userApi.resetPassword,
    {
      manual: true,
      onSuccess: () => {
        message.success(t('users.resetPasswordSuccess'));
      },
    }
  );

  // 切换用户状态
  const { loading: toggling, run: toggleUserStatus } = useRequest(
    userApi.toggleUserStatus,
    {
      manual: true,
      onSuccess: () => {
        message.success(t('users.statusUpdateSuccess'));
        fetchUsers();
      },
    }
  );

  // 查询字段配置
  const queryFields: FormField[] = [
    {
      name: 'keyword',
      label: t('users.keyword'),
      type: 'input',
      placeholder: t('users.keywordPlaceholder'),
      colProps: { span: 6 },
    },
    {
      name: 'status',
      label: t('users.status'),
      type: 'select',
      options: [
        { label: t('users.statusActive'), value: 'active' },
        { label: t('users.statusInactive'), value: 'inactive' },
        { label: t('users.statusLocked'), value: 'locked' },
      ],
      colProps: { span: 4 },
    },
    {
      name: 'role',
      label: t('users.role'),
      type: 'select',
      options: roles.map(role => ({ label: role.displayName, value: role.id })),
      colProps: { span: 4 },
    },
    {
      name: 'department',
      label: t('users.department'),
      type: 'input',
      colProps: { span: 4 },
    },
  ];

  // 表单字段配置
  const formFields: FormField[] = [
    {
      name: 'username',
      label: t('users.username'),
      type: 'input',
      required: true,
      rules: [
        { required: true, message: t('users.usernameRequired') },
        { min: 3, max: 20, message: t('users.usernameLength') },
        { pattern: /^[a-zA-Z0-9_]+$/, message: t('users.usernamePattern') },
      ],
      colProps: { span: 12 },
    },
    {
      name: 'email',
      label: t('users.email'),
      type: 'input',
      required: true,
      rules: [
        { required: true, message: t('users.emailRequired') },
        { type: 'email', message: t('users.emailFormat') },
      ],
      colProps: { span: 12 },
    },
    {
      name: 'realName',
      label: t('users.realName'),
      type: 'input',
      required: true,
      rules: [{ required: true, message: t('users.realNameRequired') }],
      colProps: { span: 12 },
    },
    {
      name: 'phone',
      label: t('users.phone'),
      type: 'input',
      rules: [
        { pattern: /^1[3-9]\d{9}$/, message: t('users.phoneFormat') },
      ],
      colProps: { span: 12 },
    },
    {
      name: 'department',
      label: t('users.department'),
      type: 'input',
      colProps: { span: 12 },
    },
    {
      name: 'position',
      label: t('users.position'),
      type: 'input',
      colProps: { span: 12 },
    },
    {
      name: 'roles',
      label: t('users.roles'),
      type: 'select',
      mode: 'multiple',
      options: roles.map(role => ({ label: role.displayName, value: role.id })),
      required: true,
      rules: [{ required: true, message: t('users.rolesRequired') }],
      colProps: { span: 24 },
    },
    {
      name: 'status',
      label: t('users.status'),
      type: 'select',
      options: [
        { label: t('users.statusActive'), value: 'active' },
        { label: t('users.statusInactive'), value: 'inactive' },
        { label: t('users.statusLocked'), value: 'locked' },
      ],
      defaultValue: 'active',
      colProps: { span: 12 },
    },
    {
      name: 'avatar',
      label: t('users.avatar'),
      type: 'upload',
      uploadProps: {
        listType: 'picture-card',
        maxCount: 1,
        beforeUpload: () => false, // 阻止自动上传
      },
      colProps: { span: 12 },
    },
  ];

  // 表格列配置
  const columns = [
    {
      title: t('users.avatar'),
      dataIndex: 'avatar',
      key: 'avatar',
      width: 80,
      render: (avatar: string, record: User) => (
        <Avatar
          src={avatar}
          icon={<UserOutlined />}
          style={{ cursor: avatar ? 'pointer' : 'default' }}
          onClick={() => {
            if (avatar) {
              setPreviewImage(avatar);
              setPreviewVisible(true);
            }
          }}
        />
      ),
    },
    {
      title: t('users.username'),
      dataIndex: 'username',
      key: 'username',
      sorter: true,
    },
    {
      title: t('users.realName'),
      dataIndex: 'realName',
      key: 'realName',
      sorter: true,
    },
    {
      title: t('users.email'),
      dataIndex: 'email',
      key: 'email',
    },
    {
      title: t('users.phone'),
      dataIndex: 'phone',
      key: 'phone',
    },
    {
      title: t('users.department'),
      dataIndex: 'department',
      key: 'department',
    },
    {
      title: t('users.roles'),
      dataIndex: 'roles',
      key: 'roles',
      render: (roleIds: string[]) => (
        <Space wrap>
          {roleIds.map(roleId => {
            const role = roles.find(r => r.id === roleId);
            return role ? (
              <Tag key={roleId} color="blue">
                {role.displayName}
              </Tag>
            ) : null;
          })}
        </Space>
      ),
    },
    {
      title: t('users.status'),
      dataIndex: 'status',
      key: 'status',
      render: (status: string, record: User) => {
        const statusConfig = {
          active: { color: 'green', text: t('users.statusActive') },
          inactive: { color: 'orange', text: t('users.statusInactive') },
          locked: { color: 'red', text: t('users.statusLocked') },
        };
        const config = statusConfig[status as keyof typeof statusConfig];
        return (
          <Space>
            <Tag color={config.color}>{config.text}</Tag>
            <Switch
              size="small"
              checked={status === 'active'}
              loading={toggling}
              onChange={(checked) => toggleUserStatus(record.id, checked ? 'active' : 'inactive')}
            />
          </Space>
        );
      },
    },
    {
      title: t('users.lastLoginTime'),
      dataIndex: 'lastLoginTime',
      key: 'lastLoginTime',
      sorter: true,
      render: (time: string) => time || t('common.never'),
    },
    {
      title: t('common.actions'),
      key: 'actions',
      width: 120,
      render: (_, record: User) => {
        const menuItems = [
          {
            key: 'edit',
            label: t('common.edit'),
            icon: <EditOutlined />,
            onClick: () => handleEdit(record),
          },
          {
            key: 'resetPassword',
            label: t('users.resetPassword'),
            icon: <LockOutlined />,
            onClick: () => handleResetPassword(record),
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
            onClick: () => handleDelete(record),
          },
        ];

        return (
          <Space>
            <Button
              type="link"
              size="small"
              icon={<EditOutlined />}
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
    fetchUsers({ ...values, page: 1, pageSize: 10 });
  };

  // 处理重置
  const handleReset = () => {
    queryBarRef.current?.resetFields();
    fetchUsers({ page: 1, pageSize: 10 });
  };

  // 处理添加
  const handleAdd = () => {
    modalFormRef.current?.open({
      title: t('users.add'),
      mode: 'create',
    });
  };

  // 处理编辑
  const handleEdit = (record: User) => {
    modalFormRef.current?.open({
      title: t('users.edit'),
      mode: 'edit',
      initialValues: record,
    });
  };

  // 处理查看
  const handleView = (record: User) => {
    modalFormRef.current?.open({
      title: t('users.view'),
      mode: 'view',
      initialValues: record,
    });
  };

  // 处理删除
  const handleDelete = (record: User) => {
    Modal.confirm({
      title: t('users.confirmDelete'),
      content: t('users.confirmDeleteMessage', { name: record.realName }),
      onOk: () => deleteUser(record.id),
    });
  };

  // 处理批量删除
  const handleBatchDelete = () => {
    if (selectedRowKeys.length === 0) {
      message.warning(t('users.selectUsersToDelete'));
      return;
    }

    Modal.confirm({
      title: t('users.confirmBatchDelete'),
      content: t('users.confirmBatchDeleteMessage', { count: selectedRowKeys.length }),
      onOk: () => batchDeleteUsers(selectedRowKeys),
    });
  };

  // 处理重置密码
  const handleResetPassword = (record: User) => {
    Modal.confirm({
      title: t('users.confirmResetPassword'),
      content: t('users.confirmResetPasswordMessage', { name: record.realName }),
      onOk: () => resetPassword(record.id),
    });
  };

  // 处理表单提交
  const handleSubmit = (values: any, mode: string) => {
    if (mode === 'create') {
      createUser(values);
    } else if (mode === 'edit') {
      updateUser(values.id, values);
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

    fetchUsers(params);
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
              {t('users.add')}
            </Button>
            <Button
              danger
              icon={<DeleteOutlined />}
              disabled={selectedRowKeys.length === 0}
              loading={batchDeleting}
              onClick={handleBatchDelete}
            >
              {t('users.batchDelete')}
            </Button>
          </Space>
        </div>

        {/* 数据表格 */}
        <DataTable
          columns={columns}
          dataSource={usersData?.list || []}
          loading={usersLoading}
          error={usersError}
          rowKey="id"
          rowSelection={{
            selectedRowKeys,
            onChange: setSelectedRowKeys,
          }}
          pagination={{
            current: usersData?.pagination?.current || 1,
            pageSize: usersData?.pagination?.pageSize || 10,
            total: usersData?.pagination?.total || 0,
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
          onRefresh={() => fetchUsers()}
        />
      </Card>

      {/* 用户表单弹窗 */}
      <ModalForm
        ref={modalFormRef}
        fields={formFields}
        onSubmit={handleSubmit}
        loading={creating || updating}
        width={800}
      />

      {/* 头像预览 */}
      <Image
        width={200}
        style={{ display: 'none' }}
        src={previewImage}
        preview={{
          visible: previewVisible,
          src: previewImage,
          onVisibleChange: (visible) => {
            setPreviewVisible(visible);
            if (!visible) {
              setPreviewImage('');
            }
          },
        }}
      />
    </div>
  );
};

export default Users;