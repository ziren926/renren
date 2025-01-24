from flask import Flask
from flask_pymongo import PyMongo
from flask_login import LoginManager
from config import Config
import logging
from logging.handlers import RotatingFileHandler
import os

mongo = PyMongo()
login_manager = LoginManager()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # 初始化扩展
    mongo.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # 注册蓝图
    from .routes import main, auth
    app.register_blueprint(main.bp)
    app.register_blueprint(auth.bp)

    # 配置日志
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/renren.log',
                                         maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Renren startup')

    return app 