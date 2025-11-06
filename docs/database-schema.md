# データベース設計

## 概要

**SQLite3** をメインデータベース、**Redis** をセッション・キャッシュストアとして使用します。

### SQLite3 を選んだ理由

✅ **セットアップが簡単**: ファイルベース、サーバー不要
✅ **依存関係が少ない**: デプロイが容易
✅ **バックアップが簡単**: ファイルコピーだけ
✅ **十分なパフォーマンス**: 小〜中規模（数千ユーザー）まで対応可能

### 制限事項

⚠️ **並行書き込み**: 同時に1つの書き込みのみ（読み込みは複数可）
⚠️ **UUID型なし**: TEXT型で保存（アプリケーション側で生成）
⚠️ **INET型なし**: IPアドレスは TEXT型で保存

この認証サーバーの用途では、これらの制限は問題になりません。

## SQLite3 スキーマ

### 1. users テーブル

ユーザー情報を保存します。

```sql
CREATE TABLE users (
    id TEXT PRIMARY KEY,  -- UUID（アプリケーション側で生成）
    email TEXT NOT NULL UNIQUE,
    display_name TEXT,
    passphrase_hash TEXT NOT NULL,  -- Argon2idハッシュ
    role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'admin')),
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
    locked INTEGER NOT NULL DEFAULT 0,  -- SQLite3はBOOLEANをINTEGERで保存 (0=false, 1=true)
    locked_until TEXT,  -- ISO 8601形式のタイムスタンプ
    lock_reason TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    last_login_at TEXT,
    deleted_at TEXT  -- 論理削除用
);

-- インデックス
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_status ON users(status);
CREATE INDEX idx_users_deleted_at ON users(deleted_at) WHERE deleted_at IS NULL;
```

### 2. login_history テーブル

ログイン履歴を保存します。

```sql
CREATE TABLE login_history (
    id TEXT PRIMARY KEY,  -- UUID
    user_id TEXT NOT NULL,
    email TEXT NOT NULL,  -- 削除されたユーザーの履歴保持のため
    login_at TEXT NOT NULL DEFAULT (datetime('now')),
    logout_at TEXT,
    logout_type TEXT CHECK (logout_type IN ('user', 'admin_forced', 'session_expired')),
    ip_address TEXT NOT NULL,  -- IPアドレスを文字列で保存
    user_agent TEXT,
    result TEXT NOT NULL CHECK (result IN ('success', 'failed')),
    failure_reason TEXT CHECK (failure_reason IN (
        'invalid_passphrase',
        'invalid_otp',
        'locked',
        'user_not_found',
        'rate_limited'
    )),
    session_id TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- インデックス
CREATE INDEX idx_login_history_user_id ON login_history(user_id);
CREATE INDEX idx_login_history_login_at ON login_history(login_at DESC);
CREATE INDEX idx_login_history_result ON login_history(result);
CREATE INDEX idx_login_history_session_id ON login_history(session_id);
```

### 3. notifications テーブル

通知を保存します。

```sql
CREATE TABLE notifications (
    id TEXT PRIMARY KEY,  -- UUID
    type TEXT NOT NULL CHECK (type IN ('admin', 'personal', 'system')),
    target_user_id TEXT,  -- personalの場合のみ
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    priority TEXT NOT NULL DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
    created_by TEXT,  -- 作成した管理者のID
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    expires_at TEXT,  -- 有効期限（オプション）
    FOREIGN KEY (target_user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

-- インデックス
CREATE INDEX idx_notifications_type ON notifications(type);
CREATE INDEX idx_notifications_target_user_id ON notifications(target_user_id);
CREATE INDEX idx_notifications_created_at ON notifications(created_at DESC);
```

### 4. notification_reads テーブル

通知の既読状態を保存します。

```sql
CREATE TABLE notification_reads (
    id TEXT PRIMARY KEY,  -- UUID
    notification_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    read_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(notification_id, user_id),
    FOREIGN KEY (notification_id) REFERENCES notifications(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- インデックス
CREATE INDEX idx_notification_reads_user_id ON notification_reads(user_id);
CREATE INDEX idx_notification_reads_notification_id ON notification_reads(notification_id);
```

### 5. user_dashboards テーブル

ユーザーのダッシュボードカスタマイズ内容を保存します。

```sql
CREATE TABLE user_dashboards (
    id TEXT PRIMARY KEY,  -- UUID
    user_id TEXT NOT NULL UNIQUE,
    content TEXT,  -- Markdown形式
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- インデックス
CREATE INDEX idx_user_dashboards_user_id ON user_dashboards(user_id);
```

### 6. audit_logs テーブル

監査ログを保存します。

```sql
CREATE TABLE audit_logs (
    id TEXT PRIMARY KEY,  -- UUID
    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    action TEXT NOT NULL,
    actor_type TEXT NOT NULL CHECK (actor_type IN ('user', 'admin', 'system')),
    actor_id TEXT,
    actor_email TEXT,
    target_type TEXT,
    target_id TEXT,
    ip_address TEXT,
    user_agent TEXT,
    details TEXT,  -- JSON形式の文字列
    FOREIGN KEY (actor_id) REFERENCES users(id) ON DELETE SET NULL
);

-- インデックス
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_actor_id ON audit_logs(actor_id);
CREATE INDEX idx_audit_logs_target_id ON audit_logs(target_id);
```

### 7. system_settings テーブル

システム設定を保存します。

```sql
CREATE TABLE system_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,  -- JSON形式の文字列
    description TEXT,
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_by TEXT,
    FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL
);

-- 初期データ
INSERT INTO system_settings (key, value, description) VALUES
    ('security.fail_lock_threshold', '5', '認証失敗回数の閾値'),
    ('security.fail_lock_window_hours', '2', '認証失敗カウントのウィンドウ時間（時間）'),
    ('security.fail_lock_duration_hours', '6', 'ロック期間（時間）'),
    ('security.otp_expiration_minutes', '10', 'OTPの有効期限（分）'),
    ('security.session_duration_hours', '24', 'セッションの有効期限（時間）'),
    ('security.rate_limit_per_minute', '10', '1分あたりのレート制限');
```

### 8. sessions テーブル（セッション管理）

**デフォルト構成ではSQLite3でセッションを管理します。**

```sql
CREATE TABLE sessions (
    session_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    email TEXT NOT NULL,
    role TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    expires_at TEXT NOT NULL,  -- セッション有効期限（24時間後）
    ip_address TEXT,
    user_agent TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- インデックス
CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_expires_at ON sessions(expires_at);
```

#### 期限切れセッションの削除

定期的に実行（1時間ごと）：
```sql
DELETE FROM sessions WHERE expires_at < datetime('now');
```

### 9. otps テーブル（OTP管理）

**デフォルト構成ではSQLite3でOTPを管理します。**

```sql
CREATE TABLE otps (
    user_id TEXT PRIMARY KEY,
    otp TEXT NOT NULL,
    attempts INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    expires_at TEXT NOT NULL,  -- OTP有効期限（10分後）
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- インデックス
CREATE INDEX idx_otps_expires_at ON otps(expires_at);
```

#### 期限切れOTPの削除

定期的に実行（10分ごと）：
```sql
DELETE FROM otps WHERE expires_at < datetime('now');
```

### 10. fail_locks テーブル（fail lock管理）

**デフォルト構成ではSQLite3でfail lockを管理します。**

```sql
CREATE TABLE fail_locks (
    user_id TEXT PRIMARY KEY,
    failed_attempts TEXT NOT NULL,  -- JSON配列 ["2025-10-23T14:30:00Z", ...]
    locked_until TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- インデックス
CREATE INDEX idx_fail_locks_locked_until ON fail_locks(locked_until);
```

#### 期限切れロックの削除

定期的に実行（1時間ごと）：
```sql
DELETE FROM fail_locks WHERE locked_until < datetime('now');
```

---

## Redis データ構造（オプション）

**大規模環境（500+同時ユーザー）では、パフォーマンス向上のためRedisの使用を推奨します。**

### Redis使用時のメリット
- ✅ auth_requestが超高速（1-5ms）
- ✅ TTL自動管理（期限切れデータが自動削除）
- ✅ セッション書き込みの並行性向上

### Redis使用時のデメリット
- ❌ Redisサーバーの運用が必要
- ❌ 学習コスト（Redis知識）
- ❌ Docker構成が複雑化

### 実装の選択
- **小〜中規模（〜500ユーザー）**: SQLite3のみ
- **大規模（500+ユーザー）**: SQLite3 + Redis

---

## Redisデータ構造（オプション使用時）

### 1. セッション情報

```
キー: session:{session_id}
TTL: 24時間（セッション有効期限）
値（JSON）:
{
  "user_id": "user_123",
  "email": "user@example.com",
  "role": "user",
  "login_at": "2025-10-23T14:30:00Z",
  "expires_at": "2025-10-24T14:30:00Z",
  "ip_address": "192.168.1.1",
  "user_agent": "Mozilla/5.0..."
}
```

### 2. OTP（ワンタイムパスワード）

```
キー: otp:{user_id}
TTL: 10分
値（JSON）:
{
  "otp": "123456",
  "created_at": "2025-10-23T14:30:00Z",
  "attempts": 0
}
```

### 3. fail lock

```
キー: fail_lock:{user_id}
TTL: ロック期間 + 2時間
値（JSON）:
{
  "failed_attempts": [
    "2025-10-23T14:30:00Z",
    "2025-10-23T14:35:00Z",
    "2025-10-23T14:40:00Z"
  ],
  "locked_until": "2025-10-23T20:30:00Z"
}
```

### 4. レート制限

```
キー: rate_limit:{ip_address}:{endpoint}
TTL: 60秒
値: リクエスト回数（整数）
```

### 5. CSRFトークン

```
キー: csrf:{session_id}
TTL: セッション有効期限と同じ
値: CSRFトークン（ランダムな文字列）
```

### 6. ユーザーキャッシュ（オプション）

頻繁にアクセスされるユーザー情報をキャッシュします。

```
キー: user_cache:{user_id}
TTL: 5分
値（JSON）:
{
  "user_id": "user_123",
  "email": "user@example.com",
  "role": "user",
  "locked": false
}
```

## データベース関係図

```
users (1) ----< (*) login_history
  |
  +----< (*) notifications (target_user_id)
  |
  +----< (*) notification_reads
  |
  +----< (1) user_dashboards
  |
  +----< (*) audit_logs (actor_id)
  |
  +----< (*) system_settings (updated_by)

notifications (1) ----< (*) notification_reads
```

## マイグレーション戦略

### 初回セットアップ

SQLite3はファイルベースなので、データベースファイルを作成するだけです。

```bash
# データベースファイルを作成
touch simple_auth.db

# スキーマを適用
sqlite3 simple_auth.db < migrations/001_initial_schema.sql
```

### マイグレーションツール

- **golang-migrate** を使用（SQLite3対応）
- マイグレーションファイルは `migrations/` ディレクトリに配置

```
migrations/
  000001_create_users_table.up.sql
  000001_create_users_table.down.sql
  000002_create_login_history_table.up.sql
  000002_create_login_history_table.down.sql
  ...
```

### マイグレーション実行

```bash
# アップ（最新まで適用）
migrate -path ./migrations -database "sqlite3://simple_auth.db" up

# ダウン（1つ戻す）
migrate -path ./migrations -database "sqlite3://simple_auth.db" down 1
```

### ロールバック

各マイグレーションに対応する `down.sql` を用意し、ロールバック可能にします。

## バックアップとリストア

### バックアップスクリプト

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)

# SQLite3データベースをバックアップ
cp simple_auth.db backups/simple_auth_${DATE}.db

# 圧縮（オプション）
gzip backups/simple_auth_${DATE}.db
```

### オンラインバックアップ（推奨）

SQLite3の `.backup` コマンドを使用すると、データベースをロックせずにバックアップできます。

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
sqlite3 simple_auth.db ".backup backups/simple_auth_${DATE}.db"
gzip backups/simple_auth_${DATE}.db
```

### リストアスクリプト

```bash
#!/bin/bash
# バックアップファイルを解凍
gunzip -c backups/simple_auth_20251023_143000.db.gz > simple_auth.db
```

### Redisのバックアップ

- RDB または AOF を使用
- 定期的にスナップショットを保存

```bash
# Redisのスナップショットを保存
redis-cli SAVE
cp /var/lib/redis/dump.rdb backups/redis_${DATE}.rdb
```

## パフォーマンス最適化

### 1. インデックス戦略

- 頻繁に検索されるカラムにインデックスを作成
- 複合インデックスの検討（例: `(user_id, login_at)`）

```sql
-- 複合インデックスの例
CREATE INDEX idx_login_history_user_date ON login_history(user_id, login_at DESC);
```

### 2. VACUUM

SQLite3では、削除したデータの領域を再利用するために定期的にVACUUMを実行します。

```sql
-- 手動VACUUM
VACUUM;

-- 自動VACUUM を有効化（データベース作成時）
PRAGMA auto_vacuum = FULL;
```

### 3. WAL（Write-Ahead Logging）モード

並行読み取りのパフォーマンスを向上させるため、WALモードを有効にします。

```sql
-- WALモードを有効化
PRAGMA journal_mode = WAL;
```

WALモードのメリット:
- 読み取りと書き込みがブロックしない
- 書き込みが高速化
- クラッシュ回復が容易

### 4. その他の最適化

```sql
-- キャッシュサイズを増やす（デフォルトは2000ページ、1ページ=4KB）
PRAGMA cache_size = -64000;  -- 64MBのキャッシュ

-- 外部キー制約を有効化
PRAGMA foreign_keys = ON;

-- 同期モードを調整（パフォーマンス重視の場合）
PRAGMA synchronous = NORMAL;  -- デフォルトはFULL
```

## データ保持ポリシー

### login_history
- 保持期間: 2年
- 2年以上前のデータは削除

```sql
-- 古いログイン履歴を削除（定期実行）
DELETE FROM login_history
WHERE login_at < datetime('now', '-2 years');
```

### audit_logs
- 保持期間: 5年（法令遵守のため）
- 古いデータはアーカイブ（別のSQLiteファイルへエクスポート）

```bash
# 古いログをエクスポート
sqlite3 simple_auth.db "
  SELECT * FROM audit_logs
  WHERE timestamp < datetime('now', '-5 years')
" | sqlite3 archive_$(date +%Y).db
```

### notifications
- 有効期限（expires_at）を過ぎた通知は削除
- 未設定の場合は作成から1年後に削除

```sql
-- 期限切れの通知を削除
DELETE FROM notifications
WHERE expires_at < datetime('now')
   OR (expires_at IS NULL AND created_at < datetime('now', '-1 year'));
```

## データ整合性

### 外部キー制約

SQLite3では、デフォルトで外部キー制約が無効です。アプリケーション起動時に有効化します。

```sql
PRAGMA foreign_keys = ON;
```

### トランザクション

複数のテーブルを更新する場合は、トランザクションを使用します。

```sql
BEGIN TRANSACTION;

-- 複数のSQL文
INSERT INTO users ...;
INSERT INTO audit_logs ...;

COMMIT;
```

## モニタリング

### メトリクス

- データベースファイルサイズ
- クエリ実行時間（アプリケーション側でログ）
- テーブルの行数

```bash
# データベースファイルサイズを確認
ls -lh simple_auth.db

# テーブルの行数を確認
sqlite3 simple_auth.db "SELECT COUNT(*) FROM users;"
```

### クエリの最適化

```sql
-- EXPLAIN QUERY PLAN でクエリの実行計画を確認
EXPLAIN QUERY PLAN
SELECT * FROM login_history WHERE user_id = 'user_123' ORDER BY login_at DESC;
```

### ツール

- **DB Browser for SQLite** - GUIでデータベースを管理
- **sqlite-web** - Web UIでデータベースを管理
- **Prometheus + Grafana** - アプリケーションメトリクスを可視化

## セキュリティ

### 1. ファイルパーミッション

データベースファイルのパーミッションを適切に設定します。

```bash
# データベースファイルの所有者とパーミッションを設定
chown app_user:app_group simple_auth.db
chmod 600 simple_auth.db  # 所有者のみ読み書き可能
```

### 2. バックアップの暗号化

バックアップファイルは暗号化して保存します。

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)

# バックアップして暗号化
sqlite3 simple_auth.db ".backup backups/simple_auth_${DATE}.db"
gpg --encrypt --recipient admin@example.com backups/simple_auth_${DATE}.db
rm backups/simple_auth_${DATE}.db  # 平文のバックアップを削除
```

### 3. データベース暗号化（オプション）

SQLite3のデータベース全体を暗号化する場合は、**SQLCipher** を使用します。

```go
import _ "github.com/mutecomm/go-sqlcipher/v4"

db, err := sql.Open("sqlite3", "file:simple_auth.db?_key=your_encryption_key")
```

## UUID生成

SQLite3にはUUID生成機能がないため、アプリケーション側で生成します。

```go
import "github.com/google/uuid"

// UUIDを生成
id := uuid.New().String()
```

## JSON操作

SQLite3はJSON関数をサポートしているため、`details` カラムのJSON操作が可能です。

```sql
-- JSONから値を取得
SELECT json_extract(details, '$.user_agent') FROM audit_logs;

-- JSONで検索
SELECT * FROM audit_logs
WHERE json_extract(details, '$.action') = 'login_success';
```

## まとめ

SQLite3は以下の特徴を持つため、この認証サーバーに最適です：

✅ **シンプル**: サーバー不要、ファイルベース
✅ **軽量**: 依存関係が少ない
✅ **高速**: 小〜中規模なら十分なパフォーマンス
✅ **バックアップが簡単**: ファイルコピーだけ
✅ **デプロイが簡単**: 実行ファイルとDBファイルだけ

並行書き込みの制限はありますが、認証サーバーは読み取りが多く、書き込みは少ないため問題になりません。
