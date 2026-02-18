"""ParcelData Python SDK — Real estate data for AI agents."""

from .client import ParcelData
from .models import Property, Listing, Valuation, Zoning, Permit

__version__ = "0.1.0"
__all__ = ["ParcelData", "Property", "Listing", "Valuation", "Zoning", "Permit"]
