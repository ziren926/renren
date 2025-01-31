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
from .extensions import mongo, login_manager, moment, init_fs

# 配置日志格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

bootstrap = Bootstrap()
login_manager = LoginManager()
moment = Moment()
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
    
    # 初始化 MongoDB
    mongo.init_app(app)
    
    with app.app_context():
        init_fs(app)  # 初始化 GridFS
    
    # 确保数据库连接
    with app.app_context():
        # 测试数据库连接
        try:
            # 尝试访问数据库
            mongo.db.command('ping')
            app.logger.info("Successfully connected to MongoDB!")
            app.logger.info(f"MongoDB version: {mongo.db.command('buildInfo')['version']}")
            app.logger.info(f"MongoDB server: {mongo.db.client.address[0]}")
            
            # 确保users集合存在
            if 'users' not in mongo.db.list_collection_names():
                mongo.db.create_collection('users')
                app.logger.info("Created users collection")
                
        except Exception as e:
            app.logger.error(f"MongoDB connection error: {str(e)}")
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