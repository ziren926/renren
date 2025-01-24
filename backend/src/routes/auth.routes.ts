import express, { Response } from 'express';
import jwt from 'jsonwebtoken';
import { AuthRequest, ApiResponse, AuthResponse, UserType } from '../types';
import User from '../models/User';
import { auth } from '../middleware/auth';

const router = express.Router();
const JWT_SECRET = 'your-secret-key';

// 注册路由
router.post('/register', async (req: AuthRequest, res: Response<ApiResponse<AuthResponse>>) => {
  try {
    const { username, password } = req.body;
    
    const existingUser = await User.findOne({ username });
    if (existingUser) {
      return res.status(400).json({
        success: false,
        message: '用户名已存在'
      });
    }

    const user = new User({ username, password });
    await user.save();

    const userResponse: UserType = {
      id: user._id.toString(),
      username: user.username
    };

    const token = jwt.sign({ _id: user._id }, JWT_SECRET);
    
    res.status(201).json({
      success: true,
      data: {
        token,
        user: userResponse
      }
    });
  } catch (error) {
    res.status(400).json({
      success: false,
      message: error instanceof Error ? error.message : '注册失败'
    });
  }
});

// 登录路由
router.post('/login', async (req: AuthRequest, res: Response<ApiResponse<AuthResponse>>) => {
  try {
    const { username, password } = req.body;
    
    const user = await User.findOne({ username });
    if (!user) {
      return res.status(401).json({
        success: false,
        message: '用户名或密码错误'
      });
    }

    const isMatch = await user.comparePassword(password);
    if (!isMatch) {
      return res.status(401).json({
        success: false,
        message: '用户名或密码错误'
      });
    }

    const userResponse: UserType = {
      id: user._id.toString(),
      username: user.username
    };

    const token = jwt.sign({ _id: user._id }, JWT_SECRET);
    
    res.json({
      success: true,
      data: {
        token,
        user: userResponse
      }
    });
  } catch (error) {
    res.status(400).json({
      success: false,
      message: error instanceof Error ? error.message : '登录失败'
    });
  }
});

// 验证 token
router.post('/verify-token', async (req: AuthRequest, res: Response<ApiResponse<UserType>>) => {
  try {
    const token = req.header('Authorization')?.replace('Bearer ', '');
    if (!token) {
      return res.status(401).json({
        success: false,
        message: '未提供认证令牌'
      });
    }

    const decoded = jwt.verify(token, JWT_SECRET) as { _id: string };
    const user = await User.findById(decoded._id);
    
    if (!user) {
      return res.status(401).json({
        success: false,
        message: '用户不存在'
      });
    }

    const userResponse: UserType = {
      id: user._id.toString(),
      username: user.username
    };

    res.json({
      success: true,
      data: userResponse
    });
  } catch (error) {
    res.status(401).json({
      success: false,
      message: '无效的认证令牌'
    });
  }
});

// 获取当前用户信息
router.get('/me', auth, async (req: AuthRequest, res: Response<ApiResponse<UserType>>) => {
  try {
    if (!req.user) {
      return res.status(401).json({
        success: false,
        message: '未找到用户信息'
      });
    }
    
    res.json({
      success: true,
      data: req.user
    });
  } catch (error) {
    res.status(401).json({
      success: false,
      message: error instanceof Error ? error.message : '获取用户信息失败'
    });
  }
});

export default router;