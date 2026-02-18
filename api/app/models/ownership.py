"""Ownership model for property owner information."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.property import Property


class Ownership(Base, TimestampMixin):
    """Current ownership record for a property."""

    __tablename__ = "ownerships"
    __table_args__ = {"schema": "parcel"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    property_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("parcel.properties.id"), unique=True
    )

    # Current owner
    owner_name: Mapped[str | None] = mapped_column(
        String(200), index=True
    )
    owner_name_2: Mapped[str | None] = mapped_column(String(200))
    owner_type: Mapped[str | None] = mapped_column(String(50))

    # Entity resolution
    owner_entity_id: Mapped[str | None] = mapped_column(
        String(50), index=True
    )

    # Mailing address (may differ from property)
    mailing_street: Mapped[str | None] = mapped_column(String(200))
    mailing_city: Mapped[str | None] = mapped_column(String(100))
    mailing_state: Mapped[str | None] = mapped_column(String(2))
    mailing_zip: Mapped[str | None] = mapped_column(String(10))

    # Occupancy
    owner_occupied: Mapped[bool | None] = mapped_column(Boolean)

    # Acquisition
    acquisition_date: Mapped[date | None] = mapped_column(
        Date, index=True
    )
    acquisition_price: Mapped[int | None] = mapped_column(Integer)
    acquisition_type: Mapped[str | None] = mapped_column(String(50))

    # Duration
    ownership_length_years: Mapped[float | None] = mapped_column(Float)

    property: Mapped[Property] = relationship(
        "Property", back_populates="ownership"
    )
