"""
管理者用サービス

ユーザー管理、システム設定、ログ閲覧などの管理者向け機能を提供します。
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.models.user import User
from app.models.system_setting import SystemSetting
from app.models.login_attempt import LoginAttempt
from app.schemas.admin import UserListItem, SystemSettings
from app.utils.datetime import format_datetime


def get_all_users(db: Session, skip: int = 0, limit: int = 100) -> List[UserListItem]:
    """
    全ユーザー一覧を取得します。
    
    Args:
        db: データベースセッション
        skip: スキップ数
        limit: 取得上限
        
    Returns:
        ユーザー一覧
    """
    users = db.query(User).offset(skip).limit(limit).all()
    
    result = []
    for user in users:
        user_item = UserListItem(
            id=user.id,
            username=user.username,
            email=user.email,
            is_active=user.is_active,
            is_admin=user.is_admin,
            is_locked=user.is_locked,
            created_at=format_datetime(user.created_at),
            last_login=format_datetime(user.last_login) if user.last_login else None,
            login_attempts=user.login_attempts
        )
        result.append(user_item)
    
    return result


def lock_user(db: Session, user_id: int) -> bool:
    """
    ユーザーアカウントをロックします。
    
    Args:
        db: データベースセッション
        user_id: ユーザーID
        
    Returns:
        ロック成功時はTrue、失敗時はFalse
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        return False
    
    user.is_locked = True
    db.commit()
    
    return True


def unlock_user(db: Session, user_id: int) -> bool:
    """
    ユーザーアカウントのロックを解除します。
    
    Args:
        db: データベースセッション
        user_id: ユーザーID
        
    Returns:
        ロック解除成功時はTrue、失敗時はFalse
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        return False
    
    user.is_locked = False
    user.login_attempts = 0
    user.locked_until = None
    db.commit()
    
    return True


def get_system_settings(db: Session) -> SystemSettings:
    """
    システム設定を取得します。
    
    Args:
        db: データベースセッション
        
    Returns:
        システム設定
    """
    # 設定をデータベースから取得
    settings_dict = {}
    
    settings = db.query(SystemSetting).all()
    for setting in settings:
        settings_dict[setting.key] = setting.value
    
    # SystemSettingsオブジェクトを作成
    return SystemSettings(
        fail_lock_attempts=int(settings_dict.get("fail_lock_attempts", 5)),
        fail_lock_window=int(settings_dict.get("fail_lock_window", 30)),
        fail_lock_duration=int(settings_dict.get("fail_lock_duration", 120)),
        session_timeout=int(settings_dict.get("session_timeout", 24)),
        min_passphrase_length=int(settings_dict.get("min_passphrase_length", 32)),
        default_passphrase_length=int(settings_dict.get("default_passphrase_length", 64)),
        max_passphrase_length=int(settings_dict.get("max_passphrase_length", 128))
    )


def update_system_settings(db: Session, settings: SystemSettings) -> bool:
    """
    システム設定を更新します。
    
    Args:
        db: データベースセッション
        settings: 更新するシステム設定
        
    Returns:
        更新成功時はTrue、失敗時はFalse
    """
    try:
        # 設定をデータベースに保存
        settings_dict = settings.model_dump()
        
        for key, value in settings_dict.items():
            setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
            
            if setting:
                # 既存の設定を更新
                setting.value = str(value)
                setting.updated_at = datetime.utcnow()
            else:
                # 新しい設定を作成
                new_setting = SystemSetting(
                    key=key,
                    value=str(value),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(new_setting)
        
        db.commit()
        return True
    
    except Exception:
        db.rollback()
        return False


def get_login_attempts(
    db: Session, 
    username: Optional[str] = None, 
    success: Optional[bool] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0, 
    limit: int = 100
) -> List[LoginAttempt]:
    """
    ログイン試行ログを取得します。
    
    Args:
        db: データベースセッション
        username: フィルタするユーザー名（省略可）
        success: 成功/失敗でフィルタ（省略可）
        start_date: 開始日時（省略可）
        end_date: 終了日時（省略可）
        skip: スキップ数
        limit: 取得上限
        
    Returns:
        ログイン試行ログのリスト
    """
    query = db.query(LoginAttempt)
    
    # フィルタ条件を適用
    if username:
        query = query.filter(LoginAttempt.username == username)
    
    if success is not None:
        query = query.filter(LoginAttempt.success == success)
    
    if start_date:
        query = query.filter(LoginAttempt.timestamp >= start_date)
    
    if end_date:
        query = query.filter(LoginAttempt.timestamp <= end_date)
    
    # 並び替えとページング
    query = query.order_by(LoginAttempt.timestamp.desc()).offset(skip).limit(limit)
    
    return query.all()

