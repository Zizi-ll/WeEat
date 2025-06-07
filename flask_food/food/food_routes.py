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
from flask_food.models import Post, Category, Notification
from flask_food.models import Comment

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
    form.category.choices = [(str(c.id), c.name) for c in categories]

    if form.validate_on_submit():
        try:
            title = form.title.data
            category_id = form.category.data
            content = form.content.data

            uploaded_recipe_images = request.files.getlist('recipe_images')
            saved_image_paths = []

            # 确保至少有一张图片上传
            if not uploaded_recipe_images or not any(f.filename for f in uploaded_recipe_images):
                saved_image_paths = ['uploads/recipes/default_recipe.jpg']
            else:
                upload_path_full = os.path.join(current_app.root_path, UPLOAD_FOLDER)
                os.makedirs(upload_path_full, exist_ok=True)

                for file in uploaded_recipe_images:
                    if file and file.filename:  # 确保有文件名
                        original_filename = secure_filename(file.filename)
                        # 更安全的扩展名获取方式
                        if '.' in original_filename:
                            extension = original_filename.rsplit('.', 1)[1].lower()
                        else:
                            extension = 'jpg'  # 默认扩展名
                            original_filename = f"{original_filename}.{extension}"

                        if extension in ALLOWED_EXTENSIONS:
                            unique_filename = f"{uuid.uuid4().hex}.{extension}"
                            file_path_full = os.path.join(upload_path_full, unique_filename)
                            file.save(file_path_full)
                            saved_image_paths.append(
                                os.path.join(UPLOAD_FOLDER.replace('static/', '', 1), unique_filename))


            # 如果没有成功保存任何图片，使用默认图片
            if not saved_image_paths:
                saved_image_paths = ['uploads/recipes/default_recipe.jpg']

            category_object = Category.query.get(int(category_id))
            if not category_object:
                return jsonify({'success': False, 'message': '选择的分类不存在'}), 400

            new_recipe = Post(
                title=title,
                category=category_object,
                content_body=content,
                author=current_user,
                author_id=current_user.id,
                image_paths=json.dumps(saved_image_paths)  # 确保保存为JSON字符串
            )
            db.session.add(new_recipe)
            db.session.commit()

            return jsonify({'success': True, 'redirect_url': url_for('food.recipe_detail', recipe_id=new_recipe.id)})

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error adding recipe: {e}", exc_info=True)
            return jsonify({'success': False, 'message': f'发布食谱时出错: {str(e)}'}), 500

    return render_template('food/add_recipe.html', title='发布新食谱', form=form, categories=categories)

def get_first_image_filename(image_paths_str):
    if not image_paths_str:
        return 'default_recipe.jpg'  # 返回默认图片
    try:
        # 处理不同类型的输入
        if isinstance(image_paths_str, str):
            paths = json.loads(image_paths_str) if image_paths_str.startswith('[') else [image_paths_str]
        elif isinstance(image_paths_str, list):
            paths = image_paths_str
        else:
            paths = []

        if paths:
            img_path = paths[0].replace('\\', '/')
            if img_path.startswith('uploads/recipes/'):
                img_path = img_path[len('uploads/recipes/'):]
            return img_path
    except Exception as e:
        current_app.logger.error(f"解析图片路径错误: {e}")
    return 'default_recipe.jpg'  # 确保总是返回一个默认值

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
    recipe = Post.query.get_or_404(recipe_id)

    # 统一处理图片路径
    if recipe.image_paths:
        try:
            if isinstance(recipe.image_paths, str):
                paths = json.loads(recipe.image_paths)
            else:
                paths = recipe.image_paths

            # 标准化所有路径
            processed_paths = []
            for path in paths:
                # 替换反斜杠，移除重复的uploads/recipes
                clean_path = path.replace('\\', '/').replace('uploads/recipes/uploads/recipes', 'uploads/recipes')
                if not clean_path.startswith('uploads/recipes/'):
                    clean_path = f"uploads/recipes/{clean_path}"
                processed_paths.append(clean_path)

            recipe.image_paths = processed_paths
        except Exception as e:
            current_app.logger.error(f"Error processing image paths: {e}")
            recipe.image_paths = ['uploads/recipes/default_recipe.jpg']
    else:
        recipe.image_paths = ['uploads/recipes/default_recipe.jpg']

    return render_template(
        'food/recipeDetail.html',
        title=recipe.title,
        recipe=recipe,
        comments=Comment.query.filter_by(post_id=recipe_id).order_by(Comment.created_at).all()
    )

# 添加以下路由到 food_routes.py

@food_bp.route('/recipe/<int:recipe_id>/like', methods=['POST'])
@login_required
def like_recipe(recipe_id):
    recipe = Post.query.get_or_404(recipe_id)
    if current_user in recipe.liked_by_users:
        # 已经点赞，执行取消点赞
        recipe.liked_by_users.remove(current_user)
        action = 'unliked'
    else:
        # 未点赞，执行点赞
        recipe.liked_by_users.append(current_user)
        action = 'liked'

    db.session.commit()

    # 返回点赞数和当前状态
    return jsonify({
        'success': True,
        'action': action,
        'likes_count': len(recipe.liked_by_users)
    })

@food_bp.route('/recipe/<int:recipe_id>/favorite', methods=['POST'])
@login_required
def favorite_recipe(recipe_id):
    recipe = Post.query.get_or_404(recipe_id)
    if current_user in recipe.favorited_by_users:
        # 已经收藏，执行取消收藏
        recipe.favorited_by_users.remove(current_user)
        action = 'unfavorited'
    else:
        # 未收藏，执行收藏
        recipe.favorited_by_users.append(current_user)
        action = 'favorited'

    db.session.commit()

    # 返回收藏数和当前状态
    return jsonify({
        'success': True,
        'action': action,
        'favorites_count': len(recipe.favorited_by_users)
    })

@food_bp.route('/recipe/<int:recipe_id>/comment', methods=['POST'])
@login_required
def add_comment(recipe_id):
    recipe = Post.query.get_or_404(recipe_id)
    comment_content = request.form.get('comment', '').strip()

    if not comment_content:
        return jsonify({'success': False, 'message': '评论内容不能为空'}), 400

    try:
        parent_id = request.form.get('parent_id')
        parent_comment = Comment.query.get(parent_id) if parent_id else None

        new_comment = Comment(
            text_content=comment_content,
            author=current_user,
            post=recipe,
            parent=parent_comment
        )

        db.session.add(new_comment)
        db.session.commit()

        # 创建通知（如果不是回复自己的评论）
        if parent_comment and parent_comment.author_id != current_user.id:
            notification = Notification(
                recipient_id=parent_comment.author_id,
                actor_id=current_user.id,
                related_post_id=recipe.id,
                related_comment_id=new_comment.id,
                notification_type='reply',
                message=f"{current_user.username} 回复了你的评论"
            )
            db.session.add(notification)
            db.session.commit()

        return jsonify({
            'success': True,
            'comment_id': new_comment.id,
            'author_name': current_user.username,
            'author_avatar': current_user.profile_picture_url or url_for('static',
                                                                         filename='images/default_avatar.jpg'),
            'created_at': new_comment.created_at.strftime('%Y-%m-%d %H:%M'),
            'content': new_comment.text_content
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error adding comment: {e}")
        return jsonify({'success': False, 'message': '添加评论失败'}), 500
