from app import mongo
from bson import ObjectId
from datetime import datetime

class Post:
    def __init__(self, post_data):
        self.post_data = post_data
        
    @staticmethod
    def create(title, content, author_id, category='分享'):
        post_data = {
            'title': title,
            'content': content,
            'author_id': author_id,
            'category': category,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'views': 0,
            'likes': 0
        }
        result = mongo.db.posts.insert_one(post_data)
        return str(result.inserted_id)
        
    @staticmethod
    def get_by_id(post_id):
        post_data = mongo.db.posts.find_one({'_id': ObjectId(post_id)})
        return Post(post_data) if post_data else None

    @staticmethod
    def from_db(post_data):
        if not post_data:
            return None
        return Post(post_data)

    def save(self):
        post_data = {
            'title': self.post_data['title'],
            'content': self.post_data['content'],
            'category': self.post_data['category'],
            'author_id': self.post_data['author_id'],
            'created_at': self.post_data['created_at'],
            'updated_at': self.post_data['updated_at'],
            'views': self.post_data.get('views', 0),
            'likes': self.post_data.get('likes', 0)
        }
        if '_id' in self.post_data:
            mongo.db.posts.update_one({'_id': self.post_data['_id']}, {'$set': post_data}, upsert=True)
        else:
            result = mongo.db.posts.insert_one(post_data)
            self.post_data['_id'] = result.inserted_id

    @staticmethod
    def get_all(page=1, per_page=10):
        total = mongo.db.posts.count_documents({})
        posts = mongo.db.posts.find().sort('created_at', -1).skip((page-1)*per_page).limit(per_page)
        return [Post.from_db(post) for post in posts], total 