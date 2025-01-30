from flask_pymongo import PyMongo
from flask_login import LoginManager

# 创建扩展实例
mongo = PyMongo()
login_manager = LoginManager() 