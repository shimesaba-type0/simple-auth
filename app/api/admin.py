"""
管理者用APIエンドポイント

ユーザー管理、システム設定、ログ閲覧などの管理者向けエンドポイントを提供します。
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas.admin import UserListItem, SystemSettings
from app.services.admin import (
    get_all_users, 
    lock_user, 
    unlock_user, 
    get_system_settings, 
    update_system_settings
)
from app.services.auth import get_current_admin_user

# ルーターの作成
router = APIRouter()

@router.get("/users", response_model=List[UserListItem])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_admin_id: int = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    ユーザー一覧を取得します。
    """
    users = get_all_users(db, skip=skip, limit=limit)
    return users

@router.post("/users/{user_id}/lock")
async def lock_user_account(
    user_id: int,
    current_admin_id: int = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    指定されたユーザーアカウントをロックします。
    """
    success = lock_user(db, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return {"detail": "User locked successfully"}

@router.post("/users/{user_id}/unlock")
async def unlock_user_account(
    user_id: int,
    current_admin_id: int = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    指定されたユーザーアカウントのロックを解除します。
    """
    success = unlock_user(db, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return {"detail": "User unlocked successfully"}

@router.get("/settings", response_model=SystemSettings)
async def read_system_settings(
    current_admin_id: int = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    システム設定を取得します。
    """
    settings = get_system_settings(db)
    return settings

@router.put("/settings")
async def update_settings(
    settings: SystemSettings,
    current_admin_id: int = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    システム設定を更新します。
    """
    success = update_system_settings(db, settings)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update settings",
        )
    return {"detail": "Settings updated successfully"}

