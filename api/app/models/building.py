"""Building model for structures on a property."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.property import Property


class Building(Base, TimestampMixin):
    """A structure (building) located on a property parcel."""

    __tablename__ = "buildings"
    __table_args__ = (
        Index("ix_buildings_beds_baths", "bedrooms", "bathrooms"),
        {"schema": "parcel"},
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    property_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("parcel.properties.id"), index=True
    )
    building_number: Mapped[int] = mapped_column(Integer, default=1)

    # Size
    sqft: Mapped[int | None] = mapped_column(Integer)
    sqft_finished: Mapped[int | None] = mapped_column(Integer)
    sqft_unfinished: Mapped[int | None] = mapped_column(Integer)

    # Structure
    stories: Mapped[int | None] = mapped_column(Integer)
    bedrooms: Mapped[int | None] = mapped_column(Integer, index=True)
    bathrooms: Mapped[float | None] = mapped_column(Float)
    bathrooms_full: Mapped[int | None] = mapped_column(Integer)
    bathrooms_half: Mapped[int | None] = mapped_column(Integer)

    # Age
    year_built: Mapped[int | None] = mapped_column(Integer, index=True)
    year_renovated: Mapped[int | None] = mapped_column(Integer)
    effective_year_built: Mapped[int | None] = mapped_column(Integer)

    # Construction
    construction_type: Mapped[str | None] = mapped_column(String(50))
    exterior_wall: Mapped[str | None] = mapped_column(String(50))
    roof_type: Mapped[str | None] = mapped_column(String(50))
    roof_material: Mapped[str | None] = mapped_column(String(50))
    foundation_type: Mapped[str | None] = mapped_column(String(50))
    heating_type: Mapped[str | None] = mapped_column(String(50))
    cooling_type: Mapped[str | None] = mapped_column(String(50))

    # Features
    garage_type: Mapped[str | None] = mapped_column(String(50))
    garage_spaces: Mapped[int | None] = mapped_column(Integer)
    parking_spaces: Mapped[int | None] = mapped_column(Integer)
    pool: Mapped[bool] = mapped_column(Boolean, default=False)
    pool_type: Mapped[str | None] = mapped_column(String(50))
    fireplace: Mapped[bool] = mapped_column(Boolean, default=False)
    fireplace_count: Mapped[int | None] = mapped_column(Integer)
    basement: Mapped[bool] = mapped_column(Boolean, default=False)
    basement_type: Mapped[str | None] = mapped_column(String(50))
    attic: Mapped[bool] = mapped_column(Boolean, default=False)

    # Quality
    quality_grade: Mapped[str | None] = mapped_column(String(20))
    condition: Mapped[str | None] = mapped_column(String(20))

    property: Mapped[Property] = relationship(
        "Property", back_populates="buildings"
    )
