import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev'
    UPLOAD_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 3 * 1024 * 1024  # 3MB
    
    # MongoDB 配置 - 从环境变量获取，如果没有则使用默认值
    MONGO_URI = os.environ.get('MONGODB_URI') or 'mongodb://zirenwang163:a1t4kCF2EhoO6D7W@mongo:27017/renren?authSource=admin'
    
    # CKEditor 配置
    CKEDITOR_SERVE_LOCAL = True
    CKEDITOR_HEIGHT = 400
    CKEDITOR_ENABLE_CODESNIPPET = True
    
    # 上传配置
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads') 