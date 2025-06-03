#配置文件（数据库连接...）
import os

basedir = os.path.abspath(os.path.dirname(__file__))#获取当前脚本文件所在目录的绝对路径
#用来做路径拼接

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'linyanzichenyingzhuhujialeguokaimeng' # 设置安全密钥
    #保护Flask的会话session——记住用户的信息。表单CSFR——"跨站请求伪造"：攻击者诱导用户点击链接，悄悄以用户身份提交恶意请求
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql+pymysql://root:Gkm104021@localhost:3306/weeat' # 连接weeat数据库
    SQLALCHEMY_TRACK_MODIFICATIONS = False