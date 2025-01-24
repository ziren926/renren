from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from app.forms import LoginForm, RegisterForm
from app.models import User
from app import db
from bson import ObjectId

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        # 检查用户名是否已存在
        if db.users.find_one({'username': form.username.data}):
            flash('用户名已存在', 'danger')
            return render_template('auth/register.html', form=form)
        
        # 创建新用户
        user_data = {
            'username': form.username.data,
            'email': form.email.data,
            'password_hash': generate_password_hash(form.password.data)  # 修改字段名为 password_hash
        }
        db.users.insert_one(user_data)
        flash('注册成功，请登录', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', form=form)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = db.users.find_one({'username': form.username.data})
        if user and check_password_hash(user.get('password_hash', ''), form.password.data):  # 修改字段名为 password_hash
            user_obj = User(user)
            login_user(user_obj)
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('main.index'))
        flash('用户名或密码错误', 'danger')
    
    return render_template('auth/login.html', form=form)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('已退出登录', 'info')
    return redirect(url_for('main.index'))

@bp.route('/profile')
@login_required
def profile():
    # 获取用户的帖子
    user_posts = list(db.posts.find({'author_id': ObjectId(current_user.get_id())}).sort('created_at', -1))
    
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
