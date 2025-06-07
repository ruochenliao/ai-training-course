import React, {useCallback, useEffect, useState} from 'react';
import {Button, Card, Form, Input, InputNumber, message, Modal, Popconfirm, Space, Table, TreeSelect} from 'antd';
import {
    DeleteOutlined,
    EditOutlined,
    FolderOutlined,
    PlusOutlined,
    ReloadOutlined,
    SearchOutlined
} from '@ant-design/icons';
import {type Dept, deptApi, type DeptCreate, type DeptUpdate} from '@/api/dept';
import {useTheme} from '@/contexts/ThemeContext';
import {cn} from '@/utils';

// TreeSelect数据项接口
interface TreeDataItem {
  title: string;
  value: number;
  children?: TreeDataItem[] | undefined;
}

const DeptManagement: React.FC = () => {
  const { isDark, primaryColor } = useTheme();
  const [loading, setLoading] = useState<boolean>(false);
  const [deptList, setDeptList] = useState<Dept[]>([]);
  const [modalVisible, setModalVisible] = useState<boolean>(false);
  const [currentDept, setCurrentDept] = useState<Dept | null>(null);
  const [isDisabled, setIsDisabled] = useState<boolean>(false);
  const [expandedKeys, setExpandedKeys] = useState<React.Key[]>([]);
  const [form] = Form.useForm();
  const [searchForm] = Form.useForm();

  // 加载部门数据
  useEffect(() => {
    fetchDeptList();
  }, []);

  // 获取部门列表
  const fetchDeptList = useCallback(async () => {
    setLoading(true);
    try {
      const values = searchForm.getFieldsValue();
      const response = await deptApi.list(values);
      
      if (response.code === 200) {
        setDeptList(response.data || []);
        
        // 默认展开所有部门
        const keys = getAllKeys(response.data || []);
        setExpandedKeys(keys);
      } else {
        message.error(response.msg || '获取部门列表失败');
        setDeptList([]);
      }
    } catch (error) {
      console.error('获取部门列表失败:', error);
      message.error('获取部门列表失败');
      setDeptList([]);
    } finally {
      setLoading(false);
    }
  }, [searchForm]);

  // 获取所有部门的key用于展开
  const getAllKeys = (data: Dept[]): React.Key[] => {
    const keys: React.Key[] = [];
    const extract = (items: Dept[]) => {
      items.forEach(item => {
        keys.push(item.id);
        if (item.children && item.children.length > 0) {
          extract(item.children);
        }
      });
    };
    extract(data);
    return keys;
  };

  // 搜索部门
  const handleSearch = () => {
    fetchDeptList();
  };

  // 重置搜索
  const handleReset = () => {
    searchForm.resetFields();
    fetchDeptList();
  };

  // 表格列配置
  const columns = [
    {
      title: '部门名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string) => (
        <div className="flex items-center">
          <FolderOutlined className="mr-2 text-blue-500" />
          <span className="font-medium">{text}</span>
        </div>
      )
    },
    {
      title: '排序',
      dataIndex: 'order',
      key: 'order',
      width: 100,
      render: (order: number) => (
        <div className="text-center">
          <span className="px-2 py-1 rounded-md bg-gray-100 text-gray-700">{order}</span>
        </div>
      )
    },
    {
      title: '备注',
      dataIndex: 'remark',
      key: 'remark',
      ellipsis: true,
      render: (remark: string) => (
        <div className="text-gray-600">{remark || '-'}</div>
      )
    },
    {
      title: '操作',
      key: 'actions',
      width: 220,
      render: (_: any, record: Dept) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<PlusOutlined />}
            onClick={() => handleAddSubDept(record)}
          >
            添加下级
          </Button>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定删除此部门吗？"
            description={<>删除后不可恢复，确认删除<b>{record.name}</b>吗？</>}
            onConfirm={() => handleDelete(record.id)}
            okButtonProps={{ danger: true }}
            okText="删除"
            cancelText="取消"
          >
            <Button 
              type="link" 
              danger 
              size="small" 
              icon={<DeleteOutlined />}
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  // 处理新增部门
  const handleAdd = () => {
    setCurrentDept(null);
    setIsDisabled(false);
    form.resetFields();
    form.setFieldsValue({ 
      parent_id: 0,
      order: 0 
    });
    setModalVisible(true);
  };

  // 处理添加子部门
  const handleAddSubDept = (parentDept: Dept) => {
    setCurrentDept(null);
    setIsDisabled(false);
    form.resetFields();
    form.setFieldsValue({ 
      parent_id: parentDept.id,
      order: 0 
    });
    setModalVisible(true);
  };

  // 处理编辑
  const handleEdit = (dept: Dept) => {
    setCurrentDept(dept);
    // 如果是顶级部门（parent_id为0），禁用父级部门选择
    setIsDisabled(dept.parent_id === 0);
    form.setFieldsValue({
      name: dept.name,
      parent_id: dept.parent_id,
      remark: dept.remark,
      order: dept.order,
    });
    setModalVisible(true);
  };

  // 处理删除
  const handleDelete = async (id: number) => {
    try {
      const response = await deptApi.delete(id);
      
      if (response.code === 200) {
        message.success('删除部门成功');
        fetchDeptList();
      } else {
        message.error(response.msg || '删除部门失败');
      }
    } catch (error) {
      console.error('删除部门失败:', error);
      message.error('删除部门失败');
    }
  };

  // 处理表单提交
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      let response;
      
      if (currentDept) {
        // 编辑
        const updateData: DeptUpdate = {
          id: currentDept.id,
          name: values.name,
          parent_id: values.parent_id,
          order: values.order,
          remark: values.remark,
        };
        response = await deptApi.update(updateData);
      } else {
        // 新增
        const createData: DeptCreate = {
          name: values.name,
          parent_id: values.parent_id,
          order: values.order,
          remark: values.remark,
        };
        response = await deptApi.create(createData);
      }
      
      if (response.code === 200) {
        message.success(currentDept ? '更新部门成功' : '添加部门成功');
        setModalVisible(false);
        fetchDeptList();
      } else {
        message.error(response.msg || (currentDept ? '更新部门失败' : '添加部门失败'));
      }
    } catch (error) {
      console.error(currentDept ? '更新部门失败' : '添加部门失败', error);
      message.error(currentDept ? '更新部门失败' : '添加部门失败');
    }
  };

  // 将部门列表转换为TreeSelect所需的数据结构
  const convertToTreeData = (deptList: Dept[]): TreeDataItem[] => {
    return deptList.map(item => ({
      title: item.name,
      value: item.id,
      children: item.children ? convertToTreeData(item.children) : undefined,
    }));
  };

  return (
    <div className="dept-management h-full">
      <Card 
        className={cn(
          "h-full rounded-lg overflow-hidden",
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
            className="gap-4 flex-wrap"
            style={{ rowGap: '12px' }}
          >
            <Form.Item name="name" label="部门名称">
              <Input placeholder="请输入部门名称" allowClear />
            </Form.Item>
            <Form.Item>
              <Space>
                <Button 
                  type="primary" 
                  htmlType="submit" 
                  icon={<SearchOutlined />}
                  style={{ backgroundColor: primaryColor }}
                >
                  搜索
                </Button>
                <Button 
                  icon={<ReloadOutlined />} 
                  onClick={handleReset}
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
            "text-lg font-medium",
            isDark ? "text-white" : "text-gray-800"
          )}>
            部门列表
          </div>
          <Space>
            <Button 
              type="primary" 
              icon={<PlusOutlined />} 
              onClick={handleAdd}
              style={{ backgroundColor: primaryColor }}
            >
              新增部门
            </Button>
            <Button 
              icon={<ReloadOutlined />} 
              onClick={() => fetchDeptList()}
            >
              刷新
            </Button>
          </Space>
        </div>
        
        {/* 部门表格 */}
        <Table
          columns={columns}
          dataSource={deptList}
          rowKey="id"
          loading={loading}
          pagination={false}
          expandable={{
            expandedRowKeys: expandedKeys,
            onExpandedRowsChange: (expandedRows) => {
              setExpandedKeys(expandedRows as React.Key[]);
            }
          }}
          className={isDark ? "ant-table-dark" : ""}
        />
      </Card>

      {/* 部门表单弹窗 */}
      <Modal
        title={currentDept ? '编辑部门' : '新增部门'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        width={550}
      >
        <Form
          form={form}
          layout="vertical"
          requiredMark={false}
        >
          <Form.Item
            name="parent_id"
            label="上级部门"
            rules={[{ required: true, message: '请选择上级部门' }]}
          >
            <TreeSelect
              treeData={[
                { title: '顶级部门', value: 0 },
                ...convertToTreeData(deptList)
              ]}
              placeholder="请选择上级部门"
              style={{ width: '100%' }}
              dropdownStyle={{ maxHeight: 400, overflow: 'auto' }}
              allowClear
              showSearch
              treeNodeFilterProp="title"
              disabled={isDisabled}
            />
          </Form.Item>
          
          <Form.Item
            name="name"
            label="部门名称"
            rules={[{ required: true, message: '请输入部门名称' }]}
          >
            <Input placeholder="请输入部门名称" />
          </Form.Item>
          
          <Form.Item
            name="order"
            label="排序"
            rules={[{ required: true, message: '请输入排序' }]}
          >
            <InputNumber min={0} placeholder="请输入排序" style={{ width: '100%' }} />
          </Form.Item>
          
          <Form.Item
            name="remark"
            label="备注"
          >
            <Input.TextArea rows={3} placeholder="请输入备注" maxLength={200} showCount />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default DeptManagement;