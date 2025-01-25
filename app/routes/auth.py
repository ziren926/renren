from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import mongo  # 改为导入 mongo
from app.forms import LoginForm, RegisterForm
from app.models.user import User
from bson import ObjectId
from datetime import datetime
import logging

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        try:
            # 检查用户名和邮箱是否已存在
            if mongo.db.users.find_one({'username': form.username.data}):
                flash('用户名已存在', 'danger')
                return render_template('auth/register.html', form=form)
                
            if mongo.db.users.find_one({'email': form.email.data.lower()}):
                flash('邮箱已被注册', 'danger')
                return render_template('auth/register.html', form=form)
            
            # 创建新用户
            user = {
                'username': form.username.data,
                'email': form.email.data.lower(),
                'password': generate_password_hash(form.password.data),
                'created_at': datetime.utcnow()
            }
            
            result = mongo.db.users.insert_one(user)
            
            if result.inserted_id:
                flash('注册成功！请登录', 'success')
                return redirect(url_for('auth.login'))
            else:
                flash('注册失败，请重试', 'danger')
                
        except Exception as e:
            current_app.logger.error(f"Registration error: {str(e)}")
            flash('注册失败，请重试', 'danger')
            
    return render_template('auth/register.html', form=form)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    form = LoginForm()
    if form.validate_on_submit():
        try:
            # 获取表单数据
            username = form.username.data
            password = form.password.data
            
            # 查找用户
            user_data = mongo.db.users.find_one({'username': username})
            
            if user_data and 'password' in user_data and check_password_hash(user_data['password'], password):
                # 创建用户对象
                user = User(str(user_data['_id']))
                
                # 登录用户
                remember = form.remember.data if hasattr(form, 'remember') else False
                login_user(user, remember=remember)
                
                # 获取下一页URL
                next_page = request.args.get('next')
                if not next_page or not next_page.startswith('/'):
                    next_page = url_for('main.index')
                    
                flash('登录成功！', 'success')
                return redirect(next_page)
            else:
                flash('用户名或密码错误', 'danger')
                
        except Exception as e:
            current_app.logger.error(f"Login error: {str(e)}")
            flash('登录过程中发生错误', 'danger')
            
    return render_template('auth/login.html', form=form)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@bp.route('/profile')
@login_required
def profile():
    # 获取用户的帖子
    user_posts = list(mongo.db.posts.find({'author_id': ObjectId(current_user.get_id())}).sort('created_at', -1))
    
    # 获取用户的点赞数据
    total_likes = sum(post.get('likes', 0) for post in user_posts)
    total_views = sum(post.get('views', 0) for post in user_posts)
    total_posts = len(user_posts)
    
    return render_template('auth/profile.html',
                         user=current_user,
                         posts=user_posts,
                         total_likes=total_likes,
                         total_views=total_views,
                         total_posts=total_posts)
