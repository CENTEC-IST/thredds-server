import netCDF4 as nc
import time

url="http://193.136.153.163/thredds/dodsC/WAVERYS_collection/WAVERYS_Collection_fmrc.ncd?VHM0[0:1:0][0:1:1][0:1:0][0:1:0]"


def load_points(filename):
	with open(filename, 'r') as fp:
		return [line.strip('\n').split() for line in fp]

points = load_points('points.txt')
print(points)
