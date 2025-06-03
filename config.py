#配置文件（数据库连接...）
import os

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))#获取当前脚本文件所在目录的绝对路径
#用来做路径拼接

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'linyanzichenyingzhuhujialeguokaimeng' # 设置安全密钥
    #保护Flask的会话session——记住用户的信息。表单CSFR——“跨站请求伪造”：攻击者诱导用户点击链接，悄悄以用户身份提交恶意请求
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql+pymysql://root:linyanzi2005@localhost:3307/mydatabase' # Keep your credentials safe 连接我的数据库
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True  # 确保CSRF保护开启

    # 上传配置
    # STATIC_FOLDER_PATH 指向 'app/static' 文件夹的绝对路径
    STATIC_FOLDER_PATH = os.path.join(BASE_DIR, 'app', 'static')

    # 食谱图片上传的绝对路径
    UPLOAD_FOLDER_RECIPES_ABS = os.path.join(STATIC_FOLDER_PATH, 'uploads', 'recipes')
    # 食谱图片上传的相对路径 (相对于 static 文件夹)，用于生成 URL
    UPLOAD_FOLDER_RECIPES_REL = 'uploads/recipes'