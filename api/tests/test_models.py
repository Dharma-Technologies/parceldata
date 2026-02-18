"""Tests for all data models (S2-S13)."""

from __future__ import annotations

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

# ── S2: Property Model ──────────────────────────────────────────


class TestPropertyModel:
    """Property model columns, indexes, and relationships."""

    def test_tablename_and_schema(self) -> None:
        assert Property.__tablename__ == "properties"
        assert Property.__table_args__[-1]["schema"] == "parcel"

    def test_primary_key(self) -> None:
        pk_cols = [c.name for c in Property.__table__.primary_key.columns]
        assert pk_cols == ["id"]

    def test_required_county_columns(self) -> None:
        cols = {c.name for c in Property.__table__.columns}
        for col in [
            "state_fips",
            "county_fips",
            "county_name",
            "county_apn",
        ]:
            assert col in cols

    def test_spatial_columns_exist(self) -> None:
        cols = {c.name for c in Property.__table__.columns}
        assert "location" in cols
        assert "boundary" in cols

    def test_embedding_column_exists(self) -> None:
        cols = {c.name for c in Property.__table__.columns}
        assert "embedding" in cols

    def test_entity_resolution_columns(self) -> None:
        cols = {c.name for c in Property.__table__.columns}
        assert "canonical_id" in cols
        assert "entity_confidence" in cols

    def test_indexes(self) -> None:
        index_names = {idx.name for idx in Property.__table__.indexes}
        assert "ix_properties_state_county" in index_names

    def test_relationships_defined(self) -> None:
        rel_keys = set(Property.__mapper__.relationships.keys())
        expected = {
            "address",
            "buildings",
            "valuation",
            "ownership",
            "zoning",
            "listing",
            "transactions",
            "permits",
            "environmental",
            "school",
            "hoa",
            "tax",
        }
        assert expected.issubset(rel_keys)

    def test_inherits_mixins(self) -> None:
        cols = {c.name for c in Property.__table__.columns}
        # TimestampMixin
        assert "created_at" in cols
        assert "updated_at" in cols
        # DataQualityMixin
        assert "quality_score" in cols
        # ProvenanceMixin
        assert "source_system" in cols


# ── S3: Address Model ───────────────────────────────────────────


class TestAddressModel:
    """Address model columns and indexes."""

    def test_tablename_and_schema(self) -> None:
        assert Address.__tablename__ == "addresses"
        assert Address.__table_args__[-1]["schema"] == "parcel"

    def test_foreign_key_to_property(self) -> None:
        fk = list(Address.__table__.c.property_id.foreign_keys)[0]
        assert str(fk.column) == "properties.id"

    def test_normalized_address_fields(self) -> None:
        cols = {c.name for c in Address.__table__.columns}
        for field in [
            "street_number",
            "street_name",
            "city",
            "state",
            "zip_code",
        ]:
            assert field in cols

    def test_geocoding_fields(self) -> None:
        cols = {c.name for c in Address.__table__.columns}
        assert "latitude" in cols
        assert "longitude" in cols
        assert "geocode_accuracy" in cols

    def test_indexes(self) -> None:
        index_names = {idx.name for idx in Address.__table__.indexes}
        assert "ix_addresses_city_state" in index_names
        assert "ix_addresses_lat_lng" in index_names


# ── S4: Building Model ──────────────────────────────────────────


class TestBuildingModel:
    """Building model columns and indexes."""

    def test_tablename_and_schema(self) -> None:
        assert Building.__tablename__ == "buildings"
        assert Building.__table_args__[-1]["schema"] == "parcel"

    def test_structural_columns(self) -> None:
        cols = {c.name for c in Building.__table__.columns}
        for field in [
            "sqft",
            "stories",
            "bedrooms",
            "bathrooms",
            "year_built",
        ]:
            assert field in cols

    def test_feature_columns(self) -> None:
        cols = {c.name for c in Building.__table__.columns}
        for field in ["pool", "fireplace", "basement", "attic"]:
            assert field in cols

    def test_beds_baths_index(self) -> None:
        index_names = {idx.name for idx in Building.__table__.indexes}
        assert "ix_buildings_beds_baths" in index_names


# ── S5: Valuation Model ─────────────────────────────────────────


class TestValuationModel:
    """Valuation model columns."""

    def test_tablename_and_schema(self) -> None:
        assert Valuation.__tablename__ == "valuations"
        assert Valuation.__table_args__ == {"schema": "parcel"}

    def test_assessed_value_columns(self) -> None:
        cols = {c.name for c in Valuation.__table__.columns}
        for field in [
            "assessed_total",
            "assessed_land",
            "assessed_improvements",
        ]:
            assert field in cols

    def test_estimated_value_columns(self) -> None:
        cols = {c.name for c in Valuation.__table__.columns}
        assert "estimated_value" in cols
        assert "estimate_confidence" in cols

    def test_unique_property_constraint(self) -> None:
        assert Valuation.__table__.c.property_id.unique is True


# ── S6: Ownership Model ─────────────────────────────────────────


class TestOwnershipModel:
    """Ownership model columns."""

    def test_tablename_and_schema(self) -> None:
        assert Ownership.__tablename__ == "ownerships"
        assert Ownership.__table_args__ == {"schema": "parcel"}

    def test_owner_columns(self) -> None:
        cols = {c.name for c in Ownership.__table__.columns}
        for field in [
            "owner_name",
            "owner_type",
            "owner_entity_id",
            "owner_occupied",
        ]:
            assert field in cols

    def test_acquisition_columns(self) -> None:
        cols = {c.name for c in Ownership.__table__.columns}
        for field in [
            "acquisition_date",
            "acquisition_price",
            "acquisition_type",
        ]:
            assert field in cols


# ── S7: Zoning Model ────────────────────────────────────────────


class TestZoningModel:
    """Zoning model columns."""

    def test_tablename_and_schema(self) -> None:
        assert Zoning.__tablename__ == "zonings"
        assert Zoning.__table_args__ == {"schema": "parcel"}

    def test_zone_classification_columns(self) -> None:
        cols = {c.name for c in Zoning.__table__.columns}
        for field in ["zone_code", "zone_description", "zone_category"]:
            assert field in cols

    def test_dimensional_requirement_columns(self) -> None:
        cols = {c.name for c in Zoning.__table__.columns}
        for field in [
            "setback_front_ft",
            "max_height_ft",
            "max_far",
            "max_lot_coverage",
        ]:
            assert field in cols

    def test_adu_columns(self) -> None:
        cols = {c.name for c in Zoning.__table__.columns}
        assert "adu_permitted" in cols
        assert "adu_rules" in cols


# ── S8: Listing Model ───────────────────────────────────────────


class TestListingModel:
    """Listing model columns."""

    def test_tablename_and_schema(self) -> None:
        assert Listing.__tablename__ == "listings"
        assert Listing.__table_args__ == {"schema": "parcel"}

    def test_mls_columns(self) -> None:
        cols = {c.name for c in Listing.__table__.columns}
        assert "mls_number" in cols
        assert "mls_source" in cols
        assert "status" in cols

    def test_pricing_columns(self) -> None:
        cols = {c.name for c in Listing.__table__.columns}
        for field in [
            "list_price",
            "original_list_price",
            "sold_price",
        ]:
            assert field in cols

    def test_agent_columns(self) -> None:
        cols = {c.name for c in Listing.__table__.columns}
        assert "listing_agent_name" in cols
        assert "buyer_agent_name" in cols

    def test_mls_number_unique(self) -> None:
        assert Listing.__table__.c.mls_number.unique is True


# ── S9: Transaction Model ───────────────────────────────────────


class TestTransactionModel:
    """Transaction model columns."""

    def test_tablename_and_schema(self) -> None:
        assert Transaction.__tablename__ == "transactions"
        assert Transaction.__table_args__ == {"schema": "parcel"}

    def test_recording_columns(self) -> None:
        cols = {c.name for c in Transaction.__table__.columns}
        for field in ["document_number", "recording_date", "book", "page"]:
            assert field in cols

    def test_financial_columns(self) -> None:
        cols = {c.name for c in Transaction.__table__.columns}
        for field in ["sale_price", "loan_amount", "lender_name"]:
            assert field in cols

    def test_party_columns(self) -> None:
        cols = {c.name for c in Transaction.__table__.columns}
        assert "grantor" in cols
        assert "grantee" in cols

    def test_inherits_provenance(self) -> None:
        cols = {c.name for c in Transaction.__table__.columns}
        assert "source_system" in cols
        assert "raw_data_hash" in cols


# ── S10: Permit Model ───────────────────────────────────────────


class TestPermitModel:
    """Permit model columns."""

    def test_tablename_and_schema(self) -> None:
        assert Permit.__tablename__ == "permits"
        assert Permit.__table_args__ == {"schema": "parcel"}

    def test_permit_info_columns(self) -> None:
        cols = {c.name for c in Permit.__table__.columns}
        for field in [
            "permit_number",
            "permit_type",
            "status",
        ]:
            assert field in cols

    def test_inspection_columns(self) -> None:
        cols = {c.name for c in Permit.__table__.columns}
        assert "inspections_passed" in cols
        assert "inspections_failed" in cols

    def test_inherits_provenance(self) -> None:
        cols = {c.name for c in Permit.__table__.columns}
        assert "source_system" in cols


# ── S11: Environmental Model ────────────────────────────────────


class TestEnvironmentalModel:
    """Environmental model columns."""

    def test_tablename_and_schema(self) -> None:
        assert Environmental.__tablename__ == "environmentals"
        assert Environmental.__table_args__ == {"schema": "parcel"}

    def test_flood_columns(self) -> None:
        cols = {c.name for c in Environmental.__table__.columns}
        for field in [
            "flood_zone",
            "in_100yr_floodplain",
            "flood_insurance_required",
        ]:
            assert field in cols

    def test_hazard_columns(self) -> None:
        cols = {c.name for c in Environmental.__table__.columns}
        for field in [
            "wildfire_risk",
            "earthquake_risk",
            "superfund_site",
        ]:
            assert field in cols

    def test_risk_score(self) -> None:
        cols = {c.name for c in Environmental.__table__.columns}
        assert "overall_risk_score" in cols


# ── S12: School Model ───────────────────────────────────────────


class TestSchoolModel:
    """School model columns."""

    def test_tablename_and_schema(self) -> None:
        assert School.__tablename__ == "schools"
        assert School.__table_args__ == {"schema": "parcel"}

    def test_district_columns(self) -> None:
        cols = {c.name for c in School.__table__.columns}
        assert "district_name" in cols
        assert "district_rating" in cols

    def test_school_level_columns(self) -> None:
        cols = {c.name for c in School.__table__.columns}
        for level in ["elementary", "middle", "high"]:
            assert f"{level}_name" in cols
            assert f"{level}_rating" in cols
            assert f"{level}_distance_miles" in cols


# ── S13: Tax and HOA Models ─────────────────────────────────────


class TestTaxModel:
    """Tax model columns."""

    def test_tablename_and_schema(self) -> None:
        assert Tax.__tablename__ == "taxes"
        assert Tax.__table_args__ == {"schema": "parcel"}

    def test_tax_columns(self) -> None:
        cols = {c.name for c in Tax.__table__.columns}
        for field in [
            "annual_amount",
            "tax_year",
            "tax_rate",
            "delinquent",
        ]:
            assert field in cols

    def test_exemption_columns(self) -> None:
        cols = {c.name for c in Tax.__table__.columns}
        assert "exemptions" in cols
        assert "exemption_amount" in cols


class TestHOAModel:
    """HOA model columns."""

    def test_tablename_and_schema(self) -> None:
        assert HOA.__tablename__ == "hoas"
        assert HOA.__table_args__ == {"schema": "parcel"}

    def test_hoa_columns(self) -> None:
        cols = {c.name for c in HOA.__table__.columns}
        for field in [
            "hoa_name",
            "hoa_exists",
            "fee_monthly",
            "fee_annual",
        ]:
            assert field in cols

    def test_rules_columns(self) -> None:
        cols = {c.name for c in HOA.__table__.columns}
        assert "rental_allowed" in cols
        assert "pet_policy" in cols
