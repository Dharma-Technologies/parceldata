"""Tests for address normalization service."""

from __future__ import annotations

import pytest

from app.services.address import NormalizedAddress, normalize


class TestNormalize:
    """Tests for the normalize function."""

    def test_full_address(self) -> None:
        """Normalizes a complete address."""
        result = normalize("123 Main Street, Austin, TX 78701")
        assert result.street_number == "123"
        assert result.street_name == "Main"
        assert result.street_suffix == "St"
        assert result.city == "Austin"
        assert result.state == "TX"
        assert result.zip_code == "78701"
        assert result.confidence == pytest.approx(1.0)

    def test_formatted_address(self) -> None:
        """Produces a formatted address string."""
        result = normalize("456 Oak Avenue, Dallas, TX 75201")
        assert result.formatted_address is not None
        assert "456" in result.formatted_address
        assert "Oak" in result.formatted_address
        assert "Dallas" in result.formatted_address
        assert "TX" in result.formatted_address

    def test_street_suffix_standardization(self) -> None:
        """Standardizes common suffixes."""
        result = normalize("100 Congress Avenue, Austin, TX")
        assert result.street_suffix == "Ave"

    def test_boulevard_suffix(self) -> None:
        result = normalize("500 Park Boulevard, Houston, TX")
        assert result.street_suffix == "Blvd"

    def test_drive_suffix(self) -> None:
        result = normalize("200 Sunset Drive, Dallas, TX")
        assert result.street_suffix == "Dr"

    def test_empty_string(self) -> None:
        """Empty input returns zero confidence."""
        result = normalize("")
        assert result.confidence == 0.0
        assert result.street_number is None
        assert result.formatted_address is None

    def test_whitespace_only(self) -> None:
        """Whitespace-only input returns zero confidence."""
        result = normalize("   ")
        assert result.confidence == 0.0

    def test_partial_address(self) -> None:
        """Partial address still parses what it can."""
        result = normalize("123 Main St")
        assert result.street_number == "123"
        assert result.street_name == "Main"
        assert result.confidence > 0.0

    def test_address_with_unit(self) -> None:
        """Parses unit/apartment information."""
        result = normalize("100 Main St Apt 4B, Austin, TX 78701")
        assert result.street_number == "100"
        assert result.unit_type == "Apt"
        assert result.unit_number == "4B"

    def test_address_with_suite(self) -> None:
        """Parses suite information."""
        result = normalize("500 Congress Ave Suite 200, Austin, TX")
        assert result.unit_type == "Ste"

    def test_zip_code_extraction(self) -> None:
        """Extracts 5-digit ZIP code."""
        result = normalize("123 Main St, Austin, TX 78701")
        assert result.zip_code == "78701"

    def test_zip_plus_4(self) -> None:
        """Extracts ZIP+4."""
        result = normalize("123 Main St, Austin, TX 78701-1234")
        assert result.zip_code == "78701"
        assert result.zip4 == "1234"

    def test_state_validation(self) -> None:
        """State must be a 2-letter alpha code."""
        result = normalize("123 Main St, Austin, TX 78701")
        assert result.state == "TX"

    def test_city_title_case(self) -> None:
        """City name is title-cased."""
        result = normalize("123 main st, AUSTIN, TX")
        assert result.city == "Austin"

    def test_confidence_scoring(self) -> None:
        """Confidence increases with more components."""
        full = normalize("123 Main St, Austin, TX 78701")
        partial = normalize("123 Main St")
        assert full.confidence > partial.confidence

    def test_street_address_built(self) -> None:
        """street_address combines number, name, suffix."""
        result = normalize("789 Elm Road, Dallas, TX")
        assert result.street_address is not None
        assert "789" in result.street_address
        assert "Elm" in result.street_address


class TestNormalizedAddressDataclass:
    """Tests for the NormalizedAddress dataclass."""

    def test_fields_accessible(self) -> None:
        addr = NormalizedAddress(
            street_number="100",
            street_name="Main",
            street_suffix="St",
            street_direction=None,
            unit_type=None,
            unit_number=None,
            city="Austin",
            state="TX",
            zip_code="78701",
            zip4=None,
            street_address="100 Main St",
            formatted_address="100 Main St Austin, TX 78701",
            confidence=1.0,
        )
        assert addr.street_number == "100"
        assert addr.city == "Austin"
        assert addr.confidence == 1.0

    def test_all_none_fields(self) -> None:
        addr = NormalizedAddress(
            street_number=None,
            street_name=None,
            street_suffix=None,
            street_direction=None,
            unit_type=None,
            unit_number=None,
            city=None,
            state=None,
            zip_code=None,
            zip4=None,
            street_address=None,
            formatted_address=None,
            confidence=0.0,
        )
        assert addr.confidence == 0.0
