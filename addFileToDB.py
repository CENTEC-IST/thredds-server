#!/home/rmc/progs/python/anaconda3/bin/python
import sys
import netCDF4 as nc
import psycopg2

import io
import numpy

if len(sys.argv) != 2:
    print(f"Usage {__file__} [your_netcdf4file.nc]")
    sys.exit(1)

try:
	d = nc.Dataset(sys.argv[1])
except FileNotFoundError:
	print(f"File not found: {sys.argv[1]}")
	sys.exit(1)

# ==========================
# DATABASE SETTINS
connection = psycopg2.connect(
		dbname = "tutorial",
		user = "eximus",
		host = "localhost",
		password = "1234")

cursor = connection.cursor()

file_date = sys.argv[1].split('.')[-2] # format "%Y%m"
timestamps = [f"{file_date}{int(i/24)+1:02} {i%24:02}0000" for i in range(len(d.variables['time']))] # format "%Y%m%d %H0000"

strio = io.StringIO()

data = list(d.variables['10u'])
lon = list(d.variables['lon'])
lat = list(d.variables['lat'])

for k, t in enumerate(timestamps):
	for i, x in enumerate(lon):
		for j, y in enumerate(lat):
			strio.write(f"POINT({x} {y})\t{t}\t{data[k][j][i]}\n")
	print(f"\rInserting {t}")
	strio.seek(0)
	cursor.copy_from(strio, 'metrics', columns=('location', 'time', 'w10u'))
	if k%5==0:
		connection.commit()



# for i, x in enumerate(lon):
# 	for j, y in enumerate(lat):
# 		print(x,y)
# 			cursor.execute(f"""
# 				INSERT INTO metrics (location, time, w10u)
# 				VALUES ('POINT({x} {y})', '{t}', '{data[k][j][i]}');
# 			""")

