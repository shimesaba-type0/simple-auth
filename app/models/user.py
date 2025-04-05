from sqlalchemy import Boolean, Column, Integer, String, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base
from app.utils.datetime import get_current_datetime_str, get_current_timestamp

class User(Base):
    """
    ユーザー情報を管理するモデル
    
    Attributes:
        id (int): ユーザーID
        username (str): ユーザー名（一意）
        password_hash (str): Argon2idでハッシュ化されたパスフレーズ
        created_at (str): アカウント作成日時（ISO 8601形式）
        updated_at (str): アカウント情報更新日時（ISO 8601形式）
        is_admin (bool): 管理者権限フラグ（False=一般ユーザー、True=管理者）
        is_locked (bool): アカウントロックフラグ（False=アンロック、True=ロック）
        locked_until (int): ロック解除予定日時（Unixtime形式）
        failed_login_attempts (int): 連続ログイン失敗回数
        last_failed_attempt (int): 最後のログイン失敗日時（Unixtime形式）
        last_login (str): 最後のログイン成功日時（ISO 8601形式）
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(String, nullable=False, default=get_current_datetime_str)
    updated_at = Column(String, nullable=False, default=get_current_datetime_str, onupdate=get_current_datetime_str)
    is_admin = Column(Boolean, nullable=False, default=False)
    is_locked = Column(Boolean, nullable=False, default=False)
    locked_until = Column(Integer, nullable=True)
    failed_login_attempts = Column(Integer, nullable=False, default=0)
    last_failed_attempt = Column(Integer, nullable=True)
    last_login = Column(String, nullable=True)

    # リレーションシップ
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    login_attempts = relationship("LoginAttempt", back_populates="user", cascade="all, delete-orphan")

    def is_account_locked(self) -> bool:
        """
        アカウントがロックされているかどうかを確認
        
        Returns:
            bool: アカウントがロックされている場合はTrue、そうでない場合はFalse
        """
        if not self.is_locked:
            return False
        
        if self.locked_until is None:
            return True  # 無期限ロック
            
        current_time = get_current_timestamp()
        return current_time < self.locked_until
    
    def lock_account(self, duration_minutes: int = None) -> None:
        """
        アカウントをロックする
        
        Args:
            duration_minutes (int, optional): ロック期間（分）。Noneの場合は無期限ロック。
        """
        self.is_locked = True
        if duration_minutes is not None:
            self.locked_until = get_current_timestamp() + (duration_minutes * 60)
        else:
            self.locked_until = None
    
    def unlock_account(self) -> None:
        """アカウントのロックを解除する"""
        self.is_locked = False
        self.locked_until = None
        self.failed_login_attempts = 0
        self.last_failed_attempt = None
    
    def record_login_failure(self) -> None:
        """ログイン失敗を記録する"""
        self.failed_login_attempts += 1
        self.last_failed_attempt = get_current_timestamp()
    
    def record_login_success(self) -> None:
        """ログイン成功を記録する"""
        self.failed_login_attempts = 0
        self.last_failed_attempt = None
        self.last_login = get_current_datetime_str()
    
    def reset_password(self, new_password_hash: str) -> None:
        """
        パスフレーズをリセットする
        
        Args:
            new_password_hash (str): 新しいパスフレーズのハッシュ
        """
        self.password_hash = new_password_hash
        self.updated_at = get_current_datetime_str()

