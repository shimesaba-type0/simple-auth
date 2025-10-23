# 認証フロー

## 概要

2段階認証を採用し、事前共有パスフレーズとメールOTPで多段認証を実現します。

## 認証フロー図

```
[ユーザー]
    ↓
[ログインページ (/login)]
    ↓
[第1段階: 事前共有パスフレーズ入力]
 - 64文字の事前共有パスフレーズを入力
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
 - Redisにセッション情報を保存
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
   - Redisに保存（有効期限: 10分）
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
   - Redisから保存されたOTPを取得
   - 入力されたOTPと比較
   - 有効期限チェック

2. セッション確立
   - ランダムなセッションIDを生成
   - Redisにセッション情報を保存
     ```json
     {
       "user_id": "user_123",
       "email": "user@example.com",
       "role": "user",
       "login_at": "2025-10-23T14:30:00Z",
       "ip_address": "192.168.1.1",
       "user_agent": "Mozilla/5.0..."
     }
     ```
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
 - Redisからセッション情報を取得
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
2. Redisからセッション情報を削除
3. セッションCookieを削除（Max-Age=0）
4. ログアウトを監査ログに記録

## セキュリティ考慮事項

- **CSRF対策**: ログインフローではCSRFトークン不要（Cookieを使わない認証開始）、ログアウトはCSRFトークン必須
- **レート制限**: IPアドレスごとに1分間に10回までのリクエスト制限
- **fail lock**: ユーザーごとに2時間で5回失敗したら6時間ロック
- **セッション固定攻撃対策**: ログイン成功時に必ず新しいセッションIDを発行
- **監査ログ**: すべての認証試行を記録（成功・失敗・ロック）
