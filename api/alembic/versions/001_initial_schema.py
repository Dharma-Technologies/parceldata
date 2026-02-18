"""Initial schema with all property models.

Revision ID: 001
Revises:
Create Date: 2026-02-18

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _create_core_tables() -> None:
    """Create properties, addresses, and buildings tables."""
    op.create_table(
        "properties",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("state_fips", sa.String(2), nullable=False),
        sa.Column("county_fips", sa.String(3), nullable=False),
        sa.Column("county_name", sa.String(100), nullable=False),
        sa.Column("county_apn", sa.String(50), nullable=False),
        sa.Column("legal_description", sa.Text, nullable=True),
        sa.Column("subdivision_name", sa.String(200), nullable=True),
        sa.Column("lot_number", sa.String(50), nullable=True),
        sa.Column("block_number", sa.String(50), nullable=True),
        sa.Column("lot_sqft", sa.Integer, nullable=True),
        sa.Column("lot_acres", sa.Float, nullable=True),
        sa.Column("lot_depth_ft", sa.Float, nullable=True),
        sa.Column("lot_width_ft", sa.Float, nullable=True),
        sa.Column("lot_dimensions", sa.String(50), nullable=True),
        sa.Column("property_type", sa.String(50), nullable=True),
        sa.Column("property_use", sa.String(100), nullable=True),
        sa.Column("census_tract", sa.String(20), nullable=True),
        sa.Column("census_block_group", sa.String(20), nullable=True),
        sa.Column("canonical_id", sa.String(50), nullable=True),
        sa.Column("entity_confidence", sa.Float, default=1.0),
        # TimestampMixin
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        # DataQualityMixin
        sa.Column("quality_score", sa.Float, default=0.0),
        sa.Column("quality_completeness", sa.Float, default=0.0),
        sa.Column("quality_accuracy", sa.Float, default=0.0),
        sa.Column("quality_consistency", sa.Float, default=0.0),
        sa.Column("quality_timeliness", sa.Float, default=0.0),
        sa.Column("quality_validity", sa.Float, default=0.0),
        sa.Column("quality_uniqueness", sa.Float, default=0.0),
        sa.Column("freshness_hours", sa.Integer, default=0),
        # ProvenanceMixin
        sa.Column("source_system", sa.String(100), nullable=True),
        sa.Column("source_type", sa.String(50), nullable=True),
        sa.Column("source_record_id", sa.String(100), nullable=True),
        sa.Column("extraction_timestamp", sa.DateTime, nullable=True),
        sa.Column("raw_data_hash", sa.String(64), nullable=True),
        sa.Column("transformation_version", sa.String(20), nullable=True),
        schema="parcel",
    )
    op.create_index("ix_properties_state_fips", "properties", ["state_fips"], schema="parcel")
    op.create_index("ix_properties_county_fips", "properties", ["county_fips"], schema="parcel")
    op.create_index("ix_properties_county_apn", "properties", ["county_apn"], schema="parcel")
    op.create_index("ix_properties_property_type", "properties", ["property_type"], schema="parcel")
    op.create_index("ix_properties_census_tract", "properties", ["census_tract"], schema="parcel")
    op.create_index("ix_properties_canonical_id", "properties", ["canonical_id"], schema="parcel")
    op.create_index("ix_properties_state_county", "properties", ["state_fips", "county_fips"], schema="parcel")

    op.create_table(
        "addresses",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("property_id", sa.String(50), sa.ForeignKey("parcel.properties.id"), unique=True),
        sa.Column("raw_address", sa.String(500), nullable=True),
        sa.Column("street_number", sa.String(20), nullable=True),
        sa.Column("street_name", sa.String(200), nullable=True),
        sa.Column("street_suffix", sa.String(20), nullable=True),
        sa.Column("street_direction", sa.String(10), nullable=True),
        sa.Column("unit_type", sa.String(20), nullable=True),
        sa.Column("unit_number", sa.String(20), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("state", sa.String(2), nullable=True),
        sa.Column("zip_code", sa.String(5), nullable=True),
        sa.Column("zip4", sa.String(4), nullable=True),
        sa.Column("county", sa.String(100), nullable=True),
        sa.Column("street_address", sa.String(300), nullable=True),
        sa.Column("formatted_address", sa.String(500), nullable=True),
        sa.Column("latitude", sa.Float, nullable=True),
        sa.Column("longitude", sa.Float, nullable=True),
        sa.Column("geocode_accuracy", sa.String(20), nullable=True),
        sa.Column("geocode_source", sa.String(50), nullable=True),
        sa.Column("usps_validated", sa.Boolean, default=False),
        sa.Column("normalization_score", sa.Float, default=0.0),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        schema="parcel",
    )
    op.create_index("ix_addresses_city", "addresses", ["city"], schema="parcel")
    op.create_index("ix_addresses_state", "addresses", ["state"], schema="parcel")
    op.create_index("ix_addresses_zip_code", "addresses", ["zip_code"], schema="parcel")
    op.create_index("ix_addresses_city_state", "addresses", ["city", "state"], schema="parcel")
    op.create_index("ix_addresses_lat_lng", "addresses", ["latitude", "longitude"], schema="parcel")

    op.create_table(
        "buildings",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("property_id", sa.String(50), sa.ForeignKey("parcel.properties.id")),
        sa.Column("building_number", sa.Integer, default=1),
        sa.Column("sqft", sa.Integer, nullable=True),
        sa.Column("sqft_finished", sa.Integer, nullable=True),
        sa.Column("sqft_unfinished", sa.Integer, nullable=True),
        sa.Column("stories", sa.Integer, nullable=True),
        sa.Column("bedrooms", sa.Integer, nullable=True),
        sa.Column("bathrooms", sa.Float, nullable=True),
        sa.Column("bathrooms_full", sa.Integer, nullable=True),
        sa.Column("bathrooms_half", sa.Integer, nullable=True),
        sa.Column("year_built", sa.Integer, nullable=True),
        sa.Column("year_renovated", sa.Integer, nullable=True),
        sa.Column("effective_year_built", sa.Integer, nullable=True),
        sa.Column("construction_type", sa.String(50), nullable=True),
        sa.Column("exterior_wall", sa.String(50), nullable=True),
        sa.Column("roof_type", sa.String(50), nullable=True),
        sa.Column("roof_material", sa.String(50), nullable=True),
        sa.Column("foundation_type", sa.String(50), nullable=True),
        sa.Column("heating_type", sa.String(50), nullable=True),
        sa.Column("cooling_type", sa.String(50), nullable=True),
        sa.Column("garage_type", sa.String(50), nullable=True),
        sa.Column("garage_spaces", sa.Integer, nullable=True),
        sa.Column("parking_spaces", sa.Integer, nullable=True),
        sa.Column("pool", sa.Boolean, default=False),
        sa.Column("pool_type", sa.String(50), nullable=True),
        sa.Column("fireplace", sa.Boolean, default=False),
        sa.Column("fireplace_count", sa.Integer, nullable=True),
        sa.Column("basement", sa.Boolean, default=False),
        sa.Column("basement_type", sa.String(50), nullable=True),
        sa.Column("attic", sa.Boolean, default=False),
        sa.Column("quality_grade", sa.String(20), nullable=True),
        sa.Column("condition", sa.String(20), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        schema="parcel",
    )
    op.create_index("ix_buildings_property_id", "buildings", ["property_id"], schema="parcel")
    op.create_index("ix_buildings_bedrooms", "buildings", ["bedrooms"], schema="parcel")
    op.create_index("ix_buildings_year_built", "buildings", ["year_built"], schema="parcel")
    op.create_index("ix_buildings_beds_baths", "buildings", ["bedrooms", "bathrooms"], schema="parcel")


def _create_value_tables() -> None:
    """Create valuations, ownerships, and zonings tables."""
    op.create_table(
        "valuations",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("property_id", sa.String(50), sa.ForeignKey("parcel.properties.id"), unique=True),
        sa.Column("assessed_total", sa.Integer, nullable=True),
        sa.Column("assessed_land", sa.Integer, nullable=True),
        sa.Column("assessed_improvements", sa.Integer, nullable=True),
        sa.Column("assessed_year", sa.Integer, nullable=True),
        sa.Column("assessment_date", sa.Date, nullable=True),
        sa.Column("estimated_value", sa.Integer, nullable=True),
        sa.Column("estimated_value_low", sa.Integer, nullable=True),
        sa.Column("estimated_value_high", sa.Integer, nullable=True),
        sa.Column("estimate_confidence", sa.Float, nullable=True),
        sa.Column("estimate_date", sa.Date, nullable=True),
        sa.Column("estimate_model", sa.String(50), nullable=True),
        sa.Column("price_per_sqft", sa.Float, nullable=True),
        sa.Column("price_per_acre", sa.Float, nullable=True),
        sa.Column("value_change_1yr", sa.Float, nullable=True),
        sa.Column("value_change_5yr", sa.Float, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        schema="parcel",
    )
    op.create_index("ix_valuations_estimated_value", "valuations", ["estimated_value"], schema="parcel")

    op.create_table(
        "ownerships",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("property_id", sa.String(50), sa.ForeignKey("parcel.properties.id"), unique=True),
        sa.Column("owner_name", sa.String(200), nullable=True),
        sa.Column("owner_name_2", sa.String(200), nullable=True),
        sa.Column("owner_type", sa.String(50), nullable=True),
        sa.Column("owner_entity_id", sa.String(50), nullable=True),
        sa.Column("mailing_street", sa.String(200), nullable=True),
        sa.Column("mailing_city", sa.String(100), nullable=True),
        sa.Column("mailing_state", sa.String(2), nullable=True),
        sa.Column("mailing_zip", sa.String(10), nullable=True),
        sa.Column("owner_occupied", sa.Boolean, nullable=True),
        sa.Column("acquisition_date", sa.Date, nullable=True),
        sa.Column("acquisition_price", sa.Integer, nullable=True),
        sa.Column("acquisition_type", sa.String(50), nullable=True),
        sa.Column("ownership_length_years", sa.Float, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        schema="parcel",
    )
    op.create_index("ix_ownerships_owner_name", "ownerships", ["owner_name"], schema="parcel")
    op.create_index("ix_ownerships_owner_entity_id", "ownerships", ["owner_entity_id"], schema="parcel")
    op.create_index("ix_ownerships_acquisition_date", "ownerships", ["acquisition_date"], schema="parcel")

    op.create_table(
        "zonings",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("property_id", sa.String(50), sa.ForeignKey("parcel.properties.id"), unique=True),
        sa.Column("zone_code", sa.String(20), nullable=True),
        sa.Column("zone_description", sa.String(200), nullable=True),
        sa.Column("zone_category", sa.String(50), nullable=True),
        sa.Column("overlay_districts", postgresql.ARRAY(sa.String), nullable=True),
        sa.Column("historic_district", sa.Boolean, default=False),
        sa.Column("permitted_uses", postgresql.ARRAY(sa.String), nullable=True),
        sa.Column("conditional_uses", postgresql.ARRAY(sa.String), nullable=True),
        sa.Column("prohibited_uses", postgresql.ARRAY(sa.String), nullable=True),
        sa.Column("setback_front_ft", sa.Float, nullable=True),
        sa.Column("setback_rear_ft", sa.Float, nullable=True),
        sa.Column("setback_side_ft", sa.Float, nullable=True),
        sa.Column("max_height_ft", sa.Float, nullable=True),
        sa.Column("max_stories", sa.Integer, nullable=True),
        sa.Column("max_far", sa.Float, nullable=True),
        sa.Column("max_lot_coverage", sa.Float, nullable=True),
        sa.Column("min_lot_size_sqft", sa.Integer, nullable=True),
        sa.Column("min_lot_width_ft", sa.Float, nullable=True),
        sa.Column("max_units_per_acre", sa.Float, nullable=True),
        sa.Column("parking_spaces_required", sa.Integer, nullable=True),
        sa.Column("adu_permitted", sa.Boolean, nullable=True),
        sa.Column("adu_rules", postgresql.JSONB, nullable=True),
        sa.Column("jurisdiction", sa.String(100), nullable=True),
        sa.Column("ordinance_reference", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        schema="parcel",
    )
    op.create_index("ix_zonings_zone_code", "zonings", ["zone_code"], schema="parcel")


def _create_market_tables() -> None:
    """Create listings, transactions, and permits tables."""
    op.create_table(
        "listings",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("property_id", sa.String(50), sa.ForeignKey("parcel.properties.id")),
        sa.Column("mls_number", sa.String(20), unique=True),
        sa.Column("mls_source", sa.String(50), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("list_date", sa.Date, nullable=True),
        sa.Column("pending_date", sa.Date, nullable=True),
        sa.Column("sold_date", sa.Date, nullable=True),
        sa.Column("expiration_date", sa.Date, nullable=True),
        sa.Column("days_on_market", sa.Integer, nullable=True),
        sa.Column("cumulative_dom", sa.Integer, nullable=True),
        sa.Column("list_price", sa.Integer, nullable=True),
        sa.Column("original_list_price", sa.Integer, nullable=True),
        sa.Column("sold_price", sa.Integer, nullable=True),
        sa.Column("price_per_sqft", sa.Float, nullable=True),
        sa.Column("public_remarks", sa.Text, nullable=True),
        sa.Column("private_remarks", sa.Text, nullable=True),
        sa.Column("features", postgresql.ARRAY(sa.String), nullable=True),
        sa.Column("appliances", postgresql.ARRAY(sa.String), nullable=True),
        sa.Column("photo_count", sa.Integer, default=0),
        sa.Column("photo_urls", postgresql.ARRAY(sa.String), nullable=True),
        sa.Column("virtual_tour_url", sa.String(500), nullable=True),
        sa.Column("showing_instructions", sa.Text, nullable=True),
        sa.Column("lockbox_type", sa.String(50), nullable=True),
        sa.Column("listing_agent_name", sa.String(100), nullable=True),
        sa.Column("listing_agent_phone", sa.String(20), nullable=True),
        sa.Column("listing_agent_email", sa.String(100), nullable=True),
        sa.Column("listing_agent_license", sa.String(50), nullable=True),
        sa.Column("listing_office_name", sa.String(100), nullable=True),
        sa.Column("listing_office_phone", sa.String(20), nullable=True),
        sa.Column("buyer_agent_name", sa.String(100), nullable=True),
        sa.Column("buyer_office_name", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        schema="parcel",
    )
    op.create_index("ix_listings_property_id", "listings", ["property_id"], schema="parcel")
    op.create_index("ix_listings_mls_number", "listings", ["mls_number"], schema="parcel")
    op.create_index("ix_listings_status", "listings", ["status"], schema="parcel")
    op.create_index("ix_listings_list_date", "listings", ["list_date"], schema="parcel")
    op.create_index("ix_listings_sold_date", "listings", ["sold_date"], schema="parcel")
    op.create_index("ix_listings_list_price", "listings", ["list_price"], schema="parcel")

    _provenance_cols = [
        sa.Column("source_system", sa.String(100), nullable=True),
        sa.Column("source_type", sa.String(50), nullable=True),
        sa.Column("source_record_id", sa.String(100), nullable=True),
        sa.Column("extraction_timestamp", sa.DateTime, nullable=True),
        sa.Column("raw_data_hash", sa.String(64), nullable=True),
        sa.Column("transformation_version", sa.String(20), nullable=True),
    ]

    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("property_id", sa.String(50), sa.ForeignKey("parcel.properties.id")),
        sa.Column("document_number", sa.String(50), nullable=True),
        sa.Column("recording_date", sa.Date, nullable=True),
        sa.Column("book", sa.String(20), nullable=True),
        sa.Column("page", sa.String(20), nullable=True),
        sa.Column("transaction_date", sa.Date, nullable=True),
        sa.Column("deed_type", sa.String(50), nullable=True),
        sa.Column("transaction_type", sa.String(50), nullable=True),
        sa.Column("grantor", sa.String(200), nullable=True),
        sa.Column("grantee", sa.String(200), nullable=True),
        sa.Column("sale_price", sa.Integer, nullable=True),
        sa.Column("price_per_sqft", sa.Float, nullable=True),
        sa.Column("loan_amount", sa.Integer, nullable=True),
        sa.Column("lender_name", sa.String(200), nullable=True),
        sa.Column("arms_length", sa.Boolean, nullable=True),
        sa.Column("distressed", sa.Boolean, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        *_provenance_cols,
        schema="parcel",
    )
    op.create_index("ix_transactions_property_id", "transactions", ["property_id"], schema="parcel")
    op.create_index("ix_transactions_document_number", "transactions", ["document_number"], schema="parcel")
    op.create_index("ix_transactions_recording_date", "transactions", ["recording_date"], schema="parcel")

    _provenance_cols2 = [
        sa.Column("source_system", sa.String(100), nullable=True),
        sa.Column("source_type", sa.String(50), nullable=True),
        sa.Column("source_record_id", sa.String(100), nullable=True),
        sa.Column("extraction_timestamp", sa.DateTime, nullable=True),
        sa.Column("raw_data_hash", sa.String(64), nullable=True),
        sa.Column("transformation_version", sa.String(20), nullable=True),
    ]

    op.create_table(
        "permits",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("property_id", sa.String(50), sa.ForeignKey("parcel.properties.id")),
        sa.Column("permit_number", sa.String(50), nullable=False),
        sa.Column("permit_type", sa.String(50), nullable=True),
        sa.Column("permit_subtype", sa.String(100), nullable=True),
        sa.Column("status", sa.String(50), nullable=True),
        sa.Column("application_date", sa.Date, nullable=True),
        sa.Column("issue_date", sa.Date, nullable=True),
        sa.Column("expiration_date", sa.Date, nullable=True),
        sa.Column("final_date", sa.Date, nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("work_class", sa.String(50), nullable=True),
        sa.Column("valuation", sa.Integer, nullable=True),
        sa.Column("fee_paid", sa.Float, nullable=True),
        sa.Column("contractor_name", sa.String(200), nullable=True),
        sa.Column("contractor_license", sa.String(50), nullable=True),
        sa.Column("contractor_phone", sa.String(20), nullable=True),
        sa.Column("last_inspection_date", sa.Date, nullable=True),
        sa.Column("last_inspection_result", sa.String(50), nullable=True),
        sa.Column("inspections_passed", sa.Integer, default=0),
        sa.Column("inspections_failed", sa.Integer, default=0),
        sa.Column("jurisdiction", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        *_provenance_cols2,
        schema="parcel",
    )
    op.create_index("ix_permits_property_id", "permits", ["property_id"], schema="parcel")
    op.create_index("ix_permits_permit_number", "permits", ["permit_number"], schema="parcel")
    op.create_index("ix_permits_permit_type", "permits", ["permit_type"], schema="parcel")
    op.create_index("ix_permits_status", "permits", ["status"], schema="parcel")
    op.create_index("ix_permits_issue_date", "permits", ["issue_date"], schema="parcel")


def _create_supplementary_tables() -> None:
    """Create environmental, schools, taxes, and HOA tables."""
    op.create_table(
        "environmentals",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("property_id", sa.String(50), sa.ForeignKey("parcel.properties.id"), unique=True),
        sa.Column("flood_zone", sa.String(10), nullable=True),
        sa.Column("flood_zone_description", sa.String(200), nullable=True),
        sa.Column("in_100yr_floodplain", sa.Boolean, nullable=True),
        sa.Column("in_500yr_floodplain", sa.Boolean, nullable=True),
        sa.Column("flood_insurance_required", sa.Boolean, nullable=True),
        sa.Column("flood_map_date", sa.String(20), nullable=True),
        sa.Column("flood_panel_number", sa.String(20), nullable=True),
        sa.Column("base_flood_elevation", sa.Float, nullable=True),
        sa.Column("wildfire_risk", sa.String(20), nullable=True),
        sa.Column("wildfire_score", sa.Float, nullable=True),
        sa.Column("in_wui", sa.Boolean, nullable=True),
        sa.Column("earthquake_risk", sa.String(20), nullable=True),
        sa.Column("earthquake_score", sa.Float, nullable=True),
        sa.Column("near_fault_line", sa.Boolean, nullable=True),
        sa.Column("fault_distance_miles", sa.Float, nullable=True),
        sa.Column("liquefaction_risk", sa.Boolean, nullable=True),
        sa.Column("superfund_site", sa.Boolean, nullable=True),
        sa.Column("superfund_distance_miles", sa.Float, nullable=True),
        sa.Column("brownfield_site", sa.Boolean, nullable=True),
        sa.Column("underground_storage_tanks", sa.Boolean, nullable=True),
        sa.Column("radon_zone", sa.String(10), nullable=True),
        sa.Column("tornado_risk", sa.String(20), nullable=True),
        sa.Column("hurricane_risk", sa.String(20), nullable=True),
        sa.Column("hail_risk", sa.String(20), nullable=True),
        sa.Column("overall_risk_score", sa.Float, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        schema="parcel",
    )

    op.create_table(
        "schools",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("property_id", sa.String(50), sa.ForeignKey("parcel.properties.id"), unique=True),
        sa.Column("district_name", sa.String(100), nullable=True),
        sa.Column("district_id", sa.String(20), nullable=True),
        sa.Column("district_rating", sa.Integer, nullable=True),
        sa.Column("elementary_name", sa.String(100), nullable=True),
        sa.Column("elementary_id", sa.String(20), nullable=True),
        sa.Column("elementary_rating", sa.Integer, nullable=True),
        sa.Column("elementary_distance_miles", sa.Float, nullable=True),
        sa.Column("middle_name", sa.String(100), nullable=True),
        sa.Column("middle_id", sa.String(20), nullable=True),
        sa.Column("middle_rating", sa.Integer, nullable=True),
        sa.Column("middle_distance_miles", sa.Float, nullable=True),
        sa.Column("high_name", sa.String(100), nullable=True),
        sa.Column("high_id", sa.String(20), nullable=True),
        sa.Column("high_rating", sa.Integer, nullable=True),
        sa.Column("high_distance_miles", sa.Float, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        schema="parcel",
    )

    op.create_table(
        "taxes",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("property_id", sa.String(50), sa.ForeignKey("parcel.properties.id"), unique=True),
        sa.Column("annual_amount", sa.Float, nullable=True),
        sa.Column("tax_year", sa.Integer, nullable=True),
        sa.Column("tax_rate", sa.Float, nullable=True),
        sa.Column("exemptions", postgresql.ARRAY(sa.String), nullable=True),
        sa.Column("exemption_amount", sa.Float, nullable=True),
        sa.Column("last_paid_date", sa.Date, nullable=True),
        sa.Column("last_paid_amount", sa.Float, nullable=True),
        sa.Column("delinquent", sa.Boolean, default=False),
        sa.Column("delinquent_amount", sa.Float, nullable=True),
        sa.Column("tax_lien", sa.Boolean, default=False),
        sa.Column("tax_sale_scheduled", sa.Boolean, default=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        schema="parcel",
    )

    op.create_table(
        "hoas",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("property_id", sa.String(50), sa.ForeignKey("parcel.properties.id"), unique=True),
        sa.Column("hoa_name", sa.String(200), nullable=True),
        sa.Column("hoa_exists", sa.Boolean, nullable=True),
        sa.Column("fee_monthly", sa.Float, nullable=True),
        sa.Column("fee_annual", sa.Float, nullable=True),
        sa.Column("fee_includes", postgresql.ARRAY(sa.String), nullable=True),
        sa.Column("special_assessment", sa.Boolean, default=False),
        sa.Column("special_assessment_amount", sa.Float, nullable=True),
        sa.Column("rental_allowed", sa.Boolean, nullable=True),
        sa.Column("rental_restrictions", sa.String(500), nullable=True),
        sa.Column("pet_policy", sa.String(200), nullable=True),
        sa.Column("contact_name", sa.String(100), nullable=True),
        sa.Column("contact_phone", sa.String(20), nullable=True),
        sa.Column("contact_email", sa.String(100), nullable=True),
        sa.Column("management_company", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        schema="parcel",
    )


def upgrade() -> None:
    """Create parcel schema and all property-related tables."""
    op.execute("CREATE SCHEMA IF NOT EXISTS parcel")
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    _create_core_tables()
    _create_value_tables()
    _create_market_tables()
    _create_supplementary_tables()


def downgrade() -> None:
    """Drop all tables in parcel schema."""
    op.drop_table("hoas", schema="parcel")
    op.drop_table("taxes", schema="parcel")
    op.drop_table("schools", schema="parcel")
    op.drop_table("environmentals", schema="parcel")
    op.drop_table("permits", schema="parcel")
    op.drop_table("transactions", schema="parcel")
    op.drop_table("listings", schema="parcel")
    op.drop_table("zonings", schema="parcel")
    op.drop_table("ownerships", schema="parcel")
    op.drop_table("valuations", schema="parcel")
    op.drop_table("buildings", schema="parcel")
    op.drop_table("addresses", schema="parcel")
    op.drop_table("properties", schema="parcel")
    op.execute("DROP SCHEMA IF EXISTS parcel CASCADE")
