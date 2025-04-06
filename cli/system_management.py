"""
ユーザー管理CLIモジュール

ユーザーの作成、編集、削除などのユーザー管理機能を提供します。
"""

import argparse
import sys
from pathlib import Path

from sqlalchemy.orm import Session

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.user import User
from app.utils.datetime import get_current_datetime
from app.utils.password import get_password_hash, generate_passphrase


def create_user(
    db: Session, username: str, passphrase: str = None, is_admin: bool = False
):
    """
    ユーザーを作成します。

    Args:
        db: データベースセッション
        username: ユーザー名
        passphrase: パスフレーズ（指定しない場合は自動生成）
        is_admin: 管理者権限を付与するかどうか
    """
    # ユーザーが既に存在するか確認
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        print(f"ユーザー '{username}' は既に存在します。")
        return

    # パスフレーズが指定されていない場合は自動生成
    if not passphrase:
        passphrase = generate_passphrase(settings.DEFAULT_PASSPHRASE_LENGTH)
        print(f"生成されたパスフレーズ: {passphrase}")

    # パスフレーズの長さを検証
    if len(passphrase) < settings.MIN_PASSPHRASE_LENGTH:
        print(
            f"パスフレーズは{settings.MIN_PASSPHRASE_LENGTH}文字以上である必要があります。"
        )
        return

    # 現在の日時を取得
    now = get_current_datetime()

    # ユーザーを作成
    user = User(
        username=username,
        password_hash=get_password_hash(passphrase),
        created_at=now,
        updated_at=now,
        is_admin=1 if is_admin else 0,
    )

    # データベースに保存
    db.add(user)
    db.commit()
    db.refresh(user)

    print(f"ユーザー '{username}' を作成しました。")


def list_users(db: Session):
    """
    ユーザー一覧を表示します。

    Args:
        db: データベースセッション
    """
    users = db.query(User).all()
    if not users:
        print("ユーザーが存在しません。")
        return

    print(f"{'ID':<5} {'ユーザー名':<20} {'管理者':<10} {'ロック状態':<10} {'作成日時':<30}")
    print("-" * 75)
    for user in users:
        print(
            f"{user.id:<5} {user.username:<20} "
            f"{'はい' if user.is_admin else 'いいえ':<10} "
            f"{'ロック中' if user.is_locked else '通常':<10} "
            f"{user.created_at:<30}"
        )


def delete_user(db: Session, username: str):
    """
    ユーザーを削除します。

    Args:
        db: データベースセッション
        username: ユーザー名
    """
    user = db.query(User).filter(User.username == username).first()
    if not user:
        print(f"ユーザー '{username}' が見つかりません。")
        return

    db.delete(user)
    db.commit()
    print(f"ユーザー '{username}' を削除しました。")


def reset_passphrase(db: Session, username: str, passphrase: str = None):
    """
    ユーザーのパスフレーズをリセットします。

    Args:
        db: データベースセッション
        username: ユーザー名
        passphrase: 新しいパスフレーズ（指定しない場合は自動生成）
    """
    user = db.query(User).filter(User.username == username).first()
    if not user:
        print(f"ユーザー '{username}' が見つかりません。")
        return

    # パスフレーズが指定されていない場合は自動生成
    if not passphrase:
        passphrase = generate_passphrase(settings.DEFAULT_PASSPHRASE_LENGTH)
        print(f"生成されたパスフレーズ: {passphrase}")

    # パスフレーズの長さを検証
    if len(passphrase) < settings.MIN_PASSPHRASE_LENGTH:
        print(
            f"パスフレーズは{settings.MIN_PASSPHRASE_LENGTH}文字以上である必要があります。"
        )
        return

    # パスフレーズをハッシュ化して保存
    user.password_hash = get_password_hash(passphrase)
    user.updated_at = get_current_datetime()
    db.commit()
    print(f"ユーザー '{username}' のパスフレーズをリセットしました。")


def lock_user(db: Session, username: str):
    """
    ユーザーをロックします。

    Args:
        db: データベースセッション
        username: ユーザー名
    """
    user = db.query(User).filter(User.username == username).first()
    if not user:
        print(f"ユーザー '{username}' が見つかりません。")
        return

    user.is_locked = 1
    user.updated_at = get_current_datetime()
    db.commit()
    print(f"ユーザー '{username}' をロックしました。")


def unlock_user(db: Session, username: str):
    """
    ユーザーのロックを解除します。

    Args:
        db: データベースセッション
        username: ユーザー名
    """
    user = db.query(User).filter(User.username == username).first()
    if not user:
        print(f"ユーザー '{username}' が見つかりません。")
        return

    user.is_locked = 0
    user.locked_until = None
    user.failed_login_attempts = 0
    user.last_failed_attempt = None
    user.updated_at = get_current_datetime()
    db.commit()
    print(f"ユーザー '{username}' のロックを解除しました。")


def main():
    """
    CLIエントリーポイント
    """
    parser = argparse.ArgumentParser(description="SimpleAuth ユーザー管理ツール")
    subparsers = parser.add_subparsers(dest="command", help="コマンド")

    # create コマンド
    create_parser = subparsers.add_parser("create", help="ユーザーを作成します")
    create_parser.add_argument("username", help="ユーザー名")
    create_parser.add_argument("--passphrase", help="パスフレーズ（指定しない場合は自動生成）")
    create_parser.add_argument(
        "--admin", action="store_true", help="管理者権限を付与する"
    )

    # list コマンド
    list_parser = subparsers.add_parser("list", help="ユーザー一覧を表示します")

    # delete コマンド
    delete_parser = subparsers.add_parser("delete", help="ユーザーを削除します")
    delete_parser.add_argument("username", help="ユーザー名")

    # reset-passphrase コマンド
    reset_parser = subparsers.add_parser(
        "reset-passphrase", help="ユーザーのパスフレーズをリセットします"
    )
    reset_parser.add_argument("username", help="ユーザー名")
    reset_parser.add_argument(
        "--passphrase", help="新しいパスフレーズ（指定しない場合は自動生成）"
    )

    # lock コマンド
    lock_parser = subparsers.add_parser("lock", help="ユーザーをロックします")
    lock_parser.add_argument("username", help="ユーザー名")

    # unlock コマンド
    unlock_parser = subparsers.add_parser("unlock", help="ユーザーのロックを解除します")
    unlock_parser.add_argument("username", help="ユーザー名")

    args = parser.parse_args()

    # データベースセッションを作成
    db = SessionLocal()
    try:
        if args.command == "create":
            create_user(db, args.username, args.passphrase, args.admin)
        elif args.command == "list":
            list_users(db)
        elif args.command == "delete":
            delete_user(db, args.username)
        elif args.command == "reset-passphrase":
            reset_passphrase(db, args.username, args.passphrase)
        elif args.command == "lock":
            lock_user(db, args.username)
        elif args.command == "unlock":
            unlock_user(db, args.username)
        else:
            parser.print_help()
    finally:
        db.close()


if __name__ == "__main__":
    main()

