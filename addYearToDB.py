#!/home/rmc/progs/python/anaconda3/bin/python
import sys
import netCDF4 as nc
import psycopg2
import glob

import io
import numpy

if len(sys.argv) != 2:
	print(f"Usage {__file__} [year-directory-with-nc-files]\n\tExample: {__file__} /media/degas/model/ECMWF/ER5/2000")
	sys.exit(1)

files = sorted(glob.glob(f"{sys.argv[1]}/*.nc"))
datasets = {'10u':[f for f in files if '10u' in f],
			'10v':[f for f in files if '10v' in f],
			'swh':[f for f in files if 'swh' in f]}

# Verify if there are the same amount of files for each variable
if not (len(datasets['10u']) == len(datasets['10v']) == len(datasets['swh'])):
	print("There is a diferent ammount of files for each variable")
	sys.exit(1)


# MAIN CICLE TO ADD EACH MONTH
for month in range(len(datasets['10u'])):

	open_datasets = [nc.Dataset(datasets['10u'][month]), nc.Dataset(datasets['10v'][month]), nc.Dataset(datasets['swh'][month])]
	if not (open_datasets[0]['time'].size == open_datasets[1]['time'].size == open_datasets[2]['time'].size):
		print(f"Dataset timestamps sizes differ")
		sys.exit(1)

	file_date = sys.argv[1].split('.')[-2] # format "%Y%m"
	timestamps = [f"{file_date}{int(i/24)+1:02} {i%24:02}0000" for i in range(len(open_datasets.variables['time']))] # format "%Y%m%d %H0000"

	# ==========================
	# DATABASE SETTINS
	connection = psycopg2.connect(
			dbname = "timescale",
			user = "eximus",
			host = "localhost",
			password = "1234")

	cursor = connection.cursor()

	# Init string data loader and load data into memory to speed up the process
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


