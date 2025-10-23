# Simple Auth - 多段認証サーバー 仕様書

## 概要

nginx の auth_request に対応した、多段認証サーバーです。

### 認証方式

1. **第1段階**: 事前共有パスフレーズ（64文字）
2. **第2段階**: メールアドレスでのOTP（ワンタイムパスワード）

### 主な機能

- ユーザー認証（2FA）
- カスタマイズ可能なダッシュボード
- nginx auth_request 連携
- ユーザー管理（管理者機能）
- fail lock機能（ブルートフォース対策）
- 通知機能（管理者通知・個人通知）

## ドキュメント構成

- [認証フロー](./authentication-flow.md) - 認証の詳細仕様
- [一般ユーザー機能](./user-features.md) - 一般ユーザーができること
- [管理者機能](./admin-features.md) - 管理者ができること
- [nginx連携](./nginx-integration.md) - nginx auth_request の統合方法
- [セキュリティ](./security.md) - セキュリティ要件と対策
- [データベース設計](./database-schema.md) - DB スキーマ
- [API仕様](./api-specification.md) - REST API エンドポイント
- [技術スタック](./technology-stack.md) - 使用技術とアーキテクチャ

## 設計思想

- **パスワードマネージャー前提**: 64文字のパスフレーズは、パスワードマネージャーで管理することを想定
- **セキュリティ重視**: fail lock、レート制限、監査ログなど
- **高速応答**: nginx auth_request は頻繁に呼ばれるため、Redisによるセッションキャッシュ
- **柔軟性**: ユーザーごとにカスタマイズ可能なダッシュボード
