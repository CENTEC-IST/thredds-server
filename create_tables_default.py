#!/home/rmc/progs/python/anaconda3/bin/python

# ============================================
#
# Automate database creation for ERA5 dataset
# Packages needed for Ubuntu:
#
#     postgresql postgis libpq-dev
#
# ============================================

import psycopg2

# ==========================
# DATABASE SETTINS
connection = psycopg2.connect(
		dbname = "eximus",
		user = "eximus",
		host = "localhost",
		password = "1234")

# ==========================

cursor = connection.cursor()

# CREATE COORDINATES TABLE
cursor.execute("""
		CREATE TABLE IF NOT EXISTS coordinates(
			id SERIAL PRIMARY KEY);
		""")

# ADD POSTGIS EXTENSION TO IMPROVE COORDINATE QUERIES
cursor.execute("""
		CREATE EXTENSION IF NOT EXISTS postgis;
		""")

try:
	# ADD COORDINATES COLUMN
	# NOTE !! Y axis is Latitude and X axis is Longitude, so should be inserted as POINT(lon, lat)
	# 2D POINT 8 bytes
	cursor.execute("""
			SELECT AddGeometryColumn ('coordinates', 'coord', 0, 'POINT', 2);
			""")

	# ADD NOT NULL AND UNIQUE CONSTRAINT ON COORDINATES COLUMN
	cursor.execute("""
			ALTER TABLE coordinates ALTER COLUMN coord SET NOT NULL;
			""")
	cursor.execute("""
			ALTER TABLE coordinates ADD UNIQUE(coord);
			""")

except psycopg2.errors.DuplicateColumn:
	print("Table coordinates exists. Skipping...")

# CREATE TIMESTAMPS TABLE
cursor.execute("""
		CREATE TABLE IF NOT EXISTS timestamps(
			id SERIAL PRIMARY KEY,
			time TIMESTAMP NOT NULL,
			UNIQUE(time));
		""")

# CREATE METEOROLOGY DATA TABLE
cursor.execute("""
		CREATE TABLE IF NOT EXISTS meteo(
			cid INT NOT NULL,
			tid INT NOT NULL,
			wind_10u FLOAT,
			wind_10v FLOAT,
			swh FLOAT,
			CONSTRAINT fk_coordinates
				FOREIGN KEY(cid)
					REFERENCES coordinates(id),
			CONSTRAINT fk_timestamps
				FOREIGN KEY(tid)
					REFERENCES timestamps(id));
		""")

try:
	# CHANGE DEFAULT VALUES FOR VARIABLES
	cursor.execute("""
			ALTER TABLE meteo
				ALTER COLUMN wind_10u SET DEFAULT NULL,
				ALTER COLUMN wind_10v SET DEFAULT NULL,
				ALTER COLUMN swh SET DEFAULT NULL;
			""")
except psycopg2.errors.DuplicateColumn:
	print("Table coordinates exists. Skipping...")


connection.commit()

def table_info(tab_name):
	cursor.execute(f"""
			SELECT column_name, data_type, is_nullable, column_default
			FROM information_schema.columns
			WHERE table_name = '{tab_name}';
			""")
	tab = [('Column', 'Type', 'Nullable', 'Default')]
	tab.extend(cursor.fetchall())
	print('\n'.join(['| '.join([c.ljust(1+max([len(x[i]) if x[i] else 0 for x in tab])) if c else '' for i, c in enumerate(entry)]) for entry in tab]))

print('COORDINATES COLUMN: ')
table_info('coordinates')
print('\nTIMESTAMPS COLUMN: ')
table_info('timestamps')
print('\nMETEO DATA COLUMN: ')
table_info('meteo')

cursor.close()
connection.close()

