from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from ..models import Post, db

food_bp = Blueprint('food', __name__) # 蓝图名称是 'food'

@food_bp.route('/recipes')
@login_required
def index():
    """
    食谱浏览页面
    """
    recipes = Post.query.order_by(Post.created_at.desc()).all()
    return render_template('food/index.html', title='食谱浏览', recipes=recipes)

@food_bp.route('/recipe/add', methods=['GET', 'POST'])
@login_required
def add_recipe():
    """
    添加新食谱
    """
    # TODO: 实现添加食谱的功能
    return render_template('food/add_recipe.html', title='发布食谱')

@food_bp.route('/recipe/<int:recipe_id>')
@login_required
def recipe_detail(recipe_id):
    """
    食谱详情页面
    """
    recipe = Post.query.get_or_404(recipe_id)
    return render_template('food/recipe_detail.html', title=recipe.title, recipe=recipe)

@food_bp.route('/browse')
@login_required
def browse():
    return render_template('food/browse.html', title='浏览美食')
