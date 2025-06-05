# app/food/food_forms.py
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, SubmitField # SubmitField 如果你要用 {{ form.submit }}
from wtforms.validators import DataRequired, Length, Optional

class RecipeForm(FlaskForm):
    title = StringField('标题', validators=[DataRequired(), Length(min=2, max=200)])
    content_body = TextAreaField('食谱内容 (步骤、心得等)', validators=[DataRequired(), Length(min=10)])
    image_file = FileField(
        '上传封面图',
        validators=[
            FileRequired(message="请选择一张封面图片。"),
            FileAllowed(['jpg', 'png', 'jpeg', 'gif'], '仅支持图片格式 (jpg, png, jpeg, gif)!')
        ]
    )
    category_name = SelectField( # 使用 category_name 而不是 category，因为 Post 模型用的是 category_id/category关系
        '分类',
        choices=[ # 实际应用中，这些可以从数据库动态加载到 Category 表
            ('', '-- 选择分类 --'),
            ('家常菜', '家常菜'),
            ('烘焙甜点', '烘焙甜点'),
            ('快手早餐', '快手早餐'),
            ('汤羹饮品', '汤羹饮品'),
            ('宝宝辅食', '宝宝辅食'),
            ('其他', '其他'),
        ],
        validators=[Optional()] # 分类可选
    )
    # submit = SubmitField('发布食谱') # 如果你在模板中使用 <button type="submit">，这个可以不加