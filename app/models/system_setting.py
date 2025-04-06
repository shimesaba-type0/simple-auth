from sqlalchemy import Column, String, Text

from app.core.database import Base

class SystemSetting(Base):
    """
    システム設定を保存するモデル
    
    Attributes:
        key (str): 設定キー
        value (str): 設定値
        description (str): 設定の説明
    """
    __tablename__ = "system_settings"

    key = Column(String, primary_key=True, index=True)
    value = Column(String, nullable=False)
    description = Column(String, nullable=False)

    @classmethod
    def get_setting(cls, db, key: str, default_value: str = None) -> str:
        """
        設定値を取得する
        
        Args:
            db: データベースセッション
            key (str): 設定キー
            default_value (str, optional): デフォルト値
            
        Returns:
            str: 設定値。設定が存在しない場合はデフォルト値
        """
        setting = db.query(cls).filter(cls.key == key).first()
        if setting:
            return setting.value
        return default_value
    
    @classmethod
    def set_setting(cls, db, key: str, value: str,
        description: str = None) -> "SystemSetting":
        """
        設定値を設定する
        
        Args:
            db: データベースセッション
            key (str): 設定キー
            value (str): 設定値
            description (str, optional): 設定の説明
            
        Returns:
            SystemSetting: 設定オブジェクト
        """
        setting = db.query(cls).filter(cls.key == key).first()
        if setting:
            setting.value = value
            if description:
                setting.description = description
        else:
            if not description:
                description = f"Setting for {key}"
            setting = cls(key=key, value=value, description=description)
            db.add(setting)
        
        return setting
    
    @classmethod
    def get_all_settings(cls, db) -> list:
        """
        すべての設定を取得する
        
        Args:
            db: データベースセッション
            
        Returns:
            list: 設定オブジェクトのリスト
        """
        return db.query(cls).all()
    
    @classmethod
    def initialize_default_settings(cls, db) -> None:
        """
        デフォルト設定を初期化する
        
        Args:
            db: データベースセッション
        """
        default_settings = [
            {
                "key": "fail_lock_attempts",
                "value": "5",
                "description": "連続失敗回数のしきい値"
            },
            {
                "key": "fail_lock_window",
                "value": "30",
                "description": "失敗カウントのウィンドウ（分）"
            },
            {
                "key": "fail_lock_duration",
                "value": "120",
                "description": "ロック期間（分）"
            },
            {
                "key": "session_timeout",
                "value": "24",
                "description": "セッションタイムアウト（時間）"
            },
            {
                "key": "min_passphrase_length",
                "value": "32",
                "description": "最小パスフレーズ長"
            },
            {
                "key": "default_passphrase_length",
                "value": "64",
                "description": "デフォルトの自動生成パスフレーズ長"
            },
            {
                "key": "max_passphrase_length",
                "value": "128",
                "description": "最大パスフレーズ長"
            }
        ]
        
        for setting in default_settings:
            cls.set_setting(db, setting["key"], setting["value"], setting["description"])

