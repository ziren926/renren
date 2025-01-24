import { Request } from 'express';

// 用户文档接口
export interface IUser {
  username: string;
  password: string;
  comparePassword(candidatePassword: string): Promise<boolean>;
}

// API中使用的用户类型
export interface UserType {
  id: string;
  username: string;
}

// 认证请求扩展
export interface AuthRequest extends Request {
  user?: UserType;
}

// API响应格式
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
}

// 认证响应格式
export interface AuthResponse {
  token: string;
  user: UserType;
}
