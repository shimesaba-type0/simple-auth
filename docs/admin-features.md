# 管理者機能

## 概要

管理者が利用できる機能の詳細仕様です。

## 管理者の認証

管理者も一般ユーザーと同じ2段階認証を行います。
違いは、ユーザーの `role` フィールドが `admin` であることです。

## ダッシュボードの種類

管理者は2種類のダッシュボードにアクセスできます：

1. **管理者個人用ダッシュボード** (`/dashboard`)
   - 一般ユーザーと同じ機能
   - [一般ユーザー機能](./user-features.md) を参照

2. **ユーザー管理ダッシュボード** (`/admin`)
   - ユーザー管理機能
   - システム全体の監視

## 1. ユーザー管理

### 1.1 ユーザー一覧

#### エンドポイント
```
GET /api/admin/users?limit=50&offset=0&search=&status=all
```

#### パラメータ
- `limit`: 取得件数（最大100）
- `offset`: オフセット（ページネーション用）
- `search`: メールアドレスまたは表示名での検索
- `status`: `all` / `active` / `locked`

#### レスポンス
```json
{
  "total": 150,
  "users": [
    {
      "user_id": "user_123",
      "email": "user@example.com",
      "display_name": "User Name",
      "role": "user",
      "status": "active",
      "locked": false,
      "created_at": "2025-01-01T00:00:00Z",
      "last_login": "2025-10-23T14:30:00Z",
      "failed_login_count": 0
    }
  ]
}
```

### 1.2 ユーザー詳細

#### エンドポイント
```
GET /api/admin/users/:user_id
```

#### レスポンス
```json
{
  "user_id": "user_123",
  "email": "user@example.com",
  "display_name": "User Name",
  "role": "user",
  "status": "active",
  "locked": false,
  "locked_until": null,
  "created_at": "2025-01-01T00:00:00Z",
  "last_login": "2025-10-23T14:30:00Z",
  "failed_login_count": 0,
  "login_history_count": 250,
  "active_sessions": 2
}
```

### 1.3 ユーザー新規追加

#### エンドポイント
```
POST /api/admin/users
```

#### リクエスト
```json
{
  "email": "newuser@example.com",
  "display_name": "New User",
  "role": "user",
  "passphrase": "自動生成される64文字のランダムな文字列（または手動指定）"
}
```

#### レスポンス
```json
{
  "success": true,
  "user_id": "user_456",
  "email": "newuser@example.com",
  "passphrase": "generated_64_char_passphrase_here...",
  "message": "ユーザーを作成しました。パスフレーズを安全に共有してください。"
}
```

#### 処理内容
1. パスフレーズが指定されていない場合、64文字のランダムな文字列を生成
2. Argon2idでハッシュ化してデータベースに保存
3. 初回ログイン用のパスフレーズを返す（平文）
4. 管理者は、このパスフレーズを安全な方法で新規ユーザーに共有

### 1.4 ユーザーのロック

#### エンドポイント
```
POST /api/admin/users/:user_id/lock
```

#### リクエスト
```json
{
  "reason": "不正アクセスの疑い",
  "duration_hours": 24
}
```

#### レスポンス
```json
{
  "success": true,
  "message": "ユーザーをロックしました",
  "locked_until": "2025-10-24T14:30:00Z"
}
```

#### 処理内容
- ユーザーを指定時間ロック
- ロック理由を監査ログに記録
- すべてのアクティブセッションを無効化

### 1.5 ユーザーのロック解除

#### エンドポイント
```
POST /api/admin/users/:user_id/unlock
```

#### レスポンス
```json
{
  "success": true,
  "message": "ユーザーのロックを解除しました"
}
```

#### 処理内容
- fail lock を解除
- 失敗カウントをリセット
- ロック解除を監査ログに記録

### 1.6 ユーザーの削除

#### エンドポイント
```
DELETE /api/admin/users/:user_id
```

#### リクエスト
```json
{
  "confirm": true,
  "reason": "退職のため"
}
```

#### レスポンス
```json
{
  "success": true,
  "message": "ユーザーを削除しました"
}
```

#### 処理内容
- ユーザー情報を削除（論理削除 or 物理削除）
- すべてのアクティブセッションを無効化
- 削除理由を監査ログに記録
- ログイン履歴は保持（監査目的）

### 1.7 事前共有パスフレーズの変更

#### エンドポイント
```
POST /api/admin/users/:user_id/reset-passphrase
```

#### リクエスト
```json
{
  "passphrase": "新しい64文字のパスフレーズ（省略時は自動生成）"
}
```

#### レスポンス
```json
{
  "success": true,
  "passphrase": "new_generated_64_char_passphrase_here...",
  "message": "パスフレーズをリセットしました"
}
```

#### 処理内容
- 新しいパスフレーズを生成（または受け取る）
- Argon2idでハッシュ化してデータベースに保存
- すべてのアクティブセッションを無効化（再ログイン必須）
- パスフレーズ変更を監査ログに記録
- 平文のパスフレーズを返す（管理者が安全に共有）

### 1.8 強制ログアウト

#### エンドポイント
```
POST /api/admin/users/:user_id/force-logout
```

#### レスポンス
```json
{
  "success": true,
  "message": "ユーザーの全セッションを無効化しました",
  "sessions_terminated": 2
}
```

#### 処理内容
- ユーザーのすべてのアクティブセッションを削除
- 強制ログアウトを監査ログに記録

### 1.9 認証ログの確認

#### エンドポイント
```
GET /api/admin/users/:user_id/login-history?limit=100&offset=0
```

#### パラメータ
- `limit`: 取得件数（最大500）
- `offset`: オフセット

#### レスポンス
```json
{
  "total": 1250,
  "login_history": [
    {
      "id": "log_789",
      "user_id": "user_123",
      "email": "user@example.com",
      "login_at": "2025-10-23T14:30:00Z",
      "ip_address": "192.168.1.1",
      "user_agent": "Mozilla/5.0 ...",
      "result": "success",
      "logout_at": null,
      "logout_type": null
    },
    {
      "id": "log_788",
      "user_id": "user_123",
      "email": "user@example.com",
      "login_at": "2025-10-23T10:00:00Z",
      "ip_address": "192.168.1.1",
      "user_agent": "Mozilla/5.0 ...",
      "result": "failed",
      "failure_reason": "invalid_passphrase",
      "logout_at": null,
      "logout_type": null
    }
  ]
}
```

### 1.10 ユーザーの権限変更

#### エンドポイント
```
PUT /api/admin/users/:user_id/role
```

#### リクエスト
```json
{
  "role": "admin"
}
```

#### レスポンス
```json
{
  "success": true,
  "message": "ユーザーの権限を変更しました"
}
```

#### 処理内容
- `user` から `admin` へ、または `admin` から `user` へ変更
- 権限変更を監査ログに記録

## 2. 通知管理

### 2.1 管理者通知の作成（全ユーザー向け）

#### エンドポイント
```
POST /api/admin/notifications/broadcast
```

#### リクエスト
```json
{
  "title": "システムメンテナンスのお知らせ",
  "content": "2025年10月25日 02:00-04:00 にメンテナンスを実施します。",
  "priority": "high"
}
```

#### レスポンス
```json
{
  "success": true,
  "notification_id": "notif_456",
  "message": "全ユーザーに通知を送信しました"
}
```

### 2.2 個人通知の送信（特定ユーザー向け）

#### エンドポイント
```
POST /api/admin/notifications/personal
```

#### リクエスト
```json
{
  "user_id": "user_123",
  "title": "アカウントの確認",
  "content": "不審なアクティビティが検出されました。確認してください。",
  "priority": "high"
}
```

#### レスポンス
```json
{
  "success": true,
  "notification_id": "notif_457",
  "message": "通知を送信しました"
}
```

### 2.3 通知の削除

#### エンドポイント
```
DELETE /api/admin/notifications/:notification_id
```

#### レスポンス
```json
{
  "success": true,
  "message": "通知を削除しました"
}
```

## 3. システム監視

### 3.1 ダッシュボード概要

#### エンドポイント
```
GET /api/admin/dashboard/stats
```

#### レスポンス
```json
{
  "total_users": 150,
  "active_users_today": 85,
  "locked_users": 3,
  "failed_login_attempts_today": 12,
  "active_sessions": 42,
  "system_status": "healthy"
}
```

### 3.2 監査ログ

#### エンドポイント
```
GET /api/admin/audit-logs?limit=100&offset=0&action=&user_id=
```

#### パラメータ
- `limit`: 取得件数
- `offset`: オフセット
- `action`: アクションでフィルタ（`login`, `logout`, `lock`, `unlock`, `delete`, etc.）
- `user_id`: ユーザーIDでフィルタ

#### レスポンス
```json
{
  "total": 5000,
  "audit_logs": [
    {
      "id": "audit_999",
      "timestamp": "2025-10-23T14:30:00Z",
      "action": "login_success",
      "user_id": "user_123",
      "email": "user@example.com",
      "ip_address": "192.168.1.1",
      "details": {
        "user_agent": "Mozilla/5.0 ..."
      }
    },
    {
      "id": "audit_998",
      "timestamp": "2025-10-23T14:25:00Z",
      "action": "user_locked",
      "admin_id": "admin_1",
      "target_user_id": "user_456",
      "ip_address": "192.168.1.100",
      "details": {
        "reason": "不正アクセスの疑い",
        "duration_hours": 24
      }
    }
  ]
}
```

## 4. システム設定

### 4.1 セキュリティ設定

#### エンドポイント
```
GET /api/admin/settings/security
```

#### レスポンス
```json
{
  "fail_lock_threshold": 5,
  "fail_lock_window_hours": 2,
  "fail_lock_duration_hours": 6,
  "otp_expiration_minutes": 10,
  "session_duration_hours": 24,
  "rate_limit_per_minute": 10
}
```

#### 設定変更
```
PUT /api/admin/settings/security
```

#### リクエスト
```json
{
  "fail_lock_threshold": 3,
  "fail_lock_duration_hours": 12
}
```

## UI/UX 要件

### 管理画面のデザイン
- テーブルビューでユーザー一覧を表示
- 検索・フィルタ・ソート機能
- 一括操作（複数ユーザーの選択とロック・削除など）
- リアルタイム更新（WebSocket or Polling）

### アクセス制御
- 管理者のみアクセス可能（`/admin/*`）
- 一般ユーザーがアクセスした場合は403エラー
