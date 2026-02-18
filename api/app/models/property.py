"""Core Property model — the central entity in the parcel schema."""

from __future__ import annotations

from typing import TYPE_CHECKING

from geoalchemy2 import Geometry
from pgvector.sqlalchemy import Vector
from sqlalchemy import Float, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import (
    Base,
    DataQualityMixin,
    ProvenanceMixin,
    TimestampMixin,
)

if TYPE_CHECKING:
    from app.models.address import Address
    from app.models.building import Building
    from app.models.environmental import Environmental
    from app.models.hoa import HOA
    from app.models.listing import Listing
    from app.models.ownership import Ownership
    from app.models.permit import Permit
    from app.models.school import School
    from app.models.tax import Tax
    from app.models.transaction import Transaction
    from app.models.valuation import Valuation
    from app.models.zoning import Zoning


class Property(Base, TimestampMixin, DataQualityMixin, ProvenanceMixin):
    """A real-estate parcel identified by a Dharma Parcel ID."""

    __tablename__ = "properties"
    __table_args__ = (
        Index("ix_properties_state_county", "state_fips", "county_fips"),
        {"schema": "parcel"},
    )

    # Primary key — format: {STATE}-{COUNTY}-{APN_HASH}
    id: Mapped[str] = mapped_column(String(50), primary_key=True)

    # County parcel info
    state_fips: Mapped[str] = mapped_column(String(2), index=True)
    county_fips: Mapped[str] = mapped_column(String(3), index=True)
    county_name: Mapped[str] = mapped_column(String(100))
    county_apn: Mapped[str] = mapped_column(String(50), index=True)

    # Legal description
    legal_description: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    subdivision_name: Mapped[str | None] = mapped_column(
        String(200), nullable=True
    )
    lot_number: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )
    block_number: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )

    # Lot dimensions
    lot_sqft: Mapped[int | None] = mapped_column(Integer, nullable=True)
    lot_acres: Mapped[float | None] = mapped_column(Float, nullable=True)
    lot_depth_ft: Mapped[float | None] = mapped_column(Float, nullable=True)
    lot_width_ft: Mapped[float | None] = mapped_column(Float, nullable=True)
    lot_dimensions: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )

    # Property type
    property_type: Mapped[str | None] = mapped_column(
        String(50), index=True
    )
    property_use: Mapped[str | None] = mapped_column(String(100))

    # Spatial (PostGIS)
    location: Mapped[object | None] = mapped_column(
        Geometry("POINT", srid=4326), nullable=True
    )
    boundary: Mapped[object | None] = mapped_column(
        Geometry("POLYGON", srid=4326), nullable=True
    )

    # Census geography
    census_tract: Mapped[str | None] = mapped_column(
        String(20), index=True
    )
    census_block_group: Mapped[str | None] = mapped_column(String(20))

    # Embedding for semantic search (pgvector)
    embedding: Mapped[object | None] = mapped_column(
        Vector(1536), nullable=True
    )

    # Entity resolution
    canonical_id: Mapped[str | None] = mapped_column(
        String(50), index=True
    )
    entity_confidence: Mapped[float] = mapped_column(Float, default=1.0)

    # Relationships (populated as related models are created)
    address: Mapped[Address | None] = relationship(
        "Address", back_populates="property", uselist=False
    )
    buildings: Mapped[list[Building]] = relationship(
        "Building", back_populates="property"
    )
    valuation: Mapped[Valuation | None] = relationship(
        "Valuation", back_populates="property", uselist=False
    )
    ownership: Mapped[Ownership | None] = relationship(
        "Ownership", back_populates="property", uselist=False
    )
    zoning: Mapped[Zoning | None] = relationship(
        "Zoning", back_populates="property", uselist=False
    )
    listing: Mapped[Listing | None] = relationship(
        "Listing", back_populates="property", uselist=False
    )
    transactions: Mapped[list[Transaction]] = relationship(
        "Transaction", back_populates="property"
    )
    permits: Mapped[list[Permit]] = relationship(
        "Permit", back_populates="property"
    )
    environmental: Mapped[Environmental | None] = relationship(
        "Environmental", back_populates="property", uselist=False
    )
    school: Mapped[School | None] = relationship(
        "School", back_populates="property", uselist=False
    )
    hoa: Mapped[HOA | None] = relationship(
        "HOA", back_populates="property", uselist=False
    )
    tax: Mapped[Tax | None] = relationship(
        "Tax", back_populates="property", uselist=False
    )


# Spatial index on location (GiST)
Index(
    "ix_properties_location",
    Property.location,
    postgresql_using="gist",
)
