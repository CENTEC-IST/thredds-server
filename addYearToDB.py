#!/home/rmc/progs/python/anaconda3/bin/python

# NOTE:
# This script was made to load files from /ECMWF/ERA5/[year]

import sys
import netCDF4 as nc
import psycopg2
import glob

import io
import numpy

####################################################
VARIABLES = ['10u', '10v'] # NOTE CHANGE HERE
####################################################

LOG_FILE_NAME = 'log/addFiles.log'
_log_file = None

def log(msg):
	'''Function to send output to a file as well as a console,
	Call this instead of print throughout the file to generate log files
	'''
	global _log_file
	if not _log_file:
		_log_file = open(LOG_FILE_NAME, 'w')
	_log_file.write(msg + '\n')
	_log_file.flush()
	print(msg)

#     ===================  MAIN  ===================

if len(sys.argv) != 2:
	log(f"Usage {__file__} [year-directory-with-nc-files]\n\tExample: {__file__} /media/degas/model/ECMWF/ER5/2000")
	sys.exit(1)

year = sys.argv[1].strip('/').split('/')[-1]

files = sorted(glob.glob(f"{sys.argv[1]}/*.nc"))

# Create dictionary with files for each variable (measurement) defined above
measurement_files = {k:[f for f in files if k in f] for k in VARIABLES}

# Verify if there are the same amount of files for each measurement (usually there is)
lens = [len(x) for x in measurement_files.values()]
if not all(x == lens[0] for x in lens):
	log("There is a diferent ammount of files for each variable")
	sys.exit(1)


# ==========================
# DATABASE SETTINS
connection = psycopg2.connect(
		dbname = "timescale",
		user = "eximus",
		host = "localhost",
		password = "1234")

cursor = connection.cursor()

# Init string data loader to load data into memory and speed up insertion process
strio = io.StringIO()

# ============================


# Main cicle to add each month
for month in range(lens[0]):
	# Open the files
	open_datasets = {k:nc.Dataset(measurement_files[k][month]) for k in VARIABLES}
	
	# Compare measurement sizes to see if they match
	measurement_sizes = [open_datasets[k].variables[k].size for k in VARIABLES]
	if not all(x == measurement_sizes[0] for x in measurement_sizes):
		log(f"The size of the datasets differ:\n{chr(10).join(['%d -> %s' % (i, measurement_files[k][month]) for k, i in zip(measurement_files, measurement_sizes)])}")
		sys.exit(1)
	
	one_of_the_datasets = list(open_datasets.values()).pop()

	# generate list of timestamps -- PROBABLY GOING TO BE DISCARDED
	timestamps = [f"{year}{month+1:02}{int(i/24)+1:02} {i%24:02}0000" for i in range(len(one_of_the_datasets.variables['time']))] # format "%Y%m%d %H0000"

	log("Loading measurement data into memory (may take some time)...")
	data = {k:list(open_datasets[k].variables[k]) for k in VARIABLES}

	lon = list(one_of_the_datasets.variables['lon'])
	lat = list(one_of_the_datasets.variables['lat'])

	for k, t in enumerate(timestamps):
		log('Building string')
		for i, x in enumerate(lon):
			for j, y in enumerate(lat):
				strio.write(f"POINT({x} {y})\t{t}\t{data['10u'][k][j][i]}\t{data['10v'][k][j][i]}\n") # FIXME fix this hardcode
		log(f"\rInserting {t}")
		strio.seek(0)
		cursor.copy_from(strio, 'metrics', columns=('location', 'time', 'w10u', 'w10v')) # FIXME fix this hardcode
		if k%5==0:
			connection.commit()


