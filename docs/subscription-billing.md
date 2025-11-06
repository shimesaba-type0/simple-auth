# サブスクリプション・課金機能（オプション）

## 概要

**この仕様はオプション機能です。** 将来的に、認証サーバーに課金・サブスクリプション機能を追加する場合の設計です。

## 課金ポリシー：認証サーバーで一元管理（推奨）

### アーキテクチャ

```
[ユーザー]
    ↓
[認証サーバー（課金管理）]
    ├→ [バックエンドサービスA] - 課金ロジックなし
    ├→ [バックエンドサービスB] - 課金ロジックなし
    └→ [バックエンドサービスC] - 課金ロジックなし
```

### なぜ認証サーバーで課金するのか

✅ **一元管理** - ユーザー情報とサブスクリプション情報が同じ場所にある
✅ **疎結合** - バックエンドサービスは課金ロジックを持たない（シンプル）
✅ **UX** - ユーザーは1箇所で課金を管理できる
✅ **SSO思想に合致** - 1つのアカウントで複数サービスを利用

## 課金モデル

### モデル1: プラン型（推奨・シンプル）

| プラン | 価格 | 機能 |
|--------|------|------|
| **Free** | 無料 | - 基本サービスのみアクセス可能<br>- ダッシュボードカスタマイズ制限<br>- ログイン履歴30日間 |
| **Premium** | ¥1,000/月 | - 全サービスアクセス可能<br>- ダッシュボード完全カスタマイズ<br>- ログイン履歴1年間<br>- 優先サポート |
| **Enterprise** | 要相談 | - Premiumの全機能<br>- カスタムドメイン<br>- SLA保証<br>- 専用サポート |

### モデル2: サービス単位課金

```
基本料金: ¥500/月
追加サービス: ¥300/月/サービス
```

ユーザーは利用したいサービスだけ選択して課金。

### モデル3: ユーザー数課金（企業向け）

```
1-10ユーザー: ¥5,000/月
11-50ユーザー: ¥20,000/月
51-100ユーザー: ¥35,000/月
101ユーザー以上: 要相談
```

## データベース設計

### subscriptions テーブル

```sql
CREATE TABLE subscriptions (
    id TEXT PRIMARY KEY,  -- UUID
    user_id TEXT NOT NULL UNIQUE,
    plan TEXT NOT NULL CHECK (plan IN ('free', 'premium', 'enterprise')),
    status TEXT NOT NULL CHECK (status IN ('active', 'canceled', 'past_due', 'trialing')),
    current_period_start TEXT NOT NULL,
    current_period_end TEXT NOT NULL,
    cancel_at TEXT,  -- キャンセル予定日時
    canceled_at TEXT,  -- キャンセル実行日時
    trial_end TEXT,  -- トライアル終了日時
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);
```

### payment_methods テーブル

```sql
CREATE TABLE payment_methods (
    id TEXT PRIMARY KEY,  -- UUID
    user_id TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('card', 'bank_transfer', 'paypal')),
    is_default INTEGER NOT NULL DEFAULT 0,
    -- カード情報（Stripe/PAY.JPなどのトークン）
    provider TEXT NOT NULL,  -- 'stripe', 'payjp', etc.
    provider_payment_method_id TEXT NOT NULL,  -- 決済プロバイダーのID
    last4 TEXT,  -- カード下4桁
    brand TEXT,  -- Visa, Mastercard, etc.
    exp_month INTEGER,
    exp_year INTEGER,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_payment_methods_user_id ON payment_methods(user_id);
```

### invoices テーブル

```sql
CREATE TABLE invoices (
    id TEXT PRIMARY KEY,  -- UUID
    user_id TEXT NOT NULL,
    subscription_id TEXT NOT NULL,
    amount INTEGER NOT NULL,  -- 金額（円、整数）
    currency TEXT NOT NULL DEFAULT 'JPY',
    status TEXT NOT NULL CHECK (status IN ('draft', 'open', 'paid', 'void', 'uncollectible')),
    invoice_pdf_url TEXT,  -- 請求書PDFのURL
    hosted_invoice_url TEXT,  -- 決済ページのURL
    due_date TEXT,
    paid_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (subscription_id) REFERENCES subscriptions(id) ON DELETE CASCADE
);

CREATE INDEX idx_invoices_user_id ON invoices(user_id);
CREATE INDEX idx_invoices_status ON invoices(status);
```

### service_access テーブル（サービス単位課金の場合）

```sql
CREATE TABLE service_access (
    id TEXT PRIMARY KEY,  -- UUID
    user_id TEXT NOT NULL,
    service_id TEXT NOT NULL,  -- 'service-a', 'service-b', etc.
    granted INTEGER NOT NULL DEFAULT 1,  -- アクセス権限 (0=なし, 1=あり)
    granted_at TEXT NOT NULL DEFAULT (datetime('now')),
    revoked_at TEXT,
    UNIQUE(user_id, service_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_service_access_user_id ON service_access(user_id);
CREATE INDEX idx_service_access_service_id ON service_access(service_id);
```

## API エンドポイント

### 1. サブスクリプション情報取得

```
GET /api/user/subscription
```

#### レスポンス
```json
{
  "success": true,
  "data": {
    "plan": "premium",
    "status": "active",
    "current_period_start": "2025-10-01T00:00:00Z",
    "current_period_end": "2025-11-01T00:00:00Z",
    "cancel_at": null,
    "trial_end": null
  }
}
```

### 2. プラン変更

```
POST /api/user/subscription/upgrade
```

#### リクエスト
```json
{
  "plan": "premium"
}
```

#### レスポンス
```json
{
  "success": true,
  "message": "プランをPremiumに変更しました",
  "hosted_page_url": "https://checkout.stripe.com/..."
}
```

### 3. サブスクリプションキャンセル

```
POST /api/user/subscription/cancel
```

#### リクエスト
```json
{
  "immediate": false  // false: 期間終了時にキャンセル, true: 即座にキャンセル
}
```

#### レスポンス
```json
{
  "success": true,
  "message": "サブスクリプションをキャンセルしました",
  "cancel_at": "2025-11-01T00:00:00Z"
}
```

### 4. 請求履歴取得

```
GET /api/user/invoices?limit=10&offset=0
```

#### レスポンス
```json
{
  "success": true,
  "data": {
    "total": 12,
    "invoices": [
      {
        "id": "inv_123",
        "amount": 1000,
        "currency": "JPY",
        "status": "paid",
        "invoice_pdf_url": "https://...",
        "paid_at": "2025-10-01T10:00:00Z",
        "created_at": "2025-10-01T09:00:00Z"
      }
    ]
  }
}
```

### 5. 支払い方法登録

```
POST /api/user/payment-methods
```

#### リクエスト
```json
{
  "payment_method_id": "pm_xxx",  // Stripeなどのトークン
  "is_default": true
}
```

## 決済プロバイダー統合

### 推奨: Stripe

- **Stripe Checkout** - ホスティングされた決済ページ
- **Stripe Billing** - サブスクリプション管理
- **Webhooks** - 決済イベントの通知

#### Webhook処理

```
POST /api/webhooks/stripe
```

処理するイベント:
- `invoice.paid` - 支払い成功
- `invoice.payment_failed` - 支払い失敗
- `customer.subscription.created` - サブスクリプション作成
- `customer.subscription.updated` - サブスクリプション更新
- `customer.subscription.deleted` - サブスクリプション削除

### 日本向け: PAY.JP

Stripeの代替として、日本市場に特化したPAY.JPも選択肢。

## アクセス制御

### auth_request でのプランチェック

```go
func VerifyAuthHandler(c *gin.Context) {
    // セッション検証
    sessionID, _ := c.Cookie("auth_session")
    session := getSession(sessionID)

    // サブスクリプションチェック
    subscription := getSubscription(session.UserID)

    // サービスへのアクセス権限チェック
    requestedService := c.GetHeader("X-Original-URI") // e.g., "/service-a/..."

    if !hasAccess(subscription, requestedService) {
        c.Header("X-Auth-Redirect", "/dashboard/upgrade")
        c.Status(403)
        return
    }

    // 認証成功
    c.Header("X-Auth-User", session.Email)
    c.Header("X-Auth-Plan", subscription.Plan)
    c.Status(200)
}
```

### プラン別アクセス制御

```go
var serviceAccessControl = map[string][]string{
    "service-a": {"free", "premium", "enterprise"},
    "service-b": {"premium", "enterprise"},
    "service-c": {"enterprise"},
}

func hasAccess(subscription *Subscription, serviceURI string) bool {
    // serviceURIからサービスIDを抽出
    serviceID := extractServiceID(serviceURI) // e.g., "service-a"

    allowedPlans := serviceAccessControl[serviceID]
    return contains(allowedPlans, subscription.Plan)
}
```

## ダッシュボード UI

### サブスクリプション管理画面

```
/dashboard/subscription
```

表示内容:
- 現在のプラン
- 次回請求日
- 支払い方法
- プラン変更ボタン
- 請求履歴

### プランアップグレード画面

```
/dashboard/upgrade
```

プラン比較表:
- 各プランの機能一覧
- 価格
- アップグレードボタン

## セキュリティ考慮事項

### 1. 決済情報の保存

⚠️ **クレジットカード情報を直接保存しない**
- Stripe/PAY.JPなどのトークンのみ保存
- PCI DSS準拠は決済プロバイダーに任せる

### 2. Webhook検証

```go
func StripeWebhookHandler(c *gin.Context) {
    payload, _ := c.GetRawData()
    signature := c.GetHeader("Stripe-Signature")

    // 署名検証
    event, err := webhook.ConstructEvent(payload, signature, webhookSecret)
    if err != nil {
        c.Status(400)
        return
    }

    // イベント処理
    handleStripeEvent(event)
}
```

### 3. 不正利用対策

- 同じメールアドレスでの複数アカウント作成制限
- トライアル期間の悪用防止
- プラン変更の頻度制限

## トライアル期間

### 無料トライアル（14日間）

```go
func CreateUser(email, passphrase string) (*User, error) {
    user := createUser(email, passphrase)

    // トライアルサブスクリプションを自動作成
    subscription := &Subscription{
        UserID: user.ID,
        Plan:   "premium",
        Status: "trialing",
        TrialEnd: time.Now().Add(14 * 24 * time.Hour),
        CurrentPeriodEnd: time.Now().Add(14 * 24 * time.Hour),
    }

    saveSubscription(subscription)
    return user, nil
}
```

## まとめ

### 実装優先度

1. **Phase 1（必須）**: 基本的な認証機能
2. **Phase 2（推奨）**: ダッシュボード、通知機能
3. **Phase 3（オプション）**: サブスクリプション・課金機能

### 課金機能のメリット

✅ **収益化** - サービスを持続可能にする
✅ **一元管理** - 認証とサブスクリプションが統合
✅ **疎結合** - バックエンドは課金ロジックを持たない
✅ **UX** - ユーザーは1箇所で管理

### 推奨決済プロバイダー

- **グローバル**: Stripe
- **日本**: PAY.JP
- **エンタープライズ**: 請求書払い（手動処理）
