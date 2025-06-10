from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from ..models import User, db
from .auth_forms import LoginForm, RegistrationForm, ChangePasswordForm, DeleteAccountForm
from urllib.parse import urlparse
from ..utils import send_registration_email, send_login_notification
import logging

logger = logging.getLogger(__name__)
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
            # 发送登录通知邮件
            if not send_login_notification(user):
                logger.warning(f"无法发送登录通知邮件到 {user.email}")
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
        # 发送注册成功邮件
        if not send_registration_email(user):
            logger.warning(f"无法发送注册成功邮件到 {user.email}")
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

@auth_bp.route('/account/settings', methods=['GET', 'POST'])
@login_required
def account_settings():
    change_password_form = ChangePasswordForm()
    delete_account_form = DeleteAccountForm()
    
    if 'submit' in request.form:
        if request.form['submit'] == '更新密码':
            if change_password_form.validate_on_submit():
                if current_user.check_password(change_password_form.current_password.data):
                    current_user.set_password(change_password_form.new_password.data)
                    db.session.commit()
                    flash('密码已成功更新！', 'success')
                    return redirect(url_for('auth.account_settings'))
                else:
                    flash('当前密码错误，请重试。', 'danger')
        elif request.form['submit'] == '确认注销':
            if delete_account_form.validate_on_submit():
                if current_user.check_password(delete_account_form.confirm_password.data):
                    # 删除用户相关的所有数据
                    # 这里需要根据实际情况添加删除用户相关数据的代码
                    db.session.delete(current_user)
                    db.session.commit()
                    logout_user()
                    flash('您的账号已成功注销。', 'success')
                    return redirect(url_for('main.index'))
                else:
                    flash('密码错误，请重试。', 'danger')
    
    return render_template('user/account_settings.html', 
                         title='账号设置',
                         change_password_form=change_password_form,
                         delete_account_form=delete_account_form)

@auth_bp.route('/account/delete', methods=['POST'])
@login_required
def delete_account():
    form = DeleteAccountForm()
    if form.validate_on_submit():
        if current_user.check_password(form.confirm_password.data):
            # 删除用户相关的所有数据
            # 这里需要根据实际情况添加删除用户相关数据的代码
            db.session.delete(current_user)
            db.session.commit()
            logout_user()
            flash('您的账号已成功注销。', 'success')
            return redirect(url_for('main.index'))
        else:
            flash('密码错误，请重试。', 'danger')
    return redirect(url_for('auth.account_settings'))