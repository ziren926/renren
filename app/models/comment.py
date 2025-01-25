from app import mongo
from bson import ObjectId
from datetime import datetime

class Comment:
    def __init__(self, comment_data):
        self.comment_data = comment_data
        
    @staticmethod
    def create(content, post_id, author_id):
        comment_data = {
            'content': content,
            'post_id': post_id,
            'author_id': author_id,
            'created_at': datetime.utcnow()
        }
        result = mongo.db.comments.insert_one(comment_data)
        return str(result.inserted_id)
        
    @staticmethod
    def get_by_post_id(post_id):
        comments = mongo.db.comments.find({'post_id': post_id}).sort('created_at', -1)
        return list(comments)
        
    @staticmethod
    def get_by_id(comment_id):
        comment_data = mongo.db.comments.find_one({'_id': ObjectId(comment_id)})
        return Comment(comment_data) if comment_data else None

    def save(self):
        comment_data = {
            'content': self.content,
            'post_id': self.post_id,
            'author_id': self.author_id,
            'created_at': self.created_at
        }
        if hasattr(self, '_id'):
            comment_data['_id'] = self._id
            mongo.db.comments.update_one({'_id': self._id}, {'$set': comment_data}, upsert=True)
        else:
            result = mongo.db.comments.insert_one(comment_data)
            self._id = result.inserted_id
            # 更新帖子的评论计数
            mongo.db.posts.update_one(
                {'_id': self.post_id},
                {'$inc': {'comment_count': 1}}
            ) 