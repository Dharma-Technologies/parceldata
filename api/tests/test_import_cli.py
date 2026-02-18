"""Tests for the batch import CLI."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.cli.import_data import PROVIDERS, build_parser, import_region, main
from app.services.ingestion.base import RawPropertyRecord


class TestBuildParser:
    """Tests for CLI argument parser."""

    def test_required_args(self) -> None:
        """Parser requires --provider and --state."""
        parser = build_parser()
        args = parser.parse_args(["--provider", "regrid", "--state", "TX"])
        assert args.provider == "regrid"
        assert args.state == "TX"

    def test_optional_county(self) -> None:
        parser = build_parser()
        args = parser.parse_args([
            "--provider", "attom",
            "--state", "CA",
            "--county", "Los Angeles",
        ])
        assert args.county == "Los Angeles"

    def test_optional_limit(self) -> None:
        parser = build_parser()
        args = parser.parse_args([
            "--provider", "regrid",
            "--state", "TX",
            "--limit", "100",
        ])
        assert args.limit == 100

    def test_dry_run_flag(self) -> None:
        parser = build_parser()
        args = parser.parse_args([
            "--provider", "regrid",
            "--state", "TX",
            "--dry-run",
        ])
        assert args.dry_run is True

    def test_dry_run_default_false(self) -> None:
        parser = build_parser()
        args = parser.parse_args([
            "--provider", "regrid",
            "--state", "TX",
        ])
        assert args.dry_run is False


class TestProviders:
    """Tests for the PROVIDERS mapping."""

    def test_regrid_registered(self) -> None:
        assert "regrid" in PROVIDERS

    def test_attom_registered(self) -> None:
        assert "attom" in PROVIDERS


class TestImportRegion:
    """Tests for the import_region async function."""

    @pytest.mark.asyncio
    async def test_unknown_provider(self) -> None:
        """Unknown provider returns 0, 0."""
        count, errors = await import_region(
            provider="nonexistent", state="TX"
        )
        assert count == 0
        assert errors == 0

    @pytest.mark.asyncio
    async def test_dry_run(self) -> None:
        """Dry run counts records without processing."""

        async def mock_stream(
            state: str,
            county: str | None = None,
            limit: int | None = None,
        ):  # type: ignore[no-untyped-def]
            for i in range(3):
                yield RawPropertyRecord(
                    source_system="regrid",
                    source_type="parcel_data",
                    source_record_id=f"dry-{i}",
                    extraction_timestamp=datetime.utcnow(),
                    raw_data={},
                )

        mock_adapter_cls = MagicMock()
        mock_adapter = mock_adapter_cls.return_value
        mock_adapter.stream_region = mock_stream

        with patch.dict(
            "app.cli.import_data.PROVIDERS",
            {"regrid": mock_adapter_cls},
        ):
            count, errors = await import_region(
                provider="regrid",
                state="TX",
                dry_run=True,
                limit=3,
            )

        assert count == 3
        assert errors == 0

    @pytest.mark.asyncio
    async def test_import_with_limit(self) -> None:
        """Import respects the limit."""

        async def mock_stream(
            state: str,
            county: str | None = None,
            limit: int | None = None,
        ):  # type: ignore[no-untyped-def]
            for i in range(10):
                yield RawPropertyRecord(
                    source_system="regrid",
                    source_type="parcel_data",
                    source_record_id=f"rec-{i}",
                    extraction_timestamp=datetime.utcnow(),
                    raw_data={},
                )

        mock_adapter_cls = MagicMock()
        mock_adapter = mock_adapter_cls.return_value
        mock_adapter.stream_region = mock_stream

        with patch.dict(
            "app.cli.import_data.PROVIDERS",
            {"regrid": mock_adapter_cls},
        ), patch(
            "app.cli.import_data.IngestionPipeline"
        ) as mock_pipeline_cls:
            mock_pipeline = mock_pipeline_cls.return_value
            mock_pipeline.process_record = AsyncMock(
                return_value="processed"
            )

            count, errors = await import_region(
                provider="regrid",
                state="TX",
                limit=2,
            )

        assert count == 2
        assert errors == 0


class TestMain:
    """Tests for the main CLI entry point."""

    def test_main_returns_int(self) -> None:
        """main() returns an integer exit code."""
        with patch(
            "app.cli.import_data.asyncio.run",
            return_value=(5, 0),
        ):
            result = main([
                "--provider", "regrid",
                "--state", "TX",
                "--dry-run",
            ])
        assert result == 0

    def test_main_returns_1_on_errors(self) -> None:
        """main() returns 1 when errors occur."""
        with patch(
            "app.cli.import_data.asyncio.run",
            return_value=(3, 2),
        ):
            result = main([
                "--provider", "regrid",
                "--state", "TX",
            ])
        assert result == 1
