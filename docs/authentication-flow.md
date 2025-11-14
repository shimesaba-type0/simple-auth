# 認証フロー

## 概要

2段階認証を採用し、事前共有パスフレーズとメールOTPで多段認証を実現します。

### ユーザー登録方式

**招待制**を採用しています。管理者が発行した招待リンクからのみユーザー登録が可能です。

- 管理者が招待リンクを作成
- 招待リンクは複数回使用可能（上限設定可能）
- ユーザーは招待リンクから登録し、パスフレーズを取得

## ユーザー登録フロー

```
[管理者] 招待リンク作成
    ↓
POST /api/admin/invitations
{
  "max_uses": 10,
  "expires_in_days": 7,
  "description": "2025年10月新入社員"
}
    ↓
[招待リンク生成]
https://auth.example.com/invite?token=xxx
    ↓
[管理者] ユーザーにリンクを共有（メール/Slack等）
    ↓
[ユーザー] 招待リンクにアクセス
    ↓
GET /invite?token=xxx
    ↓
[登録画面表示]
 - メールアドレス入力フォーム
    ↓
POST /api/auth/register
{
  "invitation_token": "xxx",
  "email": "user@example.com"
}
    ↓
[サーバー側処理]
 1. 招待トークン検証（有効期限、使用回数チェック）
 2. メールアドレス重複チェック
 3. パスフレーズ生成（64文字以上、英数字のみ）
 4. ユーザー作成（Argon2idでハッシュ化）
 5. 招待使用カウントをインクリメント
    ↓
[パスフレーズ表示画面]
「このパスフレーズをパスワードマネージャーに保存してください」
⚠️ 二度と表示されません
[コピー] ボタン
    ↓
[ユーザー] パスワードマネージャーに保存
    ↓
完了！
```

### パスフレーズ仕様

- **長さ**: 64文字以上
- **文字種**: 英数字のみ（A-Za-z0-9）
- **生成**: 暗号学的に安全な乱数生成器（crypto/rand）
- **保存**: Argon2idでハッシュ化
- **表示**: 登録時に1回だけ表示（再表示不可）

### 登録APIエンドポイント

```
POST /api/auth/register
```

#### リクエスト
```json
{
  "invitation_token": "abc123def456",
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

#### レスポンス（エラー）
```json
{
  "success": false,
  "error": "invalid_invitation",
  "message": "招待リンクが無効です"
}
```

#### エラーケース
- `invalid_invitation`: トークンが存在しない
- `invitation_expired`: 招待リンクの有効期限切れ
- `invitation_exhausted`: 使用回数上限に達している
- `email_already_exists`: メールアドレスが既に登録されている

## 認証フロー図

```
[ユーザー]
    ↓
[ログインページ (/login)]
    ↓
[第1段階: 事前共有パスフレーズ入力]
 - 64文字以上の事前共有パスフレーズを入力
    ↓
[サーバー側検証]
 - パスフレーズの検証（ハッシュ比較）
 - fail lockチェック
    ↓ (成功)
[OTP送信]
 - メールアドレスにOTPを送信
 - OTPは6桁の数字（有効期限: 10分）
    ↓
[第2段階: OTP入力画面]
 - メールで受信したOTPを入力
    ↓
[サーバー側検証]
 - OTPの検証
 - 有効期限チェック
    ↓ (成功)
[セッション確立]
 - セッションCookie発行（HttpOnly, Secure, SameSite=Lax）
 - データベースにセッション情報を保存（SQLite3 または Redis）
    ↓
[ダッシュボードへリダイレクト]
 または
[元のリクエスト先へリダイレクト（auth_request経由の場合）]
```

## 第1段階: 事前共有パスフレーズ認証

### エンドポイント
```
POST /api/auth/login/passphrase
```

### リクエスト
```json
{
  "passphrase": "64文字の事前共有パスフレーズ"
}
```

### レスポンス（成功）
```json
{
  "success": true,
  "next_step": "otp",
  "message": "OTPをメールアドレスに送信しました"
}
```

### レスポンス（失敗）
```json
{
  "success": false,
  "error": "invalid_passphrase",
  "message": "パスフレーズが正しくありません",
  "remaining_attempts": 3
}
```

### 処理内容

1. パスフレーズの検証
   - データベースからユーザー情報を取得
   - Argon2idでハッシュ化されたパスフレーズと比較

2. fail lockチェック
   - 2時間以内に5回失敗していないかチェック
   - ロック中の場合はエラーを返す

3. 失敗カウント
   - 失敗した場合、失敗回数をインクリメント
   - 5回目の失敗で6時間のロック

4. OTP生成と送信
   - 6桁のランダムなOTPを生成
   - データベース（SQLite3）に保存（有効期限: 10分）
     ```sql
     INSERT OR REPLACE INTO otps (user_id, otp, expires_at)
     VALUES (?, ?, datetime('now', '+10 minutes'));
     ```
   - ※大規模環境ではRedisでTTL自動管理も可能
   - メール送信

## 第2段階: OTP認証

### エンドポイント
```
POST /api/auth/login/otp
```

### リクエスト
```json
{
  "otp": "123456"
}
```

### レスポンス（成功）
```json
{
  "success": true,
  "message": "認証が完了しました",
  "redirect_url": "/dashboard"
}
```

### レスポンス（失敗）
```json
{
  "success": false,
  "error": "invalid_otp",
  "message": "OTPが正しくありません"
}
```

### 処理内容

1. OTPの検証
   - データベース（SQLite3）から保存されたOTPを取得
   - 入力されたOTPと比較
   - 有効期限チェック
   - ※大規模環境ではRedisを使用可能

2. セッション確立
   - ランダムなセッションIDを生成
   - データベース（SQLite3）にセッション情報を保存
     ```sql
     INSERT INTO sessions (session_id, user_id, email, role, expires_at, ip_address, user_agent)
     VALUES (?, ?, ?, ?, datetime('now', '+24 hours'), ?, ?);
     ```
   - ※大規模環境ではRedisでセッション管理も可能
   - セッションCookieを発行
     - 名前: `auth_session`
     - HttpOnly: true
     - Secure: true（HTTPS必須）
     - SameSite: Lax
     - Max-Age: 86400（24時間）

3. 監査ログ記録
   - ログインに成功したことをデータベースに記録

4. リダイレクト
   - auth_request経由の場合: 元のURL
   - 通常ログインの場合: ダッシュボード

## nginx auth_request からの認証

### フロー

```
[nginx]
    ↓
[auth_request /auth/verify]
    ↓
[認証サーバー: GET /api/auth/verify]
 - セッションCookieをチェック
 - データベースからセッション情報を取得（SQLite3 または Redis）
    ↓
[認証済み?]
 Yes → 200 OK（nginxがリクエストを通す）
 No  → 401 Unauthorized + リダイレクト先ヘッダー
    ↓
[nginx が 302 リダイレクト]
 /login?redirect=/protected/resource
```

### エンドポイント
```
GET /api/auth/verify
```

### レスポンス（認証済み）
```
HTTP/1.1 200 OK
X-Auth-User: user@example.com
X-Auth-Role: user
```

### レスポンス（未認証）
```
HTTP/1.1 401 Unauthorized
X-Auth-Redirect: /login?redirect=/protected/resource
```

## ログアウト

### エンドポイント
```
POST /api/auth/logout
```

### 処理内容

1. セッションCookieから セッションID を取得
2. データベースからセッション情報を削除（SQLite3 または Redis）
   ```sql
   DELETE FROM sessions WHERE session_id = ?;
   ```
3. セッションCookieを削除（Max-Age=0）
4. ログアウトを監査ログに記録

## セキュリティ考慮事項

- **CSRF対策**: ログインフローではCSRFトークン不要（Cookieを使わない認証開始）、ログアウトはCSRFトークン必須
- **レート制限**: IPアドレスごとに1分間に10回までのリクエスト制限
- **fail lock**: ユーザーごとに2時間で5回失敗したら6時間ロック
- **セッション固定攻撃対策**: ログイン成功時に必ず新しいセッションIDを発行
- **監査ログ**: すべての認証試行を記録（成功・失敗・ロック）
