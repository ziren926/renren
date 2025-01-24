// src/hooks/useSearch.ts - 自定义 Hook
import { useNavigate, useSearchParams } from 'react-router-dom';
import { message } from 'antd';
import { searchPosts } from '../services/api';

// 自定义 Hook 用于处理搜索逻辑
export const useSearch = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const handleSearch = async (value: string) => {
    if (!value.trim()) {
      navigate('/');
      return;
    }

    try {
      // 更新 URL 参数
      navigate(`/?search=${encodeURIComponent(value.trim())}`, { replace: true });
      const response = await searchPosts(value.trim());
      return response;
    } catch (error) {
      message.error('搜索失败，请稍后重试');
    }
  };

  // 从 URL 参数中获取当前搜索词
  const currentSearchValue = searchParams.get('search') || '';

  return {
    handleSearch,
    currentSearchValue
  };
};