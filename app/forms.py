from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField, SubmitField, FileField, EmailField, BooleanField
from wtforms.validators import DataRequired, Email, Length, Optional, EqualTo, ValidationError
from flask_wtf.file import FileAllowed
import re

class LoginForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired()])
    password = PasswordField('密码', validators=[DataRequired()])
    remember = BooleanField('记住我')
    submit = SubmitField('登录')

class RegistrationForm(FlaskForm):
    username = StringField('用户名', validators=[
        DataRequired(message='用户名不能为空'),
        Length(min=3, max=20, message='用户名长度必须在3-20位之间')
    ])
    password = PasswordField('密码', validators=[
        DataRequired(message='密码不能为空'),
        Length(min=6, message='密码长度不能少于6位')
    ])
    confirm_password = PasswordField('确认密码', validators=[
        DataRequired(message='请确认密码'),
        EqualTo('password', message='两次输入的密码不一致')
    ])
    submit = SubmitField('注册')

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