# app/food/food_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from .food_forms import RecipeForm # 从同级目录的 food_forms.py 导入
from flask_food.models import Post, Category # 从 app.models 导入
from flask_food import db # 从 app/__init__.py 导入 db 实例
import os
from werkzeug.utils import secure_filename
import uuid

food_bp = Blueprint('food', __name__,
                    template_folder='templates', # 告诉蓝图模板在 'app/food/templates/'
                    static_folder='static',      # 蓝图特定的静态文件 (如果需要)
                    static_url_path='/food/static') # 访问蓝图静态文件的URL路径

@food_bp.route('/recipes')
def index():
    # posts = Post.query.order_by(Post.created_at.desc()).all()
    # return render_template('food/index.html', title='所有食谱', posts=posts)
    return "食谱列表页面 (food.index)"

@food_bp.route('/add_recipe', methods=['GET', 'POST']) # 更改路由以匹配模板中的 url_for
@login_required
def add_recipe():
    form = RecipeForm()
    if form.validate_on_submit():
        title = form.title.data
        content_body = form.content_body.data
        category_name_selected = form.category_name.data
        image_file_data = form.image_file.data

        category_instance = None
        if category_name_selected:
            category_instance = Category.query.filter_by(name=category_name_selected).first()
            if not category_instance: # 如果希望自动创建不存在的分类
                category_instance = Category(name=category_name_selected)
                db.session.add(category_instance)
                # db.session.flush() # 如果需要立即获得ID

        saved_image_path = None
        if image_file_data:
            try:
                filename = secure_filename(image_file_data.filename)
                unique_id = str(uuid.uuid4().hex)[:8]
                file_ext = os.path.splitext(filename)[1].lower() # 确保扩展名是小写
                unique_filename = f"{os.path.splitext(filename)[0]}_{unique_id}{file_ext}"

                upload_folder_abs_path = current_app.config.get('UPLOAD_FOLDER_RECIPES_ABS')
                upload_folder_rel_path = current_app.config.get('UPLOAD_FOLDER_RECIPES_REL')

                if not upload_folder_abs_path or not upload_folder_rel_path:
                    flash('服务器上传配置错误。', 'danger')
                    current_app.logger.error("UPLOAD_FOLDER_RECIPES_ABS or UPLOAD_FOLDER_RECIPES_REL not configured.")
                    return render_template('food/add_recipe.html', title='发布新食谱', form=form)

                if not os.path.exists(upload_folder_abs_path):
                    os.makedirs(upload_folder_abs_path)

                filepath_abs = os.path.join(upload_folder_abs_path, unique_filename)
                image_file_data.save(filepath_abs)
                saved_image_path = os.path.join(upload_folder_rel_path, unique_filename).replace("\\", "/")
            except Exception as e:
                db.session.rollback()
                flash(f'图片上传失败: {str(e)}', 'danger')
                current_app.logger.error(f"Error uploading image: {e}", exc_info=True)
                return render_template('food/add_recipe.html', title='发布新食谱', form=form)
        else: # FileRequired 应该已经处理了，但再次检查
            flash('请上传封面图片。', 'warning')
            return render_template('food/add_recipe.html', title='发布新食谱', form=form)

        new_post = Post(
            title=title,
            content_body=content_body,
            image_url=saved_image_path,
            author_id=current_user.id, # 确保 current_user 有 id 属性
            category=category_instance # 直接关联 Category 对象
        )
        try:
            db.session.add(new_post)
            db.session.commit()
            flash('新食谱已成功发布！', 'success')
            return redirect(url_for('food.index')) # 或者详情页
        except Exception as e:
            db.session.rollback()
            flash(f'发布食谱时出错: {str(e)}', 'danger')
            current_app.logger.error(f"Error adding recipe to DB: {e}", exc_info=True)

    return render_template('food/add_recipe.html', title='发布新食谱', form=form)