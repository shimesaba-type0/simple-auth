#!/bin/bash

# Phase 1: 基盤構築

gh issue create --title "プロジェクトセットアップ（Go + SQLite3）" --body "$(cat <<'EOF'
## 概要
Go言語プロジェクトの初期セットアップとSQLite3データベースの基盤構築

## 実装内容

### 1. Goプロジェクト初期化
- \`go mod init github.com/shimesaba-type0/simple-auth\`
- 必要なライブラリのインストール:
  - Gin (Webフレームワーク)
  - GORM (ORM)
  - go-sqlite3 (SQLite3ドライバ)
  - argon2 (パスワードハッシュ)
  - godotenv (環境変数)
  - zap/logrus (ログ)
  - gomail (メール送信)
  - bluemonday (Markdownサニタイズ)

### 2. プロジェクト構造作成
\`\`\`
simple-auth/
├── cmd/server/main.go
├── internal/
│   ├── api/
│   ├── models/
│   ├── services/
│   ├── repositories/
│   ├── email/
│   ├── config/
│   └── utils/
├── migrations/
├── web/
├── .env.example
└── README.md
\`\`\`

### 3. 設定ファイル
- \`.env.example\` 作成
- \`config.go\` 実装（環境変数読み込み）
- SQLite3接続設定（WALモード、PRAGMA設定）

### 4. 基本的なmain.go
- Ginサーバー起動
- データベース接続
- ヘルスチェックエンドポイント (\`/api/health\`)

## チェックリスト
- [ ] \`go.mod\` と \`go.sum\` 作成
- [ ] ディレクトリ構造作成
- [ ] \`.env.example\` 作成
- [ ] \`internal/config/config.go\` 実装
- [ ] \`cmd/server/main.go\` 実装
- [ ] SQLite3接続確認（WALモード有効化）
- [ ] \`/api/health\` エンドポイント動作確認
- [ ] \`go run cmd/server/main.go\` でサーバー起動確認

## 参考
- docs/technology-stack.md
- docs/database-schema.md (PRAGMA設定)

## Phase
Phase 1: 基盤構築
EOF
)" --label "enhancement,phase-1"

gh issue create --title "データベースマイグレーション作成" --body "$(cat <<'EOF'
## 概要
SQLite3データベースのテーブル定義とマイグレーションファイルの作成

## 実装内容

### 1. マイグレーションツール導入
- golang-migrate インストール
- \`migrations/\` ディレクトリ作成

### 2. テーブル定義（up/downファイル作成）
以下のテーブルをマイグレーションファイルで作成：

1. \`000001_create_users_table.up.sql\`
2. \`000002_create_login_history_table.up.sql\`
3. \`000003_create_notifications_tables.up.sql\`
4. \`000004_create_user_dashboards_table.up.sql\`
5. \`000005_create_invitations_tables.up.sql\`
6. \`000006_create_audit_logs_table.up.sql\`
7. \`000007_create_system_settings_table.up.sql\`
8. \`000008_create_sessions_table.up.sql\`
9. \`000009_create_otps_table.up.sql\`
10. \`000010_create_fail_locks_table.up.sql\`

各テーブルに対応する \`.down.sql\` も作成

### 3. 初期データ投入
- \`system_settings\` テーブルの初期値（セキュリティ設定）
- 初期管理者アカウント作成用スクリプト（別途手動実行）

### 4. マイグレーション実行スクリプト
- \`scripts/migrate.sh\` 作成
- up/down/version確認コマンド

## チェックリスト
- [ ] golang-migrate インストール
- [ ] 全テーブルの \`.up.sql\` 作成
- [ ] 全テーブルの \`.down.sql\` 作成
- [ ] インデックス定義（docs/database-schema.md参照）
- [ ] 外部キー制約設定
- [ ] CHECK制約設定
- [ ] \`system_settings\` 初期データINSERT
- [ ] マイグレーション実行確認（up）
- [ ] ロールバック確認（down）
- [ ] \`scripts/migrate.sh\` 作成

## 参考
- docs/database-schema.md（完全なスキーマ定義）

## 依存
- #4 プロジェクトセットアップ

## Phase
Phase 1: 基盤構築
EOF
)" --label "enhancement,phase-1"

gh issue create --title "基本的なミドルウェア実装" --body "$(cat <<'EOF'
## 概要
認証・セキュリティに必要な基本的なミドルウェアの実装

## 実装内容

### 1. ロガーミドルウェア
- \`internal/api/middleware/logger.go\`
- リクエスト/レスポンスのロギング
- zap または logrus 使用
- 構造化ログ（JSON形式）

### 2. CORSミドルウェア
- \`internal/api/middleware/cors.go\`
- 開発環境用CORS設定
- 本番環境用の制限付きCORS

### 3. エラーハンドリングミドルウェア
- \`internal/api/middleware/error_handler.go\`
- 統一エラーレスポンス形式
\`\`\`json
{
  "success": false,
  "error": "error_code",
  "message": "エラーメッセージ"
}
\`\`\`

### 4. リカバリーミドルウェア
- パニック時のリカバリー
- エラーログ記録
- 500エラー返却

### 5. セキュリティヘッダーミドルウェア
- \`X-Content-Type-Options: nosniff\`
- \`X-Frame-Options: DENY\`
- \`X-XSS-Protection: 1; mode=block\`
- \`Content-Security-Policy\` 設定

## チェックリスト
- [ ] \`logger.go\` 実装
- [ ] \`cors.go\` 実装
- [ ] \`error_handler.go\` 実装
- [ ] リカバリーミドルウェア実装
- [ ] セキュリティヘッダーミドルウェア実装
- [ ] main.goでミドルウェア登録
- [ ] ログ出力確認
- [ ] エラーレスポンス形式確認

## 参考
- docs/security.md（セキュリティヘッダー）
- docs/api-specification.md（エラーレスポンス形式）

## 依存
- #4 プロジェクトセットアップ

## Phase
Phase 1: 基盤構築
EOF
)" --label "enhancement,phase-1"

# Phase 2: 認証機能（コア）

gh issue create --title "招待システムAPI実装" --body "$(cat <<'EOF'
## 概要
管理者が招待リンクを作成・管理するAPIの実装

## 実装内容

### 1. データモデル
- \`internal/models/invitation.go\`
- Invitation構造体
- InvitationUse構造体

### 2. リポジトリ層
- \`internal/repositories/invitation_repository.go\`
- Create, Get, List, Revoke, IncrementUseCount

### 3. サービス層
- \`internal/services/invitation_service.go\`
- 招待トークン生成（128ビット）
- 有効期限計算
- 使用回数チェック

### 4. APIエンドポイント
- POST \`/api/admin/invitations\` - 招待リンク作成
- GET \`/api/admin/invitations\` - 招待リンク一覧
- GET \`/api/admin/invitations/:token\` - 招待リンク詳細
- POST \`/api/admin/invitations/:token/revoke\` - 招待リンク無効化
- GET \`/api/admin/invitations/:token/users\` - 登録ユーザー一覧

### 5. バリデーション
- max_uses: 1-1000
- expires_in_days: 1-365
- description: 最大500文字

## チェックリスト
- [ ] \`invitation.go\` モデル作成
- [ ] \`invitation_repository.go\` 実装
- [ ] \`invitation_service.go\` 実装
- [ ] トークン生成関数（crypto/rand使用）
- [ ] 5つのAPIエンドポイント実装
- [ ] バリデーション実装
- [ ] 管理者権限チェック
- [ ] 監査ログ記録
- [ ] 単体テスト作成

## 参考
- docs/admin-features.md（セクション3）
- docs/api-specification.md（#18-22）
- docs/database-schema.md（invitations, invitation_uses）

## 依存
- #4 プロジェクトセットアップ
- #5 データベースマイグレーション

## Phase
Phase 2: 認証機能（コア）
EOF
)" --label "enhancement,phase-2"

gh issue create --title "ユーザー登録API実装" --body "$(cat <<'EOF'
## 概要
招待リンクを使用したユーザー登録機能の実装

## 実装内容

### 1. データモデル
- \`internal/models/user.go\`
- User構造体

### 2. ユーティリティ
- \`internal/utils/passphrase.go\` - パスフレーズ生成
  - 64文字以上
  - 英数字のみ（A-Za-z0-9）
  - crypto/rand使用
- \`internal/utils/hash.go\` - Argon2idハッシュ

### 3. リポジトリ層
- \`internal/repositories/user_repository.go\`
- Create, GetByEmail, GetByID

### 4. サービス層
- \`internal/services/auth_service.go\`
- Register関数

### 5. APIエンドポイント
- POST \`/api/auth/register\`

### 6. 処理フロー
1. 招待トークン検証（存在、期限、使用回数、無効化チェック）
2. メールアドレス重複チェック
3. パスフレーズ生成（64文字以上、英数字）
4. Argon2idでハッシュ化
5. ユーザー作成
6. 招待使用カウントインクリメント
7. invitation_uses レコード作成
8. 監査ログ記録
9. パスフレーズを返却（平文、1回のみ）

## チェックリスト
- [ ] \`user.go\` モデル作成
- [ ] \`passphrase.go\` 実装（生成関数）
- [ ] \`hash.go\` 実装（Argon2id）
- [ ] \`user_repository.go\` 実装
- [ ] \`auth_service.Register\` 実装
- [ ] POST \`/api/auth/register\` 実装
- [ ] エラーハンドリング（全エラーコード対応）
- [ ] バリデーション（メールアドレス形式）
- [ ] トランザクション管理
- [ ] 単体テスト作成

## 参考
- docs/authentication-flow.md（ユーザー登録フロー）
- docs/api-specification.md（#1）
- docs/security.md（パスフレーズ要件、Argon2id設定）

## 依存
- #5 データベースマイグレーション
- #7 招待システムAPI実装

## Phase
Phase 2: 認証機能（コア）
EOF
)" --label "enhancement,phase-2"

gh issue create --title "パスフレーズ認証（第1段階）実装" --body "$(cat <<'EOF'
## 概要
事前共有パスフレーズによる第1段階認証の実装

## 実装内容

### 1. APIエンドポイント
- POST \`/api/auth/login/passphrase\`

### 2. 処理フロー
1. パスフレーズ入力受け取り
2. ユーザー検索（パスフレーズハッシュからユーザー特定は不可のため、全ユーザーと照合）
3. Argon2idハッシュ検証
4. fail lockチェック（SQLite3の\`fail_locks\`テーブル）
5. OTP生成（6桁）
6. OTP保存（SQLite3の\`otps\`テーブル、10分有効）
7. メール送信
8. ログイン履歴記録（result: failed/success）
9. 失敗時：fail lockカウント更新

### 3. fail lock実装
- \`internal/services/fail_lock_service.go\`
- 2時間で5回失敗 → 6時間ロック
- SQLite3 \`fail_locks\` テーブル使用

### 4. OTP生成
- \`internal/utils/otp.go\`
- 6桁の数字
- crypto/rand使用

### 5. メール送信
- \`internal/email/sender.go\`
- OTPメールテンプレート

## チェックリスト
- [ ] POST \`/api/auth/login/passphrase\` 実装
- [ ] Argon2idハッシュ検証
- [ ] \`fail_lock_service.go\` 実装
- [ ] OTP生成関数実装
- [ ] OTP保存（SQLite3）
- [ ] メール送信実装
- [ ] ログイン履歴記録
- [ ] エラーレスポンス（3種類）
- [ ] レート制限（1分10回）
- [ ] 単体テスト作成

## 参考
- docs/authentication-flow.md（第1段階）
- docs/api-specification.md（#2）
- docs/security.md（fail lock、OTP）

## 依存
- #8 ユーザー登録API実装

## Phase
Phase 2: 認証機能（コア）
EOF
)" --label "enhancement,phase-2"

gh issue create --title "OTP認証（第2段階）実装" --body "$(cat <<'EOF'
## 概要
メールOTPによる第2段階認証とセッション確立の実装

## 実装内容

### 1. APIエンドポイント
- POST \`/api/auth/login/otp\`

### 2. 処理フロー
1. OTP入力受け取り
2. SQLite3 \`otps\` テーブルからOTP取得
3. OTP検証（値、有効期限）
4. セッションID生成（128ビット、crypto/rand）
5. セッション保存（SQLite3 \`sessions\` テーブル、24時間有効）
6. セッションCookie発行
7. CSRFトークン生成・Cookie発行
8. ログイン履歴更新（result: success）
9. OTPレコード削除
10. fail lockカウントリセット

### 3. セッション管理
- \`internal/services/session_service.go\`
- Create, Get, Delete

### 4. Cookie設定
- \`auth_session\`: HttpOnly, Secure, SameSite=Lax, 24時間
- \`csrf_token\`: HttpOnly=false, Secure, SameSite=Lax, 24時間

## チェックリスト
- [ ] POST \`/api/auth/login/otp\` 実装
- [ ] OTP検証ロジック
- [ ] セッションID生成
- [ ] \`session_service.go\` 実装
- [ ] セッション保存（SQLite3）
- [ ] Cookie発行（auth_session, csrf_token）
- [ ] CSRFトークン生成
- [ ] ログイン履歴更新
- [ ] OTP削除
- [ ] fail lockリセット
- [ ] 単体テスト作成

## 参考
- docs/authentication-flow.md（第2段階）
- docs/api-specification.md（#3）
- docs/security.md（セッション管理、Cookie設定）

## 依存
- #9 パスフレーズ認証（第1段階）実装

## Phase
Phase 2: 認証機能（コア）
EOF
)" --label "enhancement,phase-2"

gh issue create --title "セッション管理とログアウト実装" --body "$(cat <<'EOF'
## 概要
セッション検証、ログアウト、認証ミドルウェアの実装

## 実装内容

### 1. 認証ミドルウェア
- \`internal/api/middleware/auth.go\`
- セッションCookie検証
- SQLite3 \`sessions\` テーブルからセッション取得
- 有効期限チェック
- ユーザーロック状態チェック
- コンテキストにユーザー情報セット

### 2. APIエンドポイント
- GET \`/api/auth/me\` - 現在のユーザー情報
- POST \`/api/auth/logout\` - ログアウト

### 3. セッションクリーンアップ
- 期限切れセッション削除（定期実行）
- \`internal/services/cleanup_service.go\`

## チェックリスト
- [ ] \`auth.go\` ミドルウェア実装
- [ ] セッション検証ロジック
- [ ] GET \`/api/auth/me\` 実装
- [ ] POST \`/api/auth/logout\` 実装
- [ ] Cookie削除処理
- [ ] ログアウト履歴記録
- [ ] セッションクリーンアップ実装
- [ ] 定期実行設定（1時間ごと）
- [ ] 単体テスト作成

## 参考
- docs/api-specification.md（#5, #6）
- docs/authentication-flow.md（ログアウト）

## 依存
- #10 OTP認証（第2段階）実装

## Phase
Phase 2: 認証機能（コア）
EOF
)" --label "enhancement,phase-2"

# Phase 3: nginx連携

gh issue create --title "auth_request エンドポイント実装" --body "$(cat <<'EOF'
## 概要
nginx auth_request用の認証検証エンドポイントの実装

## 実装内容

### 1. APIエンドポイント
- GET \`/api/auth/verify\`

### 2. 処理フロー
1. セッションCookie取得
2. SQLite3 \`sessions\` テーブルからセッション取得
3. セッション有効期限チェック
4. ユーザーロック状態チェック（データベース）
5. レスポンスヘッダー設定:
   - \`X-Auth-User\`: メールアドレス
   - \`X-Auth-Role\`: user/admin
   - \`X-Auth-User-ID\`: ユーザーID

### 3. パフォーマンス最適化
- セッション情報にユーザーの基本情報を含める
- データベースクエリ最小化
- 目標レスポンスタイム: 5-20ms（SQLite3）

## チェックリスト
- [ ] GET \`/api/auth/verify\` 実装
- [ ] セッション検証ロジック
- [ ] レスポンスヘッダー設定
- [ ] 401エラー時のリダイレクトヘッダー
- [ ] パフォーマンステスト（レスポンスタイム）
- [ ] 単体テスト作成

## 参考
- docs/nginx-integration.md（処理フロー）
- docs/api-specification.md（#4）

## 依存
- #11 セッション管理とログアウト実装

## Phase
Phase 3: nginx連携
EOF
)" --label "enhancement,phase-3"

gh issue create --title "nginx設定とテスト" --body "$(cat <<'EOF'
## 概要
nginx auth_request設定の作成とSSO動作確認

## 実装内容

### 1. nginx設定ファイル
- \`nginx/default.conf\` 作成
- auth_request設定
- エラーページ設定
- 複数バックエンドサービスの例

### 2. Docker Compose設定
- \`docker-compose.yml\` 更新
- nginxコンテナ追加
- 認証サーバーコンテナ
- テスト用バックエンドサービス（2-3個）

### 3. テスト用バックエンドサービス
- 簡易なHTTPサーバー（Go/Python）
- \`X-Auth-User\` ヘッダー表示

### 4. 動作確認
- ログインなしでアクセス → ログインページへリダイレクト
- ログイン後 → サービスAにアクセス成功
- サービスB、サービスCにもログインなしでアクセス可能（SSO）

## チェックリスト
- [ ] \`nginx/default.conf\` 作成
- [ ] auth_request設定
- [ ] エラーページ設定
- [ ] docker-compose.yml更新
- [ ] nginxコンテナ設定
- [ ] テスト用バックエンド作成（2-3個）
- [ ] SSO動作確認
- [ ] ログインフロー確認
- [ ] ログアウト確認
- [ ] ドキュメント更新（README.md）

## 参考
- docs/nginx-integration.md（設定例）

## 依存
- #12 auth_request エンドポイント実装

## Phase
Phase 3: nginx連携
EOF
)" --label "enhancement,phase-3"

# Phase 4: ユーザー機能

gh issue create --title "ダッシュボード実装" --body "$(cat <<'EOF'
## 概要
ユーザーダッシュボードの実装（サービス一覧、通知、カスタマイズエリア）

## 実装内容

### 1. APIエンドポイント
- GET \`/api/user/dashboard\` - ダッシュボードコンテンツ取得
- PUT \`/api/user/dashboard\` - ダッシュボードコンテンツ更新

### 2. フロントエンド
- \`web/templates/dashboard.html\`
- サービス一覧表示
- 通知一覧（未読バッジ）
- カスタマイズエリア（Markdown表示）
- ログイン履歴（直近10件）

### 3. Markdownサニタイズ
- bluemonday使用
- 許可タグ: h1-h6, p, a, ul, ol, li, strong, em, code, pre, blockquote
- script, iframe, object 禁止

### 4. サービス一覧設定
- 設定ファイルまたはデータベース
- サービス名、URL、説明、権限

## チェックリスト
- [ ] GET \`/api/user/dashboard\` 実装
- [ ] PUT \`/api/user/dashboard\` 実装
- [ ] \`dashboard.html\` 作成
- [ ] Markdownサニタイズ実装
- [ ] サービス一覧表示
- [ ] 通知一覧表示
- [ ] カスタマイズエリア実装
- [ ] ログイン履歴表示
- [ ] レスポンシブデザイン
- [ ] XSS対策確認

## 参考
- docs/user-features.md（ダッシュボード）
- docs/api-specification.md（#3, #4）

## 依存
- #11 セッション管理とログアウト実装

## Phase
Phase 4: ユーザー機能
EOF
)" --label "enhancement,phase-4"

gh issue create --title "プロフィール管理実装" --body "$(cat <<'EOF'
## 概要
ユーザープロフィール表示・更新機能の実装

## 実装内容

### 1. APIエンドポイント
- GET \`/api/user/profile\` - プロフィール取得
- PUT \`/api/user/profile\` - プロフィール更新

### 2. ログイン履歴
- GET \`/api/user/login-history\` - ログイン履歴取得
- ページネーション（limit, offset）

### 3. ロック状態確認
- GET \`/api/user/lock-status\` - fail lock状態確認

### 4. フロントエンド
- \`web/templates/profile.html\`
- 表示名編集
- ログイン履歴一覧
- ロック状態表示

## チェックリスト
- [ ] GET \`/api/user/profile\` 実装
- [ ] PUT \`/api/user/profile\` 実装
- [ ] GET \`/api/user/login-history\` 実装
- [ ] GET \`/api/user/lock-status\` 実装
- [ ] \`profile.html\` 作成
- [ ] 表示名更新機能
- [ ] ログイン履歴表示
- [ ] ページネーション
- [ ] 単体テスト作成

## 参考
- docs/user-features.md（プロフィール、ログイン履歴）
- docs/api-specification.md（#1, #2, #7, #8）

## 依存
- #11 セッション管理とログアウト実装

## Phase
Phase 4: ユーザー機能
EOF
)" --label "enhancement,phase-4"

gh issue create --title "通知機能実装" --body "$(cat <<'EOF'
## 概要
管理者通知・個人通知の表示と既読管理の実装

## 実装内容

### 1. データモデル
- \`internal/models/notification.go\`
- Notification構造体
- NotificationRead構造体

### 2. リポジトリ層
- \`internal/repositories/notification_repository.go\`
- Create, List, MarkAsRead

### 3. APIエンドポイント
- GET \`/api/user/notifications\` - 通知一覧取得
- POST \`/api/user/notifications/:id/read\` - 通知を既読にする

### 4. フロントエンド
- 通知バッジ（未読数表示）
- 通知一覧モーダル
- 既読/未読の表示切り替え

## チェックリスト
- [ ] \`notification.go\` モデル作成
- [ ] \`notification_repository.go\` 実装
- [ ] GET \`/api/user/notifications\` 実装
- [ ] POST \`/api/user/notifications/:id/read\` 実装
- [ ] フィルタリング（type, unread_only）
- [ ] ページネーション
- [ ] 通知UI実装
- [ ] 未読バッジ実装
- [ ] 単体テスト作成

## 参考
- docs/user-features.md（通知管理）
- docs/api-specification.md（#5, #6）

## 依存
- #5 データベースマイグレーション

## Phase
Phase 4: ユーザー機能
EOF
)" --label "enhancement,phase-4"

# Phase 5: 管理者機能

gh issue create --title "ユーザー管理API実装" --body "$(cat <<'EOF'
## 概要
管理者用ユーザー管理機能の実装

## 実装内容

### 1. APIエンドポイント
- GET \`/api/admin/users\` - ユーザー一覧
- GET \`/api/admin/users/:user_id\` - ユーザー詳細
- POST \`/api/admin/users\` - ユーザー作成
- POST \`/api/admin/users/:user_id/lock\` - ユーザーロック
- POST \`/api/admin/users/:user_id/unlock\` - ロック解除
- DELETE \`/api/admin/users/:user_id\` - ユーザー削除
- POST \`/api/admin/users/:user_id/reset-passphrase\` - パスフレーズリセット
- POST \`/api/admin/users/:user_id/force-logout\` - 強制ログアウト
- PUT \`/api/admin/users/:user_id/role\` - 権限変更
- GET \`/api/admin/users/:user_id/login-history\` - ログイン履歴

### 2. サービス層
- \`internal/services/admin_user_service.go\`
- 全セッション無効化
- パスフレーズリセット

### 3. 権限チェック
- \`internal/api/middleware/admin.go\`
- role = 'admin' のみアクセス可能

## チェックリスト
- [ ] 10個のAPIエンドポイント実装
- [ ] \`admin_user_service.go\` 実装
- [ ] 管理者権限ミドルウェア
- [ ] バリデーション
- [ ] 監査ログ記録
- [ ] エラーハンドリング
- [ ] 単体テスト作成

## 参考
- docs/admin-features.md（セクション1）
- docs/api-specification.md（#1-10）

## 依存
- #8 ユーザー登録API実装

## Phase
Phase 5: 管理者機能
EOF
)" --label "enhancement,phase-5"

gh issue create --title "招待リンク管理UI実装" --body "$(cat <<'EOF'
## 概要
管理者用招待リンク管理画面の実装

## 実装内容

### 1. フロントエンド
- \`web/templates/admin/invitations.html\`
- 招待リンク作成フォーム
- 招待リンク一覧テーブル
- 詳細表示モーダル
- 無効化ボタン

### 2. 機能
- 招待リンク作成（max_uses, expires_in_days, description）
- 一覧表示（ステータスフィルタ）
- 詳細表示（使用履歴）
- コピー機能（招待URL）
- 無効化機能

### 3. UI/UX
- ステータス別色分け（active=緑、expired=灰、exhausted=黄、revoked=赤）
- 残り使用回数表示
- 有効期限表示（残り日数）
- 登録ユーザー一覧

## チェックリスト
- [ ] \`invitations.html\` 作成
- [ ] 作成フォーム実装
- [ ] 一覧表示実装
- [ ] 詳細モーダル実装
- [ ] URLコピー機能
- [ ] 無効化機能
- [ ] ステータス表示
- [ ] ページネーション
- [ ] レスポンシブデザイン

## 参考
- docs/admin-features.md（セクション3）

## 依存
- #7 招待システムAPI実装

## Phase
Phase 5: 管理者機能
EOF
)" --label "enhancement,phase-5"

gh issue create --title "監査ログ・システム監視実装" --body "$(cat <<'EOF'
## 概要
監査ログ表示とシステム統計ダッシュボードの実装

## 実装内容

### 1. APIエンドポイント
- GET \`/api/admin/audit-logs\` - 監査ログ取得
- GET \`/api/admin/dashboard/stats\` - システム統計

### 2. 監査ログ
- フィルタリング（action, user_id）
- ページネーション
- JSON詳細表示

### 3. システム統計
- 総ユーザー数
- 今日のアクティブユーザー
- ロック中ユーザー
- 今日の失敗ログイン試行
- アクティブセッション数
- システムステータス

### 4. フロントエンド
- \`web/templates/admin/audit-logs.html\`
- \`web/templates/admin/dashboard.html\`

## チェックリスト
- [ ] GET \`/api/admin/audit-logs\` 実装
- [ ] GET \`/api/admin/dashboard/stats\` 実装
- [ ] 監査ログUI実装
- [ ] フィルタリング機能
- [ ] 統計ダッシュボードUI
- [ ] グラフ表示（オプション）
- [ ] 単体テスト作成

## 参考
- docs/admin-features.md（セクション4）
- docs/api-specification.md（#14, #15）

## 依存
- #5 データベースマイグレーション

## Phase
Phase 5: 管理者機能
EOF
)" --label "enhancement,phase-5"

gh issue create --title "セキュリティ設定API実装" --body "$(cat <<'EOF'
## 概要
セキュリティ設定の取得・更新APIの実装

## 実装内容

### 1. APIエンドポイント
- GET \`/api/admin/settings/security\` - セキュリティ設定取得
- PUT \`/api/admin/settings/security\` - セキュリティ設定更新

### 2. 設定項目
- fail_lock_threshold（1-100）
- fail_lock_window_hours（1-24）
- fail_lock_duration_hours（1-168）
- otp_expiration_minutes（1-60）
- session_duration_hours（1-720）
- rate_limit_per_minute（1-1000）

### 3. バリデーション
- 各設定値の範囲チェック
- 論理的整合性チェック

### 4. フロントエンド
- \`web/templates/admin/settings.html\`
- 設定フォーム
- デフォルト値リセット機能

## チェックリスト
- [ ] GET \`/api/admin/settings/security\` 実装
- [ ] PUT \`/api/admin/settings/security\` 実装
- [ ] バリデーション実装
- [ ] \`settings.html\` 作成
- [ ] 監査ログ記録
- [ ] 単体テスト作成

## 参考
- docs/admin-features.md（セクション5）
- docs/api-specification.md（#16, #17）

## 依存
- #5 データベースマイグレーション

## Phase
Phase 5: 管理者機能
EOF
)" --label "enhancement,phase-5"

# Phase 6: セキュリティ強化

gh issue create --title "レート制限実装" --body "$(cat <<'EOF'
## 概要
IPアドレスベースのレート制限の実装

## 実装内容

### 1. ミドルウェア
- \`internal/api/middleware/rate_limit.go\`
- IPアドレス取得（X-Forwarded-For考慮）
- SQLite3での実装（デフォルト）

### 2. レート制限設定
- 認証エンドポイント: 1分10回
- その他のエンドポイント: 1分60回
- 管理者API: 1分200回

### 3. ストレージ
- SQLite3テーブル \`rate_limits\` 作成（オプション）
- または メモリ内カウンター（sync.Map）

### 4. レスポンス
- 429 Too Many Requests
- Retry-After ヘッダー

## チェックリスト
- [ ] \`rate_limit.go\` ミドルウェア実装
- [ ] IPアドレス取得ロジック
- [ ] レート制限ストレージ実装
- [ ] エンドポイント別制限設定
- [ ] 429エラーレスポンス
- [ ] Retry-Afterヘッダー
- [ ] クリーンアップ処理
- [ ] 単体テスト作成

## 参考
- docs/security.md（レート制限）
- docs/api-specification.md（レート制限）

## 依存
- #6 基本的なミドルウェア実装

## Phase
Phase 6: セキュリティ強化
EOF
)" --label "enhancement,phase-6,security"

gh issue create --title "CSRF対策実装" --body "$(cat <<'EOF'
## 概要
CSRF（クロスサイトリクエストフォージェリ）対策の実装

## 実装内容

### 1. CSRFミドルウェア
- \`internal/api/middleware/csrf.go\`
- 二重送信Cookie方式
- POST/PUT/DELETEリクエストで検証
- ログイン関連エンドポイントは除外

### 2. トークン生成
- \`internal/utils/csrf.go\`
- 128ビットランダム値
- crypto/rand使用

### 3. 検証ロジック
- Cookie: \`csrf_token\`
- Header: \`X-CSRF-Token\`
- 値の一致確認

### 4. エラーレスポンス
- 403 Forbidden
- error: "csrf_token_invalid"

## チェックリスト
- [ ] \`csrf.go\` ミドルウェア実装
- [ ] トークン生成関数
- [ ] Cookie発行（ログイン時）
- [ ] ヘッダー検証
- [ ] 除外エンドポイント設定
- [ ] エラーレスポンス
- [ ] フロントエンド対応（JSでヘッダー設定）
- [ ] 単体テスト作成

## 参考
- docs/security.md（CSRF対策）

## 依存
- #10 OTP認証（第2段階）実装

## Phase
Phase 6: セキュリティ強化
EOF
)" --label "enhancement,phase-6,security"

gh issue create --title "通知管理API実装（管理者）" --body "$(cat <<'EOF'
## 概要
管理者用通知作成・管理APIの実装

## 実装内容

### 1. APIエンドポイント
- POST \`/api/admin/notifications/broadcast\` - 全ユーザー向け通知
- POST \`/api/admin/notifications/personal\` - 個人向け通知
- DELETE \`/api/admin/notifications/:notification_id\` - 通知削除

### 2. サービス層
- \`internal/services/notification_service.go\`
- 通知作成
- Markdown検証

### 3. バリデーション
- title: 最大200文字
- content: 最大10000文字
- priority: low/normal/high/urgent

## チェックリスト
- [ ] POST \`/api/admin/notifications/broadcast\` 実装
- [ ] POST \`/api/admin/notifications/personal\` 実装
- [ ] DELETE \`/api/admin/notifications/:notification_id\` 実装
- [ ] \`notification_service.go\` 実装
- [ ] バリデーション
- [ ] 監査ログ記録
- [ ] 単体テスト作成

## 参考
- docs/admin-features.md（セクション2）
- docs/api-specification.md（#11, #12, #13）

## 依存
- #16 通知機能実装

## Phase
Phase 5: 管理者機能
EOF
)" --label "enhancement,phase-5"

# Phase 7: テスト・デプロイ

gh issue create --title "統合テスト作成" --body "$(cat <<'EOF'
## 概要
API統合テストとE2Eテストの作成

## 実装内容

### 1. 統合テスト
- \`test/integration/\` ディレクトリ
- 認証フロー完全テスト
- ユーザー管理テスト
- 招待システムテスト

### 2. テストデータベース
- テスト用SQLite3
- テストごとにクリーンアップ

### 3. テストカバレッジ
- 目標: 80%以上
- \`go test -cover\`

### 4. E2Eテスト（オプション）
- Playwright使用
- ログインフロー
- ダッシュボード操作

## チェックリスト
- [ ] 統合テストフレームワーク設定
- [ ] 認証フローテスト
- [ ] ユーザー管理テスト
- [ ] 招待システムテスト
- [ ] nginx連携テスト
- [ ] カバレッジ80%達成
- [ ] CI/CD設定（GitHub Actions）

## 参考
- docs/technology-stack.md（テスト）

## Phase
Phase 7: テスト・デプロイ
EOF
)" --label "enhancement,phase-7,testing"

gh issue create --title "Docker Compose設定" --body "$(cat <<'EOF'
## 概要
本番環境用Docker Compose設定の作成

## 実装内容

### 1. Dockerfile作成
- マルチステージビルド
- Goアプリケーション
- 軽量イメージ（alpine）

### 2. docker-compose.yml
- 認証サーバーコンテナ
- nginxコンテナ
- SQLite3永続化（volume）

### 3. 環境変数
- \`.env.example\` 完成
- 必須環境変数リスト

### 4. ヘルスチェック
- コンテナヘルスチェック設定
- 起動順序制御

## チェックリスト
- [ ] Dockerfile作成
- [ ] docker-compose.yml作成
- [ ] \`.env.example\` 完成
- [ ] volumeマウント設定
- [ ] nginxコンテナ設定
- [ ] ヘルスチェック設定
- [ ] \`docker-compose up\` 動作確認
- [ ] ドキュメント作成（デプロイ手順）

## 参考
- docs/technology-stack.md（インフラ）

## Phase
Phase 7: テスト・デプロイ
EOF
)" --label "enhancement,phase-7"

gh issue create --title "READMEと実装ガイド作成" --body "$(cat <<'EOF'
## 概要
プロジェクトREADMEと実装ガイドの作成

## 実装内容

### 1. README.md更新
- プロジェクト概要
- 機能一覧
- クイックスタート
- デプロイ手順
- ライセンス

### 2. 実装ガイド
- 開発環境セットアップ
- ビルド方法
- テスト実行方法
- デバッグ方法

### 3. API ドキュメント
- Swagger/OpenAPI生成（オプション）
- エンドポイント一覧

### 4. 運用ガイド
- 初期管理者作成
- バックアップ方法
- ログ確認方法

## チェックリスト
- [ ] README.md更新
- [ ] 開発ガイド作成
- [ ] デプロイガイド作成
- [ ] 運用ガイド作成
- [ ] トラブルシューティング追加
- [ ] スクリーンショット追加（オプション）

## Phase
Phase 7: テスト・デプロイ
EOF
)" --label "enhancement,phase-7,documentation"

echo "✅ 全issueの作成が完了しました！"
