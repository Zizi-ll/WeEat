# app/food/food_routes.py
import os
import json
import uuid
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField, MultipleFileField
from wtforms.validators import DataRequired, Length

from flask_food import db
from flask_food.models import Post, Category

food_bp = Blueprint('food', __name__,
                    template_folder='templates',
                    static_folder='static',
                    static_url_path='/food/static')

UPLOAD_FOLDER = 'static/uploads/recipes'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

class RecipeForm(FlaskForm):
    title = StringField('标题', validators=[DataRequired(), Length(min=2, max=150)])
    category = SelectField('分类', choices=[], validators=[DataRequired()])  # choices 运行时动态注入
    content = TextAreaField('内容', validators=[DataRequired()])
    submit = SubmitField('发布食谱')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@food_bp.route('/recipes')
@login_required
def index():
    recipes = Post.query.order_by(Post.created_at.desc()).all()
    return render_template('food/favourites.html', title='我的收藏', recipes=recipes)

@food_bp.route('/add_recipe', methods=['GET', 'POST'])
@login_required
def add_recipe():
    form = RecipeForm()
    categories = Category.query.all()
    form.category.choices = [(str(c.id), c.name) for c in categories]  # 填充分类

    if form.validate_on_submit():
        try:
            title = form.title.data
            category_id = form.category.data  # 这里用 form.category.data，而不是 request.form.get()
            content = form.content.data
            uploaded_recipe_images = request.files.getlist('recipe_images[]')

            saved_image_paths = []
            if uploaded_recipe_images:
                upload_path_full = os.path.join(current_app.root_path, UPLOAD_FOLDER)
                os.makedirs(upload_path_full, exist_ok=True)

                for file in uploaded_recipe_images:
                    if file and allowed_file(file.filename):
                        original_filename = secure_filename(file.filename)
                        extension = original_filename.rsplit('.', 1)[1].lower()
                        unique_filename = f"{uuid.uuid4().hex}.{extension}"
                        file_path_full = os.path.join(upload_path_full, unique_filename)
                        file.save(file_path_full)
                        saved_image_paths.append(f"uploads/recipes/{unique_filename}")

            category_object = Category.query.get(int(category_id))
            if not category_object:
                return jsonify({'success': False, 'message': '选择的分类不存在'}), 400

            new_recipe = Post(
                title=title,
                category=category_object,
                content_body=content,
                author=current_user,
                author_id=current_user.id,
                image_paths=json.dumps(saved_image_paths)
            )
            db.session.add(new_recipe)
            db.session.commit()

            return jsonify({'success': True, 'redirect_url': url_for('food.recipe_detail', recipe_id=new_recipe.id)})

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error adding recipe: {e}")
            return jsonify({'success': False, 'message': '发布食谱时数据库出错，请稍后再试。'}), 500

    return render_template('food/add_recipe.html', title='发布新食谱', form=form, categories=categories)

def get_first_image_filename(image_paths_str):
    if not image_paths_str:
        return None
    try:
        paths = json.loads(image_paths_str) if not isinstance(image_paths_str, list) else image_paths_str
        if isinstance(paths, list) and paths:
            img_path = paths[0].replace('\\', '/')
            if img_path.startswith('uploads/recipes/'):
                img_path = img_path[len('uploads/recipes/'):]
            return img_path
    except Exception as e:
        current_app.logger.error(f"解析图片路径错误: {e}")
    return None

@food_bp.route('/browsePage', endpoint='browsePage')
@login_required
def browse():
    category_keyword = request.args.get('category', '').strip()
    recipes = []

    if category_keyword:
        recipes = Post.query.join(Category).filter(Category.name.ilike(f"%{category_keyword}%")).order_by(Post.created_at.desc()).all()
    else:
        recipes = Post.query.order_by(Post.created_at.desc()).all()

    for r in recipes:
        r.image_filename = get_first_image_filename(r.image_paths)

    return render_template('food/browsePage.html',
                           title='浏览美食',
                           recipes=recipes,
                           category_keyword=category_keyword)

@food_bp.route('/recipe/<int:recipe_id>')
def recipe_detail(recipe_id):
    recipe_or_post = Post.query.get_or_404(recipe_id)
    return render_template(
        'food/recipeDetail.html',
        title=recipe_or_post.title,
        recipe=recipe_or_post
    )
