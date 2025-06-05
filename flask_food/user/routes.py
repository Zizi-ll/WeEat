from flask import Blueprint, render_template
from flask_login import login_required, current_user
from ..models import User

user_bp = Blueprint('user', __name__)

@user_bp.route('/profile/<username>')
@login_required
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('user/profile.html', user=user) 