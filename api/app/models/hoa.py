"""HOA model for homeowners association data."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ARRAY, Boolean, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.property import Property


class HOA(Base, TimestampMixin):
    """Homeowners association details for a property."""

    __tablename__ = "hoas"
    __table_args__ = {"schema": "parcel"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    property_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("parcel.properties.id"), unique=True
    )

    # HOA info
    hoa_name: Mapped[str | None] = mapped_column(String(200))
    hoa_exists: Mapped[bool | None] = mapped_column(Boolean)

    # Fees
    fee_monthly: Mapped[float | None] = mapped_column(Float)
    fee_annual: Mapped[float | None] = mapped_column(Float)
    fee_includes: Mapped[list[str]] = mapped_column(
        ARRAY(String), default=[]
    )

    # Special assessments
    special_assessment: Mapped[bool] = mapped_column(
        Boolean, default=False
    )
    special_assessment_amount: Mapped[float | None] = mapped_column(Float)

    # Rules
    rental_allowed: Mapped[bool | None] = mapped_column(Boolean)
    rental_restrictions: Mapped[str | None] = mapped_column(String(500))
    pet_policy: Mapped[str | None] = mapped_column(String(200))

    # Contact
    contact_name: Mapped[str | None] = mapped_column(String(100))
    contact_phone: Mapped[str | None] = mapped_column(String(20))
    contact_email: Mapped[str | None] = mapped_column(String(100))
    management_company: Mapped[str | None] = mapped_column(String(200))

    property: Mapped[Property] = relationship(
        "Property", back_populates="hoa"
    )
