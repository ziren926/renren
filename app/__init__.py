from flask import Flask
from flask_pymongo import PyMongo
from flask_login import LoginManager
from flask_ckeditor import CKEditor
from config import Config
import logging
from logging.handlers import RotatingFileHandler
import os
import certifi

mongo = PyMongo()
login_manager = LoginManager()
ckeditor = CKEditor()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # CKEditor配置
    app.config['CKEDITOR_PKG_TYPE'] = 'standard'  # 改为 standard 版本
    app.config['CKEDITOR_SERVE_LOCAL'] = False    # 使用 CDN
    app.config['CKEDITOR_HEIGHT'] = 400
    
    # 配置日志
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    # 设置日志格式
    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    )
    
    # 文件处理器
    file_handler = RotatingFileHandler(
        'logs/renren.log', 
        maxBytes=10240000,  # 10MB
        backupCount=10,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    
    # 设置应用日志
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Renren startup...')

    try:
        # 使用 certifi 进行 SSL 验证
        app.config['MONGO_URI'] += f'&tlsCAFile={certifi.where()}'
        mongo.init_app(app)
        ckeditor.init_app(app)
        
        # 测试数据库连接
        mongo.db.command('ping')
        app.logger.info("Successfully connected to MongoDB!")
        
        # 打印现有的集合
        collections = mongo.db.list_collection_names()
        app.logger.info(f"Available collections: {collections}")
        
        # 打印各集合的文档数量
        for collection in collections:
            count = mongo.db.get_collection(collection).count_documents({})
            app.logger.info(f"Collection '{collection}' has {count} documents")
            
    except Exception as e:
        app.logger.error(f"MongoDB connection error: {str(e)}")
        raise  # 重新抛出异常，这样如果连接失败，应用会停止启动

    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '请先登录'
    login_manager.login_message_category = 'info'

    # 注册蓝图
    from .routes import main, auth
    app.register_blueprint(main.bp)
    app.register_blueprint(auth.bp)

    app.logger.info('Renren startup completed')
    return app 