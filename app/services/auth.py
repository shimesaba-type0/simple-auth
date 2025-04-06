"""
認証関連のサービス

ユーザー認証、セッション管理などの認証関連の機能を提供します。
"""

import secrets
import uuid
from datetime import datetime, timedelta
from typing import Optional, Union, Dict, Any

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.core.database import get_db
from app.core.config import settings
from app.models.user import User
from app.models.session import Session as SessionModel
from app.models.login_attempt import LoginAttempt
from app.utils.password import verify_password
from app.utils.datetime import get_current_datetime, format_datetime

# OAuth2のトークン取得エンドポイント
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """
    ユーザー名とパスワードでユーザーを認証します。
    
    Args:
        db: データベースセッション
        username: ユーザー名
        password: パスワード
        
    Returns:
        認証成功時はユーザーオブジェクト、失敗時はNone
    """
    # ユーザーを検索
    user = db.query(User).filter(User.username == username).first()
    
    if not user:
        # ユーザーが存在しない場合はログイン試行を記録して失敗
        record_login_attempt(db, username, False)
        return None
    
    if not user.is_active:
        # アカウントが無効の場合はログイン試行を記録して失敗
        record_login_attempt(db, username, False)
        return None
    
    if user.is_locked:
        # アカウントがロックされている場合、ロック期限をチェック
        if user.locked_until and user.locked_until > datetime.utcnow():
            # ロック中の場合はログイン試行を記録して失敗
            record_login_attempt(db, username, False)
            return None
        else:
            # ロック期限が切れている場合はロックを解除
            user.is_locked = False
            user.locked_until = None
            user.login_attempts = 0
            db.commit()
    
    # パスワードを検証
    if not verify_password(password, user.hashed_passphrase):
        # パスワードが一致しない場合はログイン試行回数を増やす
        user.login_attempts += 1
        
        # Fail Lockの閾値を超えた場合はアカウントをロック
        if user.login_attempts >= settings.FAIL_LOCK_ATTEMPTS:
            user.is_locked = True
            user.locked_until = datetime.utcnow() + timedelta(minutes=settings.FAIL_LOCK_DURATION)
        
        db.commit()
        
        # ログイン試行を記録
        record_login_attempt(db, username, False)
        return None
    
    # 認証成功時はログイン試行回数をリセット
    user.login_attempts = 0
    user.last_login = datetime.utcnow()
    db.commit()
    
    # ログイン試行を記録
    record_login_attempt(db, username, True)
    
    return user


def record_login_attempt(db: Session, username: str, success: bool, request: Optional[Request] = None) -> None:
    """
    ログイン試行を記録します。
    
    Args:
        db: データベースセッション
        username: ユーザー名
        success: 成功/失敗
        request: リクエストオブジェクト（IPアドレス、User-Agentの取得用）
    """
    ip_address = None
    user_agent = None
    
    if request:
        ip_address = request.client.host if hasattr(request.client, "host") else None
        user_agent = request.headers.get("User-Agent")
    
    login_attempt = LoginAttempt(
        username=username,
        success=success,
        ip_address=ip_address,
        user_agent=user_agent,
        timestamp=datetime.utcnow()
    )
    
    db.add(login_attempt)
    db.commit()


def create_session(db: Session, user_id: int, request: Optional[Request] = None) -> str:
    """
    ユーザーセッションを作成します。
    
    Args:
        db: データベースセッション
        user_id: ユーザーID
        request: リクエストオブジェクト（IPアドレス、User-Agentの取得用）
        
    Returns:
        セッショントークン
    """
    # セッショントークンを生成
    token = secrets.token_hex(32)
    
    # 有効期限を計算
    expires_at = datetime.utcnow() + timedelta(hours=settings.SESSION_TIMEOUT)
    
    ip_address = None
    user_agent = None
    
    if request:
        ip_address = request.client.host if hasattr(request.client, "host") else None
        user_agent = request.headers.get("User-Agent")
    
    # セッションを作成
    session = SessionModel(
        id=str(uuid.uuid4()),
        user_id=user_id,
        token=token,
        ip_address=ip_address,
        user_agent=user_agent,
        created_at=datetime.utcnow(),
        expires_at=expires_at
    )
    
    db.add(session)
    db.commit()
    
    return token


def get_session(db: Session, token: str) -> Optional[SessionModel]:
    """
    トークンからセッションを取得します。
    
    Args:
        db: データベースセッション
        token: セッショントークン
        
    Returns:
        セッションオブジェクト（存在しない場合はNone）
    """
    return db.query(SessionModel).filter(
        and_(
            SessionModel.token == token,
            SessionModel.expires_at > datetime.utcnow()
        )
    ).first()


def delete_session(db: Session, token: str) -> bool:
    """
    セッションを削除します。
    
    Args:
        db: データベースセッション
        token: セッショントークン
        
    Returns:
        削除成功時はTrue、失敗時はFalse
    """
    session = db.query(SessionModel).filter(SessionModel.token == token).first()
    
    if not session:
        return False
    
    db.delete(session)
    db.commit()
    
    return True


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> int:
    """
    現在のユーザーIDを取得します。
    
    Args:
        token: アクセストークン
        db: データベースセッション
        
    Returns:
        ユーザーID
        
    Raises:
        HTTPException: 認証エラー時
    """
    session = get_session(db, token)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # ユーザーが存在するか確認
    user = db.query(User).filter(User.id == session.user_id).first()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User inactive or deleted",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user.id


def get_current_admin_user(
    current_user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> int:
    """
    現在の管理者ユーザーIDを取得します。
    
    Args:
        current_user_id: 現在のユーザーID
        db: データベースセッション
        
    Returns:
        管理者ユーザーID
        
    Raises:
        HTTPException: 権限エラー時
    """
    user = db.query(User).filter(User.id == current_user_id).first()
    
    if not user or not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    return user.id

