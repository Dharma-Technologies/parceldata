"""API key and account models for authentication and billing."""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.usage import UsageRecord

__all__ = ["APIKey", "Account", "TierEnum"]


class TierEnum(str, enum.Enum):
    """Account and API key tier levels."""

    FREE = "free"
    PRO = "pro"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"


class Account(Base, TimestampMixin):
    """User account for API access and billing."""

    __tablename__ = "accounts"
    __table_args__ = {"schema": "parcel"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Identity
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    # Profile
    name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    company: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Billing
    stripe_customer_id: Mapped[str | None] = mapped_column(
        String(50), index=True, nullable=True
    )
    tier: Mapped[TierEnum] = mapped_column(
        Enum(TierEnum, schema="parcel"), default=TierEnum.FREE
    )

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    api_keys: Mapped[list[APIKey]] = relationship(
        "APIKey", back_populates="account"
    )
    usage_records: Mapped[list[UsageRecord]] = relationship(
        "UsageRecord", back_populates="account"
    )


class APIKey(Base, TimestampMixin):
    """API key for authenticating requests."""

    __tablename__ = "api_keys"
    __table_args__ = {"schema": "parcel"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    key_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    key_prefix: Mapped[str] = mapped_column(String(10))

    # Account
    account_id: Mapped[int] = mapped_column(
        ForeignKey("parcel.accounts.id"), index=True
    )

    # Key metadata
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tier: Mapped[TierEnum] = mapped_column(
        Enum(TierEnum, schema="parcel", create_type=False), default=TierEnum.FREE
    )
    scopes: Mapped[list[object]] = mapped_column(JSONB, default=["read"])

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_used: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Limits
    rate_limit_override: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    daily_limit_override: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )

    # Expiration
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    account: Mapped[Account] = relationship(
        "Account", back_populates="api_keys"
    )
