#forms——表单 网页上让用户输入数据的一种结构，用来提交内容到服务器

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField
from wtforms.validators import InputRequired, Length

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=150)])
    password = PasswordField('Password', validators=[InputRequired()])

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=150)])
    password = PasswordField('Password', validators=[InputRequired()])

class RecipeForm(FlaskForm):
    title = StringField('Title', validators=[InputRequired()])
    category = StringField('Category')
    content = TextAreaField('Content', validators=[InputRequired()])
