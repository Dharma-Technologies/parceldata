"""Listing model for MLS listing data."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import ARRAY, Date, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.property import Property


class Listing(Base, TimestampMixin):
    """An MLS listing associated with a property."""

    __tablename__ = "listings"
    __table_args__ = {"schema": "parcel"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    property_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("parcel.properties.id"), index=True
    )
    mls_number: Mapped[str] = mapped_column(
        String(20), unique=True, index=True
    )
    mls_source: Mapped[str | None] = mapped_column(String(50))

    # Status
    status: Mapped[str] = mapped_column(String(20), index=True)

    # Dates
    list_date: Mapped[date | None] = mapped_column(Date, index=True)
    pending_date: Mapped[date | None] = mapped_column(Date)
    sold_date: Mapped[date | None] = mapped_column(Date, index=True)
    expiration_date: Mapped[date | None] = mapped_column(Date)
    days_on_market: Mapped[int | None] = mapped_column(Integer)
    cumulative_dom: Mapped[int | None] = mapped_column(Integer)

    # Pricing
    list_price: Mapped[int | None] = mapped_column(Integer, index=True)
    original_list_price: Mapped[int | None] = mapped_column(Integer)
    sold_price: Mapped[int | None] = mapped_column(Integer)
    price_per_sqft: Mapped[float | None] = mapped_column(Float)

    # Description
    public_remarks: Mapped[str | None] = mapped_column(Text)
    private_remarks: Mapped[str | None] = mapped_column(Text)

    # Features
    features: Mapped[list[str]] = mapped_column(
        ARRAY(String), default=[]
    )
    appliances: Mapped[list[str]] = mapped_column(
        ARRAY(String), default=[]
    )

    # Photos
    photo_count: Mapped[int] = mapped_column(Integer, default=0)
    photo_urls: Mapped[list[str]] = mapped_column(
        ARRAY(String), default=[]
    )
    virtual_tour_url: Mapped[str | None] = mapped_column(String(500))

    # Showing
    showing_instructions: Mapped[str | None] = mapped_column(Text)
    lockbox_type: Mapped[str | None] = mapped_column(String(50))

    # Listing agent
    listing_agent_name: Mapped[str | None] = mapped_column(String(100))
    listing_agent_phone: Mapped[str | None] = mapped_column(String(20))
    listing_agent_email: Mapped[str | None] = mapped_column(String(100))
    listing_agent_license: Mapped[str | None] = mapped_column(String(50))
    listing_office_name: Mapped[str | None] = mapped_column(String(100))
    listing_office_phone: Mapped[str | None] = mapped_column(String(20))

    # Buyer agent (if sold)
    buyer_agent_name: Mapped[str | None] = mapped_column(String(100))
    buyer_office_name: Mapped[str | None] = mapped_column(String(100))

    property: Mapped[Property] = relationship(
        "Property", back_populates="listing"
    )
