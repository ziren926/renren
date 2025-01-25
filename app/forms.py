from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField, SubmitField, FileField, EmailField, BooleanField
from wtforms.validators import DataRequired, Email, Length, Optional, EqualTo, ValidationError
from flask_wtf.file import FileAllowed
import re

class LoginForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(message='用户名不能为空')])
    password = PasswordField('密码', validators=[DataRequired(message='密码不能为空')])
    remember = BooleanField('记住我')
    submit = SubmitField('登录')

class RegisterForm(FlaskForm):
    username = StringField('用户名', validators=[
        DataRequired(message='用户名不能为空'),
        Length(min=3, max=20, message='用户名长度必须在3-20个字符之间')
    ])
    
    email = EmailField('邮箱', validators=[
        DataRequired(message='邮箱不能为空'),
        Email(message='请输入有效的邮箱地址')
    ])
    
    password = PasswordField('密码', validators=[
        DataRequired(message='密码不能为空'),
        Length(min=6, max=20, message='密码长度必须在6-20个字符之间')
    ])
    
    confirm = PasswordField('确认密码', validators=[
        DataRequired(message='请确认密码'),
        EqualTo('password', message='两次输入的密码不一致')
    ])
    
    def validate_username(self, field):
        # 检查用户名是否只包含字母、数字和下划线
        if not re.match(r'^[a-zA-Z0-9_]+$', field.data):
            raise ValidationError('用户名只能包含字母、数字和下划线')
        
        # 检查用户名是否已存在
        from app import mongo
        if mongo.db.users.find_one({'username': field.data}):
            raise ValidationError('该用户名已被使用')
    
    def validate_email(self, field):
        # 检查邮箱是否已存在
        from app import mongo
        if mongo.db.users.find_one({'email': field.data.lower()}):
            raise ValidationError('该邮箱已被注册')

    def validate_password(self, field):
        # 密码强度验证
        password = field.data
        if not re.search(r'[A-Z]', password):
            raise ValidationError('密码必须包含至少一个大写字母')
        if not re.search(r'[a-z]', password):
            raise ValidationError('密码必须包含至少一个小写字母')
        if not re.search(r'\d', password):
            raise ValidationError('密码必须包含至少一个数字')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError('密码必须包含至少一个特殊字符')

class PostForm(FlaskForm):
    title = StringField('标题', validators=[DataRequired(), Length(min=1, max=100)])
    content = TextAreaField('内容', validators=[DataRequired()])
    preview_image = FileField('预览图片')
    post_type = SelectField('类型', choices=[
        ('normal', '经验分享'),
        ('market', '需求帖')
    ], default='normal')
    submit = SubmitField('发布文章')

class CommentForm(FlaskForm):
    content = TextAreaField('评论内容', validators=[DataRequired()])
    submit = SubmitField('发布评论') 