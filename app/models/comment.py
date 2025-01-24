from app import db
from datetime import datetime
from bson import ObjectId

class Comment:
    def __init__(self, content, post_id, author_id, created_at=None, _id=None):
        self.content = content
        self.post_id = post_id
        self.author_id = author_id
        self.created_at = created_at if created_at else datetime.utcnow()
        self._id = _id if _id else ObjectId()

    @staticmethod
    def from_db(comment_data):
        if not comment_data:
            return None
        return Comment(
            content=comment_data['content'],
            post_id=comment_data['post_id'],
            author_id=comment_data['author_id'],
            created_at=comment_data['created_at'],
            _id=comment_data['_id']
        )

    def save(self):
        comment_data = {
            'content': self.content,
            'post_id': self.post_id,
            'author_id': self.author_id,
            'created_at': self.created_at
        }
        if hasattr(self, '_id'):
            comment_data['_id'] = self._id
            db.comments.update_one({'_id': self._id}, {'$set': comment_data}, upsert=True)
        else:
            result = db.comments.insert_one(comment_data)
            self._id = result.inserted_id
            # 更新帖子的评论计数
            db.posts.update_one(
                {'_id': self.post_id},
                {'$inc': {'comment_count': 1}}
            ) 