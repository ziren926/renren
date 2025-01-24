"use strict";
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = __importDefault(require("express"));
const jsonwebtoken_1 = __importDefault(require("jsonwebtoken"));
const User_1 = __importDefault(require("../models/User"));
const router = express_1.default.Router();
const JWT_SECRET = 'your-secret-key'; // 在生产环境中应该使用环境变量
// 注册路由
router.post('/register', (req, res) => __awaiter(void 0, void 0, void 0, function* () {
    try {
        const { username, password } = req.body;
        // 检查用户是否已存在
        const existingUser = yield User_1.default.findOne({ username });
        if (existingUser) {
            return res.status(400).json({
                success: false,
                message: '用户名已存在'
            });
        }
        // 创建新用户
        const user = new User_1.default({ username, password });
        yield user.save();
        // 创建用户响应对象
        const userResponse = {
            id: user._id.toString(),
            username: user.username
        };
        // 生成 JWT token
        const token = jsonwebtoken_1.default.sign({ _id: user._id }, JWT_SECRET);
        res.status(201).json({
            success: true,
            data: {
                token,
                user: userResponse
            }
        });
    }
    catch (error) {
        res.status(400).json({
            success: false,
            message: error instanceof Error ? error.message : '注册失败'
        });
    }
}));
exports.default = router;
