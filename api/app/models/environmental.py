"""Environmental model for hazards and risk data."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.property import Property


class Environmental(Base, TimestampMixin):
    """Environmental hazard and risk data for a property."""

    __tablename__ = "environmentals"
    __table_args__ = {"schema": "parcel"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    property_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("parcel.properties.id"), unique=True
    )

    # Flood
    flood_zone: Mapped[str | None] = mapped_column(String(10))
    flood_zone_description: Mapped[str | None] = mapped_column(String(200))
    in_100yr_floodplain: Mapped[bool | None] = mapped_column(Boolean)
    in_500yr_floodplain: Mapped[bool | None] = mapped_column(Boolean)
    flood_insurance_required: Mapped[bool | None] = mapped_column(Boolean)
    flood_map_date: Mapped[str | None] = mapped_column(String(20))
    flood_panel_number: Mapped[str | None] = mapped_column(String(20))
    base_flood_elevation: Mapped[float | None] = mapped_column(Float)

    # Wildfire
    wildfire_risk: Mapped[str | None] = mapped_column(String(20))
    wildfire_score: Mapped[float | None] = mapped_column(Float)
    in_wui: Mapped[bool | None] = mapped_column(Boolean)

    # Earthquake
    earthquake_risk: Mapped[str | None] = mapped_column(String(20))
    earthquake_score: Mapped[float | None] = mapped_column(Float)
    near_fault_line: Mapped[bool | None] = mapped_column(Boolean)
    fault_distance_miles: Mapped[float | None] = mapped_column(Float)
    liquefaction_risk: Mapped[bool | None] = mapped_column(Boolean)

    # Environmental contamination
    superfund_site: Mapped[bool | None] = mapped_column(Boolean)
    superfund_distance_miles: Mapped[float | None] = mapped_column(Float)
    brownfield_site: Mapped[bool | None] = mapped_column(Boolean)
    underground_storage_tanks: Mapped[bool | None] = mapped_column(Boolean)

    # Other hazards
    radon_zone: Mapped[str | None] = mapped_column(String(10))
    tornado_risk: Mapped[str | None] = mapped_column(String(20))
    hurricane_risk: Mapped[str | None] = mapped_column(String(20))
    hail_risk: Mapped[str | None] = mapped_column(String(20))

    # Composite score
    overall_risk_score: Mapped[float | None] = mapped_column(Float)

    property: Mapped[Property] = relationship(
        "Property", back_populates="environmental"
    )
