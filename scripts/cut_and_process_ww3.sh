#!/bin/bash

# This script is used to clean the WW3 nopp-phase2 dataset on partition files.
# Give the files to process as arguments to the script
#
# Behavior:
#  - Limit latitude and longitude to a box (containing the atlantic)
#  - Check the minimum amount for the partition size that contains data
#  - Remove partition points that exceed this minimum amount

set -e

PYTHON_EXEC="/home/rmc/progs/python/anaconda3/bin/python3"
TEMP="/tmp/nc/"

# limits for domain selection
latmin=-77.5
latmax=90.
lonmin=-102.
lonmax=30.

if [[ $# = 0 ]]; then
	echo "Give the files to be processed as arguments to the script."
	exit
fi

# Sort files given
files=$(sort <(printf "%s\n" "$@"))
mkdir -p $TEMP

n_files=$(printf "%s\n" "$@" | wc -l)
i=0

for file in $files; do
	i=$((i+1))
	echo Processing $i/$n_files $file
	/usr/bin/cdo sellonlatbox,-180,180,-90,90 $file ${TEMP}/$(basename $file).tmp
	echo STEP 1
	/usr/bin/ncks -4 -L 7 -d latitude,${latmin},${latmax} ${TEMP}/$(basename $file).tmp ${TEMP}/$(basename $file).2.tmp
	echo STEP 2
	# /usr/bin/ncks -4 -L 7 -d longitude,${lonmin},${lonmax} ${TEMP}/$(basename $file).2.tmp ${TEMP}/$(basename $file) # TODO uncoment this
	/usr/bin/ncks -4 -L 7 -d longitude,${lonmin},${lonmax} ${TEMP}/$(basename $file).2.tmp /media/monet/public/model/hindcast/NCEP/wave/nopp-phase2/netcdf_subset/$(basename $file)
	echo DONE
	rm $TEMP/*.tmp
done

# TODO Verify how many partitions to remove from the files and remove them

rm -r $TEMP
