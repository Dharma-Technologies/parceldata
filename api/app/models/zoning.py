"""Zoning model for land use restrictions and regulations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import ARRAY, Boolean, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.property import Property


class Zoning(Base, TimestampMixin):
    """Zoning classification and dimensional requirements for a property."""

    __tablename__ = "zonings"
    __table_args__ = {"schema": "parcel"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    property_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("parcel.properties.id"), unique=True
    )

    # Zone classification
    zone_code: Mapped[str | None] = mapped_column(
        String(20), index=True
    )
    zone_description: Mapped[str | None] = mapped_column(String(200))
    zone_category: Mapped[str | None] = mapped_column(String(50))

    # Overlay districts
    overlay_districts: Mapped[list[str]] = mapped_column(
        ARRAY(String), default=[]
    )
    historic_district: Mapped[bool] = mapped_column(
        Boolean, default=False
    )

    # Permitted uses
    permitted_uses: Mapped[list[str]] = mapped_column(
        ARRAY(String), default=[]
    )
    conditional_uses: Mapped[list[str]] = mapped_column(
        ARRAY(String), default=[]
    )
    prohibited_uses: Mapped[list[str]] = mapped_column(
        ARRAY(String), default=[]
    )

    # Dimensional requirements
    setback_front_ft: Mapped[float | None] = mapped_column(Float)
    setback_rear_ft: Mapped[float | None] = mapped_column(Float)
    setback_side_ft: Mapped[float | None] = mapped_column(Float)
    max_height_ft: Mapped[float | None] = mapped_column(Float)
    max_stories: Mapped[int | None] = mapped_column(Integer)
    max_far: Mapped[float | None] = mapped_column(Float)
    max_lot_coverage: Mapped[float | None] = mapped_column(Float)
    min_lot_size_sqft: Mapped[int | None] = mapped_column(Integer)
    min_lot_width_ft: Mapped[float | None] = mapped_column(Float)

    # Density
    max_units_per_acre: Mapped[float | None] = mapped_column(Float)

    # Parking requirements
    parking_spaces_required: Mapped[int | None] = mapped_column(Integer)

    # ADU rules
    adu_permitted: Mapped[bool | None] = mapped_column(Boolean)
    adu_rules: Mapped[dict[str, Any]] = mapped_column(JSONB, default={})

    # Source
    jurisdiction: Mapped[str | None] = mapped_column(String(100))
    ordinance_reference: Mapped[str | None] = mapped_column(String(200))

    property: Mapped[Property] = relationship(
        "Property", back_populates="zoning"
    )
