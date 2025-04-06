"""
日時ユーティリティモジュール

日時の取得、変換、フォーマットなどの機能を提供します。
"""

from datetime import datetime, timezone
import time


def get_current_datetime_str() -> str:
    """
    現在の日時をISO 8601形式の文字列で返す
    例: 2025-04-01T00:00:00+09:00
    """
    return datetime.now(timezone.utc).astimezone().isoformat()


def get_current_datetime() -> str:
    """
    現在の日時をISO 8601形式の文字列で返す
    get_current_datetime_str()のエイリアス
    """
    return get_current_datetime_str()


def get_current_timestamp() -> int:
    """
    現在の日時をUnixtime形式（秒）で返す
    """
    return int(time.time())


def timestamp_to_datetime_str(timestamp: int) -> str:
    """
    Unixtime形式の日時をISO 8601形式の文字列に変換
    """
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).astimezone().isoformat()


def datetime_str_to_timestamp(datetime_str: str) -> int:
    """
    ISO 8601形式の文字列をUnixtime形式に変換
    """
    dt = datetime.fromisoformat(datetime_str)
    return int(dt.timestamp())

