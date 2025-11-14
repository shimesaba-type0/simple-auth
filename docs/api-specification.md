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

### 1. ユーザー登録（招待制）

```
POST /api/auth/register
```

#### リクエスト
```json
{
  "invitation_token": "abc123def456ghi789jkl012",
  "email": "user@example.com"
}
```

#### レスポンス（成功）
```json
{
  "success": true,
  "data": {
    "user_id": "user_123",
    "email": "user@example.com",
    "passphrase": "a3K9pL2qR8sT4vX7yZ1bC5dF6gH9jM2nP4rS8tV1wX3zA6bD9eG2hJ5kN7mQ1rT9v"
  },
  "message": "アカウントが作成されました。パスフレーズを保存してください。"
}
```

⚠️ **重要**: パスフレーズは登録時に1回だけ表示されます。必ずパスワードマネージャーに保存してください。

#### レスポンス（エラー）
```json
{
  "success": false,
  "error": "invalid_invitation",
  "message": "招待リンクが無効です"
}
```

#### エラーコード
- `invalid_invitation`: トークンが存在しない
- `invitation_expired`: 招待リンクの有効期限切れ
- `invitation_exhausted`: 使用回数上限に達している
- `invitation_revoked`: 招待リンクが無効化されている
- `email_already_exists`: メールアドレスが既に登録されている

### 2. パスフレーズ認証（第1段階）

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

### 3. OTP認証（第2段階）

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

### 4. セッション検証（nginx auth_request用）

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

### 5. ログアウト

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

### 6. 現在のユーザー情報取得

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

### 18. 招待リンク作成

```
POST /api/admin/invitations
```

#### リクエスト
```json
{
  "max_uses": 10,
  "expires_in_days": 7,
  "description": "2025年10月新入社員"
}
```

#### パラメータ
- `max_uses`: 最大使用回数（デフォルト: 1）
- `expires_in_days`: 有効期限（日数、デフォルト: 7）
- `description`: 招待リンクの説明（オプション）

#### レスポンス
```json
{
  "success": true,
  "data": {
    "token": "abc123def456ghi789jkl012",
    "invitation_url": "https://auth.example.com/invite?token=abc123def456ghi789jkl012",
    "max_uses": 10,
    "used_count": 0,
    "expires_at": "2025-10-30T14:30:00Z",
    "description": "2025年10月新入社員"
  },
  "message": "招待リンクを作成しました"
}
```

### 19. 招待リンク一覧取得

```
GET /api/admin/invitations?limit=50&offset=0&status=all
```

#### パラメータ
- `limit`: 取得件数（最大100、デフォルト: 50）
- `offset`: オフセット（デフォルト: 0）
- `status`: `all` | `active` | `expired` | `exhausted` | `revoked` (デフォルト: `all`)

#### レスポンス
```json
{
  "success": true,
  "data": {
    "total": 25,
    "invitations": [
      {
        "token": "abc123def456ghi789jkl012",
        "invitation_url": "https://auth.example.com/invite?token=abc123def456ghi789jkl012",
        "max_uses": 10,
        "used_count": 3,
        "description": "2025年10月新入社員",
        "created_by_email": "admin@example.com",
        "created_at": "2025-10-23T14:30:00Z",
        "expires_at": "2025-10-30T14:30:00Z",
        "revoked": false,
        "status": "active"
      },
      {
        "token": "xyz789abc456def123ghi012",
        "invitation_url": "https://auth.example.com/invite?token=xyz789abc456def123ghi012",
        "max_uses": 5,
        "used_count": 5,
        "description": "マーケティングチーム",
        "created_by_email": "admin@example.com",
        "created_at": "2025-10-20T10:00:00Z",
        "expires_at": "2025-10-27T10:00:00Z",
        "revoked": false,
        "status": "exhausted"
      }
    ]
  }
}
```

#### ステータス説明
- `active`: 有効で使用可能
- `expired`: 有効期限切れ
- `exhausted`: 使用回数上限に達した
- `revoked`: 管理者によって無効化された

### 20. 招待リンク詳細取得

```
GET /api/admin/invitations/:token
```

#### レスポンス
```json
{
  "success": true,
  "data": {
    "token": "abc123def456ghi789jkl012",
    "invitation_url": "https://auth.example.com/invite?token=abc123def456ghi789jkl012",
    "max_uses": 10,
    "used_count": 3,
    "description": "2025年10月新入社員",
    "created_by": "admin_123",
    "created_by_email": "admin@example.com",
    "created_at": "2025-10-23T14:30:00Z",
    "expires_at": "2025-10-30T14:30:00Z",
    "revoked": false,
    "revoked_at": null,
    "revoked_by": null,
    "status": "active",
    "recent_uses": [
      {
        "user_id": "user_123",
        "email": "user1@example.com",
        "used_at": "2025-10-23T15:00:00Z"
      },
      {
        "user_id": "user_124",
        "email": "user2@example.com",
        "used_at": "2025-10-24T09:30:00Z"
      }
    ]
  }
}
```

### 21. 招待リンク無効化

```
POST /api/admin/invitations/:token/revoke
```

#### リクエスト
```json
{
  "reason": "不要になったため"
}
```

#### レスポンス
```json
{
  "success": true,
  "message": "招待リンクを無効化しました"
}
```

### 22. 招待リンクからの登録ユーザー一覧

```
GET /api/admin/invitations/:token/users?limit=50&offset=0
```

#### パラメータ
- `limit`: 取得件数（最大100、デフォルト: 50）
- `offset`: オフセット（デフォルト: 0）

#### レスポンス
```json
{
  "success": true,
  "data": {
    "total": 3,
    "users": [
      {
        "user_id": "user_123",
        "email": "user1@example.com",
        "display_name": "User 1",
        "registered_at": "2025-10-23T15:00:00Z",
        "last_login": "2025-10-24T10:00:00Z",
        "status": "active"
      },
      {
        "user_id": "user_124",
        "email": "user2@example.com",
        "display_name": "User 2",
        "registered_at": "2025-10-24T09:30:00Z",
        "last_login": "2025-10-24T11:00:00Z",
        "status": "active"
      }
    ]
  }
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
