import React, {useEffect, useState} from 'react';
import {Button, Card, Form, Input, InputNumber, message, Modal, Popconfirm, Space, Table, TreeSelect,} from 'antd';
import {DeleteOutlined, EditOutlined, PlusOutlined} from '@ant-design/icons';
import {type Dept, deptApi, type DeptCreate, type DeptUpdate} from '../../../api/dept';

// 查询参数接口
interface QueryParams {
  name?: string;
}

// TreeSelect数据项接口
interface TreeDataItem {
  title: string;
  value: number;
  children?: TreeDataItem[] | undefined;
}

const DeptManagement: React.FC = () => {
  const [loading, setLoading] = useState<boolean>(false);
  const [deptList, setDeptList] = useState<Dept[]>([]);
  const [modalVisible, setModalVisible] = useState<boolean>(false);
  const [currentDept, setCurrentDept] = useState<Dept | null>(null);
  const [queryParams, setQueryParams] = useState<QueryParams>({});
  const [isDisabled, setIsDisabled] = useState<boolean>(false);
  const [form] = Form.useForm();

  // 加载部门数据
  useEffect(() => {
    fetchDeptList();
  }, []);

  // 获取部门列表
  const fetchDeptList = async () => {
    setLoading(true);
    try {
      const response = await deptApi.list(queryParams);
      setDeptList(response.data);
    } catch (error) {
      message.error('获取部门列表失败');
    } finally {
      setLoading(false);
    }
  };

  // 搜索部门
  const handleSearch = () => {
    fetchDeptList();
  };

  // 表格列配置
  const columns = [
    {
      title: '部门名称',
      dataIndex: 'name',
      key: 'name',
      width: 'auto',
      align: 'center' as const,
      ellipsis: { tooltip: true },
    },
    {
      title: '备注',
      dataIndex: 'desc',
      key: 'desc',
      align: 'center' as const,
      width: 'auto',
      ellipsis: { tooltip: true },
    },
    {
      title: '操作',
      key: 'actions',
      width: 'auto',
      align: 'center' as const,
      fixed: 'right' as const,
      render: (text: string, record: Dept) => (
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
    setIsDisabled(false);
    form.resetFields();
    form.setFieldsValue({ order: 0 });
    setModalVisible(true);
  };

  // 处理编辑
  const handleEdit = (dept: Dept) => {
    setCurrentDept(dept);
    // 如果是顶级部门（parent_id为0），禁用父级部门选择
    setIsDisabled(dept.parent_id === 0);
    form.setFieldsValue({
      name: dept.name,
      parent_id: dept.parent_id === 0 ? undefined : dept.parent_id,
      desc: dept.remark,
      order: dept.order,
    });
    setModalVisible(true);
  };

  // 处理删除
  const handleDelete = async (id: number) => {
    try {
      await deptApi.delete(id);
      message.success('删除成功');
      fetchDeptList();
    } catch (error) {
      message.error('删除失败');
    }
  };

  // 处理表单提交
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      
      if (currentDept) {
        // 编辑
        const updateData: DeptUpdate = {
          id: currentDept.id,
          name: values.name,
          parent_id: values.parent_id || 0,
          order: values.order,
          remark: values.desc,
        };
        await deptApi.update(updateData);
        message.success('更新成功');
      } else {
        // 新增
        const createData: DeptCreate = {
          name: values.name,
          parent_id: values.parent_id || 0,
          order: values.order,
          remark: values.desc,
        };
        await deptApi.create(createData);
        message.success('添加成功');
      }
      
      setModalVisible(false);
      fetchDeptList();
    } catch (error) {
      message.error(currentDept ? '更新失败' : '添加失败');
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
    <div className="dept-management">
      <Card title="部门列表">
        {/* 查询栏 */}
        <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', gap: 16 }}>
            <Input
              placeholder="请输入部门名称"
              value={queryParams.name}
              onChange={(e) => setQueryParams({ ...queryParams, name: e.target.value })}
              onPressEnter={handleSearch}
              style={{ width: 200 }}
              allowClear
            />
            <Button type="primary" onClick={handleSearch}>
              搜索
            </Button>
          </div>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleAdd}
          >
            新建部门
          </Button>
        </div>

        {/* 表格 */}
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
          labelCol={{ span: 6 }}
          wrapperCol={{ span: 18 }}
        >
          <Form.Item
            name="parent_id"
            label="父级部门"
          >
            <TreeSelect
              placeholder="请选择父级部门"
              treeData={convertToTreeData(deptList)}
              allowClear
              treeDefaultExpandAll
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
            name="desc"
            label="备注"
          >
            <Input.TextArea placeholder="请输入备注" />
          </Form.Item>

          <Form.Item
            name="order"
            label="排序"
          >
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default DeptManagement;