"""Command-line tool for batch property data import."""

from __future__ import annotations

import argparse
import asyncio
import sys

import structlog

from app.services.ingestion.base import ProviderAdapter
from app.services.ingestion.pipeline import IngestionPipeline
from app.services.ingestion.providers.attom import ATTOMAdapter
from app.services.ingestion.providers.regrid import RegridAdapter

logger = structlog.get_logger()

PROVIDERS: dict[str, type[ProviderAdapter]] = {
    "regrid": RegridAdapter,
    "attom": ATTOMAdapter,
}


async def import_region(
    provider: str,
    state: str,
    county: str | None = None,
    limit: int | None = None,
    dry_run: bool = False,
) -> tuple[int, int]:
    """Import properties for a region from a provider.

    Args:
        provider: Provider name (regrid, attom).
        state: State code (e.g., TX, CA).
        county: Optional county name.
        limit: Maximum records to import.
        dry_run: If True, don't actually process records.

    Returns:
        Tuple of (success_count, error_count).
    """
    adapter_cls = PROVIDERS.get(provider)
    if not adapter_cls:
        logger.error("Unknown provider", provider=provider)
        return 0, 0

    adapter = adapter_cls()
    pipeline = IngestionPipeline()

    logger.info(
        "Starting import",
        provider=provider,
        state=state,
        county=county,
        limit=limit,
        dry_run=dry_run,
    )

    count = 0
    errors = 0

    async for raw_record in adapter.stream_region(state, county, limit):
        if dry_run:
            logger.info(
                "Dry run: would process",
                source_id=raw_record.source_record_id,
                address=raw_record.address_raw,
            )
            count += 1
        else:
            result = await pipeline.process_record(raw_record)
            if result:
                count += 1
            else:
                errors += 1

        if limit and count >= limit:
            break

    logger.info(
        "Import complete",
        provider=provider,
        state=state,
        imported=count,
        errors=errors,
    )

    return count, errors


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the import CLI."""
    parser = argparse.ArgumentParser(
        description="Import property data from external providers"
    )
    parser.add_argument(
        "--provider",
        required=True,
        choices=list(PROVIDERS.keys()),
        help="Data provider (regrid, attom)",
    )
    parser.add_argument(
        "--state",
        required=True,
        help="State code (TX, CA, etc.)",
    )
    parser.add_argument(
        "--county",
        help="County name (optional)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Max records to import",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't actually import, just show what would happen",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point for the import CLI.

    Args:
        argv: Command-line arguments. Defaults to sys.argv[1:].

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    count, errors = asyncio.run(
        import_region(
            provider=args.provider,
            state=args.state,
            county=args.county,
            limit=args.limit,
            dry_run=args.dry_run,
        )
    )

    if errors > 0:
        print(f"Imported {count} properties, {errors} errors")
        return 1

    print(f"Imported {count} properties")
    return 0


if __name__ == "__main__":
    sys.exit(main())
