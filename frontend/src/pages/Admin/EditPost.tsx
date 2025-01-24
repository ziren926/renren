// src/pages/Admin/EditPost.tsx
import React, { useEffect, useState } from 'react';
import { Form, Input, Button, message, Spin } from 'antd';
import { useNavigate, useParams } from 'react-router-dom';
import { getPost, updatePost } from '../../services/api';
import type { Post } from '../../types';

const { TextArea } = Input;

const EditPost: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [form] = Form.useForm();
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();

  useEffect(() => {
    const fetchPost = async () => {
      if (!id) return;
      try {
        const response = await getPost(id);
        if (response.success) {
          form.setFieldsValue(response.data);
        }
      } catch (error) {
        message.error('获取文章失败');
        navigate('/admin/posts');
      } finally {
        setLoading(false);
      }
    };

    fetchPost();
  }, [id, form, navigate]);

  const onFinish = async (values: { title: string; content: string }) => {
    if (!id) return;
    setLoading(true);
    try {
      await updatePost(id, values);
      message.success('更新文章成功');
      navigate('/admin/posts');
    } catch (error) {
      message.error('更新文章失败');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <Spin size="large" />;
  }

  return (
    <Form
      form={form}
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
          更新文章
        </Button>
      </Form.Item>
    </Form>
  );
};

export default EditPost;