#!/home/rmc/progs/python/anaconda3/bin/python3

import sys
import glob2
import netCDF4 as nc
import datetime

EXTRACT_VAR = {'Long Name' : 'long_name',
		'Units' : 'units'}

GEO_SPATIAL_DIMS = ('lat', 'latitude', 'lon', 'longitude')
TIME_DIMS = ('time', 'date')

DATE_FSTRING = '%Y-%m-%dT%H:%M:%S'

def print_table(header, data, spacing=3, md=False):
	sizes = []
	for i, v in enumerate(header):
		sizes.append(max(len(str(k[i])) for k in data+[header]))

	for i, row in enumerate([header]+data):
		if i == 1:
			if not md:
				print('-'*(sum(sizes)+len(sizes)*spacing))
			if md:
				print('| ' + '| '.join([':'+'-'*(s+spacing-3)+': ' for s in sizes]), end='|\n')
		for k, value in enumerate(row):
			if md and k == 0: print('| ', end='')
			print(f"{value:<{sizes[k]+spacing}}", end='' if not md else '| ')
		print()


if len(sys.argv) == 1 or any(item in ("help", "-help", "--help", "-h") for item in sys.argv):
	print("""This script generates documentation for a given number of files
	It generates a list of the variables contained in the files as well as dimensions ranges

	Usage:
		nc-variables [-md] [nc file] [nc file] ...

	-md     Produce GitHub flavoured Markdown output""")
	sys.exit()

MAX_PRINT_LEN = 0
files = []
USE_MARKDOWN = False
for arg in sys.argv[1:]:
	if arg == '-md': USE_MARKDOWN = True
	else: files.append(arg)

vars = {}
dims = {}

files.sort()
for f in files:
	try:
		data = nc.Dataset(f)
	except FileNotFoundError:
		print(f"File not found '{f}'")
		sys.exit(1)
	except OSError:
		print(f"File given is not a netCDF file: '{f}'")
		sys.exit(1)

	# load file dimensions
	di = list(data.dimensions)
	if dims and not all(d in dims for d in di):
		print(f"File '{f}' has different dimensions from previous files.")
		sys.exit(1)

	print(f"\rProcessing {f}", end='')
	if len(f) + 12 > MAX_PRINT_LEN: # Little hack to delete what i print, becase of \r
		MAX_PRINT_LEN = len(f) + 12 

	# Handle dimensions
	for d in di:
		if d in GEO_SPATIAL_DIMS:
			start = float(data.variables[d][0])
			end = float(data.variables[d][-1])
			units = data.variables[d].size
			if d not in dims:
				dims[d] = [start, end, units]
			elif dims[d] != [start, end, units]:
				print(dims)
				print(dims[d])
				print([start, end, units])
				print(f"Geo Spatial Dimensions of file '{f}' dont match with previous files")
				sys.exit(1)
		elif d in TIME_DIMS:
			units = data.variables[d].units.split()[0]
			if d in dims and units != dims[d][-1]:
				print(f"'{d}' dimension units on '{f}' dont match previous files")
				sys.exit(1)

			date = data.variables[d].units.split()[2]
			date = '-'.join([date[:4]] + [f"{int(a):02}" for a in date.split('-')[1:]]) # sometimes dates arent zero padded...
			hours = data.variables[d].units.split()[3][:8]
			date = f"{date}T{hours}"
			start = datetime.datetime.strptime(date, DATE_FSTRING) + datetime.timedelta(**{units:float(data.variables[d][0])})
			end = datetime.datetime.strptime(date, DATE_FSTRING) + datetime.timedelta(**{units:float(data.variables[d][-1])})

			if d not in dims:
				dims[d] = [start, end, units]
			else:
				if dims[d][0] > start:
					dims[d][0] = start
				if dims[d][1] < end:
					dims[d][1] = end
		else:
			dims[d] = d

	# Handle variables
	for v in data.variables:
		if v in dims:
			continue

		vars[v] = [data.variables[v].__dict__[key]
				if key in data.variables[v].__dict__ else ''
				for key in EXTRACT_VAR.values()]

print('\r'+' '*MAX_PRINT_LEN+'\r', end='') # clear the progress list
if USE_MARKDOWN: print('### Variables\n')
print_table([''] + list(EXTRACT_VAR), [[k, vars[k][0], vars[k][1]] for k in vars], md=USE_MARKDOWN)

print()
if USE_MARKDOWN: print('### Geospatial Coverage\n')
print_table(['', 'Start', 'End', 'Entries'], [[k, dims[k][0], dims[k][1], dims[k][2]] for k in dims if k in GEO_SPATIAL_DIMS], md=USE_MARKDOWN)

print()
if USE_MARKDOWN: print('### Time Coverage\n')
print_table(['', 'Start', 'End', 'Units'], [[k, dims[k][0].strftime(DATE_FSTRING), dims[k][1].strftime(DATE_FSTRING), dims[k][2]] for k in dims if k in TIME_DIMS], md=USE_MARKDOWN)

other = [k for k in dims if k not in TIME_DIMS and k not in GEO_SPATIAL_DIMS]
if not other:
	sys.exit()
print()
if USE_MARKDOWN: print('### Other Dimensions\n')
for o in other:
	print(o)

