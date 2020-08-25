#!/home/rmc/progs/python/anaconda3/bin/python

# NOTE:
# This script was made to load files from /ECMWF/ERA5/[year]

import sys
import netCDF4 as nc
import psycopg2
import glob
import time

import io
import numpy

####################################################
VARIABLES = ['10u', '10v', 'swh'] # NOTE CHANGE HERE
####################################################

POSTGRESQL_TABLE_NAMES = {'10u':'wind_10u', '10v':'wind_10v', 'swh':'significant_height'}

LOG_FILE_NAME = f"log/addToDB_{time.strftime('%Y%m%d.%H%M%S')}.log"
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

# ==========================
# DATABASE SETTINS
connection = psycopg2.connect(
		dbname = "era5",
		user = "eximus",
		host = "localhost",
		password = "1234")

cursor = connection.cursor()


# Init string data loader to load data into memory and speed up insertion process
strio = io.StringIO()

# ============================

for k in measurement_files:
	# Open all the datasets for each variable
	open_datasets = [nc.Dataset(f) for f in measurement_files[k]]

	# Verify datasets starting time index[0] used to acess first month since they were sorted before
	if open_datasets[0].variables['time'].units.startswith(f'hours since {year}'):
		starttime = open_datasets[0].variables['time'].units[12:]
		timescale = '1H'
	else:
		log(f"Start time is incorrect '{open_datasets[0].variables['time'].units}'. Expected  'hours since {year}...'")
		sys.exit(1)
	
	totaltime = str(sum(d.variables['time'].size for d in open_datasets)) + 'H'

	# Add Entry to the meta database
	cursor.execute(f"""INSERT INTO meta (variable, starttime, timescale, totaltime)
			VALUES ('{POSTGRESQL_TABLE_NAMES[k]}', '{starttime}', '{timescale}', '{totaltime}')
			RETURNING id;""")
	connection.commit()

	entry_id = cursor.fetchall().pop()

	t = time.time()
	print("HERE %s" % k)
	# TODO Load data by chunks of coordinates to see if it improves performance.
	# Raw querying takes about 45 seconds to get a time slice for a specific coordinate across all files
	# data = [numpy.array(d.variables[k]) for d in open_datasets]

	# dp = numpy.array(numpy.concatenate([d.variables[k][:,10,10] for d in open_datasets]))
	# print(dp.size)

	print("DONE", time.time()-t)

	sys.exit(0)
