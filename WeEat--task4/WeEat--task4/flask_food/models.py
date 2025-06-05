#数据库模型，表->类
#为所有的表创建模型，并且定义好表之间的关系！完成数据库设计之后才可以写这个文件


#当你更改了 models.py 中的模型 (例如，添加了一个新表、给表添加了新列、修改了列类型等) 之后，你需要运行此命令。它会检测模型的更改，并生成一个迁移脚本。
#flask db migrate -m "一个描述性的消息，比如 'add user table' 或 'add email to user'"
#在你运行了 flask db migrate 并生成了迁移脚本后，运行此命令会将这些更改应用到你的实际数据库中。
#flask db upgrade

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship, sessionmaker, declarative_base
from sqlalchemy.sql import func  # for func.now()
from werkzeug.security import generate_password_hash, check_password_hash  # for password hashing
import datetime

#UserMixin 提供 Flask-Login 所需的用户接口 class User(db.Model, UserMixin)
#db.Model ——SQLAlchemy 提供的 ORM（对象关系映射）模型的基类，代表数据库中的“表”
db = SQLAlchemy()

# 定义基类
Base = declarative_base()#用于声明数据库中的表结构，让 SQLAlchemy 可以把 Python 类和数据库表自动对应起来

# --- 关联表 (用于多对多关系) ---

# 用户点赞帖子关联表
post_likes = Table('post_likes', Base.metadata,
                   Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
                   Column('post_id', Integer, ForeignKey('posts.id'), primary_key=True),
                   Column('timestamp', DateTime, default=datetime.datetime.utcnow)  # 可选，记录点赞时间
                   )

# 用户收藏帖子关联表
post_favorites = Table('post_favorites', Base.metadata,
                       Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
                       Column('post_id', Integer, ForeignKey('posts.id'), primary_key=True),
                       Column('timestamp', DateTime, default=datetime.datetime.utcnow)  # 可选，记录收藏时间
                       )


# 帖子与标签的关联表 (如果一个帖子可以有多个标签)
# post_tags = Table('post_tags', Base.metadata,
#     Column('post_id', Integer, ForeignKey('posts.id'), primary_key=True),
#     Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True)
# )

def __repr__(self):
    return f'<Notification for {self.recipient.username} type {self.notification_type}>'
# --- 实体表 ---

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    password_hash = Column(String(256), nullable=False)  # 存储哈希后的密码
    profile_picture_url = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)
    role = Column(String(20), default='user', nullable=False)  # e.g., 'user', 'moderator', 'admin' (对应权限管理)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # 关系 (对应个人中心、用户发布的帖子、评论、通知等)
    posts = relationship("Post", back_populates="author", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="author", cascade="all, delete-orphan")
    notifications_received = relationship("Notification",
                                          foreign_keys="[Notification.recipient_id]",
                                          back_populates="recipient",
                                          cascade="all, delete-orphan")
    notifications_sent = relationship("Notification",
                                      foreign_keys="[Notification.actor_id]",
                                      back_populates="actor",
                                      cascade="all, delete-orphan")  # 如果需要追踪谁触发了通知

    # 多对多关系 (点赞和收藏)
    liked_posts = relationship("Post", secondary=post_likes, back_populates="liked_by_users")
    favorited_posts = relationship("Post", secondary=post_favorites, back_populates="favorited_by_users")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class Category(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # 关系 (一个分类下有多个帖子)
    posts = relationship("Post", back_populates="category")

    def __repr__(self):
        return f'<Category {self.name}>'


class Post(Base):  # 美食内容/帖子
    __tablename__ = 'posts'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    content_body = Column(Text, nullable=False)  # 菜谱步骤、描述等
    image_url = Column(String(255), nullable=True)  # 封面图
    # tags = Column(String(255), nullable=True) # 简单的标签系统，逗号分隔，或使用下面的多对多
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    is_published = Column(Boolean, default=True)  # 是否发布，后台管理可能用到
    view_count = Column(Integer, default=0)  # 浏览量

    # 外键
    author_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=True)  # 帖子可以属于某个分类

    # 关系
    author = relationship("User", back_populates="posts")
    category = relationship("Category", back_populates="posts")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")

    # 多对多关系 (点赞和收藏)
    liked_by_users = relationship("User", secondary=post_likes, back_populates="liked_posts")
    favorited_by_users = relationship("User", secondary=post_favorites, back_populates="favorited_posts")

    # 如果使用更复杂的标签系统 (多对多)
    # post_tags_relationship = relationship("Tag", secondary=post_tags, back_populates="posts_with_tag")

    def __repr__(self):
        return f'<Post "{self.title[:30]}..."> ({self.author.username})>'

# 如果需要独立的标签实体 (用于关键词搜索、分类)
# class Tag(Base):
#     __tablename__ = 'tags'
#     id = Column(Integer, primary_key=True, index=True)
#     name = Column(String(50), unique=True, nullable=False, index=True)
#     posts_with_tag = relationship("Post", secondary=post_tags, back_populates="post_tags_relationship")
#
#     def __repr__(self):
#         return f'<Tag {self.name}>'


class Comment(Base):
    __tablename__ = 'comments'

    id = Column(Integer, primary_key=True, index=True)
    text_content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    parent_id = Column(Integer, ForeignKey('comments.id'), nullable=True)  # 用于支持评论的回复

    # 外键
    author_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    post_id = Column(Integer, ForeignKey('posts.id'), nullable=False)

    # 关系
    author = relationship("User", back_populates="comments")
    post = relationship("Post", back_populates="comments")
    replies = relationship("Comment", backref=relationship("parent", remote_side=[id]),
                           cascade="all, delete-orphan")  # 子评论

    def __repr__(self):
        return f'<Comment by {self.author.username} on Post {self.post_id}>'


class Notification(Base):
    __tablename__ = 'notifications'

    id = Column(Integer, primary_key=True, index=True)
    recipient_id = Column(Integer, ForeignKey('users.id'), nullable=False)  # 通知接收者
    actor_id = Column(Integer, ForeignKey('users.id'), nullable=True)  # 触发通知的用户 (e.g., 点赞者, 评论者)
    related_post_id = Column(Integer, ForeignKey('posts.id'), nullable=True)  # 关联的帖子
    related_comment_id = Column(Integer, ForeignKey('comments.id'), nullable=True)  # 关联的评论

    # 通知类型: 'system', 'new_comment', 'new_like', 'new_favorite', 'reply_to_comment' etc.
    # 对应"互动通知"和"系统通知"
    notification_type = Column(String(50), nullable=False, index=True)
    message = Column(Text, nullable=True)  # 系统通知可能直接有消息内容
    is_read = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    # 关系
    recipient = relationship("User", foreign_keys=[recipient_id], back_populates="notifications_received")
    actor = relationship("User", foreign_keys=[actor_id], back_populates="notifications_sent")
    related_post = relationship("Post")  # 如果需要通过通知直接访问帖子
    related_comment = relationship("Comment")  # 如果需要通过通知直接访问评论



# --- 数据库引擎和会话设置 (示例) ---
if __name__ == '__main__':
    # 使用 SQLite 进行本地测试，实际部署时替换为 PostgreSQL, MySQL 等
    engine = create_engine('sqlite:///wee_eat.db')
    Base.metadata.create_all(engine)  # 创建所有表

    # SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    # db = SessionLocal()

    # --- 简单示例操作 (可选) ---
    # # 创建用户
    # user1 = User(username='alice', email='alice@example.com')
    # user1.set_password('alicepass')
    # user2 = User(username='bob', email='bob@example.com', role='admin')
    # user2.set_password('bobpass')

    # # 创建分类
    # category1 = Category(name='家常菜', description='日常家庭烹饪')
    # category2 = Category(name='烘焙甜点', description='美味的烘焙和甜点')

    # # 添加到会话
    # db.add_all([user1, user2, category1, category2])
    # db.commit() # 提交到数据库

    # # 创建帖子
    # post1 = Post(title='红烧肉教程', content_body='第一步...', author=user1, category=category1)
    # post2 = Post(title='巧克力蛋糕', content_body='烤箱预热...', author=user2, category=category2)
    # db.add_all([post1, post2])
    # db.commit()

    # # 用户点赞
    # user1.liked_posts.append(post2)
    # db.commit()

    # # 用户收藏
    # user2.favorited_posts.append(post1)
    # db.commit()

    # # 创建评论
    # comment1 = Comment(text_content='看起来很好吃！', author=user2, post=post1)
    # db.add(comment1)
    # db.commit()

    # # 创建通知 (模拟有人评论了 user1 的 post1)
    # notif1 = Notification(recipient=user1, actor=user2, related_post=post1, related_comment=comment1, notification_type='new_comment')
    # db.add(notif1)
    # db.commit()

    # # 查询
    # print("--- Users ---")
    # for user in db.query(User).all():
    #     print(user, user.role)
    #     print("  Liked posts:", [p.title for p in user.liked_posts])
    #     print("  Favorited posts:", [p.title for p in user.favorited_posts])
    #     print("  Authored posts:", [p.title for p in user.posts])

    # print("\n--- Posts ---")
    # for post in db.query(Post).all():
    #     print(post, "Category:", post.category.name if post.category else "None")
    #     print("  Liked by:", [u.username for u in post.liked_by_users])
    #     print("  Comments:", [c.text_content[:20] for c in post.comments])

    # print("\n--- Notifications for Alice ---")
    # for notif in db.query(Notification).filter(Notification.recipient == user1).all():
    #     print(f"To: {notif.recipient.username}, From: {notif.actor.username if notif.actor else 'System'}, Type: {notif.notification_type}, Read: {notif.is_read}")

    # db.close()
    print("Database schema created and example operations (if uncommented) would run.")
