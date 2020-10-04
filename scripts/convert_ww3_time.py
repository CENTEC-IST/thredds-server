#!/home/rmc/progs/python/anaconda3/bin/python3 -u

import sys
import os
import netCDF4 as nc
import numpy as np
import time

ZLIB=True
COMPLEVEL=7
TIME_VAR = 'date'
NEW_TIME_VAR = 'time'

# Ignore Warnings from Fill Value
import warnings
warnings.filterwarnings("ignore")

def dup_dataset(orig):
	new = nc.Dataset(orig.filepath() + '.tmp', 'w', persist=True, format='NETCDF4_CLASSIC')

	# COPY VARIABLE INFORMATION
	new.createDimension('latitude', orig.dimensions['latitude'].size)
	lat = new.createVariable('latitude', 'f4', ('latitude',), zlib=ZLIB, complevel=COMPLEVEL)
	lat.units = orig.variables['latitude'].units

	new.createDimension('longitude', orig.dimensions['longitude'].size)
	lon = new.createVariable('longitude', 'f4', ('longitude',), zlib=ZLIB, complevel=COMPLEVEL)
	lon.units = orig.variables['longitude'].units

	new.createDimension('partition', orig.dimensions['partition'].size)
	p = new.createVariable('partition', 'i4', ('partition',), zlib=ZLIB, complevel=COMPLEVEL)
	p.units = orig.variables['partition'].units

	new.createDimension(NEW_TIME_VAR, orig.dimensions[TIME_VAR].size)
	t = new.createVariable(NEW_TIME_VAR, 'f8', (NEW_TIME_VAR,), zlib=ZLIB, complevel=COMPLEVEL)
	t.units = "seconds since 1970-1-1 00:00:00"
	# Get the variable Name
	for var in (v for v in orig.variables if v not in orig.dimensions):
		var_orig = orig.variables[var]
		if len(var_orig.shape) == 4:
			depends_on = (NEW_TIME_VAR, 'partition', 'latitude', 'longitude')
		if len(var_orig.shape) == 3:
			depends_on = (NEW_TIME_VAR, 'latitude', 'longitude')
		if len(var_orig.shape) == 2:
			depends_on = ('latitude', 'longitude')

		print(f"Copying {var}")
		var = new.createVariable(var, 'f4', depends_on, fill_value=var_orig._FillValue, zlib=ZLIB, complevel=COMPLEVEL)
		var.units = var_orig.units

		# COPY THE ACTUAL DATA
		lat[:] = orig.variables['latitude'][:]
		lon[:] = orig.variables['longitude'][:]
		t[:] = orig.variables[TIME_VAR][:] * 3600 * 24
		p[:] = orig.variables['partition'][:]
		var[:] = var_orig[:]

	new.sync()
	new.close()
	return True


# ============================
#           MAIN
# ============================


for file in sys.argv[1:]:
	print(f"Processing {file}")
	stime = time.time()
	dup_dataset(nc.Dataset(file))
	print("Processed in %.3f" % (time.time() - stime))

