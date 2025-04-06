"""
データベース接続モジュール

SQLAlchemyを使用してデータベース接続を管理します。
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# SQLAlchemyエンジンを作成
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {},
)

# セッションファクトリを作成
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# モデルのベースクラスを作成
Base = declarative_base()


def get_db():
    """
    データベースセッションの依存関係

    FastAPIのDependencyとして使用するためのジェネレータ関数です。
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

