// src/components/Header/index.tsx
import React from 'react';
import { Layout, Input, Avatar, Space, Dropdown, Menu } from 'antd';
import { SearchOutlined, CustomerServiceOutlined, UserOutlined } from '@ant-design/icons';
import { Link, useNavigate } from 'react-router-dom';
import './styles.scss';

const { Header } = Layout;
const { Search } = Input;

interface HeaderProps {
  // 保留现有的 props
  current?: string;
  setCurrent?: (key: string) => void;
}

const AppHeader: React.FC<HeaderProps> = ({ current, setCurrent }) => {
  const navigate = useNavigate();

  const handleMenuClick = (key: string) => {
    if (setCurrent) {
      setCurrent(key);
    }
  };

  const userMenu = (
    <Menu>
      <Menu.Item key="admin" onClick={() => handleMenuClick('admin')}>
        <Link to="/admin">管理后台</Link>
      </Menu.Item>
      <Menu.Item key="profile">
        <Link to="/profile">个人信息</Link>
      </Menu.Item>
      <Menu.Item key="settings">
        <Link to="/settings">设置</Link>
      </Menu.Item>
      <Menu.Divider />
      <Menu.Item key="logout">
        退出登录
      </Menu.Item>
    </Menu>
  );

  return (
    <Header className="app-header">
      <div className="header-content">
        {/* 左侧品牌区域 */}
        <div className="brand">
          <Link to="/" onClick={() => handleMenuClick('home')}>
            {/* 如果有 logo，添加这行 */}
            {/* <img src={logo} alt="Logo" className="logo" /> */}
            <span className="brand-name">AI Chat</span>
          </Link>
        </div>

        {/* 右侧功能区域 */}
        <div className="header-right">
          <Space size="large">
            <Search
              placeholder="搜索文章..."
              allowClear
              onSearch={(value) => console.log(value)}
              className="search-input"
            />
            <Link to="/customer-service" className="nav-item">
              <CustomerServiceOutlined />
              <span>客服</span>
            </Link>
            <Dropdown overlay={userMenu} trigger={['click']}>
              <div className="user-avatar">
                <Avatar size="large" icon={<UserOutlined />} />
              </div>
            </Dropdown>
          </Space>
        </div>
      </div>
    </Header>
  );
};

export default AppHeader;