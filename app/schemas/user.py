"""
ユーザー関連のスキーマ定義

ユーザープロファイル、パスフレーズ変更リクエストなどのスキーマを定義します。
"""

from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List
from datetime import datetime

from app.core.config import settings


class UserProfile(BaseModel):
    """
    ユーザープロファイルスキーマ
    """
    id: int = Field(..., description="ユーザーID")
    username: str = Field(..., description="ユーザー名")
    email: EmailStr = Field(..., description="メールアドレス")
    is_active: bool = Field(..., description="アクティブ状態")
    is_admin: bool = Field(..., description="管理者権限")
    created_at: str = Field(..., description="作成日時")
    last_login: Optional[str] = Field(None, description="最終ログイン日時")

    class Config:
        from_attributes = True


class ChangePassphraseRequest(BaseModel):
    """
    パスフレーズ変更リクエストスキーマ
    """
    current_passphrase: str = Field(..., description="現在のパスフレーズ")
    new_passphrase: str = Field(..., description="新しいパスフレーズ")

    @validator("new_passphrase")
    def validate_passphrase_length(cls, v):
        """
        パスフレーズの長さを検証します。
        """
        if len(v) < settings.MIN_PASSPHRASE_LENGTH:
            raise ValueError(
                f"パスフレーズは{settings.MIN_PASSPHRASE_LENGTH}文字以上である必要があります"
            )
        if len(v) > settings.MAX_PASSPHRASE_LENGTH:
            raise ValueError(
                f"パスフレーズは{settings.MAX_PASSPHRASE_LENGTH}文字以下である必要があります"
            )
        return v


class CreateUserRequest(BaseModel):
    """
    ユーザー作成リクエストスキーマ
    """
    username: str = Field(..., description="ユーザー名")
    email: EmailStr = Field(..., description="メールアドレス")
    passphrase: Optional[str] = Field(None, description="パスフレーズ（指定しない場合は自動生成）")
    is_admin: bool = Field(False, description="管理者権限")

    @validator("passphrase")
    def validate_passphrase(cls, v):
        """
        パスフレーズを検証します。
        """
        if v is not None:
            if len(v) < settings.MIN_PASSPHRASE_LENGTH:
                raise ValueError(
                    f"パスフレーズは{settings.MIN_PASSPHRASE_LENGTH}文字以上である必要があります"
                )
            if len(v) > settings.MAX_PASSPHRASE_LENGTH:
                raise ValueError(
                    f"パスフレーズは{settings.MAX_PASSPHRASE_LENGTH}文字以下である必要があります"
                )
        return v


class CreateUserResponse(BaseModel):
    """
    ユーザー作成レスポンススキーマ
    """
    id: int = Field(..., description="ユーザーID")
    username: str = Field(..., description="ユーザー名")
    email: EmailStr = Field(..., description="メールアドレス")
    passphrase: Optional[str] = Field(None, description="生成されたパスフレーズ（自動生成時のみ）")

