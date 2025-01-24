// src/pages/Admin/CreatePost.tsx
import React, { useState } from 'react';
import { Form, Input, Button, message } from 'antd';
import { useNavigate } from 'react-router-dom';
import { createPost } from '../../services/api';

const { TextArea } = Input;

const CreatePost: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const onFinish = async (values: { title: string; content: string }) => {
    setLoading(true);
    try {
      await createPost(values);
      message.success('文章创建成功');
      navigate('/admin/posts');
    } catch (error) {
      message.error('创建文章失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Form
      layout="vertical"
      onFinish={onFinish}
    >
      <Form.Item
        label="标题"
        name="title"
        rules={[{ required: true, message: '请输入标题' }]}
      >
        <Input />
      </Form.Item>

      <Form.Item
        label="内容"
        name="content"
        rules={[{ required: true, message: '请输入内容' }]}
      >
        <TextArea rows={6} />
      </Form.Item>

      <Form.Item>
        <Button type="primary" htmlType="submit" loading={loading}>
          创建文章
        </Button>
      </Form.Item>
    </Form>
  );
};

export default CreatePost;