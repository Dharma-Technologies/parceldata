"""Normalized address model for properties."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Float, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.property import Property


class Address(Base, TimestampMixin):
    """Normalized, geocoded mailing address for a property."""

    __tablename__ = "addresses"
    __table_args__ = (
        Index("ix_addresses_city_state", "city", "state"),
        Index("ix_addresses_lat_lng", "latitude", "longitude"),
        {"schema": "parcel"},
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    property_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("parcel.properties.id"), unique=True
    )

    # Raw input
    raw_address: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )

    # Normalized components
    street_number: Mapped[str | None] = mapped_column(String(20))
    street_name: Mapped[str | None] = mapped_column(String(200))
    street_suffix: Mapped[str | None] = mapped_column(String(20))
    street_direction: Mapped[str | None] = mapped_column(String(10))
    unit_type: Mapped[str | None] = mapped_column(String(20))
    unit_number: Mapped[str | None] = mapped_column(String(20))
    city: Mapped[str | None] = mapped_column(String(100), index=True)
    state: Mapped[str | None] = mapped_column(String(2), index=True)
    zip_code: Mapped[str | None] = mapped_column(String(5), index=True)
    zip4: Mapped[str | None] = mapped_column(String(4))
    county: Mapped[str | None] = mapped_column(String(100))

    # Formatted versions
    street_address: Mapped[str | None] = mapped_column(String(300))
    formatted_address: Mapped[str | None] = mapped_column(String(500))

    # Geocoding
    latitude: Mapped[float | None] = mapped_column(Float, index=True)
    longitude: Mapped[float | None] = mapped_column(Float, index=True)
    geocode_accuracy: Mapped[str | None] = mapped_column(String(20))
    geocode_source: Mapped[str | None] = mapped_column(String(50))

    # Normalization
    usps_validated: Mapped[bool] = mapped_column(Boolean, default=False)
    normalization_score: Mapped[float] = mapped_column(Float, default=0.0)

    property: Mapped[Property] = relationship(
        "Property", back_populates="address"
    )
