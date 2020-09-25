#!/bin/bash

# This scripts expects a list of files as arguments.
# The files are then sorted alphabeticaly and for each pair it is verified
#  - IF TIME OVERLAP OCURRS. In which case the last time from the first file
#    of the overlapping pair is removed
#  - IF ENDING TIME BELONGS TO NEXT FILE. In which case the last time from the
#    first file is removed and stored in the next file
# 
#  The reverse is also verified
#  - IF BEGINING OF NEXT FILE BELONGS TO THE PREVIOUS FILE.	In which case it is copied and removed from the original
#


# ==============================================================================================================================
# XXX NOTE  CAREFUL WHEN STOPPING THIS SCRIPT, SINCE IT MAY LEAVE A MOVE INCOMPLETE (AND RESULT IN PROBLEMS WHEN RAN A 2ND TIME)
# ==============================================================================================================================

set -e

PYTHON_EXEC="/home/rmc/progs/python/anaconda3/bin/python3"
TEMP="/tmp/nc/"

check_forward_misplaced_times() {
	# Check how many timesteps are misplaced from the first file that belong to the second
	$PYTHON_EXEC -c "import netCDF4 as nc, sys, time; d1=nc.Dataset(sys.argv[1]);
print(len([1 for i in d1.variables['time'][-10:] if time.strftime('%Y%m', time.gmtime(int(i))) == sys.argv[2].split('.')[-2]]))" "$1" "$2"
}

check_backward_misplaced_times() {
	# Check how many timesteps are misplaced from the second file that belong to the first
	$PYTHON_EXEC -c "import netCDF4 as nc, sys, time; d2=nc.Dataset(sys.argv[2]);
print(len([1 for i in d2.variables['time'][:10] if time.strftime('%Y%m', time.gmtime(int(i))) == sys.argv[1].split('.')[-2]]))" "$1" "$2"
}

check_start_end_times_overlap() {
	# Compare the last time of file $1 and the first time of $2 -- returns a 'False' or 'True' followed by the timestamp
	$PYTHON_EXEC -c "import netCDF4 as nc, sys,time; d=nc.Dataset(sys.argv[1]);
print((d.variables['time'][-1] == nc.Dataset(sys.argv[2]).variables['time'][0]).all(), time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(int(d.variables['time'][-1]))))" "$1" "$2"
}

verify_start_end() {
	# Verify the begining and end times of a file to see if they are correct -- returns 'True' or 'False'
	$PYTHON_EXEC -c "import netCDF4 as nc, sys, time; d=nc.Dataset(sys.argv[1]);
ti=time.gmtime(int(d.variables['time'][0]));tf=time.gmtime(int(d.variables['time'][-1]));
print(f'{ti.tm_year}{ti.tm_mon:02}' == f'{tf.tm_year}{tf.tm_mon:02}' == sys.argv[1].split('.')[-2] and ti.tm_hour == 0 and tf.tm_hour == 23)" "$1"
}

# Sort files given
if [[ $# = 0 ]]; then
	echo "Give the files to be processed as arguments to the script."
	exit
fi

files=( $(sort <(printf "%s\n" "$@")) )
mkdir -p $TEMP

for (( i=1 ; i<${#files[@]} ; i++ )); do
	if [[ $(basename ${files[$i-1]} | cut -d. -f1) != $(basename ${files[$i]} | cut -d. -f1) ]]; then
		continue # skip these files since they dont have the same variable
	fi
	echo Processing $i/$((${#files[@]}-1)) -- ${files[$i-1]}   ${files[$i]}

	
	# CHECK HOW MANY DATE POINTS TO EXTRACT FROM FIRST FILE
	npoints=$(check_forward_misplaced_times ${files[$i-1]} ${files[$i]})
	if [[ $npoints != 0 ]]; then
		echo -e "  \033[33m==\033[m Times out of place. Moving $npoints timesteps out of ${files[$i-1]}..."
		# Move selected times to a new file
		ncks -O -d time,-$npoints,-1 ${files[$i-1]} "$TEMP/$(basename ${files[$i-1]}).tmp" 
		comp=$(check_start_end_times_overlap "$TEMP/$(basename ${files[$i-1]}).tmp" ${files[$i]})

		if [[ $npoints != 1 ]] || [[ ! $comp =~ "True" ]]; then
			if [[ $npoints != 1 ]] && [[ $comp =~ "True" ]]; then
				# Cut last time of file
				echo -e "  \033[33m==\033[m Times match ${comp##True }. Deleting on ${files[$i-1]}..."
				ncks -O -d time,0,-2 "$TEMP/$(basename ${files[$i-1]}).tmp" "$TEMP/$(basename ${files[$i-1]}).no_overlap.tmp" # delete and save a tmp file
				mv "$TEMP/$(basename ${files[$i-1]}).no_overlap.tmp" "$TEMP/$(basename ${files[$i-1]}).tmp" # overwrite original
			fi

			# Stich tmp file to second file
			echo -e "  \033[33m==\033[m Stiching extracted timesteps into ${files[$i]}..."
			ncrcat -O "$TEMP/$(basename ${files[$i-1]}).tmp" ${files[$i]} "$TEMP/$(basename ${files[$i]}).tmp" 
			mv "$TEMP/$(basename ${files[$i]}).tmp" ${files[$i]}  # ovewrite second file
		fi

		# Remove the extracted times from the first file
		echo -e "  \033[33m==\033[m Deleting $npoints timesteps on ${files[$i-1]}..."
		ncks -O -d time,0,-$(($npoints+1)) "${files[$i-1]}" "$TEMP/$(basename ${files[$i-1]}).tmp" # delete times moved and save tmp file
		mv "$TEMP/$(basename ${files[$i-1]}).tmp" "${files[$i-1]}" # overwrite first file
	fi
	
	# CHECK HOW MANY DATAPOINTS TO EXTRACT FROM THE SECOND FILE (basically the same but in reverse order)
	npoints=$(check_backward_misplaced_times ${files[$i-1]} ${files[$i]})
	if [[ $npoints != 0 ]]; then
		echo -e "  \033[33m==\033[m Times out of place. Moving $npoints timesteps out of ${files[$i]} into ${files[$i-1]}..."
		# Move selected times to a new file
		ncks -O -d time,0,$(($npoints-1)) ${files[$i]} "$TEMP/$(basename ${files[$i]}).tmp" 
		ncrcat -O ${files[$i-1]} "$TEMP/$(basename ${files[$i]}).tmp" "$TEMP/$(basename ${files[$i-1]}).tmp" 
		# Remove selected times from the file
		echo -e "  \033[33m==\033[m Removing $npoints timesteps out of ${files[$i]}..."
		ncks -O -d time,$npoints,-1 ${files[$i]} "$TEMP/$(basename ${files[$i]}).tmp" 
		# Overwrite existing files
		mv "$TEMP/$(basename ${files[$i-1]}).tmp" ${files[$i-1]}
		mv "$TEMP/$(basename ${files[$i]}).tmp" ${files[$i]}
	fi

	# VERIFY IF THE FILE IS CORRECT
	if [[ $(verify_start_end ${files[$i-1]}) == 'False' ]];then
		echo -e "  \033[31mXX\033[m File ${files[$i-1]} still has problems."
	fi
done
rm -r $TEMP

