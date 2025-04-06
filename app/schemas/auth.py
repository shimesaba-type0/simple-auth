"""
認証関連のスキーマ定義

認証リクエスト、レスポンス、トークンなどのスキーマを定義します。
"""

from pydantic import BaseModel, Field
from typing import Optional


class LoginRequest(BaseModel):
    """
    ログインリクエストスキーマ
    """
    username: str = Field(..., description="ユーザー名")
    password: str = Field(..., description="パスワード")


class TokenResponse(BaseModel):
    """
    トークンレスポンススキーマ
    """
    access_token: str = Field(..., description="アクセストークン")
    token_type: str = Field(..., description="トークンタイプ")


class SessionInfo(BaseModel):
    """
    セッション情報スキーマ
    """
    id: str = Field(..., description="セッションID")
    created_at: str = Field(..., description="作成日時")
    expires_at: str = Field(..., description="有効期限")
    ip_address: Optional[str] = Field(None, description="IPアドレス")
    user_agent: Optional[str] = Field(None, description="ユーザーエージェント")
    is_current: bool = Field(False, description="現在のセッションかどうか")

