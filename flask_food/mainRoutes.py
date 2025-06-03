# flask_food/mainRoutes.py

from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@main_bp.route('/index')
def index():
    """
    主页 - 显示欢迎界面
    """
    return render_template('index.html', title='欢迎')