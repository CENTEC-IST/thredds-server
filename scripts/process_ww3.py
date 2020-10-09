#!/home/rmc/progs/python/anaconda3/bin/python3 -u

import sys
import xarray
from dask.diagnostics import ProgressBar
import numpy as np
import time

LATMIN=-77.5
LATMAX=90.
LONMIN=-102.
LONMAX=30.

def process_ww3(orig, target):
	xdata = xarray.open_dataset(orig, chunks={'date':30, 'partition':4}) # process dataset in chunks (to avoid overflowing memory
	xdata = xdata.rename({'date':'time'}) # rename 

	xdata['longitude'] = xdata.longitude - 180 # adjust longitude, latitude should be fine -90, 90

	# crop
	mask_lat = (xdata.latitude >= LATMIN) & (xdata.latitude <= LATMAX)
	mask_lon = (xdata.longitude >= LONMIN ) & ( xdata.longitude <= LONMAX)
	xcrop = xdata.where(mask_lat & mask_lon, drop = True) # since chunks was used, this will only be proccessed when writing to disk

	# generate encoding for data vars
	comp = dict(zlib=True, complevel=7) # the original file uses 9 but since we are reducing its size ill use less compression here
	with ProgressBar():
		xcrop.to_netcdf(target, format='NETCDF4_CLASSIC', encoding={var: comp for var in xcrop.data_vars})


# ============================
#			MAIN
# ============================


for file in sys.argv[1:]:
	print(f"Processing {file}")
	stime = time.time()
	process_ww3(file, file + '.tmp')
	print("Processed in %.3f" % (time.time() - stime))

