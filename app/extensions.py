from flask_pymongo import PyMongo
from flask_login import LoginManager
from flask_moment import Moment

# 初始化扩展，但不传入 app
mongo = PyMongo()
login_manager = LoginManager()
moment = Moment()

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