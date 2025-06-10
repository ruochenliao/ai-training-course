import React, {useCallback, useEffect, useState} from 'react';
import {Button, Card, Drawer, Form, Input, message, Modal, Space, Table, Tabs, Tag, Tree, Typography} from 'antd';
import type {DataNode} from 'antd/es/tree';
import {
    DeleteOutlined,
    EditOutlined,
    PlusOutlined,
    ReloadOutlined,
    SafetyCertificateOutlined,
    SearchOutlined
} from '@ant-design/icons';
import {type Role, roleApi, type RoleCreateData, type RoleUpdateData} from '../../../api/role';
import {type Menu, menuApi} from '../../../api/menu';
import {apiApi, type ApiItem} from '../../../api/api';
import {useTheme} from '../../../contexts/ThemeContext';
import {cn} from '../../../utils';
import CommonPagination from '@/components/CommonPagination';

const { Title } = Typography;

// 扩展Ant Design的DataNode类型
interface MenuTreeNode extends DataNode {
  path?: string | undefined;
  component?: string | undefined;
  perms?: string | undefined;
  remark?: string | undefined;
  children?: MenuTreeNode[] | undefined;
}

interface ApiTreeNode extends DataNode {
  path?: string | undefined;
  method?: string | undefined;
  children?: ApiTreeNode[] | undefined;
}

const RoleManagement: React.FC = () => {
  const { isDark, primaryColor } = useTheme();
  const [loading, setLoading] = useState<boolean>(false);
  const [roleData, setRoleData] = useState<Role[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [current, setCurrent] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(10);
  const [modalVisible, setModalVisible] = useState<boolean>(false);
  const [drawerVisible, setDrawerVisible] = useState<boolean>(false);
  const [modalTitle, setModalTitle] = useState<string>('');
  const [currentRole, setCurrentRole] = useState<Role | null>(null);
  const [menuData, setMenuData] = useState<MenuTreeNode[]>([]);
  const [apiData, setApiData] = useState<ApiTreeNode[]>([]);
  const [selectedMenuIds, setSelectedMenuIds] = useState<React.Key[]>([]);
  const [selectedApiIds, setSelectedApiIds] = useState<React.Key[]>([]);
  const [searchPattern, setSearchPattern] = useState<string>('');
  const [form] = Form.useForm();
  const [searchForm] = Form.useForm();

  // 获取角色数据
  const fetchRoleData = useCallback(async (params?: any) => {
    setLoading(true);
    try {
      const searchValues = searchForm.getFieldsValue();
      const queryParams = {
        page: current,
        page_size: pageSize,
        role_name: searchValues.role_name,
        ...params
      };
      
      const response = await roleApi.list(queryParams);
      if (response.code === 200) {
        // 处理数据结构
        setRoleData(response.data || []);
        setTotal(response.total || 0);
        setCurrent(response.page || current);
        setPageSize(response.page_size || pageSize);
      } else {
        message.error(response.msg || '获取角色列表失败');
      }
    } catch (error) {
      console.error('获取角色数据失败:', error);
      message.error('获取角色数据失败');
    } finally {
      setLoading(false);
    }
  }, [current, pageSize, searchForm]);

  // 构建菜单树结构
  const buildMenuTree = (data: Menu[]): MenuTreeNode[] => {
    const convertToTreeData = (items: Menu[]): MenuTreeNode[] => {
      return items.map(item => ({
        key: item.id.toString(),
        title: item.name,
        path: item.path,
        component: item.component,
        perms: item.perms,
        remark: item.remark,
        children: item.children && item.children.length > 0 ? convertToTreeData(item.children) : undefined
      }));
    };
    return convertToTreeData(data);
  };

  // 过滤树数据
  const filterTreeData = (data: MenuTreeNode[], searchText: string): MenuTreeNode[] => {
    if (!searchText) return data;
    
    const filterNode = (node: MenuTreeNode): MenuTreeNode | null => {
      const searchLower = searchText.toLowerCase();
      const titleMatch = node.title && String(node.title).toLowerCase().includes(searchLower);
      const pathMatch = node.path && node.path.toLowerCase().includes(searchLower);
      const componentMatch = node.component && node.component.toLowerCase().includes(searchLower);
      const permsMatch = node.perms && node.perms.toLowerCase().includes(searchLower);
      const remarkMatch = node.remark && node.remark.toLowerCase().includes(searchLower);
      
      const filteredChildren = node.children ? node.children.map(child => filterNode(child as MenuTreeNode)).filter(Boolean) as MenuTreeNode[] : [];
      
      if (titleMatch || pathMatch || componentMatch || permsMatch || remarkMatch || filteredChildren.length > 0) {
        return {
          ...node,
          children: filteredChildren.length > 0 ? filteredChildren : undefined
        };
      }
      
      return null;
    };
    
    return data.map(filterNode).filter(Boolean) as MenuTreeNode[];
  };

  // 过滤API树数据
  const filterApiTreeData = (data: ApiTreeNode[], searchText: string): ApiTreeNode[] => {
    if (!searchText) return data;
    
    const filterApiNode = (node: ApiTreeNode): ApiTreeNode | null => {
      const searchLower = searchText.toLowerCase();
      const titleMatch = node.title && String(node.title).toLowerCase().includes(searchLower);
      const pathMatch = node.path && node.path.toLowerCase().includes(searchLower);
      const filteredChildren = node.children ? node.children.map(child => filterApiNode(child as ApiTreeNode)).filter(Boolean) as ApiTreeNode[] : [];
      
      if (titleMatch || pathMatch || filteredChildren.length > 0) {
        return {
          ...node,
          children: filteredChildren.length > 0 ? filteredChildren : undefined
        };
      }
      
      return null;
    };
    
    return data.map(filterApiNode).filter(Boolean) as ApiTreeNode[];
  };

  // 构建API树结构
  const buildApiTree = (data: ApiItem[]): ApiTreeNode[] => {
    const processedData: ApiTreeNode[] = [];
    const groupedData: { [key: string]: ApiTreeNode } = {};

    data.forEach((item) => {
      const tags = item.tags;
      const pathParts = item.path.split('/');
      const path = pathParts.slice(0, -1).join('/');
      const summary = tags.charAt(0).toUpperCase() + tags.slice(1);
      const unique_id = item.method.toLowerCase() + item.path;
      
      if (!(path in groupedData)) {
        groupedData[path] = {
          key: path,
          title: summary,
          children: []
        };
      }

      if (groupedData[path].children) {
        (groupedData[path].children as ApiTreeNode[]).push({
          key: unique_id,
          title: item.summary,
          path: item.path,
          method: item.method
        });
      }
    });
    
    processedData.push(...Object.values(groupedData));
    return processedData;
  };

  useEffect(() => {
    fetchRoleData();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // 搜索角色
  const handleSearch = () => {
    setCurrent(1); // 重置到第一页
    fetchRoleData({ page: 1 });
  };

  // 重置搜索
  const handleReset = () => {
    searchForm.resetFields();
    setCurrent(1); // 重置到第一页
    fetchRoleData({ page: 1 });
  };

  const handleAddRole = () => {
    setModalTitle('新增角色');
    setCurrentRole(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEditRole = (record: Role) => {
    setModalTitle('编辑角色');
    setCurrentRole(record);
    form.setFieldsValue({
      name: record.name,
      desc: record.desc
    });
    setModalVisible(true);
  };

  const handleDeleteRole = async (id: number) => {
    try {
      const response = await roleApi.delete(id);
      if (response.code === 200) {
        message.success('删除角色成功');
        fetchRoleData();
      } else {
        message.error(response.msg || '删除角色失败');
      }
    } catch (error) {
      console.error('删除角色失败:', error);
      message.error('删除角色失败');
    }
  };

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields();
      
      if (currentRole) {
        // 更新角色
        const updateData: RoleUpdateData = {
          id: currentRole.id,
          name: values.name,
          desc: values.desc
        };
        
        const response = await roleApi.update(updateData);
        if (response.code === 200) {
          message.success('更新角色成功');
          setModalVisible(false);
          fetchRoleData();
        } else {
          message.error(response.msg || '更新角色失败');
        }
      } else {
        // 创建角色
        const createData: RoleCreateData = {
          name: values.name,
          desc: values.desc
        };
        
        const response = await roleApi.create(createData);
        if (response.code === 200) {
          message.success('创建角色成功');
          setModalVisible(false);
          fetchRoleData();
        } else {
          message.error(response.msg || '创建角色失败');
        }
      }
    } catch (error) {
      console.error('保存角色失败:', error);
    }
  };

  const handleConfigPermission = async (record: Role) => {
    setCurrentRole(record);
    setDrawerVisible(true);
    
    try {
      // 获取该角色已分配的权限
      const roleAuthResponse = await roleApi.getAuthorized(record.id);
      
      if (roleAuthResponse.code === 200 && roleAuthResponse.data) {
        const { menus, apis } = roleAuthResponse.data;
        setSelectedMenuIds(menus.map((menu: any) => menu.id.toString()));
        
        // 转换API结构以匹配树结构的key
        const apiKeys = apis.map((api: any) => `${api.method.toLowerCase()}${api.path}`);
        setSelectedApiIds(apiKeys);
      } else {
        setSelectedMenuIds([]);
        setSelectedApiIds([]);
      }
      
      // 获取所有菜单和API
      const [menuResponse, apiResponse] = await Promise.all([
        menuApi.getMenuTree(),
        apiApi.getApis()
      ]);
      
      if (menuResponse.code === 200 && menuResponse.data) {
        const menuTree = buildMenuTree(menuResponse.data);
        setMenuData(menuTree);
      } else {
        setMenuData([]);
      }
      
      if (apiResponse.code === 200 && apiResponse.data) {
        const apiTree = buildApiTree(apiResponse.data);
        setApiData(apiTree);
      } else {
        setApiData([]);
      }
    } catch (error) {
      console.error('获取权限数据失败:', error);
      message.error('获取权限数据失败');
    }
  };

  const handlePermissionOk = async () => {
    try {
      // 将选中的API ID转换为API信息对象
      const apiInfos: Array<{ method: string; path: string }> = [];
      
      // 递归查找API信息
      const findApiInfo = (nodes: ApiTreeNode[]): Array<{ method: string; path: string }> => {
        let results: Array<{ method: string; path: string }> = [];
        
        nodes.forEach(node => {
          if (selectedApiIds.includes(node.key) && node.method && node.path) {
            results.push({ 
              method: node.method.toUpperCase(), 
              path: node.path 
            });
          }
          
          if (node.children && node.children.length > 0) {
            results = [...results, ...findApiInfo(node.children as ApiTreeNode[])];
          }
        });
        
        return results;
      };
      
      apiInfos.push(...findApiInfo(apiData));
      
      const data = {
        id: currentRole!.id,
        menu_ids: selectedMenuIds.map(id => Number(id.toString())),
        api_infos: apiInfos
      };
      
      const response = await roleApi.updateAuthorized(data);
      
      if (response.code === 200) {
        message.success('更新权限成功');
        setDrawerVisible(false);
      } else {
        message.error(response.msg || '更新权限失败');
      }
    } catch (error) {
      console.error('更新权限失败:', error);
      message.error('更新权限失败');
    }
  };

  // 处理分页变化
  const handleTableChange = (page: number, size: number) => {
    setCurrent(page);
    setPageSize(size);
    fetchRoleData({
      page: page,
      page_size: size,
    });
  };

  // 表格列定义
  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: '角色名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string) => (
        <div className="font-medium">{text}</div>
      )
    },
    {
      title: '描述',
      dataIndex: 'desc',
      key: 'desc',
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => new Date(date).toLocaleString(),
    },
    {
      title: '操作',
      key: 'action',
      width: 280,
      render: (_: any, record: Role) => (
        <Space>
          <Button 
            type="link" 
            size="small" 
            icon={<SafetyCertificateOutlined />} 
            onClick={() => handleConfigPermission(record)}
            className="action-button"
          >
            权限配置
          </Button>
          <Button 
            type="link" 
            size="small" 
            icon={<EditOutlined />} 
            onClick={() => handleEditRole(record)}
            className="action-button"
          >
            编辑
          </Button>
          {record.name !== 'admin' && (
            <Button 
              type="link" 
              danger 
              size="small" 
              icon={<DeleteOutlined />} 
              onClick={() => handleDeleteRole(record.id)}
              className="action-button delete-button"
            >
              删除
            </Button>
          )}
        </Space>
      ),
    },
  ];

  // 角色表单内容
  const roleFormContent = (
    <Form
      form={form}
      layout="vertical"
      requiredMark={false}
      className="system-form"
    >
      <Form.Item
        name="name"
        label="角色名称"
        rules={[
          { required: true, message: '请输入角色名称' },
          { min: 2, message: '角色名称至少2个字符' },
          { max: 50, message: '角色名称最多50个字符' }
        ]}
      >
        <Input placeholder="请输入角色名称" />
      </Form.Item>
      
      <Form.Item
        name="desc"
        label="角色描述"
      >
        <Input.TextArea 
          placeholder="请输入角色描述"
          rows={4}
          maxLength={200}
          showCount 
        />
      </Form.Item>
    </Form>
  );

  // 渲染API树方法节点
  const renderApiTreeTitle = (node: ApiTreeNode) => {
    if (node.method) {
      const methodColors: Record<string, string> = {
        get: 'green',
        post: 'blue',
        put: 'orange',
        delete: 'red',
        patch: 'purple'
      };
      
      const method = node.method.toLowerCase();
      const color = methodColors[method] || 'default';
      
      return (
        <div className="flex items-center">
          <Tag color={color} className="mr-2 uppercase">
            {method}
          </Tag>
          <span>{String(node.title)}</span>
          {node.path && <span className="ml-2 text-gray-400 text-xs">{node.path}</span>}
        </div>
      );
    }
    
    return <span>{String(node.title)}</span>;
  };

  return (
    <div className="role-management" style={{ padding: '24px' }}>
      {/* 角色列表卡片 */}
      <Card 
        title={<Title level={4}>角色管理</Title>}
        style={{ borderRadius: '4px', boxShadow: '0 2px 8px rgba(0,0,0,0.08)' }}
        className={cn(
          "system-card",
          isDark ? "bg-gray-800 border-gray-700" : "bg-white"
        )}
        bordered={false}
      >
        {/* 搜索表单 */}
        <div className="mb-4">
          <Form
            form={searchForm}
            layout="inline"
            onFinish={handleSearch}
            className="gap-4 flex-wrap system-form"
            style={{ rowGap: '12px' }}
          >
            <Form.Item name="role_name" label="角色名称">
              <Input placeholder="请输入角色名称" allowClear />
            </Form.Item>
            <Form.Item>
              <Space>
                <Button 
                  type="primary" 
                  htmlType="submit" 
                  icon={<SearchOutlined />}
                  className="search-button"
                  style={{ backgroundColor: primaryColor }}
                >
                  搜索
                </Button>
                <Button 
                  icon={<ReloadOutlined />} 
                  onClick={handleReset}
                  className="reset-button"
                >
                  重置
                </Button>
              </Space>
            </Form.Item>
          </Form>
        </div>
        
        {/* 工具栏 */}
        <div className="mb-4 flex justify-between">
          <div className={cn(
            isDark ? "text-white" : "text-gray-800"
          )}>
            角色列表
          </div>
          <Space>
            <Button 
              type="primary" 
              icon={<PlusOutlined />} 
              onClick={handleAddRole}
              className="add-button"
              style={{ backgroundColor: primaryColor }}
            >
              新增角色
            </Button>
            <Button 
              icon={<ReloadOutlined />} 
              onClick={() => fetchRoleData()}
              className="reset-button"
            >
              刷新
            </Button>
          </Space>
        </div>
        
        {/* 角色表格 */}
        <Table
          columns={columns}
          dataSource={roleData}
          rowKey="id"
          pagination={CommonPagination({
            current,
            pageSize,
            total,
            onChange: handleTableChange
          })}
          loading={loading}
          className={cn("system-table", isDark ? "ant-table-dark" : "")}
          bordered
          size="middle"
        />
      </Card>

      {/* 角色表单弹窗 */}
      <Modal
        title={modalTitle}
        open={modalVisible}
        onOk={handleModalOk}
        onCancel={() => setModalVisible(false)}
        width={550}
        className="system-modal"
      >
        {roleFormContent}
      </Modal>

      {/* 权限配置抽屉 */}
      <Drawer
        title={`配置权限: ${currentRole?.name || ''}`}
        width={700}
        open={drawerVisible}
        onClose={() => setDrawerVisible(false)}
        maskClosable={false}
        footer={
          <div style={{ textAlign: 'right' }}>
            <Button style={{ marginRight: 8 }} onClick={() => setDrawerVisible(false)}>
              取消
            </Button>
            <Button 
              type="primary" 
              onClick={handlePermissionOk}
              style={{ backgroundColor: primaryColor }}
            >
              保存
            </Button>
          </div>
        }
        className="system-drawer"
      >
        <Input.Search 
          placeholder="搜索权限" 
          allowClear 
          onChange={(e) => setSearchPattern(e.target.value)}
          className="mb-4"
        />
        
        <Tabs
          defaultActiveKey="menu"
          items={[
            {
              key: 'menu',
              label: '菜单权限',
              children: (
                <div className={cn(
                  "border rounded-lg p-4",
                  isDark ? "border-gray-700" : "border-gray-200"
                )}>
                  <Tree
                    checkable
                    defaultExpandAll
                    onCheck={(checked) => setSelectedMenuIds(checked as React.Key[])}
                    checkedKeys={selectedMenuIds}
                    treeData={filterTreeData(menuData, searchPattern)}
                    className={isDark ? "ant-tree-dark" : ""}
                  />
                </div>
              ),
            },
            {
              key: 'api',
              label: 'API权限',
              children: (
                <div className={cn(
                  "border rounded-lg p-4",
                  isDark ? "border-gray-700" : "border-gray-200"
                )}>
                  <Tree
                    checkable
                    defaultExpandAll
                    onCheck={(checked) => setSelectedApiIds(checked as React.Key[])}
                    checkedKeys={selectedApiIds}
                    treeData={filterApiTreeData(apiData, searchPattern)}
                    titleRender={renderApiTreeTitle}
                    className={isDark ? "ant-tree-dark" : ""}
                  />
                </div>
              ),
            },
          ]}
        />
      </Drawer>
    </div>
  );
};

export default RoleManagement;