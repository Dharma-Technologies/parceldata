"""Valuation model for property assessed and estimated values."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.property import Property


class Valuation(Base, TimestampMixin):
    """Assessed and estimated market values for a property."""

    __tablename__ = "valuations"
    __table_args__ = {"schema": "parcel"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    property_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("parcel.properties.id"), unique=True
    )

    # Assessed values (from county assessor)
    assessed_total: Mapped[int | None] = mapped_column(Integer)
    assessed_land: Mapped[int | None] = mapped_column(Integer)
    assessed_improvements: Mapped[int | None] = mapped_column(Integer)
    assessed_year: Mapped[int | None] = mapped_column(Integer)
    assessment_date: Mapped[date | None] = mapped_column(Date)

    # Market values (computed AVM)
    estimated_value: Mapped[int | None] = mapped_column(
        Integer, index=True
    )
    estimated_value_low: Mapped[int | None] = mapped_column(Integer)
    estimated_value_high: Mapped[int | None] = mapped_column(Integer)
    estimate_confidence: Mapped[float | None] = mapped_column(Float)
    estimate_date: Mapped[date | None] = mapped_column(Date)
    estimate_model: Mapped[str | None] = mapped_column(String(50))

    # Per-unit metrics
    price_per_sqft: Mapped[float | None] = mapped_column(Float)
    price_per_acre: Mapped[float | None] = mapped_column(Float)

    # Historical
    value_change_1yr: Mapped[float | None] = mapped_column(Float)
    value_change_5yr: Mapped[float | None] = mapped_column(Float)

    property: Mapped[Property] = relationship(
        "Property", back_populates="valuation"
    )
