
from flask import Blueprint, render_template, redirect, url_for, flash
# from flask_login import login_user, logout_user, current_user # 根据需要导入
# from ..forms import LoginForm, RegistrationForm # 假设表单在 flask_food/forms.py 或 auth/auth_forms.py
# from ..models import User, db # 假设模型和 db 从上层导入
# from .. import bcrypt # 假设 bcrypt 从上层导入

auth_bp = Blueprint('auth', __name__) # 蓝图名称是 'auth'

@auth_bp.route('/login', methods=['GET', 'POST'])
def login(): # <--- 这个函数名 'login' 对应了 url_for('auth.login') 中的 'login'
    print("!!!!!! Auth blueprint login() view function was called !!!!!!")
    # form = LoginForm()
    # if form.validate_on_submit():
    #     # 处理登录逻辑
    #     user = User.query.filter_by(email=form.email.data).first()
    #     if user and bcrypt.check_password_hash(user.password, form.password.data):
    #         login_user(user, remember=form.remember_me.data)
    #         next_page = request.args.get('next')
    #         return redirect(next_page) if next_page else redirect(url_for('food.index'))
    #     else:
    #         flash('Login Unsuccessful. Please check email and password', 'danger')
    # return render_template('auth/login.html', title='Login', form=form)
    return "This is the Login Page (auth.login)" # 临时返回

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    print("!!!!!! Auth blueprint register() view function was called !!!!!!")
    # form = RegistrationForm()
    # if form.validate_on_submit():
    #     # 处理注册逻辑
    #     hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
    #     user = User(username=form.username.data, email=form.email.data, password=hashed_password)
    #     db.session.add(user)
    #     db.session.commit()
    #     flash('Your account has been created! You are now able to log in', 'success')
    #     return redirect(url_for('auth.login'))
    # return render_template('auth/register.html', title='Register', form=form)
    return "This is the Register Page (auth.register)" # 临时返回

@auth_bp.route('/logout')
def logout():
    print("!!!!!! Auth blueprint logout() view function was called !!!!!!")
    # logout_user()
    # return redirect(url_for('main.index')) # 重定向到主页
    return "This is the Logout Action (auth.logout)" # 临时返回