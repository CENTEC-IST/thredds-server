/* Run with psql -d era5 -f create-era5.sql */

CREATE TABLE IF NOT EXISTS "meta" (
  "code" SERIAL PRIMARY KEY,
  "variable" varchar NOT NULL,
  "timescale" int NOT NULL,
  "totalsize" int DEFAULT 0,
  "blocksize" int DEFAULT 0,
  "starttime" timestamp NOT NULL
);

/* Add postgis extension to manage coordinate queries */
CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS "w10u" ();
CREATE TABLE IF NOT EXISTS "w10v" ();
CREATE TABLE IF NOT EXISTS "swh" ();

/* Add columns to be indexed by postgis */
SELECT AddGeometryColumn ('w10v', 'coordinate', 0, 'POINT', 2);
SELECT AddGeometryColumn ('w10u', 'coordinate', 0, 'POINT', 2);
SELECT AddGeometryColumn ('swh', 'coordinate', 0, 'POINT', 2);

ALTER TABLE w10u ADD COLUMN data oid;
ALTER TABLE w10v ADD COLUMN data oid;
ALTER TABLE swh ADD COLUMN data oid;
