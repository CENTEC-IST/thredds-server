
# This script is indented to test read speeds on a collection of files specified in the data_path variable as a glob expression


import xarray as xr
import pandas
import dask
import netCDF4 as nc
import numpy as np
import time
import glob2

# CHANGE HERE
data_path = "dump/*.nc"

start = time.time()
ds = xr.open_mfdataset(glob2.glob(data_path))
print('----');
print(repr(np.mean(ds.variables['ICEC_surface'].values[:,100,100])))
print('xarray '+repr(time.time() - start)+' seconds')
ds.close()

# -----------------------------------------------

start = time.time()
ds=nc.MFDataset(data_path)
print('----');
print(repr(np.mean(ds.variables['ICEC_surface'][:,100,100])))
print('netCDF4 '+repr(time.time() - start)+' seconds')
ds.close()

