"""SQLAlchemy and Pydantic models."""

from __future__ import annotations

from app.models.address import Address
from app.models.base import Base, DataQualityMixin, ProvenanceMixin, TimestampMixin
from app.models.building import Building
from app.models.environmental import Environmental
from app.models.hoa import HOA
from app.models.listing import Listing
from app.models.ownership import Ownership
from app.models.permit import Permit
from app.models.property import Property
from app.models.school import School
from app.models.tax import Tax
from app.models.transaction import Transaction
from app.models.valuation import Valuation
from app.models.zoning import Zoning

__all__ = [
    "Address",
    "Base",
    "Building",
    "DataQualityMixin",
    "Environmental",
    "HOA",
    "Listing",
    "Ownership",
    "Permit",
    "Property",
    "ProvenanceMixin",
    "School",
    "Tax",
    "TimestampMixin",
    "Transaction",
    "Valuation",
    "Zoning",
]
