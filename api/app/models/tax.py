"""Tax model for property tax records."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import ARRAY, Boolean, Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.property import Property


class Tax(Base, TimestampMixin):
    """Property tax record including exemptions and delinquency."""

    __tablename__ = "taxes"
    __table_args__ = {"schema": "parcel"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    property_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("parcel.properties.id"), unique=True
    )

    # Annual tax
    annual_amount: Mapped[float | None] = mapped_column(Float)
    tax_year: Mapped[int | None] = mapped_column(Integer)
    tax_rate: Mapped[float | None] = mapped_column(Float)

    # Exemptions
    exemptions: Mapped[list[str]] = mapped_column(
        ARRAY(String), default=[]
    )
    exemption_amount: Mapped[float | None] = mapped_column(Float)

    # Payment
    last_paid_date: Mapped[date | None] = mapped_column(Date)
    last_paid_amount: Mapped[float | None] = mapped_column(Float)
    delinquent: Mapped[bool] = mapped_column(Boolean, default=False)
    delinquent_amount: Mapped[float | None] = mapped_column(Float)

    # Tax sale
    tax_lien: Mapped[bool] = mapped_column(Boolean, default=False)
    tax_sale_scheduled: Mapped[bool] = mapped_column(Boolean, default=False)

    property: Mapped[Property] = relationship(
        "Property", back_populates="tax"
    )
