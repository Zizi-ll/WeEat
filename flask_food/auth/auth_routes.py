from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from ..models import User, db
from .auth_forms import LoginForm, RegistrationForm
from urllib.parse import urlparse

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('food.browsePage'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            if not next_page or urlparse(next_page).netloc != '':
                next_page = url_for('food.browsePage')
            return redirect(next_page)
        else:
            flash('用户名或密码错误，请重试。', 'danger')
    return render_template('auth/login.html', title='登录', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('注册成功，请登录！', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', title='注册', form=form)

@auth_bp.route('/profile/<username>') # 路由包含 <username> 参数
@login_required # 通常个人主页需要登录
def profile(username): # 函数名是 profile，参数名是 username
    user = User.query.filter_by(username=username).first_or_404()
    published_posts = user.posts  # 获取该用户所有食谱
    return render_template('user/profile.html', title=f'{user.username}的主页', user=user, published_posts=published_posts)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('您已成功登出。', 'info')
    return redirect(url_for('main.index'))