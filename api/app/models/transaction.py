"""Transaction model for deed transfers and sales."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, ProvenanceMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.property import Property


class Transaction(Base, TimestampMixin, ProvenanceMixin):
    """A recorded deed transfer or sale for a property."""

    __tablename__ = "transactions"
    __table_args__ = {"schema": "parcel"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    property_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("parcel.properties.id"), index=True
    )

    # Recording
    document_number: Mapped[str | None] = mapped_column(
        String(50), index=True
    )
    recording_date: Mapped[date | None] = mapped_column(
        Date, index=True
    )
    book: Mapped[str | None] = mapped_column(String(20))
    page: Mapped[str | None] = mapped_column(String(20))

    # Transaction details
    transaction_date: Mapped[date | None] = mapped_column(Date)
    deed_type: Mapped[str | None] = mapped_column(String(50))
    transaction_type: Mapped[str | None] = mapped_column(String(50))

    # Parties
    grantor: Mapped[str | None] = mapped_column(String(200))
    grantee: Mapped[str | None] = mapped_column(String(200))

    # Financial
    sale_price: Mapped[int | None] = mapped_column(Integer)
    price_per_sqft: Mapped[float | None] = mapped_column(Float)
    loan_amount: Mapped[int | None] = mapped_column(Integer)
    lender_name: Mapped[str | None] = mapped_column(String(200))

    # Flags
    arms_length: Mapped[bool | None] = mapped_column(Boolean)
    distressed: Mapped[bool | None] = mapped_column(Boolean)

    property: Mapped[Property] = relationship(
        "Property", back_populates="transactions"
    )
