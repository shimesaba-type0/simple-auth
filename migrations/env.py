"""
Alembic環境設定モジュール

マイグレーションの実行環境を設定します。
"""

import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# このスクリプトの親ディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# モデルのメタデータをインポート
from app.core.config import settings
from app.core.database import Base
from app.models import user, session, login_attempt, system_setting

# alembic.iniからの設定を読み込む
config = context.config

# セクションが存在する場合のみfileConfigを呼び出す
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# メタデータのターゲットを設定
target_metadata = Base.metadata

# 他の値は、必要に応じてalembic.iniから取得


def run_migrations_offline():
    """
    SQLを直接実行せずにマイグレーションを実行します。

    これは、データベースへの直接アクセスなしでマイグレーションを生成する
    'オフライン'モードで使用されます。
    """
    url = settings.DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """
    エンジンに接続した状態でマイグレーションを実行します。
    """
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = settings.DATABASE_URL
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

