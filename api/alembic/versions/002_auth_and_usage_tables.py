"""Add auth and usage tables.

Revision ID: 002
Revises: 001
Create Date: 2026-02-18

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _create_enum() -> None:
    """Create the tier enum type."""
    tier_enum = postgresql.ENUM(
        "free", "pro", "business", "enterprise",
        name="tierenum",
        schema="parcel",
        create_type=False,
    )
    tier_enum.create(op.get_bind(), checkfirst=True)


def _create_accounts_table() -> None:
    """Create accounts table."""
    op.create_table(
        "accounts",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        # Identity
        sa.Column("email", sa.String(255), unique=True, index=True, nullable=False),
        sa.Column("email_verified", sa.Boolean, default=False, nullable=False),
        # Profile
        sa.Column("name", sa.String(200), nullable=True),
        sa.Column("company", sa.String(200), nullable=True),
        # Billing
        sa.Column("stripe_customer_id", sa.String(50), index=True, nullable=True),
        sa.Column(
            "tier",
            postgresql.ENUM(
                "free", "pro", "business", "enterprise",
                name="tierenum",
                schema="parcel",
                create_type=False,
            ),
            default="free",
            nullable=False,
        ),
        # Status
        sa.Column("is_active", sa.Boolean, default=True, nullable=False),
        # TimestampMixin
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        schema="parcel",
    )


def _create_api_keys_table() -> None:
    """Create api_keys table."""
    op.create_table(
        "api_keys",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("key_hash", sa.String(64), unique=True, index=True, nullable=False),
        sa.Column("key_prefix", sa.String(10), nullable=False),
        # Account FK
        sa.Column(
            "account_id", sa.Integer,
            sa.ForeignKey("parcel.accounts.id"),
            index=True, nullable=False,
        ),
        # Key metadata
        sa.Column("name", sa.String(100), nullable=True),
        sa.Column(
            "tier",
            postgresql.ENUM(
                "free", "pro", "business", "enterprise",
                name="tierenum",
                schema="parcel",
                create_type=False,
            ),
            default="free",
            nullable=False,
        ),
        sa.Column("scopes", postgresql.JSONB, nullable=False),
        # Status
        sa.Column("is_active", sa.Boolean, default=True, nullable=False),
        sa.Column("last_used", sa.DateTime, nullable=True),
        # Limits
        sa.Column("rate_limit_override", sa.Integer, nullable=True),
        sa.Column("daily_limit_override", sa.Integer, nullable=True),
        # Expiration
        sa.Column("expires_at", sa.DateTime, nullable=True),
        # TimestampMixin
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        schema="parcel",
    )


def _create_usage_records_table() -> None:
    """Create usage_records table."""
    op.create_table(
        "usage_records",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "account_id", sa.Integer,
            sa.ForeignKey("parcel.accounts.id"),
            index=True, nullable=False,
        ),
        sa.Column(
            "api_key_id", sa.Integer,
            sa.ForeignKey("parcel.api_keys.id"),
            index=True, nullable=False,
        ),
        # Period
        sa.Column("usage_date", sa.Date, index=True, nullable=False),
        # Counts
        sa.Column("queries_count", sa.Integer, default=0, nullable=False),
        sa.Column("queries_billable", sa.Integer, default=0, nullable=False),
        # Breakdown
        sa.Column("property_lookups", sa.Integer, default=0, nullable=False),
        sa.Column("property_searches", sa.Integer, default=0, nullable=False),
        sa.Column("comparables_requests", sa.Integer, default=0, nullable=False),
        sa.Column("batch_requests", sa.Integer, default=0, nullable=False),
        # Cost
        sa.Column("estimated_cost", sa.Float, default=0.0, nullable=False),
        schema="parcel",
    )


def _create_usage_events_table() -> None:
    """Create usage_events table."""
    op.create_table(
        "usage_events",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "api_key_id", sa.Integer,
            sa.ForeignKey("parcel.api_keys.id"),
            index=True, nullable=False,
        ),
        # Event details
        sa.Column("endpoint", sa.String(100), index=True, nullable=False),
        sa.Column("method", sa.String(10), nullable=False),
        sa.Column("query_count", sa.Integer, default=1, nullable=False),
        # Response
        sa.Column("status_code", sa.Integer, nullable=False),
        sa.Column("response_time_ms", sa.Integer, nullable=False),
        # Timestamp
        sa.Column("timestamp", sa.DateTime, index=True, nullable=False),
        schema="parcel",
    )


def upgrade() -> None:
    """Create auth and usage tables."""
    _create_enum()
    _create_accounts_table()
    _create_api_keys_table()
    _create_usage_records_table()
    _create_usage_events_table()


def downgrade() -> None:
    """Drop auth and usage tables."""
    op.drop_table("usage_events", schema="parcel")
    op.drop_table("usage_records", schema="parcel")
    op.drop_table("api_keys", schema="parcel")
    op.drop_table("accounts", schema="parcel")
    # Don't drop the enum type — it may be used elsewhere
