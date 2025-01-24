// src/App.tsx
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from 'antd';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';
import AdminDashboard from './pages/Admin/Dashboard';
import PostManagement from './pages/Admin/PostManagement';
import CreatePost from './components/CreatePost';
import EditPost from './pages/Admin/EditPost';
import PrivateRoute from './components/PrivateRoute';
import { AuthProvider } from './contexts/AuthContext';

const { Content } = Layout;

const App: React.FC = () => {
  // 获取当前用户信息
  const user = JSON.parse(localStorage.getItem('user') || 'null');
  const currentTime = '2025-01-23 08:32:54';
  const currentUser = 'ziren926';

  // Write 路由处理组件
  const WriteRoute: React.FC = () => {
    if (user) {
      // 如果用户已登录，重定向到创建文章页面
      return <Navigate to="/admin/posts/create" />;
    }
    // 如果用户未登录，重定向到登录页面
    return <Navigate to="/login" />;
  };

  return (
    <AuthProvider>
      <Router>
        <Layout className="layout">
          <Navbar />
          <Content style={{ padding: '0 50px', marginTop: 64 }}>
            <div className="site-layout-content" style={{
              padding: 24,
              minHeight: 'calc(100vh - 64px)',
              background: '#fff'
            }}>
              <Routes>
                {/* 公共路由 */}
                <Route path="/" element={<Home />} />
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />

                {/* Write 路由 - 根据登录状态重定向 */}
                <Route path="/write" element={<WriteRoute />} />

                {/* 受保护的管理员路由 */}
                <Route
                  path="/admin"
                  element={
                    <PrivateRoute>
                      <AdminDashboard />
                    </PrivateRoute>
                  }
                />
                <Route
                  path="/admin/posts"
                  element={
                    <PrivateRoute>
                      <PostManagement />
                    </PrivateRoute>
                  }
                />
                <Route
                  path="/admin/posts/create"
                  element={
                    <PrivateRoute>
                      <CreatePost />
                    </PrivateRoute>
                  }
                />
                <Route
                  path="/admin/posts/edit/:id"
                  element={
                    <PrivateRoute>
                      <EditPost />
                    </PrivateRoute>
                  }
                />
                <Route path="/posts/create" element={<CreatePost />} />
              </Routes>
            </div>
          </Content>
        </Layout>
      </Router>
    </AuthProvider>
  );
};

export default App;