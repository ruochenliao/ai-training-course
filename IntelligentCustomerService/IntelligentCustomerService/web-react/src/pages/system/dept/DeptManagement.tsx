import React, {useEffect, useState} from 'react';
import {Button, Card, Form, Input, message, Modal, Popconfirm, Space, Switch, Table, TreeSelect,} from 'antd';
import {DeleteOutlined, EditOutlined, PlusOutlined} from '@ant-design/icons';

// 部门项接口
interface DeptItemType {
  id: number;
  name: string;
  code: string;
  parentId: number | null;
  sort: number;
  leader?: string;
  phone?: string;
  email?: string;
  status: boolean;
  children?: DeptItemType[];
}

// TreeSelect数据项接口
interface TreeDataItem {
  title: string;
  value: number;
  children?: TreeDataItem[] | undefined;
}

const DeptManagement: React.FC = () => {
  const [loading, setLoading] = useState<boolean>(false);
  const [deptList, setDeptList] = useState<DeptItemType[]>([]);
  const [modalVisible, setModalVisible] = useState<boolean>(false);
  const [currentDept, setCurrentDept] = useState<DeptItemType | null>(null);
  const [form] = Form.useForm();

  // 模拟部门数据
  const mockDeptData: DeptItemType[] = [
    {
      id: 1,
      name: '总公司',
      code: 'HQ',
      parentId: null,
      sort: 1,
      leader: '张三',
      phone: '13800138000',
      email: 'zhangsan@example.com',
      status: true,
      children: [
        {
          id: 2,
          name: '研发部',
          code: 'DEV',
          parentId: 1,
          sort: 1,
          leader: '李四',
          phone: '13800138001',
          email: 'lisi@example.com',
          status: true,
        },
        {
          id: 3,
          name: '市场部',
          code: 'MKT',
          parentId: 1,
          sort: 2,
          leader: '王五',
          phone: '13800138002',
          email: 'wangwu@example.com',
          status: true,
          children: [
            {
              id: 4,
              name: '国内市场',
              code: 'MKT-CN',
              parentId: 3,
              sort: 1,
              leader: '赵六',
              phone: '13800138003',
              email: 'zhaoliu@example.com',
              status: true,
            },
            {
              id: 5,
              name: '海外市场',
              code: 'MKT-OS',
              parentId: 3,
              sort: 2,
              leader: '钱七',
              phone: '13800138004',
              email: 'qianqi@example.com',
              status: true,
            },
          ],
        },
      ],
    },
  ];

  // 加载部门数据
  useEffect(() => {
    fetchDeptList();
  }, []);

  // 获取部门列表
  const fetchDeptList = async () => {
    setLoading(true);
    try {
      // 这里应该是从API获取数据
      // const response = await api.getDeptList();
      // setDeptList(response.data);
      
      // 使用模拟数据
      setTimeout(() => {
        setDeptList(mockDeptData);
        setLoading(false);
      }, 500);
    } catch (error) {
      message.error('获取部门列表失败');
      setLoading(false);
    }
  };

  // 表格列配置
  const columns = [
    {
      title: '部门名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '部门编码',
      dataIndex: 'code',
      key: 'code',
    },
    {
      title: '排序',
      dataIndex: 'sort',
      key: 'sort',
    },
    {
      title: '负责人',
      dataIndex: 'leader',
      key: 'leader',
    },
    {
      title: '联系电话',
      dataIndex: 'phone',
      key: 'phone',
    },
    {
      title: '邮箱',
      dataIndex: 'email',
      key: 'email',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: boolean) => (
        <Switch checked={status} disabled />
      ),
    },
    {
      title: '操作',
      key: 'action',
      render: (text: string, record: DeptItemType) => (
        <Space>
          <Button
            type="primary"
            icon={<EditOutlined />}
            size="small"
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定删除该部门吗？"
            onConfirm={() => handleDelete(record.id)}
          >
            <Button type="primary" danger icon={<DeleteOutlined />} size="small">
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  // 处理新增
  const handleAdd = () => {
    setCurrentDept(null);
    form.resetFields();
    setModalVisible(true);
  };

  // 处理编辑
  const handleEdit = (dept: DeptItemType) => {
    setCurrentDept(dept);
    form.setFieldsValue(dept);
    setModalVisible(true);
  };

  // 处理删除
  const handleDelete = (id: number) => {
    // 这里应该调用API删除部门
    message.success('删除成功');
    fetchDeptList();
  };

  // 处理表单提交
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      
      // 这里应该调用API保存数据
      if (currentDept) {
        // 编辑
        message.success('更新成功');
      } else {
        // 新增
        message.success('添加成功');
      }
      
      setModalVisible(false);
      fetchDeptList();
    } catch (error) {
      console.error('表单验证失败:', error);
    }
  };

  // 将部门列表转换为TreeSelect所需的数据结构
  const convertToTreeData = (deptList: DeptItemType[]): TreeDataItem[] => {
    return deptList.map(item => ({
      title: item.name,
      value: item.id,
      children: item.children ? convertToTreeData(item.children) : undefined,
    }));
  };

  return (
    <div className="dept-management">
      <Card
        title="部门管理"
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleAdd}
          >
            新增部门
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={deptList}
          rowKey="id"
          loading={loading}
          pagination={false}
        />
      </Card>

      {/* 部门表单对话框 */}
      <Modal
        title={currentDept ? '编辑部门' : '新增部门'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
        >
          <Form.Item
            name="name"
            label="部门名称"
            rules={[{ required: true, message: '请输入部门名称' }]}
          >
            <Input placeholder="请输入部门名称" />
          </Form.Item>

          <Form.Item
            name="code"
            label="部门编码"
            rules={[{ required: true, message: '请输入部门编码' }]}
          >
            <Input placeholder="请输入部门编码" />
          </Form.Item>

          <Form.Item
            name="parentId"
            label="上级部门"
          >
            <TreeSelect
              placeholder="请选择上级部门"
              treeData={convertToTreeData(deptList)}
              allowClear
              treeDefaultExpandAll
            />
          </Form.Item>

          <Form.Item
            name="sort"
            label="排序号"
            rules={[{ required: true, message: '请输入排序号' }]}
          >
            <Input type="number" placeholder="请输入排序号" />
          </Form.Item>

          <Form.Item
            name="leader"
            label="负责人"
          >
            <Input placeholder="请输入负责人" />
          </Form.Item>

          <Form.Item
            name="phone"
            label="联系电话"
          >
            <Input placeholder="请输入联系电话" />
          </Form.Item>

          <Form.Item
            name="email"
            label="邮箱"
          >
            <Input placeholder="请输入邮箱" />
          </Form.Item>

          <Form.Item
            name="status"
            label="状态"
            valuePropName="checked"
            initialValue={true}
          >
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default DeptManagement; 