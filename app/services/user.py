"""
ユーザー関連のサービス

ユーザープロファイル、パスフレーズ変更、セッション管理などの機能を提供します。
"""

from typing import Optional, List, Dict, Any
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.models.user import User
from app.models.session import Session as SessionModel
from app.schemas.user import UserProfile
from app.schemas.auth import SessionInfo
from app.utils.password import verify_password, get_password_hash
from app.utils.datetime import format_datetime


def get_user_profile(db: Session, user_id: int) -> Optional[UserProfile]:
    """
    ユーザープロファイルを取得します。
    
    Args:
        db: データベースセッション
        user_id: ユーザーID
        
    Returns:
        ユーザープロファイル（存在しない場合はNone）
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        return None
    
    return UserProfile(
        id=user.id,
        username=user.username,
        email=user.email,
        is_active=user.is_active,
        is_admin=user.is_admin,
        created_at=format_datetime(user.created_at),
        last_login=format_datetime(user.last_login) if user.last_login else None
    )


def change_user_passphrase(
    db: Session, 
    user_id: int, 
    current_passphrase: str, 
    new_passphrase: str
) -> bool:
    """
    ユーザーのパスフレーズを変更します。
    
    Args:
        db: データベースセッション
        user_id: ユーザーID
        current_passphrase: 現在のパスフレーズ
        new_passphrase: 新しいパスフレーズ
        
    Returns:
        変更成功時はTrue、失敗時はFalse
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        return False
    
    # 現在のパスフレーズを検証
    if not verify_password(current_passphrase, user.hashed_passphrase):
        return False
    
    # 新しいパスフレーズをハッシュ化して保存
    user.hashed_passphrase = get_password_hash(new_passphrase)
    user.passphrase_changed_at = datetime.utcnow()
    
    db.commit()
    
    return True


def get_user_sessions(db: Session, user_id: int, current_token: Optional[str] = None) -> List[SessionInfo]:
    """
    ユーザーのアクティブセッション一覧を取得します。
    
    Args:
        db: データベースセッション
        user_id: ユーザーID
        current_token: 現在のセッショントークン（現在のセッションを識別するため）
        
    Returns:
        セッション情報のリスト
    """
    sessions = db.query(SessionModel).filter(
        and_(
            SessionModel.user_id == user_id,
            SessionModel.expires_at > datetime.utcnow()
        )
    ).all()
    
    result = []
    
    for session in sessions:
        is_current = current_token is not None and session.token == current_token
        
        session_info = SessionInfo(
            id=session.id,
            created_at=format_datetime(session.created_at),
            expires_at=format_datetime(session.expires_at),
            ip_address=session.ip_address,
            user_agent=session.user_agent,
            is_current=is_current
        )
        
        result.append(session_info)
    
    return result


def delete_user_session(db: Session, user_id: int, session_id: str) -> bool:
    """
    ユーザーのセッションを削除します。
    
    Args:
        db: データベースセッション
        user_id: ユーザーID
        session_id: セッションID
        
    Returns:
        削除成功時はTrue、失敗時はFalse
    """
    session = db.query(SessionModel).filter(
        and_(
            SessionModel.id == session_id,
            SessionModel.user_id == user_id
        )
    ).first()
    
    if not session:
        return False
    
    db.delete(session)
    db.commit()
    
    return True

