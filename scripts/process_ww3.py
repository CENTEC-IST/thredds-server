#!/home/rmc/progs/python/anaconda3/bin/python3 -u

import sys, os
import xarray
from dask.diagnostics import ProgressBar
import numpy as np
import time

LATMIN=-77.5
LATMAX=90.
LONMIN=-102.
LONMAX=30.

# the original file uses 9 but since we are reducing its size ill use less compression here
COMPRESSION = 7
PARTITIONS_TO_KEEP = 19 # the file with least amount of partitions has 19

def process_ww3(orig, target):
	xdata = xarray.open_dataset(orig)

	if 'date' in xdata: # rename
		xdata = xdata.rename({'date':'time'})
	
	# process dataset in chunks (to avoid overflowing memory)
	# xdata = xdata.chunk({'time':100, 'partition':10})
	# xdata = xdata.chunk({dim:'auto' for dim in xdata.dims})
	# xdata = xdata.unify_chunks()

	if xdata.longitude[0] == 0:
		# adjust longitude, latitude should be fine -90, 90
		xdata['longitude'] = xdata.longitude - 180 

	xcrop = xdata.sel(latitude = slice(LATMIN, LATMAX),
					longitude = slice(LONMIN, LONMAX),
					partition = slice(0, PARTITIONS_TO_KEEP))

	# # crop
	# mask_lat = (xdata.latitude >= LATMIN) & (xdata.latitude <= LATMAX)
	# mask_lon = (xdata.longitude >= LONMIN ) & ( xdata.longitude <= LONMAX)
	# mask_part = (xdata.partition < REMOVE_PARTITIONS_HIGHER)
	# # since chunks was used, this will only be proccessed when writing to disk
	# xcrop = xdata.where(mask_lat & mask_lon & mask_part, drop = True)

	# generate encoding for data vars
	enc = dict(zlib=True, complevel=COMPRESSION) 
	with ProgressBar():
		xcrop.to_netcdf(target, format='NETCDF4_CLASSIC', encoding={var: enc for var in xcrop.data_vars})

	xdata.close()

# ============================
#			MAIN
# ============================

files = sys.argv[1:]
for i, file in enumerate(files):
	print(f"Processing [{i}/{len(sys.argv)-2}] {file}")
	stime = time.time()
	process_ww3(file, file + '.tmp')
	print("Processed in %.3f" % (time.time() - stime))
	print(f"Moving {file}")
	os.rename(file + '.tmp', file) # Overwrite original file

