"""Data provider adapters for property ingestion."""

from __future__ import annotations

from app.services.ingestion.providers.attom import ATTOMAdapter
from app.services.ingestion.providers.census import CensusAdapter
from app.services.ingestion.providers.fema import FEMAAdapter
from app.services.ingestion.providers.regrid import RegridAdapter

__all__ = ["ATTOMAdapter", "CensusAdapter", "FEMAAdapter", "RegridAdapter"]
