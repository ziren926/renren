from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import login_manager, mongo
from bson import ObjectId

class User(UserMixin):
    def __init__(self, user_data):
        self.user_data = user_data
        self.id = str(user_data.get('_id'))
        self.username = user_data.get('username')
        
    @staticmethod
    def get_by_id(user_id):
        try:
            user_data = mongo.db.users.find_one({'_id': ObjectId(user_id)})
            return User(user_data) if user_data else None
        except:
            return None
            
    @staticmethod
    def get_by_username(username):
        user_data = mongo.db.users.find_one({'username': username})
        return User(user_data) if user_data else None

    def get_id(self):
        return str(self.id)

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    @staticmethod
    def validate_login(password_hash, password):
        return check_password_hash(password_hash, password)

    def save(self):
        user_data = {
            '_id': self.id,
            'username': self.username,
            'password_hash': self.user_data['password_hash']
        }
        mongo.db.users.update_one(
            {'_id': self.id},
            {'$set': user_data},
            upsert=True
        )

    def set_password(self, password):
        self.user_data['password_hash'] = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.user_data['password_hash'], password)

    @staticmethod
    def get(user_id):
        if not user_id:
            return None
        try:
            user_data = mongo.db.users.find_one({'_id': ObjectId(user_id)})
            if user_data:
                return User(user_data)
            return None
        except:
            return None

@login_manager.user_loader
def load_user(user_id):
    try:
        user_data = mongo.db.users.find_one({'_id': ObjectId(user_id)})
        if user_data:
            return User(user_data)
    except Exception as e:
        return None
    return None 