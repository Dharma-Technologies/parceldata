"""Tests for base model mixins."""

from __future__ import annotations

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import (
    Base,
    DataQualityMixin,
    ProvenanceMixin,
    TimestampMixin,
)


class _Timestamped(Base, TimestampMixin):
    """Dummy model to verify TimestampMixin columns."""

    __tablename__ = "_test_timestamped"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)


class _Quality(Base, DataQualityMixin):
    """Dummy model to verify DataQualityMixin columns."""

    __tablename__ = "_test_quality"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)


class _Provenance(Base, ProvenanceMixin):
    """Dummy model to verify ProvenanceMixin columns."""

    __tablename__ = "_test_provenance"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)


def test_timestamp_mixin_columns() -> None:
    """TimestampMixin adds created_at and updated_at."""
    cols = {c.name for c in _Timestamped.__table__.columns}
    assert "created_at" in cols
    assert "updated_at" in cols
    assert isinstance(
        _Timestamped.__table__.c.created_at.type, DateTime
    )


def test_data_quality_mixin_columns() -> None:
    """DataQualityMixin adds quality score columns."""
    cols = {c.name for c in _Quality.__table__.columns}
    expected = {
        "quality_score",
        "quality_completeness",
        "quality_accuracy",
        "quality_consistency",
        "quality_timeliness",
        "quality_validity",
        "quality_uniqueness",
        "freshness_hours",
    }
    assert expected.issubset(cols)
    assert isinstance(
        _Quality.__table__.c.quality_score.type, Float
    )


def test_provenance_mixin_columns() -> None:
    """ProvenanceMixin adds source tracking columns."""
    cols = {c.name for c in _Provenance.__table__.columns}
    expected = {
        "source_system",
        "source_type",
        "source_record_id",
        "extraction_timestamp",
        "raw_data_hash",
        "transformation_version",
    }
    assert expected.issubset(cols)
    assert isinstance(
        _Provenance.__table__.c.source_system.type, String
    )


def test_provenance_fields_nullable() -> None:
    """All provenance fields should be nullable."""
    table = _Provenance.__table__
    for col_name in [
        "source_system",
        "source_type",
        "source_record_id",
        "extraction_timestamp",
        "raw_data_hash",
        "transformation_version",
    ]:
        assert table.c[col_name].nullable is True
