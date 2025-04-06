"""
パスワードユーティリティモジュール

パスワードのハッシュ化、検証、パスフレーズ生成などの機能を提供します。
"""

import random
import string
from typing import Optional

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.core.config import settings


# Argon2idパスワードハッシャーを初期化
_password_hasher = PasswordHasher(
    time_cost=settings.ARGON2_TIME_COST,
    memory_cost=settings.ARGON2_MEMORY_COST,
    parallelism=settings.ARGON2_PARALLELISM,
    hash_len=settings.ARGON2_HASH_LENGTH,
    salt_len=settings.ARGON2_SALT_LENGTH,
)


def get_password_hash(password: str) -> str:
    """
    パスワードをArgon2idでハッシュ化します。

    Args:
        password: ハッシュ化するパスワード

    Returns:
        ハッシュ化されたパスワード
    """
    return _password_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    パスワードとハッシュを検証します。

    Args:
        plain_password: 平文パスワード
        hashed_password: ハッシュ化されたパスワード

    Returns:
        検証結果（一致する場合はTrue、一致しない場合はFalse）
    """
    try:
        _password_hasher.verify(hashed_password, plain_password)
        return True
    except VerifyMismatchError:
        return False


def generate_passphrase(length: Optional[int] = None) -> str:
    """
    安全なパスフレーズを生成します。

    Args:
        length: パスフレーズの長さ（指定しない場合はデフォルト値を使用）

    Returns:
        生成されたパスフレーズ
    """
    if length is None:
        length = settings.DEFAULT_PASSPHRASE_LENGTH

    # 長さの検証
    if length < settings.MIN_PASSPHRASE_LENGTH:
        length = settings.MIN_PASSPHRASE_LENGTH
    elif length > settings.MAX_PASSPHRASE_LENGTH:
        length = settings.MAX_PASSPHRASE_LENGTH

    # 使用する文字セット（仕様書に基づく）
    # 紛らわしい文字（0, 1, O, I, l）を除外
    lowercase_chars = "abcdefghijkmnopqrstuvwxyz"
    uppercase_chars = "ABCDEFGHJKLMNPQRSTUVWXYZ"
    digit_chars = "23456789"

    # すべての文字セットを組み合わせる
    all_chars = lowercase_chars + uppercase_chars + digit_chars

    # 各文字セットから少なくとも1文字を含めるようにする
    passphrase = [
        random.choice(lowercase_chars),
        random.choice(uppercase_chars),
        random.choice(digit_chars),
    ]

    # 残りの文字をランダムに選択
    passphrase.extend(random.choice(all_chars) for _ in range(length - 3))

    # 文字列をシャッフル
    random.shuffle(passphrase)

    return "".join(passphrase)


def is_passphrase_valid(passphrase: str) -> bool:
    """
    パスフレーズが要件を満たしているかを検証します。

    Args:
        passphrase: 検証するパスフレーズ

    Returns:
        検証結果（要件を満たす場合はTrue、満たさない場合はFalse）
    """
    # 長さの検証
    if len(passphrase) < settings.MIN_PASSPHRASE_LENGTH:
        return False
    if len(passphrase) > settings.MAX_PASSPHRASE_LENGTH:
        return False

    return True

