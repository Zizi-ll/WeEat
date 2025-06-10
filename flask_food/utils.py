from flask import current_app
from flask_mail import Message
from . import mail
import logging

logger = logging.getLogger(__name__)

def send_email(to, subject, template):
    """
    发送邮件的通用函数
    :param to: 收件人邮箱
    :param subject: 邮件主题
    :param template: 邮件内容
    """
    try:
        msg = Message(
            subject,
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[to],
            html=template
        )
        mail.send(msg)
        logger.info(f"邮件成功发送到 {to}")
        return True
    except Exception as e:
        logger.error(f"发送邮件到 {to} 时出错: {str(e)}")
        return False

def send_registration_email(user):
    """
    发送注册成功邮件
    :param user: 用户对象
    """
    subject = '欢迎加入 WeEAT！'
    template = f'''
    <h1>亲爱的 {user.username}，</h1>
    <p>感谢您注册 WeEAT！</p>
    <p>您的账号已经成功创建，现在您可以开始使用我们的所有功能了。</p>
    <p>祝您使用愉快！</p>
    <p>WeEAT 团队</p>
    '''
    return send_email(user.email, subject, template)

def send_login_notification(user):
    """
    发送登录通知邮件
    :param user: 用户对象
    """
    subject = 'WeEAT 登录通知'
    template = f'''
    <h1>亲爱的 {user.username}，</h1>
    <p>我们检测到您的账号刚刚进行了登录。</p>
    <p>如果这不是您本人操作，请立即修改密码。</p>
    <p>WeEAT 团队</p>
    '''
    return send_email(user.email, subject, template) 