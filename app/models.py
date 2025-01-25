from flask_login import UserMixin
from bson import ObjectId
from werkzeug.security import check_password_hash
from datetime import datetime

class User(UserMixin):
    def __init__(self, user_data):
        self.user_data = user_data
        self._id = user_data.get('_id')
        self.username = user_data.get('username')
        self.email = user_data.get('email')
        self.password = user_data.get('password')

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

class Comment:
    def __init__(self, post_id, author_id, content, created_at=None):
        self.post_id = post_id
        self.author_id = author_id
        self.content = content
        self.created_at = created_at if created_at else datetime.utcnow() 