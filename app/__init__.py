from flask import Flask
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_moment import Moment
from flask_pymongo import PyMongo
from flask_ckeditor import CKEditor
from app.config import Config
import os
import logging
from logging.handlers import RotatingFileHandler
from bson import ObjectId

# 配置日志格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

bootstrap = Bootstrap()
login_manager = LoginManager()
moment = Moment()
mongo = PyMongo()
ckeditor = CKEditor()
login_manager.login_view = 'auth.login'
login_manager.login_message = '请先登录'
login_manager.login_message_category = 'info'

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # 初始化扩展
    bootstrap.init_app(app)
    login_manager.init_app(app)
    moment.init_app(app)
    ckeditor.init_app(app)
    
    # MongoDB 配置
    try:
        app.logger.info("="*50)
        app.logger.info("Renren Web Application Starting...")
        app.logger.info("Initializing MongoDB connection...")
        
        # 从环境变量获取 MongoDB URI
        mongodb_uri = os.environ.get('MONGODB_URI')
        if mongodb_uri:
            app.config['MONGO_URI'] = mongodb_uri
            app.logger.info(f"MongoDB URI from environment: {mongodb_uri.split('@')[-1]}")  # 只显示主机部分，不显示凭据
        else:
            default_uri = 'mongodb://zirenwang163:a1t4kCF2EhoO6D7W@mongo:27017/renren?authSource=admin'
            app.config['MONGO_URI'] = default_uri
            app.logger.warning(f"No MONGODB_URI found in environment, using default connection")
            app.logger.info(f"Default MongoDB URI: {default_uri.split('@')[-1]}")
        
        # 初始化 MongoDB
        mongo.init_app(app)
        
        # 测试连接并获取服务器信息
        with app.app_context():
            # 测试连接
            server_info = mongo.db.command('serverStatus')
            app.logger.info("Successfully connected to MongoDB!")
            app.logger.info(f"MongoDB version: {server_info.get('version', 'Unknown')}")
            app.logger.info(f"MongoDB server: {server_info.get('host', 'Unknown')}")
            
            # 获取并显示可用的数据库
            dbs = mongo.db.client.list_database_names()
            app.logger.info(f"Available databases: {', '.join(dbs)}")
            
            # 获取当前数据库的统计信息
            db_stats = mongo.db.command('dbstats')
            app.logger.info(f"Current database: {mongo.db.name}")
            app.logger.info(f"Collections count: {db_stats.get('collections', 0)}")
            app.logger.info(f"Total documents: {db_stats.get('objects', 0)}")
            
            app.logger.info("MongoDB initialization completed successfully")
            app.logger.info("="*50)
        
    except Exception as e:
        app.logger.error("="*50)
        app.logger.error("MongoDB Connection Error!")
        app.logger.error(f"Error details: {str(e)}")
        app.logger.error("Please check your MongoDB configuration and ensure the server is running")
        app.logger.error("="*50)
        raise
    
    # 配置日志
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler(
        'logs/renren.log',
        maxBytes=10240,
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    
    # 注册蓝图
    from .routes import main, auth
    app.register_blueprint(main.bp)
    app.register_blueprint(auth.bp)

    # 设置用户加载函数
    from app.models.user import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.get_by_id(user_id)
    
    app.logger.info('Renren startup completed')
    return app 