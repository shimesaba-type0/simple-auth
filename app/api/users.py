"""
ユーザー関連のAPIエンドポイント

ユーザープロファイル、パスフレーズ変更、セッション管理などのエンドポイントを提供します。
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.user import UserProfile, ChangePassphraseRequest
from app.services.user import get_user_profile, change_user_passphrase, get_user_sessions
from app.services.auth import get_current_user

# ルーターの作成
router = APIRouter()

@router.get("/me", response_model=UserProfile)
async def read_users_me(
    current_user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    現在のユーザーのプロファイル情報を取得します。
    """
    user = get_user_profile(db, current_user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user

@router.post("/change-passphrase")
async def change_passphrase(
    request: ChangePassphraseRequest,
    current_user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ユーザーのパスフレーズを変更します。
    
    - **current_passphrase**: 現在のパスフレーズ
    - **new_passphrase**: 新しいパスフレーズ
    """
    success = change_user_passphrase(
        db, 
        current_user_id, 
        request.current_passphrase, 
        request.new_passphrase
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid current passphrase",
        )
    
    return {"detail": "Passphrase changed successfully"}

@router.get("/sessions")
async def get_sessions(
    current_user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    現在のユーザーのアクティブセッション一覧を取得します。
    """
    sessions = get_user_sessions(db, current_user_id)
    return {"sessions": sessions}

@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    指定されたセッションを削除します。
    """
    # TODO: セッション削除処理を実装
    
    return {"detail": "Session deleted successfully"}

