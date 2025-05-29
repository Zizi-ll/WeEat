# flask_food/mainRoutes.py

from flask import Blueprint, render_template, redirect, url_for

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@main_bp.route('/index') #
def index():
    """
    P1: 未登录时的欢迎页 (Logo, 登录/注册链接)
    """
    print("!!!!!! Main blueprint index() view function was called !!!!!!")
    return render_template('index.html', title='欢迎') # title 会被 base.html 使用