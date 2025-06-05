# app/food/food_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user
from .food_forms import RecipeForm
from flask_food.models import Post, Category # 从 app.models 导入
from flask_food import db
import os
from werkzeug.utils import secure_filename
import uuid
from flask import jsonify
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField, MultipleFileField
from wtforms.validators import DataRequired, Length


food_bp = Blueprint('food', __name__,
                    template_folder='templates',
                    static_folder='static',
                    static_url_path='/food/static')


# 配置图片上传
UPLOAD_FOLDER = 'static/uploads/recipes'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

class RecipeForm(FlaskForm):
    title = StringField('标题', validators=[DataRequired(), Length(min=2, max=150)])
    category = SelectField('分类', choices=[...], validators=[DataRequired()]) # 把你的分类选项放这里
    content = TextAreaField('内容', validators=[DataRequired()])
    # 对于 AJAX 上传，我们不需要 FileField 在这里做主要验证，但可以保留
    # recipe_images = MultipleFileField('食谱图片', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'gif'], '只允许图片!')])
    submit = SubmitField('发布食谱')

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@food_bp.route('/recipes')
@login_required
def index():
    """
    食谱浏览页面
    """
    recipes = Post.query.order_by(Post.created_at.desc()).all()
    return render_template('food/index.html', title='食谱浏览', recipes=recipes)

@food_bp.route('/add_recipe', methods=['GET', 'POST'])
@login_required
def add_recipe():
    form = RecipeForm()
    if request.method == 'POST':
        try:
            title = request.form.get('title')
            category = request.form.get('category')
            content = request.form.get('content')

            # 获取上传的图片文件列表 (通过JS的 FormData append)
            uploaded_recipe_images = request.files.getlist('recipe_images')

            # if not title or not category or not content:
            #     flash('标题、分类和内容不能为空！', 'danger')
            #     # 因为是 AJAX 提交，flash 可能不会直接显示，需要前端配合或后端返回错误JSON
            #     return jsonify({'success': False, 'message': '标题、分类和内容不能为空！'}), 400

            saved_image_paths = []
            if uploaded_recipe_images:
                # 确保上传文件夹存在
                upload_path_full = os.path.join(current_app.root_path, UPLOAD_FOLDER)
                os.makedirs(upload_path_full, exist_ok=True)

                for file in uploaded_recipe_images:
                    if file and allowed_file(file.filename):
                        original_filename = secure_filename(file.filename)
                        extension = original_filename.rsplit('.', 1)[1].lower()
                        unique_filename = f"{uuid.uuid4().hex}.{extension}"
                        file_path_full = os.path.join(upload_path_full, unique_filename)

                        try:
                            file.save(file_path_full)
                            # 存储相对路径，相对于 static 目录，或者你的应用根目录
                            # 这里我们存储相对于 static 目录的路径，方便 url_for('static', ...)
                            # 但数据库里存 UPLOAD_FOLDER 下的相对路径更通用
                            saved_image_paths.append(os.path.join(UPLOAD_FOLDER.replace('static/', '', 1), unique_filename))
                        except Exception as e:
                            current_app.logger.error(f"Error saving file {unique_filename}: {e}")
                            flash(f'保存图片 {original_filename} 时出错。', 'danger')
                            return jsonify({'success': False, 'message': f'保存图片 {original_filename} 时出错。'}), 500
                    elif file and file.filename != '':  # 如果有文件但类型不对
                        flash(f'文件 "{file.filename}" 类型不允许。只允许 {", ".join(ALLOWED_EXTENSIONS)}。', 'warning')

            category_object = Category.query.filter_by(name=category).first()
            title_from_form = request.form.get('title')
            # 确保你从表单获取内容时，变量名可以是你自己定的，但传递给 Post 时要用模型字段名
            text_content_from_form = request.form.get('content')  # 假设你的 textarea 的 name 是
            new_recipe = Post(
                title=title_from_form,
                category=category_object,
                content_body=text_content_from_form,
                author=current_user,
                author_id=current_user.id
                # author=current_user  # 或者 user_id=current_user.id
            )
            if saved_image_paths:
                new_recipe.image_paths = saved_image_paths  # 使用我们定义的setter


                db.session.add(new_recipe)
                db.session.commit()
                flash('食谱已成功发布！', 'success')
                # 对于 AJAX 请求，返回 JSON，包含重定向 URL
                return jsonify(
                    {'success': True, 'redirect_url': url_for('food.recipe_detail', recipe_id=new_recipe.id)})  # 假设有这个路由
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error adding recipe to DB: {e}")
            flash('发布食谱时数据库出错，请稍后再试。', 'danger')
            return jsonify({'success': False, 'message': '发布食谱时数据库出错，请稍后再试。'}), 500

        # GET 请求时
    return render_template('food/add_recipe.html', title='发布新食谱',form=form)


@food_bp.route('/browsePage', endpoint='browsePage')  # 显式指定端点名
@login_required
def browse():
    return render_template('food/browsePage.html', title='浏览美食')\



@food_bp.route('/recipe/<int:recipe_id>')  # 或者 '/post/<int:post_id>'
def recipe_detail(recipe_id):  # 函数名是 recipe_detail，参数名是 recipe_id
    # 根据 recipe_id 从数据库查询食谱/帖子
    # 使用 post_id 作为参数名，与 url_for 中一致
    # 如果你的模型是 Post，并且主键是 id
    recipe_or_post = Post.query.get_or_404(recipe_id)

    # 假设你有一个模板叫 recipe_detail.html 或 post_detail.html
    return render_template(
        'food/recipeDetail.html',  # 确保模板路径正确
        title=recipe_or_post.title,
        recipe=recipe_or_post  # 将查询到的对象传递给模板
    )