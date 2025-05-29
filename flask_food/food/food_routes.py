from flask import Blueprint, render_template

food_bp = Blueprint('food', __name__) # 蓝图名称是 'food'

@food_bp.route('/recipes')
def index(): # <--- 这个函数名 'index' 对应了 url_for('food.index') 中的 'index'
    print("!!!!!! Food blueprint index() view function was called !!!!!!")
    # 临时返回一个简单的字符串，或者渲染一个 food/index.html 模板
    # recipes = [...] # 从数据库获取食谱数据
    # return render_template('food/index.html', title='All Recipes', recipes=recipes)
    return "This is the Food Recipes List Page (food.index)"
