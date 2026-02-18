"""Tests for the provider adapter package exports."""

from __future__ import annotations

from app.services.ingestion.base import ProviderAdapter
from app.services.ingestion.providers import (
    ATTOMAdapter,
    CensusAdapter,
    FEMAAdapter,
    RegridAdapter,
)
from app.services.ingestion.providers import (
    __all__ as provider_all,
)


class TestProviderExports:
    """Tests for package-level exports."""

    def test_regrid_exported(self) -> None:
        assert RegridAdapter is not None

    def test_attom_exported(self) -> None:
        assert ATTOMAdapter is not None

    def test_census_exported(self) -> None:
        assert CensusAdapter is not None

    def test_fema_exported(self) -> None:
        assert FEMAAdapter is not None

    def test_all_contains_four_adapters(self) -> None:
        assert len(provider_all) == 4

    def test_all_contains_regrid(self) -> None:
        assert "RegridAdapter" in provider_all

    def test_all_contains_attom(self) -> None:
        assert "ATTOMAdapter" in provider_all

    def test_all_contains_census(self) -> None:
        assert "CensusAdapter" in provider_all

    def test_all_contains_fema(self) -> None:
        assert "FEMAAdapter" in provider_all


class TestProviderSubclasses:
    """Verify all adapters are ProviderAdapter subclasses."""

    def test_regrid_is_provider(self) -> None:
        assert issubclass(RegridAdapter, ProviderAdapter)

    def test_attom_is_provider(self) -> None:
        assert issubclass(ATTOMAdapter, ProviderAdapter)

    def test_census_is_provider(self) -> None:
        assert issubclass(CensusAdapter, ProviderAdapter)

    def test_fema_is_provider(self) -> None:
        assert issubclass(FEMAAdapter, ProviderAdapter)


class TestProviderNames:
    """Verify provider name attributes."""

    def test_regrid_name(self) -> None:
        assert RegridAdapter.name == "regrid"

    def test_attom_name(self) -> None:
        assert ATTOMAdapter.name == "attom"

    def test_census_name(self) -> None:
        assert CensusAdapter.name == "census"

    def test_fema_name(self) -> None:
        assert FEMAAdapter.name == "fema"


class TestProviderSourceTypes:
    """Verify source_type attributes."""

    def test_regrid_source_type(self) -> None:
        assert RegridAdapter.source_type == "parcel_data"

    def test_attom_source_type(self) -> None:
        assert ATTOMAdapter.source_type == "property_records"

    def test_census_source_type(self) -> None:
        assert CensusAdapter.source_type == "demographics"

    def test_fema_source_type(self) -> None:
        assert FEMAAdapter.source_type == "flood_zones"
