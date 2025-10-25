# 技術スタック

## 概要

simple-auth の実装に使用する技術スタックの詳細です。

## バックエンド

### 言語・フレームワーク

**推奨: Go (Golang)**

理由:
- 高速な実行速度（auth_requestの応答速度が重要）
- メモリ安全性
- 並行処理が得意（Goroutine）
- シングルバイナリで配布可能
- 豊富なライブラリエコシステム
- 本番環境での実績が豊富

#### 主要ライブラリ

- **Webフレームワーク**: [Gin](https://github.com/gin-gonic/gin)
  - 高速なルーティング
  - ミドルウェアサポート
  - バリデーション機能

- **データベース**: [GORM](https://gorm.io/)
  - ORM（Object-Relational Mapping）
  - マイグレーション機能
  - SQLite3対応

- **Redis クライアント**: [go-redis](https://github.com/redis/go-redis)
  - 高速なRedisクライアント
  - コネクションプーリング

- **パスワードハッシュ**: [argon2](https://pkg.go.dev/golang.org/x/crypto/argon2)
  - Argon2idアルゴリズム
  - 業界標準のハッシュアルゴリズム

- **JWT（オプション）**: [jwt-go](https://github.com/golang-jwt/jwt)
  - セッション以外の認証方式が必要な場合

- **バリデーション**: [validator](https://github.com/go-playground/validator)
  - 構造体ベースのバリデーション

- **環境変数管理**: [godotenv](https://github.com/joho/godotenv)
  - `.env` ファイルのロード

- **ログ**: [zap](https://github.com/uber-go/zap) または [logrus](https://github.com/sirupsen/logrus)
  - 構造化ログ
  - 高速なロギング

- **メール送信**: [gomail](https://github.com/go-gomail/gomail)
  - SMTP経由でメール送信

- **Markdownサニタイズ**: [bluemonday](https://github.com/microcosm-cc/bluemonday)
  - XSS対策
  - HTMLサニタイザー

### プロジェクト構造

```
simple-auth/
├── cmd/
│   └── server/
│       └── main.go              # エントリーポイント
├── internal/
│   ├── api/
│   │   ├── handlers/            # HTTPハンドラ
│   │   │   ├── auth.go
│   │   │   ├── user.go
│   │   │   └── admin.go
│   │   ├── middleware/          # ミドルウェア
│   │   │   ├── auth.go
│   │   │   ├── csrf.go
│   │   │   ├── rate_limit.go
│   │   │   └── logger.go
│   │   └── router.go            # ルーティング設定
│   ├── models/                  # データモデル
│   │   ├── user.go
│   │   ├── notification.go
│   │   └── audit_log.go
│   ├── services/                # ビジネスロジック
│   │   ├── auth_service.go
│   │   ├── user_service.go
│   │   ├── admin_service.go
│   │   └── notification_service.go
│   ├── repositories/            # データアクセス層
│   │   ├── user_repository.go
│   │   └── audit_repository.go
│   ├── cache/                   # Redisキャッシュ
│   │   ├── session.go
│   │   ├── otp.go
│   │   └── fail_lock.go
│   ├── email/                   # メール送信
│   │   └── sender.go
│   ├── config/                  # 設定
│   │   └── config.go
│   └── utils/                   # ユーティリティ
│       ├── hash.go
│       ├── random.go
│       └── validator.go
├── migrations/                  # DBマイグレーション
│   ├── 000001_create_users_table.up.sql
│   ├── 000001_create_users_table.down.sql
│   └── ...
├── web/                         # フロントエンド（静的ファイル）
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   └── templates/               # HTMLテンプレート
│       ├── login.html
│       ├── dashboard.html
│       └── admin.html
├── test/                        # テスト
│   ├── integration/
│   └── unit/
├── scripts/                     # スクリプト
│   ├── setup.sh
│   └── migrate.sh
├── docs/                        # ドキュメント
├── .env.example                 # 環境変数のサンプル
├── Dockerfile
├── docker-compose.yml
├── go.mod
├── go.sum
└── README.md
```

## データベース

### SQLite3

- バージョン: 3.35以上（JSON関数サポート）
- 理由:
  - **セットアップが簡単**: ファイルベース、サーバー不要
  - **依存関係が少ない**: デプロイが容易
  - **バックアップが簡単**: ファイルコピーだけ
  - **軽量**: 実行ファイルとDBファイルだけで動作
  - **ACID準拠**: トランザクションサポート
  - **十分なパフォーマンス**: 小〜中規模（数千ユーザー）まで対応可能
  - **JSON関数サポート**: audit_logsのdetailsカラムで使用

- 推奨設定:
  - **WALモード**: 並行読み取りのパフォーマンス向上
  - **外部キー制約**: データ整合性を保証
  - **PRAGMA設定**: キャッシュサイズ、同期モードなどの最適化

### Redis

- バージョン: 6以上
- 用途:
  - セッション管理
  - OTP保存
  - fail lock管理
  - レート制限
  - キャッシュ

## フロントエンド

### シンプルな構成（推奨）

- **HTML5 + CSS3 + Vanilla JavaScript**
  - サーバーサイドレンダリング（Go テンプレート）
  - 軽量・高速
  - 複雑なビルドプロセス不要

- **CSSフレームワーク**: [Tailwind CSS](https://tailwindcss.com/) または [Bootstrap 5](https://getbootstrap.com/)
  - レスポンシブデザイン
  - モダンなUI

- **JavaScriptライブラリ**:
  - [Axios](https://axios-http.com/) - HTTP クライアント
  - [Marked.js](https://marked.js.org/) - Markdown レンダリング（ダッシュボード表示用）
  - [DOMPurify](https://github.com/cure53/DOMPurify) - XSS対策（クライアント側でもサニタイズ）

### 高度な構成（オプション）

SPA（Single Page Application）として実装する場合：

- **フレームワーク**: [Vue.js](https://vuejs.org/) または [React](https://react.dev/)
- **ビルドツール**: [Vite](https://vitejs.dev/)
- **状態管理**: Pinia（Vue）または Zustand（React）
- **ルーティング**: Vue Router または React Router

## インフラ

### 開発環境

- **Docker Compose**
  - Redis コンテナ
  - アプリケーション コンテナ（SQLite3はファイルベース）
  - nginx コンテナ（auth_requestのテスト用）

### 本番環境

#### オプション1: VPS / 専用サーバー

- **OS**: Ubuntu 22.04 LTS または Rocky Linux 9
- **Webサーバー**: nginx
- **アプリケーション**: systemdでサービス化
- **データベース**: SQLite3（ファイルベース、アプリケーションと同じサーバー）
- **Redis**: Redis（同じサーバーまたは別サーバー）
- **リバースプロキシ**: nginx
- **SSL/TLS**: Let's Encrypt（certbot）

#### オプション2: コンテナオーケストレーション

- **Kubernetes** または **Docker Swarm**
- **ロードバランサー**: nginx Ingress Controller
- **永続化ストレージ**: PersistentVolume（SQLite3 DBファイル, Redisデータ用）

#### オプション3: クラウド

- **AWS**:
  - EC2（アプリケーション + SQLite3）
  - ElastiCache for Redis
  - Application Load Balancer
  - Route 53（DNS）
  - ACM（SSL証明書）
  - EBS（SQLite3 DBファイルの永続化）

- **GCP**:
  - Compute Engine（アプリケーション + SQLite3）
  - Memorystore for Redis
  - Cloud Load Balancing
  - Cloud DNS
  - Persistent Disk（SQLite3 DBファイルの永続化）

## CI/CD

### GitHub Actions

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-go@v4
        with:
          go-version: '1.21'
      - name: Run tests
        run: go test ./...
      - name: Lint
        run: |
          go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest
          golangci-lint run

  build:
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-go@v4
        with:
          go-version: '1.21'
      - name: Build
        run: go build -o simple-auth ./cmd/server
```

### デプロイ

- **開発環境**: Git push → GitHub Actions → Docker イメージビルド → デプロイ
- **本番環境**: Git tag → GitHub Actions → Docker イメージビルド → 手動承認 → デプロイ

## モニタリング・ロギング

### ログ

- **アプリケーションログ**: zap（構造化ログ、JSON形式）
- **nginxアクセスログ**: `/var/log/nginx/access.log`
- **SQLite3**: 必要に応じてクエリログをアプリケーション側で記録

### メトリクス

- **Prometheus** + **Grafana**
  - アプリケーションメトリクス（リクエスト数、レスポンスタイム、エラー率）
  - データベースメトリクス（接続数、クエリ実行時間）
  - Redisメトリクス（メモリ使用量、ヒット率）

- **Exporter**:
  - [redis_exporter](https://github.com/oliver006/redis_exporter)
  - カスタムメトリクス（Go アプリケーション内で Prometheus クライアントライブラリを使用）
    - SQLite3のメトリクス（DBファイルサイズ、クエリ実行時間など）

### アラート

- **Prometheus Alertmanager**
  - 認証失敗率が高い
  - レスポンスタイムが遅い
  - データベース接続エラー
  - Redis接続エラー

### トレーシング（オプション）

- **OpenTelemetry** + **Jaeger**
  - 分散トレーシング
  - パフォーマンスボトルネックの特定

## セキュリティツール

### 脆弱性スキャン

- **Snyk** または **Dependabot**
  - 依存パッケージの脆弱性検出
  - 自動PR作成

### コード品質

- **golangci-lint**
  - 静的解析
  - コードスタイルチェック

### ペネトレーションテスト（オプション）

- **OWASP ZAP**
  - セキュリティスキャン
  - 脆弱性検出

## 開発ツール

### エディタ / IDE

- **Visual Studio Code**
  - Go拡張機能
  - Prettier（フロントエンド用）
  - ESLint（JavaScript用）

- **GoLand**（JetBrains製）
  - Go専用IDE
  - 強力なリファクタリング機能

### API テスト

- **Postman** または **Insomnia**
  - APIエンドポイントのテスト
  - コレクション共有

- **curl** または **httpie**
  - コマンドラインでのAPIテスト

### データベース管理

- **pgAdmin**（PostgreSQL）
- **RedisInsight**（Redis）

## バージョン管理

- **Git**
- **GitHub**（リポジトリホスティング）
- **ブランチ戦略**: Git Flow または GitHub Flow

## ドキュメント

- **Markdown** (このドキュメント群)
- **Swagger / OpenAPI**（API仕様書の自動生成、オプション）
  - [swaggo/swag](https://github.com/swaggo/swag) - Goのコメントから自動生成

## テスト

### 単体テスト

- **testing**（Go標準ライブラリ）
- **testify**（アサーションライブラリ）
  - [stretchr/testify](https://github.com/stretchr/testify)

### 統合テスト

- **testcontainers-go**
  - Dockerコンテナを使ったテスト
  - PostgreSQL、Redisのテスト環境を自動構築

### E2Eテスト（オプション）

- **Playwright** または **Selenium**
  - ブラウザ自動化
  - フローテスト

## パフォーマンス

### ベンチマーク

- **Go benchmarks**
  - `go test -bench=.`

### 負荷テスト

- **k6** または **Apache JMeter**
  - 認証フローの負荷テスト
  - auth_requestエンドポイントのパフォーマンステスト

### 目標パフォーマンス

- auth_request エンドポイント:
  - 平均レスポンスタイム: 10ms以下
  - 95パーセンタイル: 50ms以下
  - 同時接続数: 1000以上

- ログインフロー:
  - 第1段階（パスフレーズ認証）: 500ms以下
  - 第2段階（OTP認証）: 200ms以下

## 推奨環境

### 開発環境

- **CPU**: 2コア以上
- **メモリ**: 4GB以上
- **ストレージ**: 20GB以上

### 本番環境（小規模: ~1000ユーザー）

- **CPU**: 2コア
- **メモリ**: 4GB
- **ストレージ**: 50GB（SSD推奨）
- **帯域幅**: 100Mbps

### 本番環境（中規模: ~10000ユーザー）

- **CPU**: 4コア
- **メモリ**: 8GB
- **ストレージ**: 100GB（SSD推奨）
- **帯域幅**: 1Gbps

## まとめ

このスタックは、以下の特徴を持ちます：

✅ **高速**: Go + Redis によるパフォーマンス最適化
✅ **セキュア**: 業界標準のセキュリティプラクティス
✅ **スケーラブル**: 水平スケーリング可能
✅ **メンテナブル**: シンプルなアーキテクチャ
✅ **実績**: 本番環境で広く使われている技術

必要に応じて、プロジェクトの規模や要件に合わせて調整してください。
