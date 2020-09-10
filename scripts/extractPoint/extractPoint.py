#!/home/rmc/progs/python/anaconda3/bin/python3

import netCDF4 as nc
import time

URL_ENDPOINT = "http://193.136.153.163/thredds/dodsC/WAVERYS_collection/WAVERYS_Collection_fmrc.ncd"

def load_points(filename):
	'''Load points from file with the line format:
	latitude  longitude  name

	Returns a list of tuples (a tuple per line, with latitude and longitude as floats)
	'''
	def make_tuple(split_line):
		return (float(split_line[0]), float(split_line[1]), split_line[2])
	with open(filename, 'r') as fp:
		return [make_tuple(line.strip('\n').split()) for line in fp]

def query_thredds_opendap(endpoint=URL_ENDPOINT, **var_query):
	'''Query the opendap endpoint for a certain variable with given parameters:
	The variable must be a named function argument and the parameters must be a tuple or list of tuples
	Example:
		- Querying longitude and latitude:
		query_thredds_opendap(enpoint, longitude=(0,1799), latitude(0,10,898))
		# Result query "http://[ip]/thredds/dodsC/[collection].ncd?longitude[0:1799],latitude[0:10:898]"

		- Querying a variable with 'run', 'time', 'latitude' and 'longitude'
		query_thredds_opendap(enpoint, VHM0=[(0),(0,3),(20),(20)])
		# Result query "http://[ip]/thredds/dodsC/[collection].ncd?VHM0[0][0:3][20][20]"

	Returns the netCDF4 dataset given from the url query
	'''
	def process_tuple(t):
		return f"[{':'.join(str(i) for i in t)}]"
	def process_list(l): # also convert items that might not be tuples
		return ''.join([process_tuple(i if type(i)==tuple else (i,)) for i in l])

	def process_args():
		for var, value in var_query.items():
			if type(value) in (int, float):
				yield f"{var}{process_tuple((value,))}"
			elif type(value) == tuple:
				yield f"{var}{process_tuple(value)}"
			elif type(value) == list:
				yield f"{var}{process_list(value)}"

	url = endpoint + '?' + ','.join(process_args())
	return nc.Dataset(url)


# ==============================================
#                   MAIN
# ==============================================

# LOAD POINTS FROM FILE
points = load_points('points.txt')

# LOAD SHAPES OF DATASET
data = nc.Dataset(URL_ENDPOINT)
# Get the right variable names - TODO fix this once datasets are normalized
LATITUDE = 'lat' if 'lat' in data.variables else 'latitude'
LONGITUDE = 'lon' if 'lon' in data.variables else 'longitude'
# Get the size of each coordinate
lat_size = data.variables[LATITUDE].size
lon_size = data.variables[LONGITUDE].size

# LOAD COORDINATES
coordinates = query_thredds_opendap(URL_ENDPOINT, longitude=(0,lon_size-1), latitude=(0,lat_size-1))

# QUERY DATA NEXT TO POINTS
for p in points:

	break

# "http://193.136.153.163/thredds/dodsC/WAVERYS_collection/WAVERYS_Collection_fmrc.ncd?VHM0[0:1:0][0:1:1][0:1:0][0:1:0]"
# "http://193.136.153.163/thredds/dodsC/WAVERYS_collection/WAVERYS_Collection_fmrc.ncd?longitude[0:1799],latitude[0:898]"
