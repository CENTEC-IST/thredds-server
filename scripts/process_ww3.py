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

# the original file uses 9 but since we are reducing its size we will use less compression here, since its faster too
COMPRESSION = 6
PARTITIONS_TO_KEEP = 19 # the file with least amount of partitions has 19

def process_ww3(orig, target):
	xdata = xarray.open_dataset(orig)

	if 'date' in xdata: # rename
		xdata = xdata.rename({'date':'time'})

	# process dataset in chunks (to avoid overflowing memory)
	xdata = xdata.chunk({'time':100, 'partition':10})
	# xdata = xdata.chunk({dim:'auto' for dim in xdata.dims})
	# xdata = xdata.unify_chunks()

	# adjust longitude, latitude should be fine -90, 90
	xdata.coords['longitude'] = (xdata.coords['longitude'] + 180) % 360 - 180
	xdata = xdata.sortby(xdata.longitude)

	xcrop = xdata.sel(latitude = slice(LATMIN, LATMAX),
					longitude = slice(LONMIN, LONMAX),
					partition = slice(0, PARTITIONS_TO_KEEP))

	# generate encoding for data vars
	enc = dict(zlib=True, complevel=COMPRESSION)
	with ProgressBar():
		xcrop.to_netcdf(target, format='NETCDF4_CLASSIC', encoding={var: enc for var in xcrop.data_vars})

	xdata.close()
	return True

# ============================
#			MAIN
# ============================

files = sys.argv[1:]
for i, file in enumerate(files):
	print(f"Processing [{i+1}/{len(files)}] {file}")
	stime = time.time()
	try:
		process_ww3(file, file + '.tmp')
		print("Processed in %.3f" % (time.time() - stime))
		print(f"Moving {file}")
		os.rename(file + '.tmp', file) # Overwrite original file
	except RuntimeError as e:
		print(f"\033[31mFailed processing {file}\033[m")
