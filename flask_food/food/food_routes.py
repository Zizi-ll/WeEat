# app/food/food_routes.py
import os
import json
import uuid
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField, MultipleFileField
from wtforms.validators import DataRequired, Length, Optional

from flask_food import db
from flask_food.models import Post, Category, Notification,User
from flask_food.models import Comment
from flask_food.models import post_favorites

food_bp = Blueprint('food', __name__,
                    static_folder='static',
                    static_url_path='/food/static')

UPLOAD_FOLDER = 'static/uploads/recipes'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

class RecipeForm(FlaskForm):
    title = StringField('标题', validators=[DataRequired(), Length(min=2, max=150)])
    category = SelectField('分类', choices=[], validators=[DataRequired()])  # choices 运行时动态注入
    content = TextAreaField('内容', validators=[DataRequired()])
    recipe_images = MultipleFileField('食谱图片', validators=[Optional()])
    submit = SubmitField('发布食谱')

# 用于管理员审核的表单
class ReviewForm(FlaskForm):
    review_notes = TextAreaField('审核意见 (如果拒绝，请说明理由)', validators=[Optional(), Length(max=500)])
    submit_approve = SubmitField('批准发布')
    submit_reject = SubmitField('拒绝发布')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 用于管理员权限验证的装饰器
from functools import wraps
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('您没有权限访问此页面。', 'danger')
            return redirect(url_for('main.index')) # 或者你的主页/首页
        return f(*args, **kwargs)
    return decorated_function

@food_bp.route('/recipes')
@login_required
def index():
    recipes = Post.query.order_by(Post.created_at.desc()).all()
    return render_template('food/published.html', title='我的收藏', recipes=recipes)

@food_bp.route('/add_recipe', methods=['GET', 'POST'])
@login_required
def add_recipe():
    form = RecipeForm()
    categories = Category.query.all()
    form.category.choices = [(str(c.id), c.name) for c in categories]

    if request.method == 'POST':  # 简化：检查请求方法
        try:
            title = request.form.get('title')
            category_id = request.form.get('category')
            content = request.form.get('content')

            # 基本验证
            if not title or not category_id or not content:
                flash('标题、分类和内容不能为空。', 'danger')  # 使用 flash 消息
                # 对于 AJAX 请求，返回 JSON 错误更合适
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': False, 'message': '标题、分类和内容不能为空。'}), 400
                # 对于普通表单提交，可以重新渲染表单并显示错误
                return render_template('food/add_recipe.html', title='发布新食谱', form=form, categories=categories)

            uploaded_recipe_images = request.files.getlist('recipe_images')
            saved_image_paths = []  # 存储相对于 static 文件夹的路径

            upload_path_full_abs = os.path.join(current_app.root_path, UPLOAD_FOLDER)  # 上传的绝对路径
            os.makedirs(upload_path_full_abs, exist_ok=True)

            for file in uploaded_recipe_images:
                if file and file.filename and allowed_file(file.filename):
                    original_filename = secure_filename(file.filename)
                    extension = original_filename.rsplit('.', 1)[1].lower()
                    unique_filename = f"{uuid.uuid4().hex}.{extension}"
                    file_path_full_abs = os.path.join(upload_path_full_abs, unique_filename)
                    file.save(file_path_full_abs)
                    # 存储相对于 static 文件夹的路径，例如 'uploads/recipes/image.jpg'
                    saved_image_paths.append(os.path.join(UPLOAD_FOLDER.replace('static/', '', 1), unique_filename))

            if not saved_image_paths:  # 如果没有有效图片上传
                # 如果你有一个默认占位图，可以使用它，或者强制要求上传图片
                saved_image_paths = [os.path.join(UPLOAD_FOLDER.replace('static/', '', 1), 'default_recipe.jpg')]

            category_object = Category.query.get(int(category_id))
            if not category_object:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': False, 'message': '选择的分类不存在'}), 400
                flash('选择的分类不存在。', 'danger')
                return render_template('food/add_recipe.html', title='发布新食谱', form=form, categories=categories)

            new_recipe = Post(
                title=title,
                category=category_object,
                content_body=content,
                author=current_user,
                author_id=current_user.id,
                image_paths=json.dumps(saved_image_paths)if saved_image_paths else None, # 以 JSON 字符串形式存储
                status='pending_review',  # 默认状态为待审核
                is_published=False  # 批准前不发布
            )
            db.session.add(new_recipe)
            db.session.commit()

            # flash('食谱已提交，正在等待管理员审核。', 'info') # flash 消息
            # 对于 AJAX，返回 JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': True, 'message': '食谱已成功提交，等待管理员审核！',
                                'redirect_url': url_for('food.browsePage')})

            flash('食谱已成功提交，等待管理员审核！', 'success')
            return redirect(url_for('food.browsePage'))  # 重定向到浏览页面或用户食谱页面

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"添加食谱时出错: {e}", exc_info=True)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': f'发布食谱时出错: {str(e)}'}), 500
            flash(f'发布食谱时出错: {str(e)}', 'danger')
            return render_template('food/add_recipe.html', title='发布新食谱', form=form, categories=categories)
    # GET 请求
    return render_template('food/add_recipe.html', title='发布新食谱', form=form, categories=categories)

def get_first_image_filename(image_paths_str):
    default_image_rel_path = os.path.join(UPLOAD_FOLDER.replace('static/', '', 1), 'default_recipe.jpg')
    if not image_paths_str:
        return default_image_rel_path  # 返回默认图片
    try:
        paths = image_paths_str
        if paths:
            # 确保路径是相对于 'static/' 的，以便 url_for 使用
            img_path = paths[0].replace('\\', '/')  # 统一斜杠
            # 路径已经是 'uploads/recipes/...' 格式，这是正确的
            if img_path.startswith(UPLOAD_FOLDER.replace('static/', '', 1)):
                return img_path
            # 如果路径以 'static/' 开头，则移除它
            elif img_path.startswith('static/'):
                return img_path[len('static/'):]
            else:  # 假设它只是 UPLOAD_FOLDER 下的文件名
                return os.path.join(UPLOAD_FOLDER.replace('static/', '', 1), os.path.basename(img_path))
    except (json.JSONDecodeError, TypeError, IndexError) as e:
        current_app.logger.error(f"解析图片路径错误: {e}",)
    return default_image_rel_path  # 确保总是返回一个默认值

@food_bp.route('/browsePage', endpoint='browsePage')
@login_required
def browse():
    category_keyword = request.args.get('category', '').strip()
    query = Post.query.filter(Post.status == 'approved', Post.is_published == True)

    if category_keyword:
        query = query.join(Category).filter(Category.name.ilike(f"%{category_keyword}%"))

    recipes = query.order_by(Post.created_at.desc()).all()

    for r in recipes:
        print(f"DEBUG BROWSE: Processing recipe ID {r.id}, r.image_paths = {r.image_paths}")
        r.first_image_display_path = get_first_image_filename(r.image_paths)
        print(f"DEBUG BROWSE: Recipe ID {r.id}, first_image_display_path = {r.first_image_display_path}")

    return render_template('food/browsePage.html',
                           title='浏览美食',
                           recipes=recipes,
                           category_keyword=category_keyword)

@food_bp.route('/recipe/<int:recipe_id>')
def recipe_detail(recipe_id):
    recipe = Post.query.get_or_404(recipe_id)

    # 访问控制
    can_view = False
    if recipe.status == 'approved' and recipe.is_published:
        can_view = True
    elif current_user.is_authenticated:
        if current_user.id == recipe.author_id or current_user.role == 'admin':
            can_view = True  # 作者或管理员可以查看未批准的

    if not can_view:
        flash('该食谱正在审核中或未发布，您暂时无法查看。', 'warning')
        return redirect(url_for('food.browsePage'))

    # 处理 image_paths
    recipe.processed_image_paths = []  # 初始化为空列表
    default_image_rel_path = os.path.join(UPLOAD_FOLDER.replace('static/', '', 1), 'default_recipe.jpg')
    print(f"DEBUG: Default image relative path: {default_image_rel_path}")

    print(f"DEBUG: recipe.image_paths_json (from DB): {recipe.image_paths_json}")  # 原始JSON字符串
    original_paths = recipe.image_paths  # 这是通过 @property 解析后的列表
    print(f"DEBUG: recipe.image_paths (parsed list from @property): {original_paths}")

    if original_paths:  # 使用解析后的列表
        try:
            for i, single_path_string in enumerate(original_paths):  # path_from_db 现在是完整的路径字符串
                print(
                    f"DEBUG: Processing original path [{i}]: '{single_path_string}' (type: {type(single_path_string)})")

            for i, path_from_db in enumerate(original_paths):
                print(f"DEBUG: Processing original path [{i}]: '{path_from_db}' (type: {type(path_from_db)})")
                clean_path = str(path_from_db).replace('\\', '/')  # 确保是字符串


                processed_this_path = None
                if clean_path.startswith('static/'):
                    processed_this_path = clean_path[len('static/'):]

                elif clean_path.startswith(UPLOAD_FOLDER.replace('static/', '', 1)):
                    processed_this_path = clean_path

                else:
                    processed_this_path = os.path.join(UPLOAD_FOLDER.replace('static/', '', 1),
                                                       os.path.basename(clean_path))


                if processed_this_path:
                    if processed_this_path not in recipe.processed_image_paths:  # <--- 添加这个检查
                        recipe.processed_image_paths.append(processed_this_path)
                    else:
                        print(f"DEBUG: Path '{processed_this_path}' already in processed_image_paths, skipping.")

        except Exception as e:
            current_app.logger.error(f"处理食谱 {recipe.id} 的图片路径时出错: {e}", exc_info=True)
            recipe.processed_image_paths = [default_image_rel_path]  # Fallback

    if not recipe.processed_image_paths and original_paths:  # 如果原始有路径但处理后为空（不太可能，除非异常）
        recipe.processed_image_paths = [default_image_rel_path]
    elif not recipe.processed_image_paths:  # 如果原始路径就为空，或者处理后为空（正常情况）
        recipe.processed_image_paths = [default_image_rel_path]


    return render_template(
        'food/recipeDetail.html',
        title=recipe.title,
        recipe=recipe,
        comments=Comment.query.filter_by(post_id=recipe_id).order_by(Comment.created_at).all()
    )

# --- 管理员审核路由 ---
@food_bp.route('/admin/review_dashboard')
@login_required
@admin_required
def admin_review_dashboard():
    pending_recipes = Post.query.filter_by(status='pending_review').order_by(Post.created_at.asc()).all()
    for r in pending_recipes:  # 为列表页添加首图显示
        r.first_image_display_path = get_first_image_filename(r.image_paths)
    return render_template('admin/review_dashboard.html', title='食谱审核', recipes=pending_recipes)

@food_bp.route('/admin/review_recipe/<int:recipe_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_review_recipe_page(recipe_id):
    recipe = Post.query.get_or_404(recipe_id)
    form = ReviewForm()  # 实例化审核表单

    if recipe.status != 'pending_review':
        flash('该食谱已被处理或状态不符合审核要求。', 'warning')
        return redirect(url_for('food.admin_review_dashboard'))

    if form.validate_on_submit():
        if form.submit_approve.data:  # "批准发布" 按钮被点击
            recipe.status = 'approved'
            recipe.is_published = True
            recipe.review_notes = None  # 清除之前的审核意见
            db.session.commit()
            # 通知用户
            notification = Notification(
                recipient_id=recipe.author_id,
                actor_id=current_user.id,  # 管理员是操作者
                related_post_id=recipe.id,
                notification_type='recipe_approved',  # 新的通知类型
                message=f"恭喜！您的食谱 '{recipe.title[:30]}...' 已通过审核并成功发布。"
            )
            db.session.add(notification)
            db.session.commit()
            flash(f"食谱 '{recipe.title}' 已批准并发布。", 'success')
            return redirect(url_for('food.admin_review_dashboard'))

        elif form.submit_reject.data:  # "拒绝发布" 按钮被点击
            recipe.status = 'rejected'
            recipe.is_published = False  # 确保不发布
            recipe.review_notes = form.review_notes.data or "管理员未提供具体拒绝原因。"
            db.session.commit()
            # 通知用户
            notification = Notification(
                recipient_id=recipe.author_id,
                actor_id=current_user.id,
                related_post_id=recipe.id,
                notification_type='recipe_rejected',  # 新的通知类型
                message=f"抱歉，您的食谱 '{recipe.title[:30]}...' 未能通过审核。原因: {recipe.review_notes}"
            )
            db.session.add(notification)
            db.session.commit()
            flash(f"食谱 '{recipe.title}' 已被拒绝。", 'info')
            return redirect(url_for('food.admin_review_dashboard'))

    # GET 请求时，为审核详情页处理图片路径
    recipe.processed_image_paths = []
    default_image_rel_path = os.path.join(UPLOAD_FOLDER.replace('static/', '', 1), 'default_recipe.jpg')
    if recipe.image_paths:
        try:
            paths = json.loads(recipe.image_paths) if isinstance(recipe.image_paths, str) else recipe.image_paths
            for path in paths:
                clean_path = path.replace('\\', '/')
                if clean_path.startswith('static/'):
                    recipe.processed_image_paths.append(clean_path[len('static/'):])
                elif clean_path.startswith(UPLOAD_FOLDER.replace('static/', '', 1)):
                    recipe.processed_image_paths.append(clean_path)
                else:
                    recipe.processed_image_paths.append(
                        os.path.join(UPLOAD_FOLDER.replace('static/', '', 1), os.path.basename(clean_path)))
        except (json.JSONDecodeError, TypeError) as e:
            current_app.logger.error(f"处理食谱审核页 {recipe.id} 的图片路径时出错: {e}")
            recipe.processed_image_paths = [default_image_rel_path]

    if not recipe.processed_image_paths:
        recipe.processed_image_paths = [default_image_rel_path]

    return render_template('admin/admin_review_recipe_detail.html', title=f"审核食谱: {recipe.title}", recipe=recipe,
                           form=form)

@food_bp.route('/recipe/<int:recipe_id>/like', methods=['POST'])
@login_required
def like_recipe(recipe_id):
    recipe = Post.query.filter_by(id=recipe_id, status='approved', is_published=True).first()
    if not recipe:
        return jsonify({'success': False, 'message': '该食谱当前不可点赞或未发布。'}), 404

    if current_user in recipe.liked_by_users:
        recipe.liked_by_users.remove(current_user)
        action = 'unliked'
    else:
        recipe.liked_by_users.append(current_user)
        action = 'liked'
        # 可选: 通知作者有人点赞
        if recipe.author_id != current_user.id:
            notif = Notification(recipient_id=recipe.author_id, actor_id=current_user.id, related_post_id=recipe.id,
                                 notification_type='like',
                                 message=f"{current_user.username} 点赞了你的食谱 '{recipe.title[:20]}...'")
            db.session.add(notif)

    db.session.commit()
    return jsonify({
        'success': True,
        'action': action,
        'likes_count': len(recipe.liked_by_users)
    })

@food_bp.route('/recipe/<int:recipe_id>/comment', methods=['POST'])
@login_required
def add_comment(recipe_id):
    recipe = Post.query.filter_by(id=recipe_id, status='approved', is_published=True).first()
    if not recipe:
        return jsonify({'success': False, 'message': '该食谱当前不可评论或未发布。'}), 404

    comment_content = request.form.get('comment', '').strip()
    if not comment_content:
        return jsonify({'success': False, 'message': '评论内容不能为空。'}), 400

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
        db.session.commit()  # 尽早提交以获取 new_comment.id

        # 为食谱作者创建通知 (如果不是自己评论自己的食谱)
        if recipe.author_id != current_user.id:
            notif_author = Notification(
                recipient_id=recipe.author_id,
                actor_id=current_user.id,
                related_post_id=recipe.id,
                related_comment_id=new_comment.id,
                notification_type='comment',  # 评论通知
                message=f"{current_user.username} 评论了你的食谱 '{recipe.title[:20]}...'"
            )
            db.session.add(notif_author)

        # 如果是回复，为被回复的评论作者创建通知 (如果不是自己回复自己)
        if parent_comment and parent_comment.author_id != current_user.id:
            notif_reply = Notification(
                recipient_id=parent_comment.author_id,
                actor_id=current_user.id,
                related_post_id=recipe.id,
                related_comment_id=new_comment.id,  # 新的回复ID
                notification_type='reply',  # 回复通知
                message=f"{current_user.username} 回复了你的评论"
            )
            db.session.add(notif_reply)

        db.session.commit()  # 提交通知

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
        current_app.logger.error(f"添加评论时出错: {e}", exc_info=True)
        return jsonify({'success': False, 'message': '添加评论失败。'}), 500

from flask import render_template, request
from flask_login import current_user, login_required


@food_bp.route('/favorites')
@login_required
def favorites():
    """显示用户收藏的食谱（带分页）"""
    page = request.args.get('page', 1, type=int)

    # 使用正确的 join 查询
    pagination = Post.query.join(
        post_favorites,  # 确保这是你的关联表对象
        post_favorites.c.post_id == Post.id
    ).filter(
        post_favorites.c.user_id == current_user.id
    ).order_by(
        Post.created_at.desc()
    ).paginate(page=page, per_page=9)

    posts = pagination.items

    # 处理首图路径
    for post in posts:
        post.first_image_display_path = get_first_image_filename(post.image_paths)

    return render_template('food/favorites.html', posts=posts, pagination=pagination)

# @food_bp.route('/favorites')
# @login_required
# def show_favorites():
#     """显示用户收藏的食谱"""
#     # 获取用户收藏的食谱
#     favorites = current_user.favorited_posts
#     # 为每个食谱处理首图路径
#     for recipe in favorites:
#         recipe.first_image_display_path = get_first_image_filename(recipe.image_paths)
#     return render_template('food/favorites.html', favorites=favorites)

@food_bp.route('/favorite/<int:post_id>', methods=['POST'])
@login_required
def toggle_favorite(post_id):
    post = Post.query.get_or_404(post_id)
    if post in current_user.favorited_posts:
        current_user.favorited_posts.remove(post)
        action = 'removed'
    else:
        current_user.favorited_posts.append(post)
        action = 'added'
        # 添加收藏通知
        if post.author_id != current_user.id:
            notif = Notification(
                recipient_id=post.author_id,
                actor_id=current_user.id,
                related_post_id=post.id,
                notification_type='favorite',
                message=f"{current_user.username} 收藏了你的食谱 '{post.title[:20]}...'"
            )
            db.session.add(notif)

    db.session.commit()
    return jsonify({
        'success': True,
        'action': action,
        'favorites_count': len(post.favorited_by_users)
    })

@food_bp.route('/delete_recipe/<int:recipe_id>', methods=['POST'])
@login_required
def delete_recipe(recipe_id):
    recipe = Post.query.get_or_404(recipe_id)
    if recipe.author_id != current_user.id:
        return jsonify({'success': False, 'message': '无权删除他人食谱'}), 403
    db.session.delete(recipe)
    db.session.commit()
    return jsonify({'success': True, 'message': '删除成功'})