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
const cors_1 = __importDefault(require("cors"));
const mongoose_1 = __importDefault(require("mongoose"));
const posts_1 = __importDefault(require("./routes/posts"));
const auth_routes_1 = __importDefault(require("./routes/auth.routes"));
const app = (0, express_1.default)();
const port = 3001; // 修改端口以匹配前端请求
// MongoDB 连接
const MONGODB_URI = 'mongodb+srv://zirenwang163:a1t4kCF2EhoO6D7W@cluster0.iotq8.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0';
// 连接 MongoDB
console.log('Attempting to connect to MongoDB...');
mongoose_1.default.connect(MONGODB_URI)
    .then(() => {
    console.log('Successfully connected to MongoDB.');
})
    .catch((error) => {
    console.error('MongoDB connection error:', error);
    process.exit(1); // 如果连接失败，终止程序
});
// 监听连接事件
mongoose_1.default.connection.on('connected', () => {
    console.log('Mongoose connected to MongoDB');
});
mongoose_1.default.connection.on('error', (err) => {
    console.error('Mongoose connection error:', err);
});
mongoose_1.default.connection.on('disconnected', () => {
    console.log('Mongoose disconnected');
});
// 中间件
app.use((0, cors_1.default)());
app.use(express_1.default.json());
// 添加路由日志中间件
app.use((req, res, next) => {
    console.log(`${req.method} ${req.path}`);
    next();
});
// 路由
app.use('/api/auth', auth_routes_1.default);
app.use('/api/posts', posts_1.default);
// 测试路由
app.get('/api/health', (_req, res) => {
    res.json({
        status: 'ok',
        message: 'Server is running',
        dbStatus: mongoose_1.default.connection.readyState // 添加数据库连接状态
    });
});
// 启动服务器
app.listen(port, () => {
    console.log(`Server is running on http://localhost:${port}`);
});
// 处理程序终止
process.on('SIGINT', () => __awaiter(void 0, void 0, void 0, function* () {
    try {
        yield mongoose_1.default.connection.close();
        console.log('Mongoose connection closed through app termination');
        process.exit(0);
    }
    catch (error) {
        console.error('Error closing mongoose connection:', error);
        process.exit(1);
    }
}));
