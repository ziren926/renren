import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev'
    MONGO_URI = 'mongodb+srv://zirenwang163:a1t4kCF2EhoO6D7W@cluster0.iotq8.mongodb.net/renren?retryWrites=true&w=majority&appName=Cluster0'
    
    # CKEditor 配置
    CKEDITOR_SERVE_LOCAL = True
    CKEDITOR_HEIGHT = 400
    CKEDITOR_ENABLE_CODESNIPPET = True
    
    # 上传配置
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads') 