#!/home/rmc/progs/python/anaconda3/bin/python3

import sys
import os
import netCDF4 as nc
import numpy as np

ZLIB=True
COMPLEVEL=3

if len(sys.argv) < 2:
	print("Give me a file to process")
	sys.exit()

files = sys.argv[1:]

for i, fname in enumerate(files):
	orig = nc.Dataset(fname)

	print(f'{i+1}/{len(files)}' + fname)

	# Create output in out/ directory
	dirname = os.path.dirname(fname)  
	new = nc.Dataset(dirname + ('/' if dirname else '')  + 'out/' + os.path.basename(fname) + '.tmp', 'w', persist=True, format='NETCDF4_CLASSIC')

	# COPY VARIABLE INFORMATION
	new.createDimension('latitude', orig.dimensions['latitude'].size)
	lat = new.createVariable('latitude', 'f4', ('latitude',), zlib=ZLIB, complevel=COMPLEVEL)
	lat.units = orig.variables['latitude'].units
	lat.long_name = orig.variables['latitude'].long_name

	new.createDimension('longitude', orig.dimensions['longitude'].size)
	lon = new.createVariable('longitude', 'f4', ('longitude',), zlib=ZLIB, complevel=COMPLEVEL)
	lon.units = orig.variables['longitude'].units
	lon.long_name = orig.variables['longitude'].long_name

	new.createDimension('time', None)
	t = new.createVariable('time', 'f8', ('time',), zlib=ZLIB, complevel=COMPLEVEL)
	t.units = orig.variables['time'].units
	t.reference_time = orig.variables['time'].reference_time
	t.reference_date = orig.variables['time'].reference_date
	t.reference_time_description = orig.variables['time'].reference_time_description
	t.time_step = orig.variables['time'].time_step
	t.time_step_setting = orig.variables['time'].time_step_setting

	# dependant
	pot_orig = orig.variables['POT_5mbelowsealevel']
	pot = new.createVariable('POT_5mbelowsealevel', 'f4', ('time', 'latitude', 'longitude'), fill_value=pot_orig._FillValue, zlib=ZLIB, complevel=COMPLEVEL) # complevel doesnt really do much
	pot.units = pot_orig.units
	pot.level = pot_orig.level
	pot.short_name = pot_orig.short_name
	pot.long_name = pot_orig.long_name
	pot.add_offset = pot_orig.add_offset
	pot.scale_factor = pot_orig.scale_factor

	# COPY THE ACTUAL DATA
	lat[:] = orig.variables['latitude'][:]
	lon[:] = orig.variables['longitude'][:]

	pot[0] = pot_orig[0] # dup first entry
	pot[1:] = pot_orig[:] # copy the rest

	t[0] = orig.variables['time'][0] - 3600.0
	t[1:] = orig.variables['time'][:]

	new.sync()
	new.close()
