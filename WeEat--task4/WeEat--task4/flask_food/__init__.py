# 应用工厂函数，初始化Flask应用和扩展
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect
from config import Config

#初始化数据库 (DB)、迁移 (Migrate)、登录管理器 (LoginManager)
db=SQLAlchemy() #创建了一个 SQLAlchemy 数据库对象 db，用来管理数据库连接、模型定义、增删查改等操作
migrate = Migrate() #迁移对象
bcrypt = Bcrypt()
login_manager = LoginManager() #登录管理的对象
login_manager.login_view = 'auth.login'
csrf = CSRFProtect()

def create_app(config_class=Config):
    app = Flask(__name__) #Flask实例
    app.config.from_object(config_class) #配置 连接数据库

    #将Flask扩展与Flask实例app进行绑定
    db.init_app(app)
    migrate.init_app(app, db)# 初始化 migrate，关联 app 和 db,确保 db 在 migrate 之前被初始化并关联到 app
    login_manager.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)

    #主蓝图
    from .mainRoutes import main_bp
    app.register_blueprint(main_bp)

    from .food.food_routes import food_bp  # <--- 导入 food_bp
    app.register_blueprint(food_bp, url_prefix='/food')  # <--- 注册 food_bp，并设置 URL 前缀

    # --- 注册 auth_bp ---
    from .auth.auth_routes import auth_bp  # <--- 导入 auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')  # <--- 注册 auth_bp，并设置 URL 前缀

    # 如果有main蓝图
    # from app.main.routes import main_bp
    # app.register_blueprint(main_bp)

    from . import models  # 确保 models 被导入，Flask-Migrate 才能检测到
    @login_manager.user_loader
    def load_user(user_id):
        return models.User.query.get(int(user_id))  # 使用 models.User

    return app