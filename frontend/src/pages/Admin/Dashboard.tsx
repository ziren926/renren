import React from 'react';
import { Card, Row, Col, Button } from 'antd';
import { EditOutlined, FileTextOutlined } from '@ant-design/icons';
import { Link } from 'react-router-dom';

const AdminDashboard: React.FC = () => {
  return (
    <div>
      <h1>管理後台</h1>
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12}>
          <Card>
            <h2>
              <FileTextOutlined /> 文章管理
            </h2>
            <p>管理所有的博客文章，包括創建、編輯和刪除操作。</p>
            <Link to="/admin/posts">
              <Button type="primary">
                進入文章管理
              </Button>
            </Link>
          </Card>
        </Col>
        <Col xs={24} sm={12}>
          <Card>
            <h2>
              <EditOutlined /> 創建新文章
            </h2>
            <p>創建一篇新的博客文章。</p>
            <Link to="/admin/posts/create">
              <Button type="primary">
                創建文章
              </Button>
            </Link>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default AdminDashboard;