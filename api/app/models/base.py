"""Base model class and common mixins for all SQLAlchemy models."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base

__all__ = ["Base", "DataQualityMixin", "ProvenanceMixin", "TimestampMixin"]


class TimestampMixin:
    """Adds created_at and updated_at columns."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class DataQualityMixin:
    """Adds data quality score columns."""

    quality_score: Mapped[float] = mapped_column(Float, default=0.0)
    quality_completeness: Mapped[float] = mapped_column(Float, default=0.0)
    quality_accuracy: Mapped[float] = mapped_column(Float, default=0.0)
    quality_consistency: Mapped[float] = mapped_column(Float, default=0.0)
    quality_timeliness: Mapped[float] = mapped_column(Float, default=0.0)
    quality_validity: Mapped[float] = mapped_column(Float, default=0.0)
    quality_uniqueness: Mapped[float] = mapped_column(Float, default=0.0)
    freshness_hours: Mapped[int] = mapped_column(default=0)


class ProvenanceMixin:
    """Adds source tracking columns."""

    source_system: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    source_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )
    source_record_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    extraction_timestamp: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    raw_data_hash: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )
    transformation_version: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )
