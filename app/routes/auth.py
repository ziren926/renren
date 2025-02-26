from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.forms import LoginForm, RegistrationForm
from app.models.user import User
from bson import ObjectId
from datetime import datetime
from app.extensions import mongo
import logging

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # 检查用户名是否已存在
        if mongo.db.users.find_one({'username': form.username.data}):
            flash('用户名已被使用', 'danger')
            return redirect(url_for('auth.register'))
            
        # 创建新用户
        user = {
            'username': form.username.data,
            'password': generate_password_hash(form.password.data),
            'created_at': datetime.utcnow()
        }
        
        mongo.db.users.insert_one(user)
        flash('注册成功，请登录', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/register.html', form=form)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    form = LoginForm()
    if form.validate_on_submit():
        user = User.get_by_username(form.username.data)
        if user and check_password_hash(user.user_data.get('password'), form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('main.index'))
        flash('用户名或密码错误', 'danger')
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
