import express, { Response } from 'express';
import { AuthRequest, ApiResponse } from '../types';
import Post, { IPost } from '../models/Post';
import { auth } from '../middleware/auth';

const router = express.Router();

// 获取所有帖子
router.get('/', async (_req: AuthRequest, res: Response<ApiResponse<IPost[]>>) => {
  try {
    const posts = await Post.find().sort({ createdAt: -1 });
    res.json({
      success: true,
      data: posts
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: '获取帖子失败'
    });
  }
});

// 创建新帖子
router.post('/', auth, async (req: AuthRequest, res: Response<ApiResponse<IPost>>) => {
  try {
    const { title, content } = req.body;
    
    if (!req.user) {
      throw new Error('未找到用户信息');
    }

    const post = new Post({
      title,
      content,
      author: req.user.username
    });

    await post.save();

    res.status(201).json({
      success: true,
      data: post
    });
  } catch (error) {
    res.status(400).json({
      success: false,
      message: error instanceof Error ? error.message : '创建帖子失败'
    });
  }
});

// 获取单个帖子
router.get('/:id', async (req: AuthRequest, res: Response<ApiResponse<IPost>>) => {
  try {
    const post = await Post.findById(req.params.id);
    if (!post) {
      return res.status(404).json({
        success: false,
        message: '帖子不存在'
      });
    }

    res.json({
      success: true,
      data: post
    });
  } catch (error) {
    res.status(400).json({
      success: false,
      message: error instanceof Error ? error.message : '获取帖子失败'
    });
  }
});

export default router;