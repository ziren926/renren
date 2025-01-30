import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev'
    
    # MongoDB配置
    MONGODB_URI = os.environ.get('MONGODB_URI')
    if not MONGODB_URI:
        raise ValueError("No MongoDB URI configured!")
    
    # MongoDB配置，确保使用正确的连接参数
    MONGO_URI = MONGODB_URI
    
    # 禁用SSL/TLS
    MONGO_TLS = False
    MONGO_TLS_INSECURE = False
    
    # 其他MongoDB连接选项
    MONGO_CONNECT_TIMEOUT_MS = 5000
    MONGO_SOCKET_TIMEOUT_MS = 5000
    MONGO_SERVER_SELECTION_TIMEOUT_MS = 5000
    
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size 