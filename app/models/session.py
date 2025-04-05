from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base
from app.utils.datetime import get_current_datetime_str

class Session(Base):
    """
    ユーザーセッションを管理するモデル
    
    Attributes:
        id (str): セッションID（UUID）
        user_id (int): ユーザーID（外部キー）
        created_at (str): セッション作成日時（ISO 8601形式）
        expires_at (str): セッション有効期限（ISO 8601形式）
        ip_address (str): クライアントIPアドレス
        user_agent (str): クライアントのユーザーエージェント
    """
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(String, nullable=False, default=get_current_datetime_str)
    expires_at = Column(String, nullable=False)
    ip_address = Column(String, nullable=False)
    user_agent = Column(String, nullable=False)

    # リレーションシップ
    user = relationship("User", back_populates="sessions")

    @classmethod
    def create_session(cls, user_id: int, expires_at: str, ip_address: str, user_agent: str) -> "Session":
        """
        新しいセッションを作成する
        
        Args:
            user_id (int): ユーザーID
            expires_at (str): セッション有効期限（ISO 8601形式）
            ip_address (str): クライアントIPアドレス
            user_agent (str): クライアントのユーザーエージェント
            
        Returns:
            Session: 作成されたセッションオブジェクト
        """
        return cls(
            id=str(uuid.uuid4()),
            user_id=user_id,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    def is_expired(self, current_time: str) -> bool:
        """
        セッションが有効期限切れかどうかを確認
        
        Args:
            current_time (str): 現在の日時（ISO 8601形式）
            
        Returns:
            bool: セッションが有効期限切れの場合はTrue、そうでない場合はFalse
        """
        return current_time > self.expires_at

