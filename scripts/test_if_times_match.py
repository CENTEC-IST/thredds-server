#!/home/rmc/progs/python/anaconda3/bin/python3

import sys
import glob
import netCDF4 as nc
import argparse

DEFAULT_PATH = '/media/degas/model/ECMWF/ERA5/'

# PARSE ARGUMENTS
parser = argparse.ArgumentParser(description='Compare times between pairs of files of different variables.')
parser.add_argument('variables', nargs=2, metavar=('VAR'), help='Variables to be compared')
parser.add_argument('-p', '--path', help='Root path to find variables', default=DEFAULT_PATH)
args = parser.parse_args()

d1 = glob.glob(args.path + '**/' + args.variables[0] + '*.nc')
d2 = glob.glob(args.path + '**/' + args.variables[1] + '*.nc')
d1.sort()
d2.sort()

if len(d1) != len(d2):
	print('They dont have the same amount of files')
	sys.exit()

for f in range(len(d1)):
	print(f"Testing [{f}/{len(d1)}] {d1[f]} {d2[f]}")
	dd1 = nc.Dataset(d1[f])
	dd2 = nc.Dataset(d2[f])
	if not (dd1.variables['time'][:] == dd2.variables['time'][:]).all():
		print(f"\033[1;31m{d1[f]} and {d2[f]} times differ\033[m")
	if not (dd1.variables['time'][:] >= 0).all():
		print(f"\033[1;31m{d1[f]} has invalid times\033[m")
	if not (dd2.variables['time'][:] >= 0).all():
		print(f"\033[1;31m{d2[f]} has invalid times\033[m")
	sys.stdout.flush()

print("\033[1;32mFinished\033[0m")

