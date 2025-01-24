from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify, send_file
from flask_login import current_user, login_required
from app.models.post import Post
from app import db, fs, mongo
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

bp = Blueprint('main', __name__, url_prefix='')

@bp.route('/')
@bp.route('/index')
def index():
    try:
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        per_page = 10
        category = request.args.get('category')
        
        # 构建查询条件
        query = {}
        if category:
            query['category'] = category
            
        # 获取总数
        total = db.posts.count_documents(query)
        
        # 获取分页数据
        posts = list(db.posts.find(query)
                    .sort('created_at', -1)
                    .skip((page - 1) * per_page)
                    .limit(per_page))
                    
        # 处理每个帖子的数据
        for post in posts:
            # 获取作者信息
            author = db.users.find_one({'_id': post['author_id']})
            post['author_name'] = author['username'] if author else '未知用户'
            
            # 处理时间格式
            if isinstance(post.get('created_at'), str):
                post['created_at'] = datetime.fromisoformat(post['created_at'].replace('Z', '+00:00'))
            
            # 从内容中提取第一张图片的ID
            if 'content' in post:
                content = post['content']
                # 打印内容以便调试
                current_app.logger.info(f"Post content: {content}")
                
                # 尝试多种可能的图片格式
                image_id = None
                
                # 1. 尝试完整的Markdown格式
                markdown_match = re.search(r'!\[.*?\]\(/image/([a-f0-9]{24})\)', content)
                if markdown_match:
                    image_id = markdown_match.group(1)
                
                # 2. 尝试直接的URL格式
                if not image_id:
                    url_match = re.search(r'/image/([a-f0-9]{24})', content)
                    if url_match:
                        image_id = url_match.group(1)
                
                if image_id:
                    post['preview_image_id'] = image_id
                    current_app.logger.info(f"Found image ID in post {post['_id']}: {image_id}")
                else:
                    current_app.logger.info(f"No image found in post {post['_id']}")
            
            # 转换 ObjectId 为字符串
            post['_id'] = str(post['_id'])
            post['author_id'] = str(post['author_id'])
        
        # 在返回之前打印一下处理后的帖子数据
        for post in posts[:3]:
            current_app.logger.info(f"Post {post['_id']} preview image: {post.get('preview_image_id')}")
        
        # 计算分页信息
        total_pages = (total + per_page - 1) // per_page
        pagination = {
            'page': page,
            'total': total,
            'per_page': per_page,
            'total_pages': total_pages,
            'has_prev': page > 1,
            'has_next': page < total_pages,
            'pages': range(max(1, page - 2), min(total_pages + 1, page + 3))
        }
        
        # 获取热门排行
        hot_ranking = list(db.posts.find().sort('views', -1).limit(5))
        for post in hot_ranking:
            post['_id'] = str(post['_id'])
            
        # 获取最新动态
        trending_ranking = list(db.posts.find().sort('created_at', -1).limit(5))
        for post in trending_ranking:
            post['_id'] = str(post['_id'])
            if isinstance(post.get('created_at'), str):
                post['created_at'] = datetime.fromisoformat(post['created_at'].replace('Z', '+00:00'))
        
        return render_template('index.html',
                             posts=posts,
                             hot_ranking=hot_ranking,
                             trending_ranking=trending_ranking,
                             pagination=pagination,
                             current_category=category)
                             
    except Exception as e:
        current_app.logger.error(f"Index error: {str(e)}")
        return render_template('index.html', posts=[], hot_ranking=[], trending_ranking=[], pagination={})

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

@bp.route('/post/<post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    try:
        # 获取帖子
        post = db.posts.find_one({'_id': ObjectId(post_id)})
        if not post:
            flash('帖子不存在', 'danger')
            return redirect(url_for('main.index'))
            
        # 检查权限
        if str(post['author_id']) != current_user.get_id():
            flash('你没有权限编辑这篇帖子', 'danger')
            return redirect(url_for('main.post_detail', post_id=post_id))
            
        form = PostForm()
        
        if request.method == 'GET':
            # 填充表单
            form.title.data = post['title']
            form.content.data = post['content']
            form.category.data = post.get('category', '经验交流')
            
        if form.validate_on_submit():
            # 更新帖子
            update_data = {
                'title': form.title.data,
                'content': form.content.data,
                'category': form.category.data,
                'updated_at': datetime.utcnow()
            }
            
            # 处理图片上传
            if form.images.data:
                image_urls = []
                for image in form.images.data:
                    if image.filename:
                        # 保存到 GridFS
                        file_id = mongo.save_file(image.filename, image)
                        image_url = f"![{image.filename}](http://127.0.0.1:5000/image/{file_id})"
                        image_urls.append(image_url)
                
                # 将新图片 URL 添加到内容末尾
                if image_urls:
                    update_data['content'] = update_data['content'] + '\n' + '\n'.join(image_urls)
            
            db.posts.update_one(
                {'_id': ObjectId(post_id)},
                {'$set': update_data}
            )
            
            flash('帖子更新成功！', 'success')
            return redirect(url_for('main.post_detail', post_id=post_id))
            
        return render_template('post/edit.html', form=form, post=post)
        
    except Exception as e:
        current_app.logger.error(f"Edit post error: {str(e)}")
        flash('编辑帖子失败', 'danger')
        return redirect(url_for('main.post_detail', post_id=post_id))

@bp.route('/post/<post_id>/delete')
@login_required
def delete_post(post_id):
    post = Post.get_by_id(post_id)
    if not post or str(post.author_id) != current_user.get_id():
        flash('你没有权限删除这个帖子')
        return redirect(url_for('main.index'))
        
    db.posts.delete_one({'_id': ObjectId(post_id)})
    flash('帖子已删除')
    return redirect(url_for('main.index'))

@bp.route('/search')
def search():
    query = request.args.get('q', '')
    if not query:
        return redirect(url_for('main.index'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # 使用文本索引搜索
    search_results = db.posts.find({
        '$text': {'$search': query}
    }).sort('created_at', -1).skip((page-1)*per_page).limit(per_page)
    
    total_results = db.posts.count_documents({
        '$text': {'$search': query}
    })
    
    posts = []
    for post_data in search_results:
        post = Post.from_db(post_data)
        author = db.users.find_one({'_id': post.author_id})
        post.author_name = author['username'] if author else '未知用户'
        posts.append(post)
    
    pagination = {
        'page': page,
        'total_pages': math.ceil(total_results / per_page),
        'has_prev': page > 1,
        'has_next': page < math.ceil(total_results / per_page),
        'pages': range(max(1, page - 2), min(math.ceil(total_results / per_page) + 1, page + 3))
    }
    
    return render_template('search.html', 
                         posts=posts, 
                         query=query, 
                         pagination=pagination,
                         total_results=total_results)

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

@bp.route('/post/<post_id>', methods=['GET', 'POST'])
def post_detail(post_id):
    try:
        current_app.logger.info(f"Accessing post_detail with ID: {post_id}")
        
        # 获取帖子数据
        post_data = db.posts.find_one({'_id': ObjectId(post_id)})
        if not post_data:
            flash('帖子不存在', 'danger')
            return redirect(url_for('main.index'))
        
        # 增加浏览量
        db.posts.update_one(
            {'_id': ObjectId(post_id)},
            {'$inc': {'views': 1}}
        )
        
        # 获取作者信息
        author = db.users.find_one({'_id': post_data['author_id']})
        post_data['author_name'] = author['username'] if author else '未知用户'
        
        # 处理时间格式
        if isinstance(post_data.get('created_at'), str):
            post_data['created_at'] = datetime.fromisoformat(post_data['created_at'].replace('Z', '+00:00'))
        elif not isinstance(post_data.get('created_at'), datetime):
            post_data['created_at'] = datetime.utcnow()
        
        # 获取评论
        comments = list(db.comments.find({'post_id': ObjectId(post_id)}).sort('created_at', -1))
        for comment in comments:
            comment_user = db.users.find_one({'_id': comment['user_id']})
            comment['username'] = comment_user['username'] if comment_user else '未知用户'
            if isinstance(comment.get('created_at'), str):
                comment['created_at'] = datetime.fromisoformat(comment['created_at'].replace('Z', '+00:00'))
            elif not isinstance(comment.get('created_at'), datetime):
                comment['created_at'] = datetime.utcnow()
            comment['_id'] = str(comment['_id'])
            comment['user_id'] = str(comment['user_id'])
        
        # 处理评论表单
        form = CommentForm()
        if form.validate_on_submit():
            if not current_user.is_authenticated:
                flash('请先登录后再评论', 'warning')
                return redirect(url_for('auth.login'))
            
            comment_data = {
                'post_id': ObjectId(post_id),
                'user_id': ObjectId(current_user.get_id()),
                'content': form.content.data,
                'created_at': datetime.utcnow()
            }
            db.comments.insert_one(comment_data)
            
            # 更新帖子的评论计数
            db.posts.update_one(
                {'_id': ObjectId(post_id)},
                {'$inc': {'comment_count': 1}}
            )
            
            flash('评论发表成功！', 'success')
            return redirect(url_for('main.post_detail', post_id=post_id))
        
        # 确保所有必要的字段都存在
        post_data.setdefault('views', 0)
        post_data.setdefault('likes', 0)
        post_data.setdefault('comment_count', len(comments))
        
        # 转换 ObjectId 为字符串
        post_data['_id'] = str(post_data['_id'])
        post_data['author_id'] = str(post_data['author_id'])
        
        # 检查当前用户是否已点赞
        if current_user.is_authenticated:
            post_data['liked_by_user'] = db.likes.find_one({
                'post_id': ObjectId(post_id),
                'user_id': ObjectId(current_user.get_id())
            }) is not None
        else:
            post_data['liked_by_user'] = False
        
        return render_template('post/detail.html',
                             post=post_data,
                             comments=comments,
                             form=form)
                             
    except Exception as e:
        current_app.logger.error(f"Post detail error: {str(e)}")
        flash('获取帖子失败', 'danger')
        return redirect(url_for('main.index'))

@bp.route('/post/<post_id>/like', methods=['POST'])
@login_required
def like_post(post_id):
    post = Post.get_by_id(post_id)
    if not post:
        return jsonify({'success': False, 'error': '帖子不存在'})
    
    like = db.likes.find_one({
        'post_id': ObjectId(post_id),
        'user_id': ObjectId(current_user.get_id())
    })
    
    if like:
        # 取消点赞
        db.likes.delete_one({'_id': like['_id']})
        db.posts.update_one({'_id': ObjectId(post_id)}, {'$inc': {'likes': -1}})
        new_likes = post.likes - 1
    else:
        # 添加点赞
        db.likes.insert_one({
            'post_id': ObjectId(post_id),
            'user_id': ObjectId(current_user.get_id()),
            'created_at': datetime.utcnow()
        })
        db.posts.update_one({'_id': ObjectId(post_id)}, {'$inc': {'likes': 1}})
        new_likes = post.likes + 1
    
    return jsonify({'success': True, 'likes': new_likes})

@bp.route('/post/<post_id>/comment', methods=['POST'])
@login_required
def add_comment(post_id):
    content = request.form.get('content')
    if not content:
        flash('评论内容不能为空', 'error')
        return redirect(url_for('main.post_detail', post_id=post_id))
    
    comment = Comment(
        content=content,
        post_id=ObjectId(post_id),
        author_id=ObjectId(current_user.get_id())
    )
    comment.save()
    
    flash('评论发表成功', 'success')
    return redirect(url_for('main.post_detail', post_id=post_id))

@bp.route('/comment/<comment_id>/delete', methods=['POST'])
@login_required
def comment_delete(comment_id):
    try:
        comment = db.comments.find_one({'_id': ObjectId(comment_id)})
        if not comment:
            return jsonify({'success': False, 'message': '评论不存在'})
        
        # 检查是否是评论作者
        if str(comment['user_id']) != current_user.get_id():
            return jsonify({'success': False, 'message': '没有权限删除此评论'})
        
        # 删除评论
        db.comments.delete_one({'_id': ObjectId(comment_id)})
        
        # 更新帖子的评论计数
        db.posts.update_one(
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
            return jsonify({'success': False, 'message': '没有文件'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'success': False, 'message': '没有选择文件'}), 400
        
        if file and allowed_file(file.filename):
            # 保存到 GridFS
            filename = secure_filename(file.filename)
            content_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
            
            # 存储文件元数据
            metadata = {
                'user_id': ObjectId(current_user.get_id()),
                'upload_time': datetime.utcnow(),
                'filename': filename,
                'content_type': content_type
            }
            
            # 将文件保存到 GridFS
            file_id = fs.put(file, filename=filename, metadata=metadata)
            
            # 生成访问URL
            image_url = url_for('main.get_image', file_id=str(file_id), _external=True)
            return jsonify({'success': True, 'url': image_url})
            
        return jsonify({'success': False, 'message': '不支持的文件类型'}), 400
    
    except Exception as e:
        current_app.logger.error(f"Upload error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@bp.route('/image/<file_id>')
def get_image(file_id):
    try:
        # 添加调试日志
        current_app.logger.info(f"Fetching image with ID: {file_id}")
        
        # 从 GridFS 获取文件
        file_data = mongo.db.fs.files.find_one({'_id': ObjectId(file_id)})
        if file_data:
            # 获取文件内容
            chunks = list(mongo.db.fs.chunks.find({'files_id': ObjectId(file_id)}).sort('n', 1))
            if chunks:
                # 组合所有块
                data = b''.join(chunk['data'] for chunk in chunks)
                # 创建文件对象
                file_object = io.BytesIO(data)
                # 获取文件类型
                content_type = file_data.get('contentType', 'image/jpeg')
                
                # 添加调试日志
                current_app.logger.info(f"Serving image with content type: {content_type}")
                
                return send_file(
                    file_object,
                    mimetype=content_type,
                    as_attachment=False,
                    download_name=file_data.get('filename', 'image.jpg')
                )
        
        current_app.logger.error(f"Image not found: {file_id}")
        return "Image not found", 404
        
    except Exception as e:
        current_app.logger.error(f"Error serving image {file_id}: {str(e)}")
        return str(e), 500

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
    if form.validate_on_submit():
        post_data = {
            'title': form.title.data,
            'content': form.content.data,
            'category': form.category.data.split(' - ')[0],
            'author_id': ObjectId(current_user.get_id()),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'views': 0,
            'likes': 0,
            'comment_count': 0
        }
        
        # 处理图片上传
        if form.image.data:
            file = form.image.data
            if allowed_file(file.filename):
                try:
                    # 保存到 GridFS
                    filename = secure_filename(file.filename)
                    metadata = {
                        'user_id': ObjectId(current_user.get_id()),
                        'upload_time': datetime.utcnow(),
                        'filename': filename,
                        'content_type': file.content_type
                    }
                    file_id = fs.put(file, filename=filename, metadata=metadata)
                    
                    # 添加图片URL到内容中
                    image_url = url_for('main.get_image', file_id=str(file_id))
                    post_data['content'] += f'\n\n![{filename}]({image_url})'
                    
                except Exception as e:
                    flash(f'图片上传失败: {str(e)}', 'danger')
        
        db.posts.insert_one(post_data)
        flash('帖子发布成功！', 'success')
        return redirect(url_for('main.index'))
    
    return render_template('post/create.html', form=form)

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
    return render_template('market.html', posts=[], pagination={})
