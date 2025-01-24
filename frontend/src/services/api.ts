// src/services/api.ts
import axios, { AxiosResponse } from 'axios';
import type { Post, ApiResponse, LoginForm, RegisterForm, User, LoginResponse } from '../types';

const API_BASE_URL = 'http://localhost:3001/api';
const CURRENT_TIME = '2025-01-23 09:20:14';
const CURRENT_USER = 'ziren926';

// 创建 axios 实例
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器 - 修复类型错误
api.interceptors.response.use(
  (response: AxiosResponse) => {
    // 将响应数据包装在一个新的 AxiosResponse 对象中
    return {
      ...response,
      data: {
        success: response.data.success,
        data: response.data.data,
        message: response.data.message,
        metadata: {
          currentUser: CURRENT_USER,
          timestamp: CURRENT_TIME
        }
      }
    };
  },
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// 认证相关 API
export const login = async (data: { username: string; password: string }): Promise<ApiResponse<LoginResponse>> => {
  console.log('Making login request:', data); // 调试日志
  try {
    const response = await api.post('/auth/login', data);
    console.log('Login API response:', response); // 调试日志

    if (response.data.success) {
      // 保存 token 和用户信息
      localStorage.setItem('token', response.data.data.token);
      localStorage.setItem('user', JSON.stringify(response.data.data.user));
    }
    return response.data;
  } catch (error) {
    console.error('Login API error:', error); // 调试日志
    throw error;
  }
};

export const register = async (data: RegisterForm): Promise<ApiResponse<User>> => {
  console.log('Sending registration request:', data); // 添加调试日志
  try {
    const response = await api.post('/auth/register', data);
    console.log('Registration response:', response); // 添加调试日志
    return response.data;
  } catch (error) {
    console.error('Registration error:', error); // 添加错误日志
    throw error;
  }
};

export const logout = () => {
  localStorage.removeItem('token');
  localStorage.removeItem('user');
  window.location.reload();
};

// 帖子相关 API
export const getPosts = async (): Promise<ApiResponse<Post[]>> => {
  const response = await api.get('/posts');
  return response.data;
};

export const getPost = async (id: string): Promise<ApiResponse<Post>> => {
  const response = await api.get(`/posts/${id}`);
  return response.data;
};

export const createPost = async (data: { title: string; content: string }): Promise<ApiResponse<Post>> => {
  const response = await api.post('/posts', {
    ...data,
    author: CURRENT_USER
  });
  return response.data;
};

export const updatePost = async (id: string, data: { title: string; content: string }): Promise<ApiResponse<Post>> => {
  const response = await api.put(`/posts/${id}`, {
    ...data,
    author: CURRENT_USER
  });
  return response.data;
};

export const deletePost = async (id: string): Promise<ApiResponse<null>> => {
  const response = await api.delete(`/posts/${id}`);
  return response.data;
};

export const searchPosts = async (query: string): Promise<ApiResponse<Post[]>> => {
  const response = await api.get(`/posts/search?query=${encodeURIComponent(query)}`);
  return response.data;
};

export default api;