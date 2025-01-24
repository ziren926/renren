// src/components/Navbar/index.tsx
import React, { useState } from 'react';
import { Layout, Menu, Button, Space, Input } from 'antd';
import {
  HomeOutlined,
  FireOutlined,
  TeamOutlined,
  SearchOutlined,
  EditOutlined
} from '@ant-design/icons';
import { Link, useLocation, useNavigate, useSearchParams } from 'react-router-dom';
import { logout } from '../../services/api';
import './styles.css';

const { Header } = Layout;
const { Search } = Input;

const Navbar: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [currentTab, setCurrentTab] = useState(location.pathname);
  const [searchParams] = useSearchParams();

  // 获取用户信息
  const user = JSON.parse(localStorage.getItem('user') || 'null');

  // 搜索处理
  const handleSearch = (value: string) => {
    if (!value.trim()) {
      navigate('/');
      return;
    }
    navigate(`/?search=${encodeURIComponent(value.trim())}`, { replace: true });
  };

  const menuItems = [
    {
      key: '/',
      icon: <HomeOutlined />,
      label: '首页'
    },
    {
      key: '/trending',
      icon: <FireOutlined />,
      label: '最近热榜'
    },
    {
      key: '/discuss',
      icon: <TeamOutlined />,
      label: '需求交流'
    }
  ];

  return (
    <Header className="navbar">
      <div className="navbar-content">
        {/* 左侧品牌区域 */}
        <div className="brand">
          <Link to="/">
            <span className="brand-name">人人都是AI产品经理</span>
          </Link>
        </div>

        {/* 中间导航区域 */}
        <div className="navbar-center">
          <Menu
            mode="horizontal"
            selectedKeys={[currentTab]}
            items={menuItems}
            onClick={({key}) => {
              setCurrentTab(key);
              navigate(key);
            }}
            className="nav-menu"
          />
          <Search
            placeholder="搜索帖子..."
            allowClear
            onSearch={handleSearch}
            className="search-input"
            prefix={<SearchOutlined />}
            defaultValue={searchParams.get('search') || ''}
          />
        </div>

        {/* 右侧功能区域 */}
        <div className="navbar-right">
          <Space size="middle">
            {user ? (
              <>
                {/* 登录后显示时间和用户名 */}
                <span className="time-user-info">
                  2025-01-23 08:20:55 | ziren926
                </span>
                <Button type="primary" icon={<EditOutlined />}>
                  <Link to="/write" style={{ color: 'inherit' }}>写文档</Link>
                </Button>
                <Button type="text" onClick={logout}>
                  退出
                </Button>
              </>
            ) : (
              <>
                {/* 未登录状态 */}
                <Button type="text">
                  <Link to="/login">登录</Link>
                </Button>
                <Button type="text">
                  <Link to="/register">注册</Link>
                </Button>
                {/* 未登录时点击写文档跳转到登录页面 */}
                <Button type="primary" icon={<EditOutlined />}>
                  <Link to="/login" style={{ color: 'inherit' }}>写文档</Link>
                </Button>
              </>
            )}
          </Space>
        </div>
      </div>
    </Header>
  );
};

export default Navbar;