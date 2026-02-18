"""Tests for API key and account models (P10-04 S1-S2)."""

from __future__ import annotations

from app.models import Account, APIKey, TierEnum, UsageEvent, UsageRecord

# ── S1: API Key Model ────────────────────────────────────────────


class TestTierEnum:
    """TierEnum values."""

    def test_tier_values(self) -> None:
        assert TierEnum.FREE.value == "free"
        assert TierEnum.PRO.value == "pro"
        assert TierEnum.BUSINESS.value == "business"
        assert TierEnum.ENTERPRISE.value == "enterprise"

    def test_tier_is_string(self) -> None:
        assert isinstance(TierEnum.FREE, str)
        assert TierEnum.PRO == "pro"


class TestAccountModel:
    """Account model columns and relationships."""

    def test_tablename_and_schema(self) -> None:
        assert Account.__tablename__ == "accounts"
        assert Account.__table_args__["schema"] == "parcel"

    def test_primary_key(self) -> None:
        pk_cols = [c.name for c in Account.__table__.primary_key.columns]
        assert pk_cols == ["id"]

    def test_required_columns(self) -> None:
        cols = {c.name for c in Account.__table__.columns}
        for col in [
            "email",
            "email_verified",
            "name",
            "company",
            "stripe_customer_id",
            "tier",
            "is_active",
            "created_at",
            "updated_at",
        ]:
            assert col in cols, f"Missing column: {col}"

    def test_email_unique_index(self) -> None:
        email_col = Account.__table__.c.email
        assert email_col.unique is True
        assert email_col.index is True

    def test_stripe_customer_id_indexed(self) -> None:
        col = Account.__table__.c.stripe_customer_id
        assert col.index is True

    def test_relationships(self) -> None:
        rels = {r.key for r in Account.__mapper__.relationships}
        assert "api_keys" in rels
        assert "usage_records" in rels


class TestAPIKeyModel:
    """API Key model columns and relationships."""

    def test_tablename_and_schema(self) -> None:
        assert APIKey.__tablename__ == "api_keys"
        assert APIKey.__table_args__["schema"] == "parcel"

    def test_primary_key(self) -> None:
        pk_cols = [c.name for c in APIKey.__table__.primary_key.columns]
        assert pk_cols == ["id"]

    def test_required_columns(self) -> None:
        cols = {c.name for c in APIKey.__table__.columns}
        for col in [
            "key_hash",
            "key_prefix",
            "account_id",
            "name",
            "tier",
            "scopes",
            "is_active",
            "last_used",
            "rate_limit_override",
            "daily_limit_override",
            "expires_at",
            "created_at",
            "updated_at",
        ]:
            assert col in cols, f"Missing column: {col}"

    def test_key_hash_unique_index(self) -> None:
        col = APIKey.__table__.c.key_hash
        assert col.unique is True
        assert col.index is True

    def test_account_id_foreign_key(self) -> None:
        col = APIKey.__table__.c.account_id
        fk = list(col.foreign_keys)[0]
        assert str(fk.column) == "accounts.id"

    def test_account_relationship(self) -> None:
        rels = {r.key for r in APIKey.__mapper__.relationships}
        assert "account" in rels

    def test_scopes_is_jsonb(self) -> None:
        col = APIKey.__table__.c.scopes
        assert col.type.__class__.__name__ == "JSONB"


# ── S2: Usage Record Model ───────────────────────────────────────


class TestUsageRecordModel:
    """UsageRecord model columns and relationships."""

    def test_tablename_and_schema(self) -> None:
        assert UsageRecord.__tablename__ == "usage_records"
        assert UsageRecord.__table_args__["schema"] == "parcel"

    def test_required_columns(self) -> None:
        cols = {c.name for c in UsageRecord.__table__.columns}
        for col in [
            "account_id",
            "api_key_id",
            "usage_date",
            "queries_count",
            "queries_billable",
            "property_lookups",
            "property_searches",
            "comparables_requests",
            "batch_requests",
            "estimated_cost",
        ]:
            assert col in cols, f"Missing column: {col}"

    def test_usage_date_indexed(self) -> None:
        col = UsageRecord.__table__.c.usage_date
        assert col.index is True

    def test_foreign_keys(self) -> None:
        col_account = UsageRecord.__table__.c.account_id
        fk_account = list(col_account.foreign_keys)[0]
        assert str(fk_account.column) == "accounts.id"

        col_key = UsageRecord.__table__.c.api_key_id
        fk_key = list(col_key.foreign_keys)[0]
        assert str(fk_key.column) == "api_keys.id"

    def test_account_relationship(self) -> None:
        rels = {r.key for r in UsageRecord.__mapper__.relationships}
        assert "account" in rels


class TestUsageEventModel:
    """UsageEvent model columns."""

    def test_tablename_and_schema(self) -> None:
        assert UsageEvent.__tablename__ == "usage_events"
        assert UsageEvent.__table_args__["schema"] == "parcel"

    def test_required_columns(self) -> None:
        cols = {c.name for c in UsageEvent.__table__.columns}
        for col in [
            "api_key_id",
            "endpoint",
            "method",
            "query_count",
            "status_code",
            "response_time_ms",
            "timestamp",
        ]:
            assert col in cols, f"Missing column: {col}"

    def test_endpoint_indexed(self) -> None:
        col = UsageEvent.__table__.c.endpoint
        assert col.index is True

    def test_timestamp_indexed(self) -> None:
        col = UsageEvent.__table__.c.timestamp
        assert col.index is True

    def test_foreign_key(self) -> None:
        col = UsageEvent.__table__.c.api_key_id
        fk = list(col.foreign_keys)[0]
        assert str(fk.column) == "api_keys.id"
