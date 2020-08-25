/* Run with psql -d era5 -f create-era5.sql */

\set ON_ERROR_STOP on

CREATE TABLE IF NOT EXISTS "meta" (
  "id" SERIAL PRIMARY KEY,
  "variable" varchar NOT NULL,
  "starttime" timestamp NOT NULL,
  "timescale" interval NOT NULL,
  "totaltime" interval NOT NULL
);

/* Add postgis extension to manage coordinate queries */
CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS "wind_10u" (
	"id" int NOT NULL REFERENCES meta(id)
);
CREATE TABLE IF NOT EXISTS "wind_10v" (
	"id" int NOT NULL REFERENCES meta(id)
);
CREATE TABLE IF NOT EXISTS "significant_height" (
	"id" int NOT NULL REFERENCES meta(id)
);

/* Add columns to be indexed by postgis */
SELECT AddGeometryColumn ('wind_10u', 'coordinate', 0, 'POINT', 2);
SELECT AddGeometryColumn ('wind_10v', 'coordinate', 0, 'POINT', 2);
SELECT AddGeometryColumn ('significant_height', 'coordinate', 0, 'POINT', 2);

ALTER TABLE wind_10u ADD COLUMN data oid;
ALTER TABLE wind_10v ADD COLUMN data oid;
ALTER TABLE significant_height ADD COLUMN data oid;

\unset ON_ERROR_STOP
