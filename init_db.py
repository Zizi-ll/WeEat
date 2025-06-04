from flask_food import create_app, db
from flask_food.models import User

def init_db():
    app = create_app()
    with app.app_context():
        # 创建所有数据库表
        db.create_all()
        
        # 检查是否已存在管理员用户
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@example.com',
                role='admin'
            )
            admin.set_password('123456')
            db.session.add(admin)
            db.session.commit()
            print('管理员用户创建成功！')
        else:
            print('管理员用户已存在！')

if __name__ == '__main__':
    init_db() 