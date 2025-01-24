// frontend/src/pages/Login.tsx
import React from 'react';
import { Form, Input, Button, Card, message } from 'antd';
import { useNavigate } from 'react-router-dom';
import { login } from '../services/api';

interface LoginForm {
  username: string;
  password: string;
}

const Login: React.FC = () => {
  const navigate = useNavigate();
  const [form] = Form.useForm();

  const onFinish = async (values: LoginForm) => {
    try {
      console.log('Login attempt with:', values); // 调试日志
      const response = await login(values);
      console.log('Login response:', response); // 调试日志

      if (response.success) {
        message.success('登录成功');
        navigate('/'); // 登录成功后跳转到首页
      } else {
        message.error(response.message || '登录失败');
      }
    } catch (error: any) {
      console.error('Login error:', error); // 调试日志
      message.error(error.response?.data?.message || '登录失败');
    }
  };

  return (
    <div style={{ maxWidth: '400px', margin: '100px auto', padding: '0 24px' }}>
      <Card title="登录">
        <Form
          form={form}
          name="login"
          onFinish={onFinish}
          autoComplete="off"
        >
          <Form.Item
            name="username"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input placeholder="用户名" />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password placeholder="密码" />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" block>
              登录
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
};

export default Login;