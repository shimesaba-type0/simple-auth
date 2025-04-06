"""
アプリケーション設定モジュール

環境変数から設定を読み込み、アプリケーション全体で使用する設定値を提供します。
"""

import os
import secrets
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from dotenv import load_dotenv
from pydantic import (
    AnyHttpUrl,
    Field,
    PostgresDsn,
    field_validator,
)
from pydantic_settings import BaseSettings

# プロジェクトのルートディレクトリを取得
ROOT_DIR = Path(__file__).resolve().parent.parent.parent

# .envファイルを読み込む
load_dotenv(ROOT_DIR / ".env")


class Settings(BaseSettings):
    """アプリケーション設定クラス"""

    # アプリケーション設定
    APP_NAME: str = "SimpleAuth"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"

    # データベース設定
    DATABASE_URL: str = "sqlite:///instance/simple_auth.db"

    @field_validator("DATABASE_URL")
    def validate_database_url(cls, v: str) -> str:
        """
        SQLiteのURLを検証し、必要に応じてパスを絶対パスに変換します。
        """
        if v.startswith("sqlite:///"):
            # 相対パスの場合は絶対パスに変換
            if not v.startswith("sqlite:////"):
                db_path = v.replace("sqlite:///", "")
                if not os.path.isabs(db_path):
                    # instance ディレクトリを作成
                    instance_dir = ROOT_DIR / "instance"
                    instance_dir.mkdir(exist_ok=True)
                    return f"sqlite:///{ROOT_DIR / db_path}"
        return v

    # セキュリティ設定
    SECRET_KEY: str = Field(
        default_factory=lambda: secrets.token_hex(32)
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24時間

    # Argon2idハッシュ設定
    ARGON2_TIME_COST: int = 2
    ARGON2_MEMORY_COST: int = 102400  # 100 MB
    ARGON2_PARALLELISM: int = 8
    ARGON2_HASH_LENGTH: int = 32
    ARGON2_SALT_LENGTH: int = 16

    # Fail Lock設定
    FAIL_LOCK_ATTEMPTS: int = 5
    FAIL_LOCK_WINDOW: int = 30  # 分
    FAIL_LOCK_DURATION: int = 120  # 分

    # パスフレーズ設定
    MIN_PASSPHRASE_LENGTH: int = 32
    DEFAULT_PASSPHRASE_LENGTH: int = 64
    MAX_PASSPHRASE_LENGTH: int = 128

    # セッション設定
    SESSION_TIMEOUT: int = 24  # 時間

    model_config = {
        "env_file": ".env",
        "case_sensitive": True
    }


# 設定インスタンスを作成
settings = Settings()


def get_settings() -> Settings:
    """
    設定インスタンスを取得する関数

    依存性注入で使用するための関数です。
    """
    return settings

