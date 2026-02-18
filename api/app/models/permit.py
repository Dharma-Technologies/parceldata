"""Permit model for building permits."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, ProvenanceMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.property import Property


class Permit(Base, TimestampMixin, ProvenanceMixin):
    """A building permit issued for work on a property."""

    __tablename__ = "permits"
    __table_args__ = {"schema": "parcel"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    property_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("parcel.properties.id"), index=True
    )

    # Permit info
    permit_number: Mapped[str] = mapped_column(String(50), index=True)
    permit_type: Mapped[str | None] = mapped_column(
        String(50), index=True
    )
    permit_subtype: Mapped[str | None] = mapped_column(String(100))

    # Status
    status: Mapped[str | None] = mapped_column(String(50), index=True)

    # Dates
    application_date: Mapped[date | None] = mapped_column(Date)
    issue_date: Mapped[date | None] = mapped_column(Date, index=True)
    expiration_date: Mapped[date | None] = mapped_column(Date)
    final_date: Mapped[date | None] = mapped_column(Date)

    # Description
    description: Mapped[str | None] = mapped_column(Text)
    work_class: Mapped[str | None] = mapped_column(String(50))

    # Financial
    valuation: Mapped[int | None] = mapped_column(Integer)
    fee_paid: Mapped[float | None] = mapped_column(Float)

    # Contractor
    contractor_name: Mapped[str | None] = mapped_column(String(200))
    contractor_license: Mapped[str | None] = mapped_column(String(50))
    contractor_phone: Mapped[str | None] = mapped_column(String(20))

    # Inspection
    last_inspection_date: Mapped[date | None] = mapped_column(Date)
    last_inspection_result: Mapped[str | None] = mapped_column(String(50))
    inspections_passed: Mapped[int] = mapped_column(Integer, default=0)
    inspections_failed: Mapped[int] = mapped_column(Integer, default=0)

    # Jurisdiction
    jurisdiction: Mapped[str | None] = mapped_column(String(100))

    property: Mapped[Property] = relationship(
        "Property", back_populates="permits"
    )
