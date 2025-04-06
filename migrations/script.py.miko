"""
セッション管理ユーティリティモジュール

セッションの作成、検証、削除などの機能を提供します。
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.session import Session as SessionModel
from app.utils.datetime import get_current_datetime, get_current_datetime_str


def generate_session_id() -> str:
    """
    一意のセッションIDを生成します。

    Returns:
        生成されたセッションID（UUID）
    """
    return str(uuid.uuid4())


def create_session(
    db: Session, user_id: int, ip_address: str, user_agent: str
) -> SessionModel:
    """
    新しいセッションを作成します。

    Args:
        db: データベースセッション
        user_id: ユーザーID
        ip_address: クライアントIPアドレス
        user_agent: クライアントのユーザーエージェント

    Returns:
        作成されたセッション
    """
    # 現在の日時を取得
    now = get_current_datetime()

    # セッションの有効期限を計算
    expires_at = (
        datetime.fromisoformat(now) + timedelta(hours=settings.SESSION_TIMEOUT)
    ).isoformat()

    # セッションを作成
    session = SessionModel(
        id=generate_session_id(),
        user_id=user_id,
        created_at=now,
        expires_at=expires_at,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    # データベースに保存
    db.add(session)
    db.commit()
    db.refresh(session)

    return session


def get_session(db: Session, session_id: str) -> Optional[SessionModel]:
    """
    セッションIDからセッションを取得します。

    Args:
        db: データベースセッション
        session_id: セッションID

    Returns:
        セッション（存在しない場合はNone）
    """
    return db.query(SessionModel).filter(SessionModel.id == session_id).first()


def validate_session(db: Session, session_id: str) -> Optional[SessionModel]:
    """
    セッションを検証します。

    有効期限が切れている場合は削除します。

    Args:
        db: データベースセッション
        session_id: セッションID

    Returns:
        有効なセッション（無効な場合はNone）
    """
    session = get_session(db, session_id)
    if not session:
        return None

    # 現在の日時を取得
    now = datetime.fromisoformat(get_current_datetime())

    # 有効期限を確認
    expires_at = datetime.fromisoformat(session.expires_at)
    if now > expires_at:
        # 有効期限切れの場合は削除
        db.delete(session)
        db.commit()
        return None

    return session


def delete_session(db: Session, session_id: str) -> bool:
    """
    セッションを削除します。

    Args:
        db: データベースセッション
        session_id: セッションID

    Returns:
        削除結果（成功した場合はTrue、失敗した場合はFalse）
    """
    session = get_session(db, session_id)
    if not session:
        return False

    db.delete(session)
    db.commit()
    return True


def delete_user_sessions(db: Session, user_id: int) -> int:
    """
    ユーザーのすべてのセッションを削除します。

    Args:
        db: データベースセッション
        user_id: ユーザーID

    Returns:
        削除されたセッション数
    """
    sessions = db.query(SessionModel).filter(SessionModel.user_id == user_id).all()
    count = len(sessions)

    for session in sessions:
        db.delete(session)

    db.commit()
    return count


def extend_session(db: Session, session_id: str) -> Optional[SessionModel]:
    """
    セッションの有効期限を延長します。

    Args:
        db: データベースセッション
        session_id: セッションID

    Returns:
        更新されたセッション（存在しない場合はNone）
    """
    session = get_session(db, session_id)
    if not session:
        return None

    # 現在の日時を取得
    now = datetime.fromisoformat(get_current_datetime())

    # 有効期限を更新
    expires_at = (now + timedelta(hours=settings.SESSION_TIMEOUT)).isoformat()
    session.expires_at = expires_at

    db.commit()
    db.refresh(session)
    return session

