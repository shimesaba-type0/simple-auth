# 一般ユーザー機能

## 概要

一般ユーザーが利用できる機能の詳細仕様です。

## 1. 認証

- 事前共有パスフレーズ（64文字）+ メールOTP による2段階認証
- 詳細は [認証フロー](./authentication-flow.md) を参照

## 2. ダッシュボード

### 2.1 ダッシュボードURL

```
/dashboard
```

### 2.2 ダッシュボードの構成

ダッシュボードは以下のセクションで構成されます：

#### ヘッダー
- ユーザー名 / メールアドレス表示
- ログアウトボタン
- 設定ボタン

#### 管理者通知欄
- 管理者が設定した全ユーザー向けの通知を表示
- 新着通知は目立つように表示（未読バッジなど）
- 通知の既読管理
- 例: システムメンテナンス情報、重要なお知らせ

#### 個人通知欄
- ユーザー個人宛の通知を表示
- 管理者が特定ユーザーに送信した通知
- システムからの通知（ログイン履歴の異常など）
- 既読/未読管理

#### カスタマイズエリア
- ユーザーが自由に編集可能なエリア
- Markdown形式でコンテンツを作成可能
- 用途例:
  - よく使うリンク集
  - メモ
  - TODO リスト
  - 個人用のドキュメント

#### 最近のログイン履歴
- 直近10件のログイン履歴を表示
- 表示内容:
  - ログイン日時
  - IPアドレス
  - User-Agent（ブラウザ情報）
  - ログイン結果（成功/失敗）

### 2.3 ダッシュボードのカスタマイズ

#### エンドポイント
```
PUT /api/user/dashboard
```

#### リクエスト
```json
{
  "content": "# My Dashboard\n\n## Links\n- [Link 1](https://example.com)\n- [Link 2](https://example.com)\n\n## Notes\n..."
}
```

#### レスポンス
```json
{
  "success": true,
  "message": "ダッシュボードを更新しました"
}
```

#### 制限事項
- Markdown のみ対応（サニタイズ処理を実施）
- 最大文字数: 10,000文字
- 画像の埋め込みは外部URL参照のみ（アップロード非対応）

## 3. 通知管理

### 3.1 通知一覧取得

#### エンドポイント
```
GET /api/user/notifications?type=admin&unread_only=false
```

#### パラメータ
- `type`: `admin`（管理者通知）または `personal`（個人通知）
- `unread_only`: `true` で未読のみ、`false` で全件

#### レスポンス
```json
{
  "notifications": [
    {
      "id": "notif_123",
      "type": "admin",
      "title": "システムメンテナンスのお知らせ",
      "content": "2025年10月25日 02:00-04:00 にメンテナンスを実施します",
      "created_at": "2025-10-23T10:00:00Z",
      "read": false
    },
    {
      "id": "notif_124",
      "type": "personal",
      "title": "新しいデバイスからのログイン",
      "content": "192.168.1.100 から新しいデバイスでログインがありました",
      "created_at": "2025-10-23T12:00:00Z",
      "read": true
    }
  ]
}
```

### 3.2 通知を既読にする

#### エンドポイント
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

## 4. ログアウト

### エンドポイント
```
POST /api/auth/logout
```

### 処理内容
- セッションを無効化
- セッションCookieを削除
- ログアウトを監査ログに記録
- ログインページにリダイレクト

## 5. プロフィール設定

### 5.1 プロフィール表示

#### エンドポイント
```
GET /api/user/profile
```

#### レスポンス
```json
{
  "user_id": "user_123",
  "email": "user@example.com",
  "display_name": "User Name",
  "created_at": "2025-01-01T00:00:00Z",
  "last_login": "2025-10-23T14:30:00Z"
}
```

### 5.2 プロフィール更新

#### エンドポイント
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

## 6. ログイン履歴確認

### エンドポイント
```
GET /api/user/login-history?limit=50&offset=0
```

#### パラメータ
- `limit`: 取得件数（最大100）
- `offset`: オフセット（ページネーション用）

#### レスポンス
```json
{
  "total": 250,
  "login_history": [
    {
      "id": "log_123",
      "login_at": "2025-10-23T14:30:00Z",
      "ip_address": "192.168.1.1",
      "user_agent": "Mozilla/5.0 ...",
      "result": "success",
      "logout_at": null
    },
    {
      "id": "log_122",
      "login_at": "2025-10-22T10:00:00Z",
      "ip_address": "192.168.1.1",
      "user_agent": "Mozilla/5.0 ...",
      "result": "success",
      "logout_at": "2025-10-22T18:00:00Z"
    },
    {
      "id": "log_121",
      "login_at": "2025-10-21T15:00:00Z",
      "ip_address": "203.0.113.1",
      "user_agent": "curl/7.68.0",
      "result": "failed",
      "logout_at": null
    }
  ]
}
```

## 7. fail lock 状態の確認

### エンドポイント
```
GET /api/user/lock-status
```

#### レスポンス（ロックされていない場合）
```json
{
  "locked": false,
  "failed_attempts": 2,
  "remaining_attempts": 3
}
```

#### レスポンス（ロックされている場合）
```json
{
  "locked": true,
  "locked_until": "2025-10-23T20:30:00Z",
  "reason": "5回の認証失敗"
}
```

## UI/UX 要件

### レスポンシブデザイン
- デスクトップ、タブレット、スマートフォンに対応
- モバイルファーストのデザイン

### アクセシビリティ
- WCAG 2.1 レベルAA準拠
- キーボードナビゲーション対応
- スクリーンリーダー対応

### パフォーマンス
- ダッシュボードの初回読み込み: 1秒以内
- 通知の取得: 500ms以内

### セキュリティ
- XSS対策: Markdownのサニタイズ
- CSRF対策: すべての状態変更APIにCSRFトークン必須
