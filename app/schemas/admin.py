"""
管理者用スキーマ定義

ユーザー一覧、システム設定などの管理者向けスキーマを定義します。
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.core.config import settings


class UserListItem(BaseModel):
    """
    ユーザー一覧項目スキーマ
    """
    id: int = Field(..., description="ユーザーID")
    username: str = Field(..., description="ユーザー名")
    email: str = Field(..., description="メールアドレス")
    is_active: bool = Field(..., description="アクティブ状態")
    is_admin: bool = Field(..., description="管理者権限")
    is_locked: bool = Field(..., description="ロック状態")
    created_at: str = Field(..., description="作成日時")
    last_login: Optional[str] = Field(None, description="最終ログイン日時")
    login_attempts: int = Field(0, description="ログイン試行回数")

    class Config:
        from_attributes = True


class SystemSettings(BaseModel):
    """
    システム設定スキーマ
    """
    fail_lock_attempts: int = Field(
        settings.FAIL_LOCK_ATTEMPTS, 
        description="ログイン失敗によるロックまでの試行回数"
    )
    fail_lock_window: int = Field(
        settings.FAIL_LOCK_WINDOW, 
        description="ログイン失敗カウントのリセット時間（分）"
    )
    fail_lock_duration: int = Field(
        settings.FAIL_LOCK_DURATION, 
        description="アカウントロックの持続時間（分）"
    )
    session_timeout: int = Field(
        settings.SESSION_TIMEOUT, 
        description="セッションタイムアウト（時間）"
    )
    min_passphrase_length: int = Field(
        settings.MIN_PASSPHRASE_LENGTH, 
        description="最小パスフレーズ長"
    )
    default_passphrase_length: int = Field(
        settings.DEFAULT_PASSPHRASE_LENGTH, 
        description="デフォルトパスフレーズ長（自動生成時）"
    )
    max_passphrase_length: int = Field(
        settings.MAX_PASSPHRASE_LENGTH, 
        description="最大パスフレーズ長"
    )

    @validator("fail_lock_attempts")
    def validate_fail_lock_attempts(cls, v):
        if v < 1:
            raise ValueError("ログイン失敗によるロックまでの試行回数は1以上である必要があります")
        return v

    @validator("fail_lock_window", "fail_lock_duration")
    def validate_time_minutes(cls, v):
        if v < 1:
            raise ValueError("時間（分）は1以上である必要があります")
        return v

    @validator("session_timeout")
    def validate_session_timeout(cls, v):
        if v < 1:
            raise ValueError("セッションタイムアウト（時間）は1以上である必要があります")
        return v

    @validator("min_passphrase_length", "default_passphrase_length", "max_passphrase_length")
    def validate_passphrase_length(cls, v, values):
        if v < 8:
            raise ValueError("パスフレーズ長は8文字以上である必要があります")
        
        # 最小長、デフォルト長、最大長の関係をチェック
        if "min_passphrase_length" in values and v == "default_passphrase_length":
            if v < values["min_passphrase_length"]:
                raise ValueError("デフォルトパスフレーズ長は最小パスフレーズ長以上である必要があります")
        
        if "min_passphrase_length" in values and v == "max_passphrase_length":
            if v < values["min_passphrase_length"]:
                raise ValueError("最大パスフレーズ長は最小パスフレーズ長以上である必要があります")
        
        if "default_passphrase_length" in values and v == "max_passphrase_length":
            if v < values["default_passphrase_length"]:
                raise ValueError("最大パスフレーズ長はデフォルトパスフレーズ長以上である必要があります")
        
        return v


class LoginAttemptLog(BaseModel):
    """
    ログイン試行ログスキーマ
    """
    id: int = Field(..., description="ログID")
    username: str = Field(..., description="ユーザー名")
    ip_address: Optional[str] = Field(None, description="IPアドレス")
    user_agent: Optional[str] = Field(None, description="ユーザーエージェント")
    success: bool = Field(..., description="成功/失敗")
    timestamp: str = Field(..., description="タイムスタンプ")

    class Config:
        from_attributes = True

