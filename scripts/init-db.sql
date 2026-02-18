-- ParcelData Database Initialization
-- PostgreSQL 16 + PostGIS + pgvector

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS btree_gist;

-- Verify extensions
SELECT extname, extversion FROM pg_extension 
WHERE extname IN ('postgis', 'vector', 'pg_trgm', 'btree_gist');

-- Create schemas
CREATE SCHEMA IF NOT EXISTS parcel;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS audit;

-- Grant permissions
GRANT ALL ON SCHEMA parcel TO parceldata;
GRANT ALL ON SCHEMA analytics TO parceldata;
GRANT ALL ON SCHEMA audit TO parceldata;

-- Log successful initialization
DO $$
BEGIN
  RAISE NOTICE 'ParcelData database initialized successfully';
END $$;
