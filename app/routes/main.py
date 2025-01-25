from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify, send_file
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

@bp.route('/post/new', methods=['GET', 'POST'])
@login_required
def new_post():
    if request.method == 'POST':
        try:
            title = request.form.get('title')
            content = request.form.get('ckeditor')  # 注意这里改成了 'ckeditor'
            category = request.form.get('category')
            
            if not all([title, content, category]):
                flash('请填写所有必填字段', 'error')
                return render_template('post/new.html')
            
            post = Post(
                title=title,
                content=content,
                category=category,
                author_id=ObjectId(current_user.get_id())
            )
            post.save()
            
            flash('帖子发布成功！', 'success')
            return redirect(url_for('main.index'))
            
        except Exception as e:
            flash(f'发布失败：{str(e)}', 'error')
            return render_template('post/new.html')
        
    return render_template('post/new.html')

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
            title = form.title.data
            content = form.content.data
            
            # 处理预览图片
            preview_image_id = post.get('preview_image')  # 保持原有图片ID
            if 'preview_image' in request.files:
                file = request.files['preview_image']
                if file and file.filename:
                    if allowed_file(file.filename):
                        new_image_id = save_image(file)
                        if new_image_id:
                            preview_image_id = new_image_id
            
            # 更新帖子
            update_data = {
                'title': title,
                'content': content,
                'updated_at': datetime.utcnow()
            }
            
            if preview_image_id:
                update_data['preview_image'] = preview_image_id
            
            mongo.db.posts.update_one(
                {'_id': ObjectId(post_id)},
                {'$set': update_data}
            )
            
            flash('更新成功！', 'success')
            # 根据帖子类型返回相应页面
            if post.get('post_type') == 'market':
                return redirect(url_for('main.market'))
            return redirect(url_for('main.index'))
            
        elif request.method == 'GET':
            form.title.data = post.get('title')
            form.content.data = post.get('content')
            
        return render_template('post/edit.html', 
                             form=form, 
                             post=post,
                             title='编辑文章')
                             
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
        # 验证 post_id 格式
        if not ObjectId.is_valid(post_id):
            flash('无效的帖子ID', 'danger')
            return redirect(url_for('main.index'))
            
        # 获取帖子并增加浏览量
        post = mongo.db.posts.find_one_and_update(
            {'_id': ObjectId(post_id)},
            {'$inc': {'views': 1}},
            return_document=True
        )
        
        if not post:
            flash('帖子不存在', 'danger')
            return redirect(url_for('main.index'))
            
        # 获取作者信息
        author = mongo.db.users.find_one({'_id': post['author_id']})
        
        # 确定返回按钮的目标页面
        back_url = url_for('main.market') if post.get('post_type') == 'market' else url_for('main.index')
        
        # 处理预览图片URL
        if post.get('preview_image'):
            post['preview_image_url'] = url_for('main.get_image', file_id=post['preview_image'])
        
        # 创建评论表单
        form = CommentForm()
        
        return render_template('post/detail.html', 
                             post=post,
                             author=author,
                             back_url=back_url,
                             form=form)  # 添加表单到模板上下文
                             
    except Exception as e:
        current_app.logger.error(f"Error viewing post: {str(e)}\n{traceback.format_exc()}")
        flash('获取帖子失败', 'danger')
        return redirect(url_for('main.index'))

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
        # 确保 file_id 是有效的 ObjectId
        if not ObjectId.is_valid(file_id):
            current_app.logger.error(f"Invalid ObjectId format: {file_id}")
            return '', 404

        # 从MongoDB获取图片
        image = mongo.db.images.find_one({'_id': ObjectId(file_id)})
        
        # 详细的日志记录
        current_app.logger.info(f"Attempting to retrieve image: {file_id}")
        current_app.logger.info(f"Image found: {image is not None}")
        
        if not image:
            current_app.logger.warning(f"Image not found: {file_id}")
            return '', 404

        if 'data' not in image:
            current_app.logger.warning(f"No data field in image document: {file_id}")
            return '', 404

        # 创建内存文件对象
        image_data = BytesIO(image['data'])
        
        # 设置缓存控制
        response = send_file(
            image_data,
            mimetype=image.get('content_type', 'image/jpeg'),
            as_attachment=False,
            download_name=image.get('filename', 'image.jpg')
        )
        response.headers['Cache-Control'] = 'public, max-age=31536000'
        
        current_app.logger.info(f"Successfully sent image: {file_id}")
        return response

    except Exception as e:
        current_app.logger.error(f"Error retrieving image {file_id}: {str(e)}\n{traceback.format_exc()}")
        return '', 404

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
    # 如果是从需求集市页面来的，默认选择 market 类型
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
                if file and file.filename:
                    if allowed_file(file.filename):
                        preview_image_id = save_image(file)
            
            # 创建帖子
            post = {
                'title': title,
                'content': content,
                'author_id': ObjectId(current_user.get_id()),
                'author_name': current_user.username,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'post_type': post_type,
                'views': 0,
                'likes': 0,          # 添加点赞数
                'comment_count': 0   # 添加评论数
            }
            
            if preview_image_id:
                post['preview_image'] = preview_image_id
            
            result = mongo.db.posts.insert_one(post)
            
            if result.inserted_id:
                flash('发布成功！', 'success')
                # 根据帖子类型跳转到对应页面
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
