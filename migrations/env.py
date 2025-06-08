import os
import sys
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import logging
from multiprocessing import pool
from sqlalchemy import pool as sqlalchemy_pool
from flask import current_app
from wtforms.validators import url

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))



try:
    from flask_food import db as flask_food_db # 使用一个不同的别名以避免与可能存在的局部 db 变量冲突
    print("Successfully imported 'db' from 'flask_food' in env.py")
except ImportError as e:
    print(f"Error importing 'db' from 'flask_food' in env.py: {e}")
    # 如果这里导入失败，你需要检查你的项目结构和包名是否正确
    # 例如，如果你的主应用包名不是 flask_food，或者 db 不在 __init__.py 中
    flask_food_db = None # 或者引发一个更严重的错误，因为没有它无法进行

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

fileConfig(config.config_file_name)
logger = logging.getLogger('alembic.env')

def get_engine():
    try:
        # this works with Flask-SQLAlchemy<3 and Alchemical
        return current_app.extensions['migrate'].db.get_engine()
    except (TypeError, AttributeError):
        # this works with Flask-SQLAlchemy>=3
        return current_app.extensions['migrate'].db.engine


def get_engine_url():
    try:
        return get_engine().url.render_as_string(hide_password=False).replace(
            '%', '%%')
    except AttributeError:
        return str(get_engine().url).replace('%', '%%')

# add your model's MetaData object here
# for 'autogenerate' support
if flask_food_db: # 确保 flask_food_db 已成功导入
    target_metadata = flask_food_db.metadata
else:
    target_metadata = None
    print("CRITICAL: 'db' object not imported from 'flask_food', target_metadata is None. Migrations will likely fail.")

config.set_main_option('sqlalchemy.url', get_engine_url())
target_db = current_app.extensions['migrate'].db
target_metadata = flask_food_db.metadata

print("-" * 70)
print("DEBUGGING METADATA IN env.py FOR Alembic")
print(f"Using target_metadata object ID: {id(target_metadata)}")

if flask_food_db is not None:
    target_metadata = flask_food_db.metadata
    print(f"INFO: target_metadata IS SET using flask_food_db.metadata in env.py. Value: {target_metadata}")
    # 新增打印语句：
    print(f"INFO: Tables known to target_metadata: {list(target_metadata.tables.keys())}")
else:
    target_metadata = None
    print("ERROR: target_metadata IS None because 'flask_food_db' was not successfully imported.")

# In migrations/env.py

# 确保这里的导入是正确的，指向你应用中实际使用的 db 对象
# 例如: from flask_food import db
# 或者: from my_app.models import db (如果 db 在 models.py 定义)
# 请根据你的项目结构调整
from flask_food import db  # 假设你的 db 在 flask_food/__init__.py 或类似地方

target_metadata = db.metadata

# --- BEGIN DEBUG BLOCK ---
print("-" * 70)
print("DEBUGGING METADATA IN env.py FOR Alembic")
print(f"Using target_metadata object ID: {id(target_metadata)}")

if target_metadata is not None:
    if 'posts' in target_metadata.tables:
        posts_table_from_metadata = target_metadata.tables['posts']
        print("Columns in 'posts' table (as seen by Alembic via target_metadata):")
        for column in posts_table_from_metadata.columns:
            print(
                f"  - Name: {column.name}, Type: {column.type}, Nullable: {column.nullable}, Default: {column.default}")

        if 'status' in posts_table_from_metadata.c:  # .c is an alias for .columns
            print("  >>> VERDICT: 'status' column IS PRESENT in Alembic's view of the 'posts' model/table.")
        else:
            print("  >>> VERDICT: 'status' column IS MISSING in Alembic's view of the 'posts' model/table.")
    else:
        print("'posts' table NOT FOUND in target_metadata. This is a major issue.")

    print("All tables known to Alembic via target_metadata:", list(target_metadata.tables.keys()))
else:
    print("target_metadata is None. Alembic cannot detect model changes.")
print("-" * 70)

def get_metadata():
    if hasattr(target_db, 'metadatas'):
        return target_db.metadatas[None]
    return target_db.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.
    # ...
    """
    # ...
    context.configure(
        url=url,
        target_metadata=target_metadata,  # 确保这里使用了正确的 target_metadata
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

def run_migrations_online() -> None:
    """Run migrations in 'online' mode.
    # ...
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=sqlalchemy_pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata  # 确保这里使用了正确的 target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

