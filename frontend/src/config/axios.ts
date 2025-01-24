import axios from 'axios';

// 创建 axios 实例
const api = axios.create({
  baseURL: 'http://localhost:5000', // 确保这里的端口号与你的后端端口一致
  timeout: 10000,
});

export default api; 