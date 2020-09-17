#!/home/rmc/progs/python/anaconda3/bin/python3

import sys
import os
import netCDF4 as nc
import numpy as np
import glob2
import datetime
import argparse

ZLIB=True
COMPLEVEL=0
DEFAULT_PATH = '/media/monet/public/model/hindcast/NCEP/atmos/CFSR/'

# Ignore Warnings from Fill Value
import warnings
warnings.filterwarnings("ignore")


def check_and_remove_dups(file1, file2):
	d1 = nc.Dataset(file1)
	d2 = nc.Dataset(file2)
	if d1.variables['time'][-1] == d2.variables['time'][0]:
		print(f"  \033[31m==\033[m Times match: {datetime.datetime.fromtimestamp(d1.variables['time'][-1])}. Deleting on {file1}...")
		dup_dataset(d1, remove_last_entry=True)
		
def dup_dataset(orig, remove_last_entry=False, dup_first_entry=False):
	new = nc.Dataset(orig.filepath() + '.tmp', 'w', persist=True, format='NETCDF4_CLASSIC')

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

	# Get the variable Name 
	vars = [k for k in orig.variables if k not in ('time', 'latitude', 'longitude')]
	if len(vars) != 1:
		print(f"The file {orig.filepath()} has multiple variables {repr(vars)}. Ignoring...")
		return

	var_name = vars[0]

	var_orig = orig.variables[var_name]
	var = new.createVariable(var_name, 'f4', ('time', 'latitude', 'longitude'), fill_value=var_orig._FillValue, zlib=ZLIB, complevel=COMPLEVEL) # complevel doesnt really do much
	var.units = var_orig.units
	var.level = var_orig.level
	var.short_name = var_orig.short_name
	var.long_name = var_orig.long_name
	var.add_offset = var_orig.add_offset
	var.scale_factor = var_orig.scale_factor

	# COPY THE ACTUAL DATA
	lat[:] = orig.variables['latitude'][:]
	lon[:] = orig.variables['longitude'][:]

	if remove_last_entry:
		var[:] = var_orig[:-1]
		t[:] = orig.variables['time'][:-1]
	elif dup_first_entry:
		var[0] = var_orig[0] # dup first entry
		var[1:] = var_orig[:] # copy the rest

		t[0] = orig.variables['time'][0] - 3600.0
		t[1:] = orig.variables['time'][:]
	else: # normal copy
		var[:] = var_orig[:]
		t[:] = orig.variables['time'][:]

	new.sync()
	new.close()


# ============================
#           MAIN
# ============================

# PARSE ARGUMENTS
parser = argparse.ArgumentParser(description='Remove duplica entries in a dataset if the last time of a montly file is the same as the first time of next months file.')
parser.add_argument('variables', nargs='+', metavar='VAR', help='Variables to be processed. (Should refer to the beginning of filenames)')
parser.add_argument('-p', '--path', help='Root path to find variables', default=DEFAULT_PATH)
args = parser.parse_args()


for var in args.variables:

	files = glob2.glob(args.path + '**/' + args.variables[0] + '*.nc')
	files.sort()
	print(f"Found {len(files)} files in {args.path + '/**/' + args.variables[0] + '*.nc'}")

	for i in range(1, len(files)):
		print(f"Processing {i}/{len(files)} -- {files[i-1]}  {files[i]}")
		check_and_remove_dups(files[i-1], files[i])

