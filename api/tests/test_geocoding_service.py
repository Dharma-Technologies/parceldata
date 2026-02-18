"""Tests for the geocoding service."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.geocoding import GeocodingResult, GeocodingService


class TestGeocodingResult:
    """Tests for GeocodingResult dataclass."""

    def test_fields(self) -> None:
        result = GeocodingResult(
            latitude=30.2672,
            longitude=-97.7431,
            accuracy="rooftop",
            source="census",
            confidence=0.95,
        )
        assert result.latitude == 30.2672
        assert result.longitude == -97.7431
        assert result.accuracy == "rooftop"
        assert result.source == "census"
        assert result.confidence == 0.95


class TestGeocodingServiceInit:
    """Tests for GeocodingService init."""

    def test_client_created(self) -> None:
        svc = GeocodingService()
        assert svc.client is not None


class TestCensusGeocode:
    """Tests for Census Bureau geocoder."""

    @pytest.mark.asyncio
    async def test_success(self) -> None:
        svc = GeocodingService()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "result": {
                "addressMatches": [
                    {
                        "coordinates": {"y": 30.2672, "x": -97.7431},
                        "matchedAddress": "123 Main St, Austin, TX",
                    }
                ]
            }
        }

        with patch.object(
            svc.client,
            "get",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await svc._census_geocode(
                "123 Main St, Austin, TX"
            )

        assert result is not None
        assert result.latitude == 30.2672
        assert result.longitude == -97.7431
        assert result.source == "census"
        assert result.accuracy == "rooftop"

    @pytest.mark.asyncio
    async def test_no_matches(self) -> None:
        svc = GeocodingService()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "result": {"addressMatches": []}
        }

        with patch.object(
            svc.client,
            "get",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await svc._census_geocode("Nowhere, XX")

        assert result is None

    @pytest.mark.asyncio
    async def test_exception_returns_none(self) -> None:
        svc = GeocodingService()

        with patch.object(
            svc.client,
            "get",
            new_callable=AsyncMock,
            side_effect=Exception("network error"),
        ):
            result = await svc._census_geocode("any address")

        assert result is None


class TestNominatimGeocode:
    """Tests for Nominatim geocoder."""

    @pytest.mark.asyncio
    async def test_success(self) -> None:
        svc = GeocodingService()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = [
            {"lat": "30.2672", "lon": "-97.7431"}
        ]

        with patch.object(
            svc.client,
            "get",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await svc._nominatim_geocode("Austin, TX")

        assert result is not None
        assert result.latitude == 30.2672
        assert result.source == "nominatim"
        assert result.accuracy == "street"

    @pytest.mark.asyncio
    async def test_empty_results(self) -> None:
        svc = GeocodingService()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = []

        with patch.object(
            svc.client,
            "get",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await svc._nominatim_geocode("Fake Address")

        assert result is None


class TestGeocodeWithFallback:
    """Tests for the main geocode method with fallback."""

    @pytest.mark.asyncio
    async def test_census_succeeds(self) -> None:
        """Uses Census if it succeeds."""
        svc = GeocodingService()
        census_result = GeocodingResult(
            latitude=30.0, longitude=-97.0,
            accuracy="rooftop", source="census", confidence=0.95,
        )

        with patch.object(
            svc, "_census_geocode", return_value=census_result
        ) as mock_census:
            result = await svc.geocode("123 Main St", city="Austin")

        assert result is not None
        assert result.source == "census"
        mock_census.assert_called_once()

    @pytest.mark.asyncio
    async def test_fallback_to_nominatim(self) -> None:
        """Falls back to Nominatim when Census fails."""
        svc = GeocodingService()
        nominatim_result = GeocodingResult(
            latitude=30.0, longitude=-97.0,
            accuracy="street", source="nominatim", confidence=0.8,
        )

        with patch.object(
            svc, "_census_geocode", return_value=None
        ), patch.object(
            svc, "_nominatim_geocode", return_value=nominatim_result
        ):
            result = await svc.geocode("123 Main St")

        assert result is not None
        assert result.source == "nominatim"

    @pytest.mark.asyncio
    async def test_all_fail_returns_none(self) -> None:
        """Returns None when all providers fail."""
        svc = GeocodingService()

        with patch.object(
            svc, "_census_geocode", return_value=None
        ), patch.object(
            svc, "_nominatim_geocode", return_value=None
        ):
            result = await svc.geocode("Nowhere, XX")

        assert result is None

    @pytest.mark.asyncio
    async def test_builds_full_address(self) -> None:
        """Builds full address from components."""
        svc = GeocodingService()

        with patch.object(
            svc, "_census_geocode", return_value=None
        ) as mock_census, patch.object(
            svc, "_nominatim_geocode", return_value=None
        ):
            await svc.geocode(
                "100 Main",
                city="Austin",
                state="TX",
                zip_code="78701",
            )

        call_args = mock_census.call_args[0][0]
        assert "Austin" in call_args
        assert "TX" in call_args
        assert "78701" in call_args


class TestReverseGeocode:
    """Tests for reverse geocoding."""

    @pytest.mark.asyncio
    async def test_success(self) -> None:
        svc = GeocodingService()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "display_name": "123 Main St, Austin, TX",
            "address": {
                "house_number": "123",
                "road": "Main St",
                "city": "Austin",
                "state": "Texas",
                "postcode": "78701",
            },
        }

        with patch.object(
            svc.client,
            "get",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await svc.reverse_geocode(30.2672, -97.7431)

        assert result is not None
        assert result["city"] == "Austin"
        assert result["postcode"] == "78701"

    @pytest.mark.asyncio
    async def test_failure_returns_none(self) -> None:
        svc = GeocodingService()

        with patch.object(
            svc.client,
            "get",
            new_callable=AsyncMock,
            side_effect=Exception("fail"),
        ):
            result = await svc.reverse_geocode(0.0, 0.0)

        assert result is None
