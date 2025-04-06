"""Initial migration

Revision ID: initial_migration
Revises: 
Create Date: 2025-04-06T14:51:00+09:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'initial_migration'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Users テーブルの作成
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('created_at', sa.String(), nullable=False),
        sa.Column('updated_at', sa.String(), nullable=False),
        sa.Column('is_admin', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_locked', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('locked_until', sa.Integer(), nullable=True),
        sa.Column('failed_login_attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_failed_attempt', sa.Integer(), nullable=True),
        sa.Column('last_login', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username')
    )

    # Sessions テーブルの作成
    op.create_table(
        'sessions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.String(), nullable=False),
        sa.Column('expires_at', sa.String(), nullable=False),
        sa.Column('ip_address', sa.String(), nullable=False),
        sa.Column('user_agent', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # LoginAttempts テーブルの作成
    op.create_table(
        'login_attempts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('timestamp', sa.Integer(), nullable=False),
        sa.Column('ip_address', sa.String(), nullable=False),
        sa.Column('user_agent', sa.String(), nullable=False),
        sa.Column('success', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # SystemSettings テーブルの作成
    op.create_table(
        'system_settings',
        sa.Column('key', sa.String(), nullable=False),
        sa.Column('value', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('key')
    )

    # インデックスの作成
    op.create_index('idx_sessions_user_id', 'sessions', ['user_id'])
    op.create_index('idx_login_attempts_user_id', 'login_attempts', ['user_id'])
    op.create_index('idx_login_attempts_timestamp', 'login_attempts', ['timestamp'])

    # デフォルト設定の挿入
    op.bulk_insert(
        sa.table(
            'system_settings',
            sa.column('key', sa.String()),
            sa.column('value', sa.String()),
            sa.column('description', sa.String())
        ),
        [
            {
                'key': 'fail_lock_attempts',
                'value': '5',
                'description': '連続失敗回数のしきい値'
            },
            {
                'key': 'fail_lock_window',
                'value': '30',
                'description': '失敗カウントのウィンドウ（分）'
            },
            {
                'key': 'fail_lock_duration',
                'value': '120',
                'description': 'ロック期間（分）'
            },
            {
                'key': 'session_timeout',
                'value': '24',
                'description': 'セッションタイムアウト（時間）'
            },
            {
                'key': 'min_passphrase_length',
                'value': '32',
                'description': '最小パスフレーズ長'
            },
            {
                'key': 'default_passphrase_length',
                'value': '64',
                'description': 'デフォルトの自動生成パスフレーズ長'
            },
            {
                'key': 'max_passphrase_length',
                'value': '128',
                'description': '最大パスフレーズ長'
            }
        ]
    )


def downgrade():
    # テーブルの削除（逆順）
    op.drop_table('system_settings')
    op.drop_table('login_attempts')
    op.drop_table('sessions')
    op.drop_table('users')

