"""Tests for Alembic migration (S15)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from app.database.connection import Base
from app.models import (
    HOA,
    Address,
    Building,
    Environmental,
    Listing,
    Ownership,
    Permit,
    Property,
    School,
    Tax,
    Transaction,
    Valuation,
    Zoning,
)


def test_migration_file_exists() -> None:
    """Initial migration file exists in alembic/versions/."""
    migration = Path(
        "alembic/versions/001_initial_schema.py"
    )
    assert migration.exists()


def test_migration_is_importable() -> None:
    """Migration module can be imported without errors."""
    spec = importlib.util.spec_from_file_location(
        "initial_schema",
        "alembic/versions/001_initial_schema.py",
    )
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    assert hasattr(mod, "upgrade")
    assert hasattr(mod, "downgrade")
    assert mod.revision == "001"
    assert mod.down_revision is None


def test_all_models_in_metadata() -> None:
    """All model tables are registered in Base.metadata."""
    table_names = {t.name for t in Base.metadata.tables.values()}
    expected = {
        "properties",
        "addresses",
        "buildings",
        "valuations",
        "ownerships",
        "zonings",
        "listings",
        "transactions",
        "permits",
        "environmentals",
        "schools",
        "taxes",
        "hoas",
    }
    assert expected.issubset(table_names)


def test_all_tables_in_parcel_schema() -> None:
    """All data model tables use the parcel schema."""
    # Exclude test tables from test_models_base.py
    for table in Base.metadata.tables.values():
        if table.name.startswith("_test_"):
            continue
        assert table.schema == "parcel", (
            f"Table {table.name} should be in parcel schema"
        )


def test_model_count() -> None:
    """Verify we have all 13 data models (excluding test tables)."""
    models = [
        Property,
        Address,
        Building,
        Valuation,
        Ownership,
        Zoning,
        Listing,
        Transaction,
        Permit,
        Environmental,
        School,
        Tax,
        HOA,
    ]
    assert len(models) == 13
    # Each model has a __tablename__
    for model in models:
        assert hasattr(model, "__tablename__")
