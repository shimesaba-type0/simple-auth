# データベース設計

## 概要

PostgreSQL をメインデータベース、Redis をセッション・キャッシュストアとして使用します。

## PostgreSQL スキーマ

### 1. users テーブル

ユーザー情報を保存します。

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    display_name VARCHAR(100),
    passphrase_hash TEXT NOT NULL,  -- Argon2idハッシュ
    role VARCHAR(20) NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'admin')),
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
    locked BOOLEAN NOT NULL DEFAULT false,
    locked_until TIMESTAMP WITH TIME ZONE,
    lock_reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_login_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE  -- 論理削除用
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
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,  -- 削除されたユーザーの履歴保持のため
    login_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    logout_at TIMESTAMP WITH TIME ZONE,
    logout_type VARCHAR(20) CHECK (logout_type IN ('user', 'admin_forced', 'session_expired')),
    ip_address INET NOT NULL,
    user_agent TEXT,
    result VARCHAR(20) NOT NULL CHECK (result IN ('success', 'failed')),
    failure_reason VARCHAR(50) CHECK (failure_reason IN (
        'invalid_passphrase',
        'invalid_otp',
        'locked',
        'user_not_found',
        'rate_limited'
    )),
    session_id VARCHAR(255)
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
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type VARCHAR(20) NOT NULL CHECK (type IN ('admin', 'personal', 'system')),
    target_user_id UUID REFERENCES users(id) ON DELETE CASCADE,  -- personalの場合のみ
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    priority VARCHAR(20) NOT NULL DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,  -- 作成した管理者
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE  -- 有効期限（オプション）
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
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    notification_id UUID NOT NULL REFERENCES notifications(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    read_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(notification_id, user_id)
);

-- インデックス
CREATE INDEX idx_notification_reads_user_id ON notification_reads(user_id);
CREATE INDEX idx_notification_reads_notification_id ON notification_reads(notification_id);
```

### 5. user_dashboards テーブル

ユーザーのダッシュボードカスタマイズ内容を保存します。

```sql
CREATE TABLE user_dashboards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    content TEXT,  -- Markdown形式
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- インデックス
CREATE INDEX idx_user_dashboards_user_id ON user_dashboards(user_id);
```

### 6. audit_logs テーブル

監査ログを保存します。

```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    action VARCHAR(50) NOT NULL,
    actor_type VARCHAR(20) NOT NULL CHECK (actor_type IN ('user', 'admin', 'system')),
    actor_id UUID REFERENCES users(id) ON DELETE SET NULL,
    actor_email VARCHAR(255),
    target_type VARCHAR(50),
    target_id UUID,
    ip_address INET,
    user_agent TEXT,
    details JSONB
);

-- インデックス
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_actor_id ON audit_logs(actor_id);
CREATE INDEX idx_audit_logs_target_id ON audit_logs(target_id);
CREATE INDEX idx_audit_logs_details ON audit_logs USING gin(details);  -- JSONBの検索用
```

### 7. system_settings テーブル

システム設定を保存します。

```sql
CREATE TABLE system_settings (
    key VARCHAR(100) PRIMARY KEY,
    value JSONB NOT NULL,
    description TEXT,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_by UUID REFERENCES users(id) ON DELETE SET NULL
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

## Redis データ構造

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

```sql
-- 1. データベース作成
CREATE DATABASE simple_auth;

-- 2. ユーザー作成
CREATE USER simple_auth_user WITH PASSWORD 'secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE simple_auth TO simple_auth_user;

-- 3. 拡張機能の有効化
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 4. テーブル作成（上記のCREATE TABLE文を実行）
```

### マイグレーションツール

- **golang-migrate** を使用
- マイグレーションファイルは `migrations/` ディレクトリに配置

```
migrations/
  000001_create_users_table.up.sql
  000001_create_users_table.down.sql
  000002_create_login_history_table.up.sql
  000002_create_login_history_table.down.sql
  ...
```

### ロールバック

各マイグレーションに対応する `down.sql` を用意し、ロールバック可能にします。

## バックアップとリストア

### バックアップスクリプト

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -U simple_auth_user -h localhost simple_auth | gzip > backup_${DATE}.sql.gz
```

### リストアスクリプト

```bash
#!/bin/bash
gunzip -c backup_20251023_143000.sql.gz | psql -U simple_auth_user -h localhost simple_auth
```

### Redisのバックアップ

- RDB または AOF を使用
- 定期的にスナップショットを保存

## パフォーマンス最適化

### 1. インデックス戦略

- 頻繁に検索されるカラムにインデックスを作成
- 複合インデックスの検討（例: `(user_id, login_at)`）

### 2. パーティショニング

大量のログデータに対して、テーブルパーティショニングを検討：

```sql
-- login_history を月ごとにパーティション
CREATE TABLE login_history (
    ...
) PARTITION BY RANGE (login_at);

CREATE TABLE login_history_2025_10 PARTITION OF login_history
    FOR VALUES FROM ('2025-10-01') TO ('2025-11-01');

CREATE TABLE login_history_2025_11 PARTITION OF login_history
    FOR VALUES FROM ('2025-11-01') TO ('2025-12-01');
```

### 3. 定期的なVACUUM

```sql
-- 自動VACUUM の設定
ALTER TABLE audit_logs SET (autovacuum_vacuum_scale_factor = 0.05);
```

### 4. コネクションプーリング

- **PgBouncer** または **pgpool-II** の使用を検討
- アプリケーション側でもコネクションプールを実装

## データ保持ポリシー

### login_history
- 保持期間: 2年
- 2年以上前のデータは削除またはアーカイブ

### audit_logs
- 保持期間: 5年（法令遵守のため）
- 古いデータはアーカイブストレージに移動

### notifications
- 有効期限（expires_at）を過ぎた通知は削除
- 未設定の場合は作成から1年後に削除

## セキュリティ

### 1. データベースユーザーの権限

```sql
-- アプリケーション用ユーザー（最小権限）
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO simple_auth_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO simple_auth_user;

-- 読み取り専用ユーザー（レポート用）
CREATE USER simple_auth_readonly WITH PASSWORD 'readonly_password';
GRANT SELECT ON ALL TABLES IN SCHEMA public TO simple_auth_readonly;
```

### 2. 行レベルセキュリティ（RLS）

```sql
-- 一般ユーザーは自分のデータのみアクセス可能
ALTER TABLE user_dashboards ENABLE ROW LEVEL SECURITY;

CREATE POLICY user_dashboards_policy ON user_dashboards
    FOR ALL
    TO simple_auth_user
    USING (user_id = current_setting('app.current_user_id')::uuid);
```

### 3. SSL/TLS接続

```
# postgresql.conf
ssl = on
ssl_cert_file = '/path/to/server.crt'
ssl_key_file = '/path/to/server.key'
```

```
# pg_hba.conf
hostssl all all 0.0.0.0/0 scram-sha-256
```

## モニタリング

### メトリクス

- 接続数
- クエリ実行時間
- スロークエリ
- テーブルサイズ
- インデックスの使用状況

### ツール

- **pg_stat_statements** 拡張機能
- **pgAdmin** または **pganalyze**
- Prometheus + Grafana
