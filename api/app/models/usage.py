"""Usage tracking models for API metering and billing."""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.api_key import Account

__all__ = ["UsageEvent", "UsageRecord"]


class UsageRecord(Base):
    """Daily aggregate usage record per API key."""

    __tablename__ = "usage_records"
    __table_args__ = {"schema": "parcel"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(
        ForeignKey("parcel.accounts.id"), index=True
    )
    api_key_id: Mapped[int] = mapped_column(
        ForeignKey("parcel.api_keys.id"), index=True
    )

    # Period
    usage_date: Mapped[date] = mapped_column(Date, index=True)

    # Counts
    queries_count: Mapped[int] = mapped_column(Integer, default=0)
    queries_billable: Mapped[int] = mapped_column(Integer, default=0)

    # Breakdown by endpoint
    property_lookups: Mapped[int] = mapped_column(Integer, default=0)
    property_searches: Mapped[int] = mapped_column(Integer, default=0)
    comparables_requests: Mapped[int] = mapped_column(Integer, default=0)
    batch_requests: Mapped[int] = mapped_column(Integer, default=0)

    # Costs (for metered billing)
    estimated_cost: Mapped[float] = mapped_column(Float, default=0.0)

    # Relationships
    account: Mapped[Account] = relationship(
        "Account", back_populates="usage_records"
    )


class UsageEvent(Base):
    """Individual API usage event for detailed tracking."""

    __tablename__ = "usage_events"
    __table_args__ = {"schema": "parcel"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    api_key_id: Mapped[int] = mapped_column(
        ForeignKey("parcel.api_keys.id"), index=True
    )

    # Event details
    endpoint: Mapped[str] = mapped_column(String(100), index=True)
    method: Mapped[str] = mapped_column(String(10))
    query_count: Mapped[int] = mapped_column(Integer, default=1)

    # Response
    status_code: Mapped[int] = mapped_column(Integer)
    response_time_ms: Mapped[int] = mapped_column(Integer)

    # Timestamp
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )
