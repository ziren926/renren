from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField, SubmitField, FileField
from wtforms.validators import DataRequired, Email, Length
from flask_wtf.file import FileAllowed

class LoginForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired()])
    password = PasswordField('密码', validators=[DataRequired()])
    submit = SubmitField('登录')

class RegisterForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('邮箱', validators=[DataRequired(), Email()])
    password = PasswordField('密码', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('注册')

class PostForm(FlaskForm):
    title = StringField('标题', validators=[DataRequired(), Length(min=2, max=100)])
    content = TextAreaField('内容', validators=[DataRequired()])
    category = SelectField('分类', choices=[
        ('需求集市', '需求集市 - 发布产品需求和想法'),
        ('经验分享', '经验分享 - 分享个人经验和心得'),
        ('生活工具', '生活工具 - 推荐好用的AI工具'),
        ('情绪管理', '情绪管理 - 分享情绪管理经验'),
        ('信息收纳', '信息收纳 - 信息整理与归档'),
        ('股市盯盘', '股市盯盘 - 股市相关讨论')
    ], validators=[DataRequired()])
    image = FileField('上传图片', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], '只允许上传图片文件！')
    ])
    submit = SubmitField('发布')

class CommentForm(FlaskForm):
    content = TextAreaField('评论内容', validators=[DataRequired(), Length(min=1, max=500)])
    submit = SubmitField('发表评论') 