from flask_login import UserMixin
from app import mongo, login_manager
from bson import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin):
    def __init__(self, user_data):
        self.user_data = user_data
        self._id = user_data.get('_id')
        self.username = user_data.get('username')
        self.email = user_data.get('email')
        self.password_hash = user_data.get('password_hash')

    def get_id(self):
        return str(self._id)

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

    @staticmethod
    def get_by_username(username):
        user_data = mongo.db.users.find_one({'username': username})
        return User.from_db(user_data) if user_data else None

    @staticmethod
    def get_by_id(user_id):
        try:
            user_data = mongo.db.users.find_one({'_id': ObjectId(user_id)})
            return User.from_db(user_data) if user_data else None
        except:
            return None

    @staticmethod
    def from_db(user_data):
        if not user_data:
            return None
        return User(user_data)

    def save(self):
        user_data = {
            'username': self.username,
            'email': self.email,
            'password_hash': self.password_hash
        }
        if hasattr(self, '_id'):
            user_data['_id'] = self._id
        
        if hasattr(self, '_id'):
            mongo.db.users.update_one({'_id': self._id}, {'$set': user_data}, upsert=True)
        else:
            result = mongo.db.users.insert_one(user_data)
            self._id = result.inserted_id

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    user_data = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    if user_data:
        return User(user_data)
    return None 