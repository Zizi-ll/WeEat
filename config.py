#配置文件（数据库连接...）
import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    #保护Flask的会话session——记住用户的信息。表单CSFR——"跨站请求伪造"：攻击者诱导用户点击链接，悄悄以用户身份提交恶意请求
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True  # 确保CSRF保护开启

    # 邮件服务器配置
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or 'your-email@gmail.com'
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or 'your-app-password'
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_USERNAME') or 'your-email@gmail.com'
    MAIL_MAX_EMAILS = 5  # 限制每次发送的最大邮件数
    MAIL_ASCII_ATTACHMENTS = False  # 允许发送非ASCII字符
    MAIL_SUPPRESS_SEND = False  # 在测试环境中可以设置为True来禁用实际发送

    # 上传配置
    # STATIC_FOLDER_PATH 指向 'app/static' 文件夹的绝对路径
    STATIC_FOLDER_PATH = os.path.join(basedir, 'app', 'static')

    # 食谱图片上传的绝对路径
    UPLOAD_FOLDER_RECIPES_ABS = os.path.join(STATIC_FOLDER_PATH, 'uploads', 'recipes')
    # 食谱图片上传的相对路径 (相对于 static 文件夹)，用于生成 URL
    UPLOAD_FOLDER_RECIPES_REL = 'uploads/recipes'