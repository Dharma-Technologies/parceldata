"""School model for school district assignments."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.property import Property


class School(Base, TimestampMixin):
    """School district and assigned school data for a property."""

    __tablename__ = "schools"
    __table_args__ = {"schema": "parcel"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    property_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("parcel.properties.id"), unique=True
    )

    # District
    district_name: Mapped[str | None] = mapped_column(String(100))
    district_id: Mapped[str | None] = mapped_column(String(20))
    district_rating: Mapped[int | None] = mapped_column(Integer)

    # Elementary
    elementary_name: Mapped[str | None] = mapped_column(String(100))
    elementary_id: Mapped[str | None] = mapped_column(String(20))
    elementary_rating: Mapped[int | None] = mapped_column(Integer)
    elementary_distance_miles: Mapped[float | None] = mapped_column(Float)

    # Middle
    middle_name: Mapped[str | None] = mapped_column(String(100))
    middle_id: Mapped[str | None] = mapped_column(String(20))
    middle_rating: Mapped[int | None] = mapped_column(Integer)
    middle_distance_miles: Mapped[float | None] = mapped_column(Float)

    # High
    high_name: Mapped[str | None] = mapped_column(String(100))
    high_id: Mapped[str | None] = mapped_column(String(20))
    high_rating: Mapped[int | None] = mapped_column(Integer)
    high_distance_miles: Mapped[float | None] = mapped_column(Float)

    property: Mapped[Property] = relationship(
        "Property", back_populates="school"
    )
