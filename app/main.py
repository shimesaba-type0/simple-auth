"""
FastAPIアプリケーションのエントリーポイント

アプリケーションの初期化、ルーターの設定、ミドルウェアの設定などを行います。
"""

from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from app.core.config import settings
from app.api import auth, users, admin
from app.core.database import get_db, engine

# FastAPIアプリケーションのインスタンスを作成
app = FastAPI(
    title=settings.APP_NAME,
    description="Simple authentication and authorization system",
    version="0.1.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# 静的ファイルの設定
app.mount("/static", StaticFiles(directory=Path(__file__).parent.parent / "static"), name="static")

# テンプレートの設定
templates = Jinja2Templates(directory=Path(__file__).parent.parent / "templates")

# CORSミドルウェアの設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では適切に制限すること
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーターの設定
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])

# ルートエンドポイント
@app.get("/")
async def root(request: Request):
    """
    ルートエンドポイント
    
    ログイン画面またはダッシュボードにリダイレクトします。
    """
    return templates.TemplateResponse("auth/login.html", {"request": request})

# ヘルスチェックエンドポイント
@app.get("/health")
async def health():
    """
    ヘルスチェックエンドポイント
    
    アプリケーションの状態を返します。
    """
    return {"status": "ok"}

# 例外ハンドラー
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    グローバル例外ハンドラー
    
    未処理の例外をキャッチしてJSONレスポンスを返します。
    """
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"},
    )

