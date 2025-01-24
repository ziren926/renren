import { Response, NextFunction } from 'express';
import jwt from 'jsonwebtoken';
import { AuthRequest } from '../types';
import User from '../models/User';

const JWT_SECRET = 'your-secret-key';

export const auth = async (req: AuthRequest, res: Response, next: NextFunction) => {
  try {
    const token = req.header('Authorization')?.replace('Bearer ', '');
    if (!token) {
      throw new Error('未提供认证令牌');
    }

    const decoded = jwt.verify(token, JWT_SECRET) as { _id: string };
    const user = await User.findById(decoded._id);
    
    if (!user) {
      throw new Error('用户不存在');
    }

    req.user = {
      id: user._id.toString(),
      username: user.username
    };
    
    next();
  } catch (error) {
    res.status(401).json({
      success: false,
      message: '请先登录'
    });
  }
};