// src/pages/Admin/PostManagement.tsx
import React, { useEffect, useState } from 'react';
import { Table, Space, Button, Popconfirm, message } from 'antd';
import { Link } from 'react-router-dom';
import { getPosts, deletePost } from '../../services/api';
import type { Post } from '../../types';

const PostManagement: React.FC = () => {
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchPosts = async () => {
    try {
      const response = await getPosts();
      if (response.success) {
        setPosts(response.data);
      }
    } catch (error) {
      message.error('获取文章列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPosts();
  }, []);

  const handleDelete = async (id: string) => {
    try {
      const response = await deletePost(id);
      if (response.success) {
        message.success('删除文章成功');
        fetchPosts();
      }
    } catch (error) {
      message.error('删除文章失败');
    }
  };

  const columns = [
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
    },
    {
      title: '作者',
      dataIndex: 'author',
      key: 'author',
    },
    {
      title: '创建时间',
      dataIndex: 'createdAt',
      key: 'createdAt',
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: Post) => (
        <Space size="middle">
          <Link to={`/admin/posts/edit/${record._id}`}>
            <Button type="primary">编辑</Button>
          </Link>
          <Popconfirm
            title="确定要删除这篇文章吗？"
            onConfirm={() => handleDelete(record._id)}
            okText="确定"
            cancelText="取消"
          >
            <Button danger>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Link to="/admin/posts/create">
          <Button type="primary">创建新文章</Button>
        </Link>
      </div>
      <Table
        columns={columns}
        dataSource={posts}
        loading={loading}
        rowKey="_id"
      />
    </div>
  );
};

export default PostManagement;