from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify, send_file, abort
from flask_login import current_user, login_required
from .. import mongo
from bson import ObjectId
import math
from flask_ckeditor import upload_success, upload_fail
import os
from werkzeug.utils import secure_filename
from app.models.comment import Comment
from datetime import datetime, timedelta
from app.forms import PostForm, CommentForm
import time
import io
import mimetypes
import traceback
import re
from app import ckeditor  # 添加 ckeditor 导入
from gridfs import GridFS
from PIL import Image
from app.utils import save_image  # 添加这行导入
from io import BytesIO
from pymongo import TEXT, ASCENDING
from app.extensions import fs  # 添加 fs 的导入
from gridfs.errors import NoFile

bp = Blueprint('main', __name__, url_prefix='')

@bp.route('/')
def index():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 10
        skip = (page - 1) * per_page
        
        # 只获取普通帖子
        total = mongo.db.posts.count_documents({'post_type': 'normal'})
        
        # 获取分页的普通帖子
        posts = list(mongo.db.posts.find(
            {'post_type': 'normal'}
        ).sort('created_at', -1).skip(skip).limit(per_page))
        
        # 处理每个帖子的预览图片URL
        for post in posts:
            if post.get('preview_image'):
                post['preview_image_url'] = url_for('main.get_image', file_id=post['preview_image'])
        
        # 获取热门文章（只包含普通帖子）
        hot_posts = list(mongo.db.posts.find(
            {'post_type': 'normal'}
        ).sort('views', -1).limit(5))
        
        # 获取最近发表（只包含普通帖子）
        recent_posts = list(mongo.db.posts.find(
            {'post_type': 'normal'}
        ).sort('created_at', -1).limit(5))
        
        # 计算总页数
        total_pages = (total + per_page - 1) // per_page if total > 0 else 0
        
        return render_template('index.html', 
                             posts=posts,
                             hot_posts=hot_posts,
                             recent_posts=recent_posts,
                             page=page,
                             total_pages=total_pages,
                             total=total)
                             
    except Exception as e:
        current_app.logger.error(f"Error in index route: {str(e)}")
        return render_template('index.html', 
                             posts=[],
                             hot_posts=[],
                             recent_posts=[],
                             page=1,
                             total_pages=0,
                             total=0)

@bp.route('/new_post', methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = {
            'title': form.title.data,
            'content': form.content.data,
            'author_id': ObjectId(current_user.id),
            'author_name': current_user.username,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        # 处理图片上传
        if form.preview_image.data:
            image_file = form.preview_image.data
            if image_file:
                # 保存图片到GridFS
                file_id = fs.put(
                    image_file,
                    filename=secure_filename(image_file.filename),
                    content_type=image_file.content_type
                )
                post['preview_image'] = file_id
        
        # 保存帖子
        mongo.db.posts.insert_one(post)
        flash('帖子发布成功!', 'success')
        return redirect(url_for('main.index'))
        
    return render_template('main/new_post.html', form=form)

@bp.route('/edit/<post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    try:
        post = mongo.db.posts.find_one({'_id': ObjectId(post_id)})
        if not post:
            flash('帖子不存在', 'danger')
            return redirect(url_for('main.index'))
            
        # 检查是否是作者
        if str(post.get('author_id')) != current_user.get_id():
            flash('你没有权限编辑这篇文章', 'danger')
            return redirect(url_for('main.index'))
            
        form = PostForm()
        
        if form.validate_on_submit():
            update_data = {
                'title': form.title.data,
                'content': form.content.data,
                'updated_at': datetime.utcnow()
            }
            
            # 处理预览图片
            if form.preview_image.data:
                file = form.preview_image.data
                if file and allowed_file(file.filename):
                    # 确保获取正确的content_type
                    content_type = file.content_type or 'image/' + file.filename.rsplit('.', 1)[1].lower()
                    
                    file_id = fs.put(
                        file,
                        filename=secure_filename(file.filename),
                        content_type=content_type
                    )
                    update_data['preview_image'] = file_id
            
            mongo.db.posts.update_one(
                {'_id': ObjectId(post_id)},
                {'$set': update_data}
            )
            
            flash('更新成功！', 'success')
            return redirect(url_for('main.post_detail', post_id=post_id))
            
        elif request.method == 'GET':
            form.title.data = post.get('title')
            form.content.data = post.get('content')
            
        return render_template('post/edit.html', form=form, post=post)
                             
    except Exception as e:
        current_app.logger.error(f"Error editing post: {str(e)}")
        flash('编辑失败，请重试', 'danger')
        return redirect(url_for('main.index'))

@bp.route('/post/<post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    try:
        current_app.logger.info(f"Delete request received for post: {post_id}")
        current_app.logger.info(f"Current user: {current_user.get_id()}")
        
        # 验证 post_id 格式
        if not ObjectId.is_valid(post_id):
            current_app.logger.error(f"Invalid post_id format: {post_id}")
            return jsonify({'success': False, 'message': '无效的帖子ID'}), 400
            
        # 获取帖子
        post = mongo.db.posts.find_one({'_id': ObjectId(post_id)})
        if not post:
            current_app.logger.warning(f"Post not found: {post_id}")
            return jsonify({'success': False, 'message': '帖子不存在'}), 404
        
        # 验证用户权限
        post_author_id = str(post.get('author_id'))
        current_user_id = current_user.get_id()
        current_app.logger.info(f"Post author ID: {post_author_id}")
        current_app.logger.info(f"Current user ID: {current_user_id}")
        
        if post_author_id != current_user_id:
            current_app.logger.warning("Permission denied - user IDs don't match")
            return jsonify({'success': False, 'message': '没有权限删除此帖子'}), 403
        
        # 删除相关图片
        if post.get('preview_image'):
            try:
                mongo.db.images.delete_one({'_id': ObjectId(post['preview_image'])})
                current_app.logger.info(f"Deleted associated image: {post['preview_image']}")
            except Exception as e:
                current_app.logger.error(f"Error deleting image: {str(e)}")
        
        # 删除帖子
        result = mongo.db.posts.delete_one({'_id': ObjectId(post_id)})
        
        if result.deleted_count:
            current_app.logger.info(f"Successfully deleted post: {post_id}")
            return jsonify({'success': True, 'message': '帖子已成功删除'})
        else:
            current_app.logger.error(f"Failed to delete post: {post_id}")
            return jsonify({'success': False, 'message': '删除失败，请重试'}), 500
            
    except Exception as e:
        current_app.logger.error(f"Error deleting post {post_id}: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'success': False, 'message': f'删除时出现错误: {str(e)}'}), 500

def ensure_text_index():
    """确保文本索引存在"""
    try:
        # 获取现有索引
        existing_indexes = mongo.db.posts.list_indexes()
        has_text_index = False
        
        # 检查是否已存在文本索引
        for index in existing_indexes:
            if 'text' in index['name']:
                has_text_index = True
                break
        
        # 如果不存在文本索引，创建它
        if not has_text_index:
            mongo.db.posts.create_index(
                [('title', 'text'), ('content', 'text')],
                weights={'title': 10, 'content': 5},
                default_language='chinese'
            )
            current_app.logger.info("Text index created successfully")
    except Exception as e:
        current_app.logger.error(f"Error managing text index: {str(e)}")

@bp.route('/search')
def search():
    query = request.args.get('q', '')
    search_type = request.args.get('type', 'normal')  # 默认搜索普通帖子
    
    if not query:
        if search_type == 'market':
            return redirect(url_for('main.market'))
        return redirect(url_for('main.index'))
    
    try:
        # 构建模糊匹配的正则表达式
        pattern = re.compile(f'.*{re.escape(query)}.*', re.IGNORECASE)
        
        # 使用 $or 进行标题和内容的模糊匹配，同时限制帖子类型
        results = list(mongo.db.posts.find({
            '$and': [
                {'post_type': search_type},
                {'$or': [
                    {'title': {'$regex': pattern}},
                    {'content': {'$regex': pattern}}
                ]}
            ]
        }).sort('created_at', -1))
        
        # 处理搜索结果的预览图
        for post in results:
            if post.get('preview_image'):
                post['preview_image_url'] = url_for('main.get_image', file_id=post['preview_image'])
        
        return render_template('search_results.html', 
                             posts=results, 
                             query=query,
                             search_type=search_type)
                             
    except Exception as e:
        current_app.logger.error(f"Search error: {str(e)}")
        flash('搜索出错，请重试', 'danger')
        if search_type == 'market':
            return redirect(url_for('main.market'))
        return redirect(url_for('main.index'))

@bp.route('/upload', methods=['POST'])
@login_required
def upload():
    f = request.files.get('upload')
    # 验证文件类型
    if not allowed_file(f.filename):
        return upload_fail(message='文件类型不允许')
    
    # 保存文件
    filename = secure_filename(f.filename)
    upload_path = os.path.join(current_app.root_path, 'static/uploads')
    
    # 确保上传目录存在
    if not os.path.exists(upload_path):
        os.makedirs(upload_path)
    
    f.save(os.path.join(upload_path, filename))
    url = url_for('static', filename=f'uploads/{filename}')
    return upload_success(url=url)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

@bp.route('/post/<post_id>')
def post_detail(post_id):
    try:
        # 获取帖子信息
        post = mongo.db.posts.find_one_and_update(
            {'_id': ObjectId(post_id)},
            {'$inc': {'views': 1}},
            return_document=True
        )
        
        if not post:
            abort(404)
            
        # 获取作者信息
        author = mongo.db.users.find_one({'_id': ObjectId(post['author_id'])})
        if author:
            post['author_avatar_url'] = author.get('avatar_url')
            post['author_bio'] = author.get('bio')
        
        # 处理文章内容中的图片URL
        if post.get('content'):
            content = post['content']
            # 替换图片URL为正确的路由
            content = content.replace('/file/', '/serve_file/')
            post['content'] = content
        
        # 获取评论
        comments = list(mongo.db.comments.find({'post_id': ObjectId(post_id)}).sort('created_at', -1))
        
        # 获取作者信息和统计
        author_stats = {
            'posts_count': author.get('post_count', 0),
            'total_likes': author.get('total_likes', 0),
            'total_words': author.get('total_words', 0),
            'join_date': author.get('created_at', datetime.utcnow()),
            'last_post_at': author.get('last_post_at'),
            'avatar_url': author.get('avatar_url', url_for('static', filename='images/default-avatar.png'))
        }
        
        # 获取作者最近的帖子
        recent_posts = list(
            mongo.db.posts.find(
                {'author_id': post['author_id'], '_id': {'$ne': ObjectId(post_id)}}
            ).sort('created_at', -1).limit(5)
        )
        
        # 获取相关帖子（基于标签）
        related_posts = []
        if 'tags' in post:
            related_posts = list(
                mongo.db.posts.find({
                    '_id': {'$ne': ObjectId(post_id)},
                    'tags': {'$in': post['tags']}
                }).limit(3)
            )
        
        return render_template('post/detail.html',
                             post=post,
                             comments=comments,
                             author_stats=author_stats,
                             recent_posts=recent_posts,
                             related_posts=related_posts)
                             
    except Exception as e:
        current_app.logger.error(f"Error loading post detail: {str(e)}")
        abort(500)

@bp.route('/post/<post_id>/like', methods=['POST'])
@login_required
def like_post(post_id):
    try:
        # 更新帖子的点赞数
        result = mongo.db.posts.update_one(
            {'_id': ObjectId(post_id)},
            {'$inc': {'likes': 1}}
        )
        
        if result.modified_count > 0:
            # 获取更新后的点赞数
            post = mongo.db.posts.find_one({'_id': ObjectId(post_id)})
            return jsonify({
                'success': True,
                'likes': post.get('likes', 0)
            })
    except Exception as e:
        current_app.logger.error(f"Error liking post: {str(e)}")
    
    return jsonify({
        'success': False,
        'message': '点赞失败'
    })

@bp.route('/post/<post_id>/comment', methods=['POST'])
@login_required
def add_comment(post_id):
    form = CommentForm()
    if form.validate_on_submit():
        try:
            # 直接创建评论文档
            comment_dict = {
                'post_id': ObjectId(post_id),
                'author_id': ObjectId(current_user.get_id()),
                'content': form.content.data,
                'created_at': datetime.utcnow()
            }
            
            # 保存到数据库
            mongo.db.comments.insert_one(comment_dict)
            
            flash('评论发布成功！', 'success')
        except Exception as e:
            current_app.logger.error(f"Error adding comment: {str(e)}")
            flash('评论发布失败', 'danger')
            
    return redirect(url_for('main.post_detail', post_id=post_id))

@bp.route('/comment/<comment_id>/delete', methods=['POST'])
@login_required
def comment_delete(comment_id):
    try:
        comment = mongo.db.comments.find_one({'_id': ObjectId(comment_id)})
        if not comment:
            return jsonify({'success': False, 'message': '评论不存在'})
        
        # 检查是否是评论作者
        if str(comment['user_id']) != current_user.get_id():
            return jsonify({'success': False, 'message': '没有权限删除此评论'})
        
        # 删除评论
        mongo.db.comments.delete_one({'_id': ObjectId(comment_id)})
        
        # 更新帖子的评论计数
        mongo.db.posts.update_one(
            {'_id': comment['post_id']},
            {'$inc': {'comment_count': -1}}
        )
        
        return jsonify({'success': True})
        
    except Exception as e:
        current_app.logger.error(f"Delete comment error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/upload_image', methods=['POST'])
@login_required
def upload_image():
    try:
        if 'image' not in request.files:
            current_app.logger.error("No image file in request")
            return jsonify({'success': False, 'message': '没有找到图片文件'})

        file = request.files['image']
        if file.filename == '':
            current_app.logger.error("No selected file")
            return jsonify({'success': False, 'message': '未选择文件'})

        if file and allowed_file(file.filename):
            try:
                # 修改这里：移除重复的 filename 参数
                file_id = mongo.save_file(file.filename, file)
                url = url_for('main.get_image', file_id=str(file_id))
                return jsonify({'success': True, 'url': url})
            except Exception as e:
                current_app.logger.error(f"Error saving file: {str(e)}")
                return jsonify({'success': False, 'message': f'保存文件失败: {str(e)}'})
        else:
            current_app.logger.error(f"Invalid file type: {file.filename}")
            return jsonify({'success': False, 'message': '不支持的文件类型'})
            
    except Exception as e:
        current_app.logger.error(f"Upload error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/image/<file_id>')
def get_image(file_id):
    try:
        # 尝试从GridFS获取图片
        file_data = fs.get(ObjectId(file_id))
        
        # 设置正确的Content-Type
        response = send_file(
            io.BytesIO(file_data.read()),
            mimetype=file_data.content_type,
            as_attachment=False,
            download_name=file_data.filename
        )
        
        # 添加缓存控制
        response.headers['Cache-Control'] = 'public, max-age=31536000'
        return response
        
    except NoFile:
        current_app.logger.warning(f"Image not found: {file_id}")
        return '', 404
    except Exception as e:
        current_app.logger.error(f"Error serving image: {str(e)}")
        return '', 500

# 添加调试路由
@bp.route('/debug/image/<file_id>')
def debug_image(file_id):
    try:
        file_data = mongo.db.fs.files.find_one({'_id': ObjectId(file_id)})
        if file_data:
            return {
                'file_exists': True,
                'content_type': file_data.get('contentType'),
                'filename': file_data.get('filename'),
                'length': file_data.get('length'),
                'chunk_count': mongo.db.fs.chunks.count_documents({'files_id': ObjectId(file_id)})
            }
        return {'file_exists': False}
    except Exception as e:
        return {'error': str(e)}

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_post():
    form = PostForm()
    if request.args.get('type') == 'market' and request.method == 'GET':
        form.post_type.data = 'market'
        
    if form.validate_on_submit():
        try:
            title = form.title.data
            content = form.content.data
            post_type = form.post_type.data
            
            # 处理预览图片
            preview_image_id = None
            if 'preview_image' in request.files:
                file = request.files['preview_image']
                if file and file.filename and allowed_file(file.filename):
                    preview_image_id = save_image(file)
            
            # 创建帖子，添加新字段
            post = {
                'title': title,
                'content': content,
                'author_id': ObjectId(current_user.get_id()),
                'author_name': current_user.username,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'post_type': post_type,
                'views': 0,
                'likes': 0,
                'comment_count': 0,
                'reading_time': estimate_reading_time(content),  # 估计阅读时间
                'summary': generate_summary(content),  # 生成摘要
                'tags': extract_tags(content),  # 提取标签
                'toc': generate_toc(content),  # 生成目录结构
                'word_count': len(content)  # 字数统计
            }
            
            if preview_image_id:
                post['preview_image'] = preview_image_id
            
            result = mongo.db.posts.insert_one(post)
            
            if result.inserted_id:
                # 更新用户统计信息
                mongo.db.users.update_one(
                    {'_id': ObjectId(current_user.get_id())},
                    {
                        '$inc': {
                            'post_count': 1,
                            'total_words': len(content)
                        },
                        '$set': {
                            'last_post_at': datetime.utcnow()
                        }
                    },
                    upsert=True
                )
                
                flash('发布成功！', 'success')
                if post_type == 'market':
                    return redirect(url_for('main.market'))
                return redirect(url_for('main.index'))
            else:
                flash('发布失败，请重试', 'danger')
            
        except Exception as e:
            current_app.logger.error(f"Error creating post: {str(e)}")
            flash('发布失败，请重试', 'danger')
            
    return render_template('post/create.html', 
                         form=form, 
                         title='发布文章',
                         post_type=request.args.get('type', 'normal'))

# 添加辅助函数
def estimate_reading_time(content):
    """估计阅读时间（分钟）"""
    words_per_minute = 500  # 假设平均阅读速度
    word_count = len(content)
    minutes = max(1, round(word_count / words_per_minute))
    return minutes

def generate_summary(content, max_length=200):
    """生成文章摘要"""
    # 移除HTML标签
    text = re.sub(r'<[^>]+>', '', content)
    # 取前200个字符
    summary = text[:max_length].strip()
    if len(text) > max_length:
        summary += '...'
    return summary

def extract_tags(content):
    """从内容中提取标签"""
    # 这里可以实现标签提取逻辑
    # 例如：提取 #标签# 格式的内容
    tags = re.findall(r'#([^#]+)#', content)
    return list(set(tags))  # 去重

def generate_toc(content):
    """生成目录结构"""
    toc = []
    # 使用正则表达式匹配HTML标题标签
    headers = re.findall(r'<h([1-6])([^>]*)>(.*?)</h\1>', content)
    for level, attrs, title in headers:
        toc.append({
            'level': int(level),
            'title': re.sub(r'<[^>]+>', '', title),  # 移除标题中的HTML标签
            'id': f'section-{len(toc)}'
        })
    return toc

@bp.route('/test')
def test():
    return 'Test route works!'

@bp.route('/uploads/<file_id>')
def get_file(file_id):
    try:
        # 从 GridFS 获取文件
        file_data = mongo.db.fs.files.find_one({'_id': ObjectId(file_id)})
        if file_data:
            # 获取文件内容
            file_content = mongo.db.fs.chunks.find({'files_id': ObjectId(file_id)})
            if file_content:
                # 组合所有块
                data = b''.join(chunk['data'] for chunk in file_content)
                # 创建文件对象
                file_object = io.BytesIO(data)
                # 获取文件类型
                content_type = file_data.get('contentType', 'image/jpeg')
                # 返回文件
                return send_file(
                    file_object,
                    mimetype=content_type,
                    as_attachment=False,
                    download_name=file_data.get('filename', 'image.jpg')
                )
    except Exception as e:
        current_app.logger.error(f"Error serving GridFS file {file_id}: {str(e)}")
    return "File not found", 404

@bp.route('/market')
def market():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 10
        skip = (page - 1) * per_page
        
        # 只获取需求帖子
        total = mongo.db.posts.count_documents({'post_type': 'market'})
        
        # 获取分页的需求帖子
        posts = list(mongo.db.posts.find(
            {'post_type': 'market'}
        ).sort('created_at', -1).skip(skip).limit(per_page))
        
        # 处理每个帖子的预览图片URL
        for post in posts:
            if post.get('preview_image'):
                post['preview_image_url'] = url_for('main.get_image', file_id=post['preview_image'])
        
        # 计算总页数
        total_pages = (total + per_page - 1) // per_page if total > 0 else 0
        
        # 创建分页信息
        pagination = {
            'page': page,
            'pages': total_pages,
            'total': total,
            'has_prev': page > 1,
            'has_next': page < total_pages
        }
        
        return render_template('market.html', 
                             posts=posts,
                             pagination=pagination)  # 传递分页对象
                             
    except Exception as e:
        current_app.logger.error(f"Error in market route: {str(e)}")
        return render_template('market.html', 
                             posts=[],
                             pagination={'page': 1, 'pages': 0, 'total': 0, 'has_prev': False, 'has_next': False})

@bp.route('/upload_content_image', methods=['POST'])
@login_required
def upload_content_image():
    try:
        if 'image' not in request.files:
            return jsonify({'error': '没有上传图片'}), 400
            
        file = request.files['image']
        if not file or not file.filename:
            return jsonify({'error': '无效的图片'}), 400
            
        # 验证文件类型
        if not allowed_file(file.filename):
            return jsonify({'error': '不支持的图片格式'}), 400
            
        # 保存图片
        filename = secure_filename(file.filename)
        content = file.read()
        
        # 保存到 MongoDB
        result = mongo.db.images.insert_one({
            'content': content,
            'filename': filename,
            'upload_date': datetime.utcnow(),
            'user_id': current_user.get_id()
        })
        
        # 返回图片URL
        image_url = url_for('main.get_image', file_id=str(result.inserted_id))
        return jsonify({'url': image_url})
        
    except Exception as e:
        current_app.logger.error(f"Error uploading content image: {str(e)}")
        return jsonify({'error': '上传失败'}), 500

@bp.route('/serve_file/<file_id>')
def serve_file(file_id):
    try:
        if not file_id:
            return "Invalid file ID", 400

        # 正确初始化 GridFS
        fs = GridFS(mongo.db)
        
        # 使用 get() 方法获取文件
        try:
            file_data = fs.get(ObjectId(file_id))
        except Exception as e:
            current_app.logger.error(f"Failed to get file {file_id}: {str(e)}")
            return "File not found", 404

        # 确保有文件名和内容类型
        filename = file_data.filename
        content_type = file_data.content_type or 'application/octet-stream'

        response = send_file(
            io.BytesIO(file_data.read()),
            mimetype=content_type,
            download_name=filename,
            as_attachment=False
        )

        # 设置缓存控制
        response.headers['Cache-Control'] = 'public, max-age=31536000'
        return response

    except Exception as e:
        current_app.logger.error(f"Error serving file {file_id}: {str(e)}")
        return str(e), 500

@bp.route('/author/<author_id>')
def author_profile(author_id):
    try:
        # 获取作者信息
        author = mongo.db.users.find_one({'_id': ObjectId(author_id)})
        if not author:
            abort(404)
            
        # 获取作者统计信息
        posts_count = mongo.db.posts.count_documents({'author_id': ObjectId(author_id)})
        total_likes = sum(p.get('likes', 0) for p in mongo.db.posts.find({'author_id': ObjectId(author_id)}))
        total_views = sum(p.get('views', 0) for p in mongo.db.posts.find({'author_id': ObjectId(author_id)}))
        
        # 获取作者的帖子，按时间倒序
        posts = list(mongo.db.posts.find(
            {'author_id': ObjectId(author_id)}
        ).sort('created_at', -1))
        
        # 计算每月发帖数量
        posts_by_month = {}
        for post in posts:
            month_key = post['created_at'].strftime('%Y-%m')
            posts_by_month[month_key] = posts_by_month.get(month_key, 0) + 1
            
        return render_template('author/profile.html',
                             author=author,
                             posts=posts,
                             stats={
                                 'posts_count': posts_count,
                                 'total_likes': total_likes,
                                 'total_views': total_views,
                                 'join_date': author.get('created_at'),
                                 'posts_by_month': posts_by_month
                             })
                             
    except Exception as e:
        current_app.logger.error(f"Error loading author profile: {str(e)}")
        abort(500)

@bp.route('/upload_avatar', methods=['POST'])
@login_required
def upload_avatar():
    try:
        if 'avatar' not in request.files:
            return jsonify({'success': False, 'message': '没有找到文件'})
        
        file = request.files['avatar']
        if not file or not file.filename:
            return jsonify({'success': False, 'message': '无效的文件'})
            
        # 检查文件类型
        if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            return jsonify({'success': False, 'message': '不支持的文件类型'})
            
        # 读取并处理图片
        try:
            image = Image.open(file)
            
            # 调整图片大小为正方形
            size = 200
            if image.size[0] != image.size[1]:
                # 裁剪为正方形
                width, height = image.size
                new_size = min(width, height)
                left = (width - new_size) // 2
                top = (height - new_size) // 2
                image = image.crop((left, top, left + new_size, top + new_size))
            
            # 调整大小
            image = image.resize((size, size), Image.LANCZOS)
            
            # 保存处理后的图片
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=85)
            output.seek(0)
            
            # 正确初始化 GridFS
            fs = GridFS(mongo.db)
            
            # 保存到GridFS
            file_id = fs.put(
                output,
                filename=f'avatar_{current_user.id}.jpg',
                content_type='image/jpeg'
            )
            
            # 更新用户头像
            mongo.db.users.update_one(
                {'_id': ObjectId(current_user.id)},
                {
                    '$set': {
                        'avatar_id': file_id,
                        'avatar_url': url_for('main.serve_file', file_id=str(file_id), _external=True)
                    }
                }
            )
            
            return jsonify({
                'success': True,
                'message': '头像上传成功',
                'avatar_url': url_for('main.serve_file', file_id=str(file_id), _external=True)
            })
            
        except Exception as e:
            current_app.logger.error(f"Error processing avatar: {str(e)}")
            return jsonify({'success': False, 'message': '图片处理失败'})
            
    except Exception as e:
        current_app.logger.error(f"Error uploading avatar: {str(e)}")
        return jsonify({'success': False, 'message': '上传失败'})

@bp.route('/update_bio', methods=['POST'])
@login_required
def update_bio():
    try:
        data = request.get_json()
        bio = data.get('bio', '').strip()
        
        # 更新用户简介
        mongo.db.users.update_one(
            {'_id': ObjectId(current_user.id)},
            {'$set': {'bio': bio}}
        )
        
        return jsonify({
            'success': True,
            'message': '个人简介已更新'
        })
        
    except Exception as e:
        current_app.logger.error(f"Error updating bio: {str(e)}")
        return jsonify({
            'success': False,
            'message': '更新失败，请重试'
        })
