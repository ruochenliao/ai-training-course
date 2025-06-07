import React, {useEffect, useState} from 'react';
import {Button, Card, Drawer, Form, Input, message, Modal, Space, Table, Tabs, Tree,} from 'antd';
import {PlusOutlined,} from '@ant-design/icons';
import {Role, roleApi, RoleCreateData, RoleUpdateData} from '../../../api/role';

interface MenuData {
  id: number;
  name: string;
  children?: MenuData[];
}

interface ApiData {
  id: number;
  path: string;
  method: string;
  summary: string;
  tags: string;
}

interface ApiTreeData {
  key: string;
  title: string;
  path?: string;
  method?: string;
  children?: ApiTreeData[];
}

interface PermissionTreeData {
  key: string;
  title: string;
  children?: PermissionTreeData[];
}

const RoleManagement: React.FC = () => {
  const [loading, setLoading] = useState<boolean>(false);
  const [roleData, setRoleData] = useState<Role[]>([]);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 });
  const [modalVisible, setModalVisible] = useState<boolean>(false);
  const [drawerVisible, setDrawerVisible] = useState<boolean>(false);
  const [modalTitle, setModalTitle] = useState<string>('');
  const [currentRole, setCurrentRole] = useState<Role | null>(null);
  const [menuData, setMenuData] = useState<MenuData[]>([]);
  const [apiData, setApiData] = useState<ApiTreeData[]>([]);
  const [selectedMenuIds, setSelectedMenuIds] = useState<number[]>([]);
  const [selectedApiIds, setSelectedApiIds] = useState<string[]>([]);
  const [searchPattern, setSearchPattern] = useState<string>('');
  const [form] = Form.useForm();
  const [searchForm] = Form.useForm();

  // 获取角色数据
  const fetchRoleData = async (params?: any) => {
    setLoading(true);
    try {
      const searchValues = searchForm.getFieldsValue();
      const queryParams = {
        page: pagination.current,
        page_size: pagination.pageSize,
        role_name: searchValues.role_name,
        ...params
      };
      
      const response = await roleApi.list(queryParams);
      if (response.code === 200) {
        // 后端返回的数据结构是 { data: [...], total: number, page: number, page_size: number }
        setRoleData(response.data || []);
        setPagination({
          ...pagination,
          total: response.total || 0,
        });
      } else {
        message.error(response.msg || '获取角色列表失败');
      }
    } catch (error) {
      message.error('获取角色列表失败');
    } finally {
      setLoading(false);
    }
  };

  // 构建API树结构
  const buildApiTree = (data: ApiData[]): ApiTreeData[] => {
    const processedData: ApiTreeData[] = [];
    const groupedData: { [key: string]: ApiTreeData } = {};

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

      groupedData[path].children!.push({
        key: unique_id,
        title: item.summary,
        path: item.path,
        method: item.method
      });
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
    setPagination({ ...pagination, current: 1 });
    fetchRoleData({ page: 1 });
  };

  // 重置搜索
  const handleReset = () => {
    searchForm.resetFields();
    setPagination({ ...pagination, current: 1 });
    fetchRoleData({ page: 1 });
  };

  const handleAddRole = () => {
    setModalTitle('新建角色');
    setCurrentRole(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEditRole = (record: Role) => {
    setCurrentRole(record);
    form.setFieldsValue({
      name: record.name,
      remark: record.desc,
    });
    setModalVisible(true);
  };

  const handleDeleteRole = async (id: number) => {
    try {
      const response = await roleApi.delete(id);
      if (response.code === 200) {
        message.success('删除成功');
        fetchRoleData();
      } else {
        message.error(response.msg || '删除失败');
      }
    } catch (error) {
      message.error('删除失败');
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
          desc: values.remark,
        };
        
        const response = await roleApi.update(updateData);
        if (response.code === 200) {
          message.success('更新成功');
          fetchRoleData();
          setModalVisible(false);
        } else {
          message.error(response.msg || '更新失败');
        }
      } else {
        // 添加角色
        const createData: RoleCreateData = {
          name: values.name,
          desc: values.remark,
        };
        
        const response = await roleApi.create(createData);
        if (response.code === 200) {
          message.success('创建成功');
          fetchRoleData();
          setModalVisible(false);
        } else {
          message.error(response.msg || '创建失败');
        }
      }
    } catch (error) {
      // 表单验证失败
    }
  };

  const handleConfigPermission = async (record: Role) => {
    try {
      setCurrentRole(record);
      
      // 同时获取菜单、API和角色权限信息
      const [menusResponse, apisResponse, roleAuthorizedResponse] = await Promise.all([
        // 这里需要根据实际API调整
        // api.getMenus({ page: 1, page_size: 9999 }),
        // api.getApis({ page: 1, page_size: 9999 }),
        roleApi.getAuthorized(record.id),
      ]);
      
      // 处理菜单数据
      // setMenuData(menusResponse.data || []);
      
      // 处理API数据
      // setApiData(buildApiTree(apisResponse.data || []));
      
      // 处理角色权限
      const roleAuth = roleAuthorizedResponse.data;
      setSelectedMenuIds(roleAuth.menus.map((v: any) => v.id));
      setSelectedApiIds(roleAuth.apis.map((v: any) => v.method.toLowerCase() + v.path));
      
      setDrawerVisible(true);
    } catch (error) {
      message.error('获取权限信息失败');
      console.error('Error loading permission data:', error);
    }
  };

  const handlePermissionOk = async () => {
    try {
      if (currentRole) {
        // 构建API信息
        const apiInfos: Array<{ method: string; path: string }> = [];
        
        // 遍历选中的API ID，提取method和path
        selectedApiIds.forEach(apiId => {
          // 在API树中查找对应的API信息
          const findApiInfo = (nodes: ApiTreeData[]): { method: string; path: string } | null => {
            for (const node of nodes) {
              if (node.key === apiId && node.method && node.path) {
                return { method: node.method, path: node.path };
              }
              if (node.children) {
                const found = findApiInfo(node.children);
                if (found) return found;
              }
            }
            return null;
          };
          
          const apiInfo = findApiInfo(apiData);
          if (apiInfo) {
            apiInfos.push(apiInfo);
          }
        });
        
        const updateData = {
          id: currentRole.id,
          menu_ids: selectedMenuIds,
          api_infos: apiInfos,
        };
        
        const response = await roleApi.updateAuthorized(updateData);
        if (response.code === 200) {
          message.success('设置成功');
          setDrawerVisible(false);
        } else {
          message.error(response.msg || '设置失败');
        }
      }
    } catch (error) {
      message.error('设置权限失败');
    }
  };

  const columns = [
    {
      title: '角色名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '备注',
      dataIndex: 'desc',
      key: 'desc',
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
    },
    {
      title: '更新时间',
      dataIndex: 'updated_at',
      key: 'updated_at',
    },
    {
      title: '操作',
      key: 'action',
      render: (text: any, record: Role) => (
        <Space size="middle">
          <Button type="link" onClick={() => handleEditRole(record)}>
            编辑
          </Button>
          <Button type="link" onClick={() => handleConfigPermission(record)}>
            权限配置
          </Button>
          <Button type="link" danger onClick={() => handleDeleteRole(record.id)}>
            删除
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <Card
      title="角色管理"
    >
      {/* 搜索表单 */}
      <div style={{ marginBottom: 16 }}>
        <Form
          form={searchForm}
          layout="inline"
          onFinish={handleSearch}
        >
          <Form.Item name="name" label="角色名称">
            <Input placeholder="请输入角色名称" allowClear />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                查询
              </Button>
              <Button onClick={handleReset}>
                重置
              </Button>
              <Button type="primary" icon={<PlusOutlined />} onClick={handleAddRole}>
                新增
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </div>

      <Table
        columns={columns}
        dataSource={roleData}
        rowKey="id"
        pagination={pagination}
        loading={loading}
        onChange={(tablePagination) => {
          setPagination({
            ...pagination,
            current: tablePagination.current || 1,
          });
        }}
      />

      {/* 添加/编辑角色对话框 */}
      <Modal
        title={modalTitle}
        open={modalVisible}
        onOk={handleModalOk}
        onCancel={() => setModalVisible(false)}
        destroyOnClose
      >
        <Form
          form={form}
          layout="vertical"
        >
          <Form.Item
            name="name"
            label="角色名称"
            rules={[{ required: true, message: '请输入角色名称' }]}
          >
            <Input placeholder="请输入角色名称" />
          </Form.Item>
          
          <Form.Item
            name="remark"
            label="备注"
          >
            <Input.TextArea 
              rows={4} 
              placeholder="请输入备注" 
            />
          </Form.Item>
        </Form>
      </Modal>

      {/* 分配权限对话框 */}
      <Drawer
        title="权限配置"
        open={drawerVisible}
        onClose={() => setDrawerVisible(false)}
        width={800}
        footer={
          <div style={{ textAlign: 'right' }}>
            <Button onClick={() => setDrawerVisible(false)} style={{ marginRight: 8 }}>
              取消
            </Button>
            <Button type="primary" onClick={handlePermissionOk}>
              确定
            </Button>
          </div>
        }
      >
        <Tabs defaultActiveKey="menu">
          <Tabs.TabPane tab="菜单权限" key="menu">
            <div style={{ marginBottom: 16 }}>
              <Input.Search
                placeholder="搜索菜单"
                value={searchPattern}
                onChange={(e) => setSearchPattern(e.target.value)}
                style={{ width: 200 }}
              />
            </div>
            <Tree
              checkable
              checkedKeys={selectedMenuIds}
              onCheck={(checkedKeys) => setSelectedMenuIds(checkedKeys as number[])}
              treeData={menuData}
              height={400}
            />
          </Tabs.TabPane>
          <Tabs.TabPane tab="接口权限" key="api">
            <div style={{ marginBottom: 16 }}>
              <Input.Search
                placeholder="搜索接口"
                value={searchPattern}
                onChange={(e) => setSearchPattern(e.target.value)}
                style={{ width: 200 }}
              />
            </div>
            <Tree
              checkable
              checkedKeys={selectedApiIds}
              onCheck={(checkedKeys) => setSelectedApiIds(checkedKeys as string[])}
              treeData={apiData}
              height={400}
            />
          </Tabs.TabPane>
        </Tabs>
      </Drawer>
    </Card>
  );
};

export default RoleManagement;