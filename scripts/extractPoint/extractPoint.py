#!/home/rmc/progs/python/anaconda3/bin/python3

import netCDF4 as nc
import numpy as np
from geopy import distance
from datetime import datetime, timedelta
import time
import os, sys
import argparse

from threading import Thread
import queue

# DEFAULTS ==============================================
URL_ENDPOINT = "http://193.136.153.163/thredds/dodsC/WAVERYS/WAVERYS_fmrc.ncd"
RADIUS = 40 # radius in km
CHUNK_SIZE = 30 # size of each request
OUTPUT_DIR = 'out/'
VARIABLES = ['VHM0']
VERBOSE=False
# =======================================================

def threaded(function, daemon=False):
	'''Decorator to make a function threaded

	To acess wrapped function return value use .get() on the return value
	'''
	def wrapped_function(queue, *args, **kwargs):
		return_val = function(*args, **kwargs)
		queue.put(return_val)
	def wrap(*args, **kwargs):
		queue = queue.Queue()

		thread = Thread(target=wrapped_function, args=(queue,)+args , kwargs=kwargs)
		thread.daemon=daemon
		thread.start()
		thread.result_queue=queue
		return thread
	return wrap

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
	The tuple can have up to 3 values and the following combinations (start, step, end), (start, end), (start)
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
	if VERBOSE: print(url)
	return nc.Dataset(url)

def get_nearest_points(points, point, radius):
	'''Returns a list of indexes in points that are inside a radius of point'''
	points = np.asarray(points)
	idx = (np.abs(points - point)).argmin() # TODO Check for speed if done too many times...
	indexes = [idx]
	for i in range(len(points)):
		# TODO this is not the ideal way of calculating distances
		if idx+i+1 < len(points) and abs(points[idx]-points[idx+i+1]) <radius/110:
			indexes.append(idx+i+1)
		if idx-i-1 > 0 and abs(points[idx]-points[idx-i-1]) < radius/110:
			indexes.insert(0, idx-i-1)
	return indexes

def wf(pdist):
	'''Weight function based on distance'''
	a=(1 - pdist / RADIUS)
	return (abs(a)+a)/2

def nanaverage(A,weights):
	'''Function to calculate weighted average and ignore nan values'''
	return np.nansum(A*weights)/((~np.isnan(A))*weights).sum()

def process_data(data, point, variable, weight_function=wf):
	'''Process data using the weighted average of each data point around the point given'''

	# Calculate weights for each point around the target
	weights = np.zeros((len(data.variables[LATITUDE]), len(data.variables[LONGITUDE])))
	for i in range(len(data.variables[LATITUDE])):
		for j in range(len(data.variables[LONGITUDE])):
			dist = distance.distance((point[0],point[1]), (data.variables[LATITUDE][i], data.variables[LONGITUDE][j])).km
			weights[i,j] = weight_function(dist)

	basedate = datetime.strptime(data.variables['time'].units.split()[-1], "%Y-%m-%dT%H:%M:%SZ")
	timestep = data.variables['time'].units.split()[0] # should be "hours" in most cases
	times = data.variables['time'][:]
	size = len(times)

	print(f"Extracting {variable} from {basedate+timedelta(**{timestep:times[0][0]})} to {basedate+timedelta(**{timestep:times[-1][-1]})}")

	# Write Header
	with open(f"{OUTPUT_DIR}{point[-1]}.txt", 'w') as fp:
		fp.write(f"TIME{' '*(15)}   {variable}\n")

	# makes requests in sizes of CHUNK_SIZE. ex if CHUNK_SIZE=20 and size=47 -> [0,20] [20,40] [40,47]
	for mi, ma in ((i,i+(CHUNK_SIZE if size-i>CHUNK_SIZE else size-i)) for i in range(0,size,CHUNK_SIZE)):
		print(f"Requesting {variable} data for {point[2]} [{ma:>4}/{size}]: ", end='')
		sys.stdout.flush()
		t = time.time()
		tmp_data = data.variables[variable][mi:ma] # Request data
		print('%.1f seconds' % (time.time() - t))

		with open(f"{OUTPUT_DIR}{point[-1]}.txt", 'a') as fp:
			for i in range(len(tmp_data)):
				for j in range(d.variables['time'].shape[1]):
					x = nanaverage(tmp_data[i][j], weights) # Calculate weighted average
					tx = basedate+timedelta(**{timestep:times[mi+i][j]})
					fp.write(f"{str(tx)}   {str(x)}\n") # Write to file

# ==============================================
#                   MAIN
# ==============================================

# PARSE ARGUMENTS
parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('-v', '--variable', nargs='*', help='Variables to be extracted', default=VARIABLES)
parser.add_argument('-u', '--url', help='URL endpoint (must be an opendap URL)', default=URL_ENDPOINT)
parser.add_argument('-r', '--radius', type=int, help='Radius to around target points to take mean value', default=RADIUS)
parser.add_argument('-o', '--output', help='Output directory to save files', default=OUTPUT_DIR)
parser.add_argument('-c', '--chunk', type=int, help='Size of each data request', default=CHUNK_SIZE)
parser.add_argument('--verbose', help='Print more stuff', action='store_true', default=VERBOSE)

args = parser.parse_args()
CHUNK_SIZE = args.chunk
URL_ENDPOINT = args.url
VARIABLES = args.variable
RADIUS = args.radius
OUTPUT_DIR = args.output + '/'
VERBOSE = args.verbose

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
# Get size of time variables
time_size = data.variables['time'].shape

# LOAD COORDINATES
coordinates = query_thredds_opendap(URL_ENDPOINT, **{LONGITUDE:(0,lon_size-1),
													LATITUDE:(0,lat_size-1)})

# CREATE OUTPUT DIR
if not os.path.exists(OUTPUT_DIR):
	os.makedirs(OUTPUT_DIR)

# QUERY DATA NEXT TO POINTS
for p in points:
	lat_range = get_nearest_points(coordinates.variables[LATITUDE], p[0], RADIUS)
	lon_range = get_nearest_points(coordinates.variables[LONGITUDE], p[1], RADIUS)

	start = 0
	end = time_size[0]-1

	d = query_thredds_opendap(URL_ENDPOINT, **{VARIABLES[0]:[(start, end), (0,time_size[1]-1), (lat_range[0], lat_range[-1]), (lon_range[0], lon_range[-1])],
												'time':[(start,end), (0,time_size[1]-1)],
												LATITUDE:(lat_range[0], lat_range[-1]),
												LONGITUDE:(lon_range[0], lon_range[-1])
											})

	process_data(d, p, VARIABLES[0])

