# API 仕様

## 概要

RESTful API として設計します。すべてのエンドポイントは `/api` プレフィックスを持ちます。

## 共通仕様

### ベースURL

```
https://auth.example.com/api
```

### リクエストヘッダー

```
Content-Type: application/json
X-CSRF-Token: {csrf_token}  # POST/PUT/DELETE時のみ必須（ログイン除く）
```

### レスポンス形式

#### 成功時
```json
{
  "success": true,
  "data": { ... },
  "message": "操作が成功しました"
}
```

#### エラー時
```json
{
  "success": false,
  "error": "error_code",
  "message": "エラーメッセージ",
  "details": { ... }  // オプション
}
```

### HTTPステータスコード

- `200 OK`: 成功
- `201 Created`: リソース作成成功
- `400 Bad Request`: リクエストが不正
- `401 Unauthorized`: 未認証
- `403 Forbidden`: 権限なし
- `404 Not Found`: リソースが見つからない
- `429 Too Many Requests`: レート制限超過
- `500 Internal Server Error`: サーバーエラー

### エラーコード

- `invalid_request`: リクエストが不正
- `invalid_passphrase`: パスフレーズが間違っている
- `invalid_otp`: OTPが間違っている
- `user_locked`: ユーザーがロックされている
- `user_not_found`: ユーザーが見つからない
- `rate_limit_exceeded`: レート制限超過
- `csrf_token_invalid`: CSRFトークンが無効
- `session_expired`: セッションの有効期限切れ
- `unauthorized`: 未認証
- `forbidden`: 権限なし
- `internal_error`: サーバー内部エラー

## 認証API

### 1. パスフレーズ認証（第1段階）

```
POST /api/auth/login/passphrase
```

#### リクエスト
```json
{
  "passphrase": "64文字の事前共有パスフレーズ"
}
```

#### レスポンス（成功）
```json
{
  "success": true,
  "next_step": "otp",
  "message": "OTPをメールアドレスに送信しました"
}
```

#### レスポンス（失敗）
```json
{
  "success": false,
  "error": "invalid_passphrase",
  "message": "パスフレーズが正しくありません",
  "remaining_attempts": 3
}
```

#### レスポンス（ロック中）
```json
{
  "success": false,
  "error": "user_locked",
  "message": "アカウントがロックされています",
  "locked_until": "2025-10-23T20:30:00Z"
}
```

### 2. OTP認証（第2段階）

```
POST /api/auth/login/otp
```

#### リクエスト
```json
{
  "otp": "123456"
}
```

#### レスポンス（成功）
```json
{
  "success": true,
  "message": "認証が完了しました",
  "redirect_url": "/dashboard",
  "csrf_token": "random_csrf_token_here"
}
```

- Cookie: `auth_session`, `csrf_token` が設定される

#### レスポンス（失敗）
```json
{
  "success": false,
  "error": "invalid_otp",
  "message": "OTPが正しくありません",
  "remaining_attempts": 3
}
```

### 3. セッション検証（nginx auth_request用）

```
GET /api/auth/verify
```

#### レスポンス（認証済み）
```
HTTP/1.1 200 OK
X-Auth-User: user@example.com
X-Auth-Role: user
X-Auth-User-ID: user_123
```

#### レスポンス（未認証）
```
HTTP/1.1 401 Unauthorized
X-Auth-Redirect: /login?redirect=/protected/resource
```

### 4. ログアウト

```
POST /api/auth/logout
```

#### レスポンス
```json
{
  "success": true,
  "message": "ログアウトしました"
}
```

### 5. 現在のユーザー情報取得

```
GET /api/auth/me
```

#### レスポンス
```json
{
  "success": true,
  "data": {
    "user_id": "user_123",
    "email": "user@example.com",
    "display_name": "User Name",
    "role": "user"
  }
}
```

## ユーザーAPI

### 1. プロフィール取得

```
GET /api/user/profile
```

#### レスポンス
```json
{
  "success": true,
  "data": {
    "user_id": "user_123",
    "email": "user@example.com",
    "display_name": "User Name",
    "created_at": "2025-01-01T00:00:00Z",
    "last_login": "2025-10-23T14:30:00Z"
  }
}
```

### 2. プロフィール更新

```
PUT /api/user/profile
```

#### リクエスト
```json
{
  "display_name": "New Display Name"
}
```

#### レスポンス
```json
{
  "success": true,
  "message": "プロフィールを更新しました"
}
```

### 3. ダッシュボード取得

```
GET /api/user/dashboard
```

#### レスポンス
```json
{
  "success": true,
  "data": {
    "content": "# My Dashboard\n\n## Links\n..."
  }
}
```

### 4. ダッシュボード更新

```
PUT /api/user/dashboard
```

#### リクエスト
```json
{
  "content": "# My Dashboard\n\n## Updated content..."
}
```

#### レスポンス
```json
{
  "success": true,
  "message": "ダッシュボードを更新しました"
}
```

### 5. 通知一覧取得

```
GET /api/user/notifications?type=admin&unread_only=false&limit=20&offset=0
```

#### パラメータ
- `type`: `admin` | `personal` | `all` (デフォルト: `all`)
- `unread_only`: `true` | `false` (デフォルト: `false`)
- `limit`: 取得件数（最大100、デフォルト: 20）
- `offset`: オフセット（デフォルト: 0）

#### レスポンス
```json
{
  "success": true,
  "data": {
    "total": 50,
    "notifications": [
      {
        "id": "notif_123",
        "type": "admin",
        "title": "システムメンテナンスのお知らせ",
        "content": "2025年10月25日 02:00-04:00 にメンテナンスを実施します",
        "priority": "high",
        "created_at": "2025-10-23T10:00:00Z",
        "read": false
      }
    ]
  }
}
```

### 6. 通知を既読にする

```
POST /api/user/notifications/:id/read
```

#### レスポンス
```json
{
  "success": true,
  "message": "通知を既読にしました"
}
```

### 7. ログイン履歴取得

```
GET /api/user/login-history?limit=50&offset=0
```

#### パラメータ
- `limit`: 取得件数（最大100、デフォルト: 50）
- `offset`: オフセット（デフォルト: 0）

#### レスポンス
```json
{
  "success": true,
  "data": {
    "total": 250,
    "login_history": [
      {
        "id": "log_123",
        "login_at": "2025-10-23T14:30:00Z",
        "ip_address": "192.168.1.1",
        "user_agent": "Mozilla/5.0 ...",
        "result": "success",
        "logout_at": null
      }
    ]
  }
}
```

### 8. ロック状態確認

```
GET /api/user/lock-status
```

#### レスポンス（ロックされていない）
```json
{
  "success": true,
  "data": {
    "locked": false,
    "failed_attempts": 2,
    "remaining_attempts": 3
  }
}
```

#### レスポンス（ロックされている）
```json
{
  "success": true,
  "data": {
    "locked": true,
    "locked_until": "2025-10-23T20:30:00Z",
    "reason": "5回の認証失敗"
  }
}
```

## 管理者API

すべての管理者APIは `/api/admin` プレフィックスを持ちます。
権限チェック: `role = 'admin'` のみアクセス可能。

### 1. ユーザー一覧取得

```
GET /api/admin/users?limit=50&offset=0&search=&status=all
```

#### パラメータ
- `limit`: 取得件数（最大100、デフォルト: 50）
- `offset`: オフセット（デフォルト: 0）
- `search`: メールアドレスまたは表示名での検索（部分一致）
- `status`: `all` | `active` | `locked` (デフォルト: `all`)

#### レスポンス
```json
{
  "success": true,
  "data": {
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
}
```

### 2. ユーザー詳細取得

```
GET /api/admin/users/:user_id
```

#### レスポンス
```json
{
  "success": true,
  "data": {
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
}
```

### 3. ユーザー新規作成

```
POST /api/admin/users
```

#### リクエスト
```json
{
  "email": "newuser@example.com",
  "display_name": "New User",
  "role": "user",
  "passphrase": "optional_64_char_passphrase"
}
```

- `passphrase` が省略された場合、64文字のランダムな文字列を自動生成

#### レスポンス
```json
{
  "success": true,
  "data": {
    "user_id": "user_456",
    "email": "newuser@example.com",
    "passphrase": "generated_64_char_passphrase_here..."
  },
  "message": "ユーザーを作成しました。パスフレーズを安全に共有してください。"
}
```

### 4. ユーザーロック

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

### 5. ユーザーロック解除

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

### 6. ユーザー削除

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

### 7. パスフレーズリセット

```
POST /api/admin/users/:user_id/reset-passphrase
```

#### リクエスト
```json
{
  "passphrase": "optional_new_64_char_passphrase"
}
```

- `passphrase` が省略された場合、自動生成

#### レスポンス
```json
{
  "success": true,
  "data": {
    "passphrase": "new_generated_64_char_passphrase_here..."
  },
  "message": "パスフレーズをリセットしました"
}
```

### 8. 強制ログアウト

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

### 9. ユーザーのログイン履歴取得

```
GET /api/admin/users/:user_id/login-history?limit=100&offset=0
```

#### パラメータ
- `limit`: 取得件数（最大500、デフォルト: 100）
- `offset`: オフセット（デフォルト: 0）

#### レスポンス
```json
{
  "success": true,
  "data": {
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
      }
    ]
  }
}
```

### 10. ユーザー権限変更

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

### 11. 管理者通知作成（全ユーザー向け）

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
  "data": {
    "notification_id": "notif_456"
  },
  "message": "全ユーザーに通知を送信しました"
}
```

### 12. 個人通知送信（特定ユーザー向け）

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
  "data": {
    "notification_id": "notif_457"
  },
  "message": "通知を送信しました"
}
```

### 13. 通知削除

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

### 14. ダッシュボード統計取得

```
GET /api/admin/dashboard/stats
```

#### レスポンス
```json
{
  "success": true,
  "data": {
    "total_users": 150,
    "active_users_today": 85,
    "locked_users": 3,
    "failed_login_attempts_today": 12,
    "active_sessions": 42,
    "system_status": "healthy"
  }
}
```

### 15. 監査ログ取得

```
GET /api/admin/audit-logs?limit=100&offset=0&action=&user_id=
```

#### パラメータ
- `limit`: 取得件数（最大500、デフォルト: 100）
- `offset`: オフセット（デフォルト: 0）
- `action`: アクションでフィルタ（オプション）
- `user_id`: ユーザーIDでフィルタ（オプション）

#### レスポンス
```json
{
  "success": true,
  "data": {
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
      }
    ]
  }
}
```

### 16. セキュリティ設定取得

```
GET /api/admin/settings/security
```

#### レスポンス
```json
{
  "success": true,
  "data": {
    "fail_lock_threshold": 5,
    "fail_lock_window_hours": 2,
    "fail_lock_duration_hours": 6,
    "otp_expiration_minutes": 10,
    "session_duration_hours": 24,
    "rate_limit_per_minute": 10
  }
}
```

### 17. セキュリティ設定更新

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

#### レスポンス
```json
{
  "success": true,
  "message": "セキュリティ設定を更新しました"
}
```

## レート制限

### 制限値

- 認証エンドポイント（`/api/auth/login/*`）: 1分間に10回
- その他のエンドポイント: 1分間に60回
- 管理者API: 1分間に200回

### レート制限超過時のレスポンス

```
HTTP/1.1 429 Too Many Requests
Retry-After: 60

{
  "success": false,
  "error": "rate_limit_exceeded",
  "message": "リクエスト数が多すぎます。しばらくしてから再試行してください。",
  "retry_after": 60
}
```

## CORS設定

開発環境では、フロントエンドとバックエンドが異なるポートで動作する場合があるため、CORSを適切に設定します。

```
Access-Control-Allow-Origin: https://example.com
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type, X-CSRF-Token
Access-Control-Allow-Credentials: true
```

本番環境では、信頼されたオリジンのみ許可します。

## WebSocket（オプション）

リアルタイム通知のために WebSocket を使用する場合：

```
wss://auth.example.com/api/ws
```

### 認証

WebSocket接続時にセッションCookieで認証を行います。

### メッセージ形式

```json
{
  "type": "notification",
  "data": {
    "id": "notif_123",
    "title": "新しい通知",
    "content": "...",
    "priority": "high"
  }
}
```

## ヘルスチェック

```
GET /api/health
```

#### レスポンス
```json
{
  "status": "healthy",
  "timestamp": "2025-10-23T14:30:00Z",
  "services": {
    "database": "ok",
    "redis": "ok",
    "email": "ok"
  }
}
```
