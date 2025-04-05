from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.utils.datetime import get_current_timestamp

class LoginAttempt(Base):
    """
    ログイン試行履歴を記録するモデル
    
    Attributes:
        id (int): ログイン試行ID
        user_id (int): ユーザーID（外部キー）、存在しないユーザー名の場合はNULL
        timestamp (int): ログイン試行日時（Unixtime形式）
        ip_address (str): クライアントIPアドレス
        user_agent (str): クライアントのユーザーエージェント
        success (bool): 成功/失敗フラグ（False=失敗、True=成功）
    """
    __tablename__ = "login_attempts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    timestamp = Column(Integer, nullable=False, default=get_current_timestamp)
    ip_address = Column(String, nullable=False)
    user_agent = Column(String, nullable=False)
    success = Column(Boolean, nullable=False)

    # リレーションシップ
    user = relationship("User", back_populates="login_attempts")

    @classmethod
    def create_login_attempt(cls, user_id: int = None, ip_address: str = "", user_agent: str = "", success: bool = False) -> "LoginAttempt":
        """
        新しいログイン試行履歴を作成する
        
        Args:
            user_id (int, optional): ユーザーID。存在しないユーザー名の場合はNone。
            ip_address (str): クライアントIPアドレス
            user_agent (str): クライアントのユーザーエージェント
            success (bool): 成功/失敗フラグ（False=失敗、True=成功）
            
        Returns:
            LoginAttempt: 作成されたログイン試行履歴オブジェクト
        """
        return cls(
            user_id=user_id,
            timestamp=get_current_timestamp(),
            ip_address=ip_address,
            user_agent=user_agent,
            success=success
        )
    
    @classmethod
    def get_recent_attempts(cls, db, user_id: int, minutes: int) -> list:
        """
        指定したユーザーの最近のログイン試行履歴を取得する
        
        Args:
            db: データベースセッション
            user_id (int): ユーザーID
            minutes (int): 何分前までの履歴を取得するか
            
        Returns:
            list: ログイン試行履歴のリスト
        """
        current_time = get_current_timestamp()
        time_window = current_time - (minutes * 60)
        
        return db.query(cls).filter(
            cls.user_id == user_id,
            cls.timestamp >= time_window
        ).order_by(cls.timestamp.desc()).all()

