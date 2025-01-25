from bson import ObjectId
from app import mongo
import os
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime
from flask import current_app
from PIL import Image
from io import BytesIO
import traceback

def save_image(file):
    """
    保存图片到MongoDB，并控制图片大小
    """
    if not file:
        return None
        
    try:
        # 读取原始图片
        image = Image.open(file)
        
        # 设置最大尺寸
        MAX_SIZE = (800, 800)
        
        # 如果图片超过最大尺寸，进行等比缩放
        if image.size[0] > MAX_SIZE[0] or image.size[1] > MAX_SIZE[1]:
            image.thumbnail(MAX_SIZE, Image.Resampling.LANCZOS)
        
        # 转换图片格式为JPEG，并控制质量
        output = BytesIO()
        if image.mode in ('RGBA', 'LA'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[-1])
            image = background
        
        # 保存为JPEG格式
        image.save(output, format='JPEG', quality=85, optimize=True)
        image_data = output.getvalue()
        
        # 生成唯一文件名
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        
        # 保存到MongoDB
        file_doc = {
            'filename': unique_filename,
            'content_type': 'image/jpeg',
            'data': image_data,
            'created_at': datetime.utcnow(),
            'file_size': len(image_data)  # 添加文件大小信息
        }
        
        # 插入数据库并记录日志
        result = mongo.db.images.insert_one(file_doc)
        
        if result.inserted_id:
            current_app.logger.info(f"Image saved successfully: id={result.inserted_id}, size={file_doc['file_size']}")
            return str(result.inserted_id)
            
        current_app.logger.error("Failed to insert image into database")
        return None
        
    except Exception as e:
        current_app.logger.error(f"Error saving image: {str(e)}\n{traceback.format_exc()}")
        return None 