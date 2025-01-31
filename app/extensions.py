from flask_pymongo import PyMongo
from flask_login import LoginManager
from flask_moment import Moment
from gridfs import GridFS

# 初始化扩展
mongo = PyMongo()
login_manager = LoginManager()
moment = Moment()

# 初始化 GridFS
fs = None

def init_fs(app):
    global fs
    fs = GridFS(mongo.db)

# 配置 login_manager
login_manager.login_view = 'auth.login'
login_manager.login_message = '请先登录'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    from app.models import User
    user_data = mongo.db.users.find_one({'_id': user_id})
    if user_data:
        return User(user_data)
    return None 