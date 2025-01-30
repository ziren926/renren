from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import login_manager, mongo
from bson import ObjectId

class User(UserMixin):
    def __init__(self, username, email, password_hash=None, _id=None):
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self._id = _id if _id else ObjectId()
    
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
        if user_data:
            return User(
                username=user_data['username'],
                email=user_data['email'],
                password_hash=user_data['password_hash'],
                _id=user_data['_id']
            )
        return None

    @staticmethod
    def get_by_id(user_id):
        try:
            user_data = mongo.db.users.find_one({'_id': ObjectId(user_id)})
            if user_data:
                return User(
                    username=user_data['username'],
                    email=user_data['email'],
                    password_hash=user_data['password_hash'],
                    _id=user_data['_id']
                )
        except:
            pass
        return None

    def save(self):
        user_data = {
            '_id': self._id,
            'username': self.username,
            'email': self.email,
            'password_hash': self.password_hash
        }
        mongo.db.users.update_one(
            {'_id': self._id},
            {'$set': user_data},
            upsert=True
        )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def get(user_id):
        if not user_id:
            return None
        try:
            user_data = mongo.db.users.find_one({'_id': ObjectId(user_id)})
            if user_data:
                return User(user_data['username'], user_data['email'], user_data['password_hash'], user_data['_id'])
            return None
        except:
            return None

@login_manager.user_loader
def load_user(user_id):
    try:
        user_data = mongo.db.users.find_one({'_id': ObjectId(user_id)})
        if user_data:
            return User(user_data['username'], user_data['email'], user_data['password_hash'], user_data['_id'])
    except Exception as e:
        return None
    return None 