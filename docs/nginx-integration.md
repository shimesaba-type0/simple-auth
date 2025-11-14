# nginx auth_request 連携

## 概要

nginx の `auth_request` ディレクティブを使用して、認証サーバーと連携します。

## アーキテクチャ：SSO（Single Sign-On）

この認証サーバーは、**1回のログインで複数のバックエンドサービスにアクセスできるSSO方式**を採用しています。

```
[ユーザー]
    ↓
[nginx]
    ├→ /login, /dashboard → [認証サーバー]
    │                           ↓ (セッション管理)
    ├→ /service-a/* → [auth_request] → [バックエンドサービスA]
    ├→ /service-b/* → [auth_request] → [バックエンドサービスB]
    └→ /service-c/* → [auth_request] → [バックエンドサービスC]
```

### メリット
✅ **1回のログインで全サービスにアクセス** - ユーザーは認証サーバーに1回だけログイン
✅ **一元管理** - ユーザー管理、監査ログが1箇所に集約
✅ **疎結合** - バックエンドサービスは認証ロジックを持たない
✅ **スケーラブル** - サービスを追加してもnginx設定を増やすだけ

## nginx の設定例

### 基本設定

```nginx
# 認証サーバーのアップストリーム定義
upstream auth_backend {
    server 127.0.0.1:3000;
    keepalive 32;
}

# 認証エンドポイント
location = /auth/verify {
    internal;
    proxy_pass http://auth_backend/api/auth/verify;
    proxy_pass_request_body off;
    proxy_set_header Content-Length "";
    proxy_set_header X-Original-URI $request_uri;
    proxy_set_header X-Original-Method $request_method;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header Host $host;

    # Cookieを渡す
    proxy_pass_header Cookie;
}

# 保護されたリソース
location /protected/ {
    auth_request /auth/verify;

    # 認証エラー時のリダイレクト
    error_page 401 = @error401;

    # 認証成功時、バックエンドに転送
    proxy_pass http://backend_app;

    # 認証サーバーから返されたヘッダーをバックエンドに渡す
    auth_request_set $auth_user $upstream_http_x_auth_user;
    auth_request_set $auth_role $upstream_http_x_auth_role;
    proxy_set_header X-Auth-User $auth_user;
    proxy_set_header X-Auth-Role $auth_role;
}

# 認証エラー時のリダイレクト処理
location @error401 {
    # 元のURLをクエリパラメータとして付与してログインページにリダイレクト
    return 302 https://$host/login?redirect=$scheme://$host$request_uri;
}

# 認証サーバー自体は保護しない
location /login {
    proxy_pass http://auth_backend;
}

location /api/auth/ {
    proxy_pass http://auth_backend;
}

location /dashboard {
    proxy_pass http://auth_backend;
}

location /admin {
    proxy_pass http://auth_backend;
}
```

### SSO：複数のバックエンドサービスを保護する（推奨）

**この方式では、ユーザーは1回ログインするだけで、すべてのサービスにアクセスできます。**

```nginx
# アップストリーム定義
upstream auth_backend {
    server auth-server:3000;
    keepalive 32;
}

upstream backend_service_a {
    server service-a:8000;
}

upstream backend_service_b {
    server service-b:8001;
}

upstream backend_service_c {
    server service-c:8002;
}

# 認証エンドポイント（全サービス共通）
location = /auth/verify {
    internal;
    proxy_pass http://auth_backend/api/auth/verify;
    proxy_pass_request_body off;
    proxy_set_header Content-Length "";
    proxy_pass_header Cookie;
}

# 認証サーバー自体（ログイン、ダッシュボード、管理画面）
location / {
    proxy_pass http://auth_backend;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

# バックエンドサービスA
location /service-a/ {
    auth_request /auth/verify;
    error_page 401 = @error401;

    # 認証情報をヘッダーで渡す
    auth_request_set $auth_user $upstream_http_x_auth_user;
    auth_request_set $auth_role $upstream_http_x_auth_role;
    auth_request_set $auth_user_id $upstream_http_x_auth_user_id;

    proxy_pass http://backend_service_a/;
    proxy_set_header X-Auth-User $auth_user;
    proxy_set_header X-Auth-Role $auth_role;
    proxy_set_header X-Auth-User-ID $auth_user_id;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}

# バックエンドサービスB
location /service-b/ {
    auth_request /auth/verify;
    error_page 401 = @error401;

    auth_request_set $auth_user $upstream_http_x_auth_user;
    auth_request_set $auth_role $upstream_http_x_auth_role;
    auth_request_set $auth_user_id $upstream_http_x_auth_user_id;

    proxy_pass http://backend_service_b/;
    proxy_set_header X-Auth-User $auth_user;
    proxy_set_header X-Auth-Role $auth_role;
    proxy_set_header X-Auth-User-ID $auth_user_id;
}

# バックエンドサービスC（管理者専用）
location /service-c/ {
    auth_request /auth/verify;
    error_page 401 = @error401;

    # 認証情報を取得
    auth_request_set $auth_user $upstream_http_x_auth_user;
    auth_request_set $auth_role $upstream_http_x_auth_role;
    auth_request_set $auth_user_id $upstream_http_x_auth_user_id;

    # adminロールのみアクセス可能
    if ($auth_role != "admin") {
        return 403;
    }

    proxy_pass http://backend_service_c/;
    proxy_set_header X-Auth-User $auth_user;
    proxy_set_header X-Auth-Role $auth_role;
    proxy_set_header X-Auth-User-ID $auth_user_id;
}

# 未認証時のリダイレクト
location @error401 {
    return 302 /login?redirect=$request_uri;
}
```

### ユーザーフロー

1. **初回アクセス**
   ```
   ユーザー → /service-a/ にアクセス
      ↓ (未認証)
   /login にリダイレクト
      ↓
   パスフレーズ + OTP 入力
      ↓ (認証成功、セッション確立)
   /service-a/ にリダイレクト
      ↓
   サービスA表示
   ```

2. **他のサービスへのアクセス（SSO）**
   ```
   ユーザー → /service-b/ にアクセス
      ↓ (セッションCookieが既にある)
   auth_request → 認証OK
      ↓
   サービスB表示（ログイン不要！）
   ```

3. **ダッシュボード経由**
   ```
   ユーザー → /dashboard にアクセス
      ↓
   サービス一覧を表示
      ├→ [サービスA] クリック → /service-a/ へ（ログイン不要）
      ├→ [サービスB] クリック → /service-b/ へ（ログイン不要）
      └→ [サービスC] クリック → /service-c/ へ（ログイン不要）
   ```

## 認証サーバー側の実装

### エンドポイント: `/api/auth/verify`

#### リクエスト

nginx から以下のヘッダーが渡されます：

```
GET /api/auth/verify HTTP/1.1
Host: auth.example.com
Cookie: auth_session=xxxxxx
X-Original-URI: /protected/resource
X-Original-Method: GET
X-Real-IP: 192.168.1.1
X-Forwarded-For: 192.168.1.1
X-Forwarded-Proto: https
```

#### レスポンス（認証成功）

```
HTTP/1.1 200 OK
X-Auth-User: user@example.com
X-Auth-Role: user
X-Auth-User-ID: user_123
```

nginx はこのレスポンスを受け取ると、元のリクエストをバックエンドに転送します。

#### レスポンス（未認証）

```
HTTP/1.1 401 Unauthorized
X-Auth-Redirect: /login?redirect=https://example.com/protected/resource
```

nginx は `error_page 401` の設定に従ってリダイレクトします。

#### レスポンス（権限不足）

```
HTTP/1.1 403 Forbidden
```

nginx は `error_page 403` の設定に従って処理します。

### 処理フロー

```go
func VerifyAuthHandler(c *gin.Context) {
    // 1. セッションCookieを取得
    sessionID, err := c.Cookie("auth_session")
    if err != nil || sessionID == "" {
        c.Header("X-Auth-Redirect", "/login?redirect="+c.GetHeader("X-Original-URI"))
        c.Status(401)
        return
    }

    // 2. セッション情報を取得（SQLite3 または Redis）
    // デフォルト構成（SQLite3）の場合:
    //   SELECT user_id, email, role, expires_at FROM sessions WHERE session_id = ?
    // 大規模環境（Redis）の場合:
    //   redis.Get(ctx, "session:"+sessionID).Result()
    session, err := sessionStore.Get(ctx, sessionID)
    if err != nil {
        c.Header("X-Auth-Redirect", "/login?redirect="+c.GetHeader("X-Original-URI"))
        c.Status(401)
        return
    }

    // 3. セッション情報をパース
    var sessionData SessionData
    json.Unmarshal([]byte(session), &sessionData)

    // 4. セッションの有効期限チェック
    if time.Now().After(sessionData.ExpiresAt) {
        redis.Del(ctx, "session:"+sessionID)
        c.Header("X-Auth-Redirect", "/login?redirect="+c.GetHeader("X-Original-URI"))
        c.Status(401)
        return
    }

    // 5. ユーザーがロックされていないかチェック
    user, err := db.GetUser(sessionData.UserID)
    if err != nil || user.Locked {
        c.Status(403)
        return
    }

    // 6. 認証成功、ヘッダーを返す
    c.Header("X-Auth-User", sessionData.Email)
    c.Header("X-Auth-Role", sessionData.Role)
    c.Header("X-Auth-User-ID", sessionData.UserID)
    c.Status(200)
}
```

## パフォーマンス最適化

### 1. セッションストレージ

**デフォルト構成（SQLite3）:**
- セッション情報は `sessions` テーブルに保存
- 十分高速（〜500ユーザー、〜50同時接続）
- auth_request応答: 5-20ms
- WALモードで並行読み取りを最適化

**大規模環境（Redis - オプション）:**
- セッション情報はRedisに保存
- 超高速（500+ユーザー、50+同時接続）
- auth_request応答: 1-5ms
- キー: `session:{session_id}`
- TTL: セッションの有効期限と同じ（24時間）
- データベースへのアクセスを最小限に

**移行タイミング:**
- auth_requestのレスポンスが50ms以上かかるようになったら
- 同時接続数が100人を超えたら

### 2. コネクションプーリング

```nginx
upstream auth_backend {
    server 127.0.0.1:3000;
    keepalive 32;  # HTTP/1.1 keepalive接続を維持
}
```

### 3. 認証エンドポイントの最適化

- データベースクエリを最小限に
- セッション情報にユーザーの基本情報を含める
- ロック状態のチェックもRedisで行う（キャッシュ）

### 4. レスポンスタイム目標

- 平均: 10ms以下
- 95パーセンタイル: 50ms以下
- 99パーセンタイル: 100ms以下

## セキュリティ考慮事項

### 1. セッションCookieの設定

```go
c.SetCookie(
    "auth_session",           // name
    sessionID,                // value
    86400,                    // maxAge (24時間)
    "/",                      // path
    "example.com",            // domain
    true,                     // secure (HTTPS必須)
    true,                     // httpOnly
)

// SameSite=Lax を設定（Ginの場合は追加のヘッダーで対応）
c.Header("Set-Cookie", fmt.Sprintf(
    "auth_session=%s; Path=/; Domain=example.com; Max-Age=86400; Secure; HttpOnly; SameSite=Lax",
    sessionID,
))
```

### 2. HTTPS必須

- すべての通信をHTTPSで行う
- nginx で HTTP → HTTPS リダイレクトを設定

```nginx
server {
    listen 80;
    server_name example.com;
    return 301 https://$server_name$request_uri;
}
```

### 3. セッション固定攻撃対策

- ログイン成功時に必ず新しいセッションIDを発行
- 古いセッションIDは無効化

### 4. セッションハイジャック対策

- セッション情報にIPアドレスとUser-Agentを保存
- 認証時にチェック（完全一致または緩い検証）

## トラブルシューティング

### 認証ループが発生する場合

**原因**: `/api/auth/verify` にもauth_requestが適用されている

**解決**: `/api/auth/` を auth_request から除外する

```nginx
location /api/auth/ {
    # auth_request を適用しない
    proxy_pass http://auth_backend;
}
```

### Cookieが渡されない場合

**原因**: `proxy_pass_request_body off` の影響でCookieも削除されている

**解決**: `proxy_pass_header Cookie` を追加

```nginx
location = /auth/verify {
    internal;
    proxy_pass http://auth_backend/api/auth/verify;
    proxy_pass_request_body off;
    proxy_set_header Content-Length "";
    proxy_pass_header Cookie;  # これを追加
}
```

### リダイレクトループが発生する場合

**原因**: ログインページ自体が保護されている

**解決**: `/login` を auth_request から除外する

```nginx
location /login {
    # auth_request を適用しない
    proxy_pass http://auth_backend;
}
```

## テスト方法

### 1. 手動テスト

```bash
# 1. ログインしてセッションCookieを取得
curl -c cookies.txt -X POST https://example.com/api/auth/login/passphrase \
  -H "Content-Type: application/json" \
  -d '{"passphrase":"..."}'

curl -b cookies.txt -X POST https://example.com/api/auth/login/otp \
  -H "Content-Type: application/json" \
  -d '{"otp":"123456"}'

# 2. 保護されたリソースにアクセス
curl -b cookies.txt https://example.com/protected/resource

# 3. 認証エンドポイントを直接テスト（nginxを介さない場合）
curl -b cookies.txt https://example.com/api/auth/verify
```

### 2. 自動テスト

```bash
# auth_request のテスト用スクリプト
./test/test-auth-request.sh
```

## モニタリング

### nginx のアクセスログ

```nginx
log_format auth_log '$remote_addr - $remote_user [$time_local] '
                    '"$request" $status $body_bytes_sent '
                    '"$http_referer" "$http_user_agent" '
                    'auth_status=$upstream_status '
                    'auth_user=$upstream_http_x_auth_user';

access_log /var/log/nginx/access.log auth_log;
```

### メトリクス

- auth_request の成功率
- auth_request のレスポンスタイム
- 401エラーの頻度
- 403エラーの頻度
