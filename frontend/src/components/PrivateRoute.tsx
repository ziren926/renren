// src/components/PrivateRoute.tsx
import React from 'react';
import { Navigate } from 'react-router-dom';

interface PrivateRouteProps {
  children: React.ReactNode;
}

const PrivateRoute: React.FC<PrivateRouteProps> = ({ children }) => {
  const user = JSON.parse(localStorage.getItem('user') || 'null');

  if (!user) {
    // 如果用户未登录，重定向到登录页面
    return <Navigate to="/login" />;
  }

  // 如果用户已登录，渲染子组件
  return <>{children}</>;
};

export default PrivateRoute;