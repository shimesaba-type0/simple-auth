# セキュリティ仕様

## 概要

本システムのセキュリティ要件と対策の詳細です。

## 1. 認証セキュリティ

### 1.1 パスフレーズ管理

#### ハッシュアルゴリズム
- **Argon2id** を使用（推奨）
- パラメータ:
  - Memory: 64 MB
  - Iterations: 3
  - Parallelism: 4
  - Salt: 16バイトのランダム値（ユーザーごとに異なる）

#### パスフレーズ要件
- 長さ: 正確に64文字
- 文字種: 制限なし（すべての文字が利用可能）
- パスワードマネージャーでの管理を前提

#### 保存形式
```
$argon2id$v=19$m=65536,t=3,p=4$base64_encoded_salt$base64_encoded_hash
```

### 1.2 OTP（ワンタイムパスワード）

#### 生成方法
- 6桁のランダムな数字
- 暗号学的に安全な乱数生成器を使用（`crypto/rand`）

#### 保存方法
- Redisに保存
- キー: `otp:{user_id}`
- TTL: 10分
- 値:
  ```json
  {
    "otp": "123456",
    "created_at": "2025-10-23T14:30:00Z",
    "attempts": 0
  }
  ```

#### OTP検証時の制限
- 最大試行回数: 5回
- 5回失敗したら新しいOTPの発行が必要

#### メール送信
- TLS必須
- SPF/DKIM/DMARC設定
- レート制限: 同じメールアドレスに1分間に1回まで

### 1.3 セッション管理

#### セッションID生成
- 128ビット（16バイト）のランダムな値
- Base64エンコード
- 暗号学的に安全な乱数生成器を使用

#### セッション保存
- Redisに保存
- キー: `session:{session_id}`
- TTL: 24時間（セッション有効期限）
- 値:
  ```json
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

#### Cookie設定
- 名前: `auth_session`
- HttpOnly: `true` (JavaScriptからアクセス不可)
- Secure: `true` (HTTPS必須)
- SameSite: `Lax` (CSRF対策)
- Domain: 適切に設定
- Path: `/`
- Max-Age: 86400秒（24時間）

#### セッション固定攻撃対策
- ログイン成功時に必ず新しいセッションIDを発行
- 古いセッションIDは即座に無効化

#### セッションハイジャック対策
- IPアドレスとUser-Agentをセッション情報に保存
- 認証時にチェック（完全一致は不要、大幅な変更を検知）

## 2. ブルートフォース対策

### 2.1 fail lock

#### ロック条件
- 2時間以内に5回認証に失敗
- カウント対象: 第1段階（パスフレーズ認証）の失敗のみ

#### ロック期間
- 6時間

#### 解除方法
1. 6時間経過後に自動解除
2. 管理者による手動解除

#### 実装
- Redisに失敗回数を保存
- キー: `fail_lock:{user_id}`
- 値:
  ```json
  {
    "failed_attempts": [
      "2025-10-23T14:30:00Z",
      "2025-10-23T14:35:00Z",
      "2025-10-23T14:40:00Z"
    ],
    "locked_until": "2025-10-23T20:30:00Z"
  }
  ```
- TTL: ロック期間 + 2時間（履歴保持のため）

#### ロック時の通知
- ユーザーにメールで通知
- 管理者にも通知（オプション）

### 2.2 レート制限

#### IPアドレスベース
- 認証エンドポイント: 1分間に10回まで
- その他のエンドポイント: 1分間に60回まで
- 実装: Redisでカウント

```
キー: rate_limit:{ip_address}:{endpoint}
値: リクエスト回数
TTL: 60秒
```

#### ユーザーベース（認証後）
- API全体: 1分間に100回まで
- 管理者API: 1分間に200回まで

#### レート制限超過時
```json
HTTP/1.1 429 Too Many Requests
{
  "error": "rate_limit_exceeded",
  "message": "リクエスト数が多すぎます。しばらくしてから再試行してください。",
  "retry_after": 60
}
```

## 3. CSRF（クロスサイトリクエストフォージェリ）対策

### 3.1 対策方法

#### SameSite Cookie
- `SameSite=Lax` を設定
- クロスサイトからのPOST/PUT/DELETEリクエストでCookieが送信されない

#### CSRFトークン（二重送信Cookie方式）
- 状態変更API（POST/PUT/DELETE）には CSRFトークン必須
- ログインフローの開始時はトークン不要（Cookieを使わないため）

#### 実装
1. ログイン成功時にCSRFトークンを生成
2. Cookieとして送信（名前: `csrf_token`, HttpOnly: false）
3. クライアントはJavaScriptでCookieを読み取り、リクエストヘッダーに設定
4. サーバーはヘッダーとCookieを比較

```javascript
// クライアント側
const csrfToken = document.cookie
  .split('; ')
  .find(row => row.startsWith('csrf_token='))
  ?.split('=')[1];

fetch('/api/auth/logout', {
  method: 'POST',
  headers: {
    'X-CSRF-Token': csrfToken
  }
});
```

```go
// サーバー側
func CSRFMiddleware() gin.HandlerFunc {
    return func(c *gin.Context) {
        if c.Request.Method == "GET" || c.Request.Method == "HEAD" || c.Request.Method == "OPTIONS" {
            c.Next()
            return
        }

        // ログイン関連はCSRFチェック不要
        if strings.HasPrefix(c.Request.URL.Path, "/api/auth/login") {
            c.Next()
            return
        }

        tokenHeader := c.GetHeader("X-CSRF-Token")
        tokenCookie, _ := c.Cookie("csrf_token")

        if tokenHeader == "" || tokenCookie == "" || tokenHeader != tokenCookie {
            c.JSON(403, gin.H{"error": "csrf_token_invalid"})
            c.Abort()
            return
        }

        c.Next()
    }
}
```

## 4. XSS（クロスサイトスクリプティング）対策

### 4.1 出力のサニタイズ

#### ユーザー入力の表示
- HTMLエスケープ処理を実施
- テンプレートエンジンの自動エスケープ機能を使用

#### Markdownのサニタイズ
- ダッシュボードのカスタマイズエリアで使用
- ライブラリ: `bluemonday`（Go）または同等のもの
- 許可するタグ: `h1-h6`, `p`, `a`, `ul`, `ol`, `li`, `strong`, `em`, `code`, `pre`, `blockquote`
- `<script>`, `<iframe>`, `<object>` などは禁止

### 4.2 Content Security Policy (CSP)

```
Content-Security-Policy:
  default-src 'self';
  script-src 'self' 'unsafe-inline';
  style-src 'self' 'unsafe-inline';
  img-src 'self' https:;
  font-src 'self';
  connect-src 'self';
  frame-ancestors 'none';
```

### 4.3 HTTPヘッダー

```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
```

## 5. SQL インジェクション対策

### 5.1 プリペアドステートメント
- すべてのSQLクエリでプリペアドステートメントを使用
- 文字列連結でSQLを構築しない

```go
// Good
db.Query("SELECT * FROM users WHERE email = ?", email)

// Bad
db.Query("SELECT * FROM users WHERE email = '" + email + "'")
```

### 5.2 ORMの使用
- GORM（Go）などのORMを使用
- Raw SQLは最小限に

## 6. 監査ログ

### 6.1 記録する内容

#### 認証関連
- ログイン試行（成功/失敗）
- ログアウト
- パスフレーズ変更
- OTP送信
- fail lock発動/解除

#### ユーザー管理
- ユーザー作成
- ユーザー削除
- ユーザーロック/解除
- 権限変更
- 強制ログアウト

#### システム設定
- セキュリティ設定の変更

### 6.2 ログ形式

```json
{
  "id": "audit_12345",
  "timestamp": "2025-10-23T14:30:00Z",
  "action": "login_success",
  "actor_type": "user",
  "actor_id": "user_123",
  "actor_email": "user@example.com",
  "target_type": "session",
  "target_id": "session_abc",
  "ip_address": "192.168.1.1",
  "user_agent": "Mozilla/5.0...",
  "details": {
    "session_duration": 86400
  }
}
```

### 6.3 保存期間
- 最低1年間保存
- データベースに保存（別テーブル）
- 定期的にアーカイブ

## 7. TLS/HTTPS

### 7.1 必須要件
- すべての通信をHTTPSで行う
- TLS 1.2以上を使用
- TLS 1.0/1.1は無効化

### 7.2 推奨設定

```nginx
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
ssl_prefer_server_ciphers off;
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;
```

### 7.3 証明書
- Let's Encrypt などの信頼されたCAから取得
- ワイルドカード証明書の使用を推奨（`*.example.com`）

## 8. 依存関係のセキュリティ

### 8.1 脆弱性スキャン
- 定期的に依存パッケージの脆弱性をスキャン
- ツール: `go mod verify`, `snyk`, `dependabot`

### 8.2 最小権限の原則
- データベースユーザーは最小限の権限のみ
- アプリケーション用のユーザーを作成（root/postgres ユーザーを使わない）

## 9. データ保護

### 9.1 個人情報の取り扱い
- メールアドレスは暗号化せずに保存（検索のため）
- パスフレーズはArgon2idでハッシュ化
- セッション情報はRedisに保存（メモリ内）

### 9.2 データベースバックアップ
- 定期的にバックアップ
- バックアップは暗号化して保存
- 復元テストを定期的に実施

## 10. インシデント対応

### 10.1 異常検知
- 短時間での大量のログイン失敗
- 通常と異なるIPアドレスからのアクセス
- セッションハイジャックの可能性

### 10.2 通知
- 管理者にメール/Slack通知
- ダッシュボードにアラート表示

### 10.3 対応手順
1. 該当ユーザーをロック
2. 全セッションを無効化
3. 監査ログを確認
4. ユーザーに連絡
5. 必要に応じてパスフレーズをリセット

## 11. セキュリティチェックリスト

- [ ] パスフレーズはArgon2idでハッシュ化
- [ ] セッションCookieはHttpOnly, Secure, SameSite=Lax
- [ ] HTTPS必須（HTTP→HTTPSリダイレクト）
- [ ] CSRFトークンを実装
- [ ] XSS対策（サニタイズ、CSP）
- [ ] SQLインジェクション対策（プリペアドステートメント）
- [ ] fail lock実装
- [ ] レート制限実装
- [ ] 監査ログ記録
- [ ] セキュリティヘッダー設定
- [ ] 依存関係の脆弱性スキャン
- [ ] データベースバックアップ
- [ ] インシデント対応手順の整備
