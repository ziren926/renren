import express from 'express';
import cors from 'cors';
import mongoose from 'mongoose';
import postsRouter from './routes/posts';
import authRouter from './routes/auth.routes';

const app = express();
const port = 3001; // 修改端口以匹配前端请求

// MongoDB 连接
const MONGODB_URI = 'mongodb+srv://zirenwang163:a1t4kCF2EhoO6D7W@cluster0.iotq8.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0';

// 连接 MongoDB
console.log('Attempting to connect to MongoDB...');

mongoose.connect(MONGODB_URI)
  .then(() => {
    console.log('Successfully connected to MongoDB.');
  })
  .catch((error) => {
    console.error('MongoDB connection error:', error);
    process.exit(1); // 如果连接失败，终止程序
  });

// 监听连接事件
mongoose.connection.on('connected', () => {
  console.log('Mongoose connected to MongoDB');
});

mongoose.connection.on('error', (err) => {
  console.error('Mongoose connection error:', err);
});

mongoose.connection.on('disconnected', () => {
  console.log('Mongoose disconnected');
});

// 中间件
app.use(cors({
  origin: 'http://localhost:3000', // 允许前端域名
  credentials: true // 允许携带认证信息
}));
app.use(express.json());

// 添加路由日志中间件
app.use((req, res, next) => {
  console.log(`${req.method} ${req.path}`, {
    headers: req.headers,
    body: req.body
  });
  next();
});

// 路由
app.use('/api/auth', authRouter);
app.use('/api/posts', postsRouter);

// 测试路由
app.get('/api/health', (_req, res) => {
  res.json({ 
    status: 'ok', 
    message: 'Server is running',
    dbStatus: mongoose.connection.readyState // 添加数据库连接状态
  });
});

// 错误处理中间件
app.use((err: any, req: express.Request, res: express.Response, next: express.NextFunction) => {
  console.error('Error:', err);
  res.status(err.status || 500).json({
    success: false,
    message: err.message || '服务器内部错误'
  });
});

// 启动服务器
app.listen(port, () => {
  console.log(`Server is running on http://localhost:${port}`);
});

// 处理程序终止
process.on('SIGINT', async () => {
  try {
    await mongoose.connection.close();
    console.log('Mongoose connection closed through app termination');
    process.exit(0);
  } catch (error) {
    console.error('Error closing mongoose connection:', error);
    process.exit(1);
  }
});