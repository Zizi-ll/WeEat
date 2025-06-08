#数据库模型，表->类
#为所有的表创建模型，并且定义好表之间的关系！完成数据库设计之后才可以写这个文件
import json

#当你更改了 models.py 中的模型 (例如，添加了一个新表、给表添加了新列、修改了列类型等) 之后，你需要运行此命令。它会检测模型的更改，并生成一个迁移脚本。
#flask db migrate -m "一个描述性的消息，比如 'add user table' 或 'add email to user'"
#在你运行了 flask db migrate 并生成了迁移脚本后，运行此命令会将这些更改应用到你的实际数据库中。
#flask db upgrade

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from . import db
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship, sessionmaker, declarative_base
from sqlalchemy.sql import func  # for func.now()
from werkzeug.security import generate_password_hash, check_password_hash  # for password hashing
import datetime

#UserMixin 提供 Flask-Login 所需的用户接口 class User(db.Model, UserMixin)
#db.Model ——SQLAlchemy 提供的 ORM（对象关系映射）模型的基类，代表数据库中的“表”

# --- 关联表 (用于多对多关系) ---

# 用户点赞帖子关联表
post_likes = db.Table('post_likes', #db.Model.metadata, # 使用 db.Model.metadata
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('post_id', db.Integer, db.ForeignKey('posts.id'), primary_key=True),
    db.Column('timestamp', db.DateTime, default=datetime.datetime.utcnow)
)

post_favorites = db.Table('post_favorites', #db.Model.metadata,
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('post_id', db.Integer, db.ForeignKey('posts.id'), primary_key=True),
    db.Column('timestamp', db.DateTime, default=datetime.datetime.utcnow)
)

# 帖子与标签的关联表 (如果一个帖子可以有多个标签)
# post_tags = Table('post_tags', Base.metadata,
#     Column('post_id', Integer, ForeignKey('posts.id'), primary_key=True),
#     Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True)
# )

def __repr__(self):
    return f'<Notification for {self.recipient.username} type {self.notification_type}>'

# --- 实体表 ---
class User(db.Model, UserMixin): # 添加 UserMixin
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True, nullable=False)
    email = db.Column(db.String(120), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    profile_picture_url = db.Column(db.String(255), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    role = db.Column(db.String(20), default='user', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    posts = db.relationship("Post", back_populates="author", cascade="all, delete-orphan")
    comments = db.relationship("Comment", back_populates="author", cascade="all, delete-orphan")
    notifications_received = db.relationship("Notification",
                                          foreign_keys="[Notification.recipient_id]",
                                          back_populates="recipient",
                                          cascade="all, delete-orphan")
    notifications_sent = db.relationship("Notification",
                                      foreign_keys="[Notification.actor_id]",
                                      back_populates="actor",
                                      cascade="all, delete-orphan")

    liked_posts = db.relationship("Post", secondary=post_likes, back_populates="liked_by_users")
    favorited_posts = db.relationship("Post", secondary=post_favorites, back_populates="favorited_by_users")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True, index=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    posts = db.relationship("Post", back_populates="category")
    def __repr__(self):
        return f'<Category {self.name}>'

class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True, index=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    content_body = db.Column(db.Text, nullable=False)
    image_paths_json = db.Column(db.Text, nullable=True) # 将存储图片的相对路径
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    is_published = db.Column(db.Boolean, default=False)
    view_count = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='pending_review', nullable=False,
                       index=True)  # 可选值: 'pending_review' (待审核), 'approved' (已批准), 'rejected' (已拒绝), 'draft' (草稿)
    review_notes = db.Column(db.Text, nullable=True)  # 管理员拒绝时的审核意见
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)

    author = db.relationship("User", back_populates="posts")
    category = db.relationship("Category", back_populates="posts")
    comments = db.relationship("Comment", back_populates="post", cascade="all, delete-orphan")
    liked_by_users = db.relationship("User", secondary=post_likes, back_populates="liked_posts")
    favorited_by_users = db.relationship("User", secondary=post_favorites, back_populates="favorited_posts")

    @property
    def image_paths(self):
        if self.image_paths_json:
            print(f"DEBUG MODELS: Raw image_paths_json from DB: '{self.image_paths_json}'")
            try:
                loaded_data = json.loads(self.image_paths_json)
                print(f"DEBUG MODELS: json.loads result: {loaded_data}, type: {type(loaded_data)}")
                # 如果 loaded_data 仍然是字符串，并且看起来像一个列表的字符串表示，尝试再次解析
                if isinstance(loaded_data, str) and loaded_data.startswith('[') and loaded_data.endswith(']'):
                    print(f"DEBUG MODELS: Attempting secondary parse on string: '{loaded_data}'")
                    try:
                        loaded_data = json.loads(loaded_data)
                        print(f"DEBUG MODELS: Secondary parse result: {loaded_data}, type: {type(loaded_data)}")
                    except json.JSONDecodeError as e2:
                        print(f"DEBUG MODELS: Secondary JSONDecodeError: {e2}")
                        return []  # 或者其他错误处理
                return loaded_data
            except json.JSONDecodeError as e:
                print(f"DEBUG MODELS: Primary JSONDecodeError: {e}")
                return []  # 解析失败返回空列表
        return []

    @image_paths.setter
    def image_paths(self, paths_list):
        self.image_paths_json = json.dumps(paths_list)

    def __repr__(self):
        return f'<Post "{self.title[:30]}..."> ({self.author.username})>'

class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True, index=True)
    text_content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    parent_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=True)

    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)

    author = db.relationship("User", back_populates="comments")
    post = db.relationship("Post", back_populates="comments")
    # 对于 replies，确保 backref 正确，或者使用 back_populates
    # replies = db.relationship("Comment", backref=db.backref("parent", remote_side=[id]), cascade="all, delete-orphan")
    parent = db.relationship("Comment", remote_side=[id], backref="replies")


    def __repr__(self):
        return f'<Comment by {self.author.username} on Post {self.post_id}>'

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True, index=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    actor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    related_post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=True)
    related_comment_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=True)
    notification_type = db.Column(db.String(50), nullable=False, index=True)
    message = db.Column(db.Text, nullable=True)
    is_read = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, index=True)

    recipient = db.relationship("User", foreign_keys=[recipient_id], back_populates="notifications_received")
    actor = db.relationship("User", foreign_keys=[actor_id], back_populates="notifications_sent")
    related_post = db.relationship("Post")
    related_comment = db.relationship("Comment")

