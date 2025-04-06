"""
認証関連のAPIエンドポイント

ログイン、ログアウト、セッション管理などの認証関連のエンドポイントを提供します。
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.auth import TokenResponse, LoginRequest
from app.services.auth import authenticate_user, create_session, delete_session

# ルーターの作成
router = APIRouter()

@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    ユーザー認証を行い、アクセストークンを発行します。
    
    - **username**: ユーザー名
    - **password**: パスワード
    """
    # ユーザー認証
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # セッション作成
    token = create_session(db, user.id)
    
    return {"access_token": token, "token_type": "bearer"}

@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    現在のセッションを終了します。
    """
    # 認証ヘッダーからトークンを取得
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.replace("Bearer ", "")
        # セッション削除
        delete_session(db, token)
    
    # クッキーをクリア
    response.delete_cookie(key="session")
    
    return {"detail": "Successfully logged out"}

@router.get("/auth")
async def auth_check(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    認証チェック用エンドポイント（Nginx auth_request用）
    
    認証されていない場合は401を返します。
    """
    # 認証ヘッダーからトークンを取得
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # TODO: トークンの検証処理を実装
    
    return {"detail": "Authenticated"}

