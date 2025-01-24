// src/pages/Home.tsx
import React, { useState, useEffect } from 'react';
import { List, Space, Spin, Empty, message } from 'antd';
import { useSearchParams } from 'react-router-dom';
import { getPosts, searchPosts } from '../services/api';
import type { Post } from '../types';

const Home: React.FC = () => {
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchParams] = useSearchParams();
  const searchQuery = searchParams.get('search') || '';

  // 监听 URL 搜索参数变化
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        if (searchQuery) {
          // 如果有搜索参数，执行搜索
          const response = await searchPosts(searchQuery);
          if (response.success) {
            setPosts(response.data);
            if (response.data.length > 0) {
              message.success(`找到 ${response.data.length} 篇相关文章`);
            }
          }
        } else {
          // 否则获取所有帖子
          const response = await getPosts();
          if (response.success) {
            setPosts(response.data);
          }
        }
      } catch (error) {
        message.error('获取数据失败，请稍后重试');
        console.error('Fetch error:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [searchQuery]); // 依赖于 searchQuery，当它变化时重新获取数据

  return (
    <div style={{ padding: '24px' }}>
      {/* 搜索结果提示 */}
      {searchQuery && !loading && (
        <div style={{
          marginBottom: '24px',
          padding: '16px',
          background: '#f5f5f5',
          borderRadius: '4px'
        }}>
          <span style={{ color: '#666' }}>
            搜索 "{searchQuery}" 的结果：
            {posts.length > 0 ? `找到 ${posts.length} 篇文章` : '没有找到相关文章'}
          </span>
          <a
            href="/"
            onClick={(e) => {
              e.preventDefault();
              window.location.href = '/';
            }}
            style={{
              marginLeft: '16px',
              color: '#1890ff'
            }}
          >
            返回全部文章
          </a>
        </div>
      )}

      {/* 加载状态 */}
      {loading ? (
        <div style={{
          textAlign: 'center',
          marginTop: '50px',
          marginBottom: '50px'
        }}>
          <Spin size="large" tip="加载中..." />
        </div>
      ) : posts.length === 0 ? (
        <Empty
          description={
            searchQuery
              ? `没有找到包含 "${searchQuery}" 的文章`
              : "暂无文章"
          }
          style={{ margin: '50px 0' }}
        />
      ) : (
        // 文章列表
        <List
          itemLayout="vertical"
          size="large"
          pagination={{
            pageSize: 10,
            total: posts.length,
            showTotal: (total) => `共 ${total} 篇文章`
          }}
          dataSource={posts}
          renderItem={(post) => (
            <List.Item
              key={post._id}
              extra={
                <div style={{
                  color: '#999',
                  fontSize: '14px',
                  minWidth: '150px'
                }}>
                  <Space direction="vertical" size="small">
                    <span>作者：{post.author}</span>
                    <span>发布时间：{new Date(post.createdAt).toLocaleString('zh-CN', {
                      year: 'numeric',
                      month: '2-digit',
                      day: '2-digit',
                      hour: '2-digit',
                      minute: '2-digit',
                      second: '2-digit'
                    })}</span>
                  </Space>
                </div>
              }
            >
              <List.Item.Meta
                title={
                  <div style={{
                    fontSize: '18px',
                    fontWeight: 'bold',
                    marginBottom: '12px'
                  }}>
                    {post.title}
                  </div>
                }
                description={
                  <div style={{
                    color: 'rgba(0, 0, 0, 0.65)',
                    whiteSpace: 'pre-wrap',
                    lineHeight: '1.8'
                  }}>
                    {post.content.substring(0, 200) + (post.content.length > 200 ? '...' : '')}
                  </div>
                }
              />
            </List.Item>
          )}
        />
      )}
    </div>
  );
};

export default Home;