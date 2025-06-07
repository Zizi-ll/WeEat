# 用来构建category的内容
# 在终端 python seed_categories.py 需要单独运行

# seed_categories.py
from flask_food import create_app, db
from flask_food.models import Category
import datetime

app = create_app()

# 你要添加的分类和描述
category_list = [
    ("家常菜", "适合日常的家常美食"),
    ("快手菜", "快速简便的菜肴"),
    ("下饭菜", "特别下饭的美味"),
    ("早餐", "适合早晨食用的菜品"),
    ("肉类", "以肉为主的菜肴"),
    ("鱼虾海鲜", "海鲜类美食"),
    ("西餐", "风味西式料理"),
    ("蛋类豆制品", "以蛋或豆腐为主要食材"),
    ("汤羹", "各种汤类菜肴"),
    ("主食", "面、饭、粉类主食"),
    ("烘焙点心", "烘焙类甜点和小吃"),
    ("饮品", "果汁、奶茶等饮料"),
    ("其他", "不属于以上分类的其他菜品")
]

with app.app_context():
    for name, desc in category_list:
        if not Category.query.filter_by(name=name).first():
            new_category = Category(name=name, description=desc, created_at=datetime.datetime.utcnow())
            db.session.add(new_category)

    db.session.commit()
    print("✅ 分类数据已成功写入数据库！")
