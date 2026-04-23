"""Add PostGIS spatial and pgvector embedding columns to properties.

Revision ID: 003
Revises: 002
Create Date: 2026-04-23

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: str | None = "002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add spatial columns using raw SQL (geoalchemy2 not available in alembic)
    op.execute("ALTER TABLE parcel.properties ADD COLUMN IF NOT EXISTS location geometry(POINT, 4326)")
    op.execute("ALTER TABLE parcel.properties ADD COLUMN IF NOT EXISTS boundary geometry(POLYGON, 4326)")
    # Add pgvector embedding column
    op.execute("ALTER TABLE parcel.properties ADD COLUMN IF NOT EXISTS embedding vector(1536)")
    # Spatial GiST index on location
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_properties_location ON parcel.properties USING gist(location)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_properties_location")
    op.execute("ALTER TABLE parcel.properties DROP COLUMN IF EXISTS embedding")
    op.execute("ALTER TABLE parcel.properties DROP COLUMN IF EXISTS boundary")
    op.execute("ALTER TABLE parcel.properties DROP COLUMN IF EXISTS location")
