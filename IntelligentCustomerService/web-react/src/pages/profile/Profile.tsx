import React, {useState} from 'react'
import {Avatar, Button, Form, Input, message, Tabs} from 'antd'

const { TabPane } = Tabs

interface InfoFormData {
  avatar: string
  username: string
  email: string
}

interface PasswordFormData {
  old_password: string
  new_password: string
  confirm_password: string
}

// 模拟用户数据
const mockUser = {
  userId: '1',
  name: '管理员',
  email: 'admin@example.com',
  avatar: 'https://avatars.githubusercontent.com/u/54677442?v=4',
}

const Profile: React.FC = () => {

  const [infoForm] = Form.useForm()
  const [passwordForm] = Form.useForm()
  const [loading, setLoading] = useState(false)

  // 个人信息表单初始值
  const infoInitialValues: InfoFormData = {
    avatar: mockUser.avatar,
    username: mockUser.name,
    email: mockUser.email,
  }

  // 密码表单初始值
  const passwordInitialValues: PasswordFormData = {
    old_password: '',
    new_password: '',
    confirm_password: '',
  }

  // 更新个人信息
  const updateProfile = async () => {
    setLoading(true)
    try {
      // 这里应该调用API更新用户信息
      // await api.updateUser({ ...values, id: mockUser.userId });
      message.success('个人信息更新成功')
    } catch (error) {
      message.error('更新失败，请重试')
    } finally {
      setLoading(false)
    }
  }

  // 更新密码
  const updatePassword = async () => {
    setLoading(true)
    try {
      // 这里应该调用API更新密码
      // await api.updatePassword({ ...values, id: mockUser.userId });
      message.success('密码更新成功')
      passwordForm.resetFields()
    } catch (error) {
      message.error('密码更新失败，请重试')
    } finally {
      setLoading(false)
    }
  }

  // 密码确认验证
  const validateConfirmPassword = (_: unknown, value: string) => {
    const newPassword = passwordForm.getFieldValue('new_password')
    if (value && value !== newPassword) {
      return Promise.reject(new Error('两次输入的密码不一致'))
    }
    return Promise.resolve()
  }

  return (
    <div style={{ padding: '24px' }}>
      <Tabs type='line' animated>
        <TabPane tab='修改信息' key='info'>
          <div style={{ margin: '30px', display: 'flex', alignItems: 'center' }}>
            <Form
              form={infoForm}
              labelCol={{ span: 4 }}
              wrapperCol={{ span: 16 }}
              style={{ width: '400px' }}
              initialValues={infoInitialValues}
              onFinish={updateProfile}
            >
              <Form.Item label='头像' name='avatar'>
                <Avatar size={100} src={infoInitialValues.avatar} />
              </Form.Item>

              <Form.Item label='用户名' name='username' rules={[{ required: true, message: '请输入用户名' }]}>
                <Input placeholder='请输入用户名' />
              </Form.Item>

              <Form.Item label='邮箱' name='email' rules={[{ type: 'email', message: '请输入有效的邮箱地址' }]}>
                <Input placeholder='请输入邮箱' />
              </Form.Item>

              <Form.Item wrapperCol={{ offset: 4, span: 16 }}>
                <Button type='primary' htmlType='submit' loading={loading}>
                  更新
                </Button>
              </Form.Item>
            </Form>
          </div>
        </TabPane>

        <TabPane tab='修改密码' key='password'>
          <Form
            form={passwordForm}
            labelCol={{ span: 6 }}
            wrapperCol={{ span: 12 }}
            style={{ margin: '30px', width: '500px' }}
            initialValues={passwordInitialValues}
            onFinish={updatePassword}
          >
            <Form.Item label='原密码' name='old_password' rules={[{ required: true, message: '请输入原密码' }]}>
              <Input.Password placeholder='请输入原密码' />
            </Form.Item>

            <Form.Item
              label='新密码'
              name='new_password'
              dependencies={['old_password']}
              rules={[
                { required: true, message: '请输入新密码' },
                ({ getFieldValue }) => ({
                  validator(_, value) {
                    if (!value || getFieldValue('old_password')) {
                      return Promise.resolve()
                    }
                    return Promise.reject(new Error('请先输入原密码'))
                  },
                }),
              ]}
            >
              <Input.Password placeholder='请输入新密码' disabled={!passwordForm.getFieldValue('old_password')} />
            </Form.Item>

            <Form.Item
              label='确认密码'
              name='confirm_password'
              dependencies={['new_password']}
              rules={[{ required: true, message: '请确认新密码' }, { validator: validateConfirmPassword }]}
            >
              <Input.Password placeholder='请确认新密码' disabled={!passwordForm.getFieldValue('new_password')} />
            </Form.Item>

            <Form.Item wrapperCol={{ offset: 6, span: 12 }}>
              <Button type='primary' htmlType='submit' loading={loading}>
                更新
              </Button>
            </Form.Item>
          </Form>
        </TabPane>
      </Tabs>
    </div>
  )
}

export default Profile
