#!/bin/bash


# This scripts expects a list of files as arguments.
# The files are then sorted alphabeticaly and for each pair it is verified
#  - IF TIME OVERLAP OCURRS. In which case the last time from the first file
#    of the overlapping pair is removed
#  - IF ENDING TIME BELONGS TO NEXT FILE. In which case the last time from the
#    first file is removed and stored in the next file

set -e

check_start_end_times_overlap() {
	# Compare the last time of file $1 and the first time of $2 -- returns a False or True followed by the timestamp
	python3 -c "import netCDF4 as nc, sys,datetime; d=nc.Dataset(sys.argv[1]);
print((d.variables['time'][-1] == nc.Dataset(sys.argv[2]).variables['time'][0]).all(), datetime.datetime.fromtimestamp(d.variables['time'][-1]))" "$1" "$2"
}

check_end_and_start_are_consecutive() {
	# Check if the end date and the start date of two files are consecutive and dont belong -- returns the number of hours that have to be moved from file $1 to file $2
	python3 -c "import netCDF4 as nc, sys, datetime; d1=nc.Dataset(sys.argv[1]); d2=nc.Dataset(sys.argv[2]);
t1=datetime.datetime.fromtimestamp(d1.variables['time'][-1]);t2=datetime.datetime.fromtimestamp(d2.variables['time'][0]);
print(t2.hour if f'{t1.year}{t1.month:02}' == sys.argv[2].split('.')[-2] and t2.hour - t1.hour == 1 else 0)" "$1" "$2"
}

verify_start_end() {
	# Verify the begining and end times of a file to see if they are correct -- returns 'True' or 'False'
	python3 -c "import netCDF4 as nc, sys, datetime; d=nc.Dataset(sys.argv[1]);
ti=datetime.datetime.fromtimestamp(d.variables['time'][0]);tf=datetime.datetime.fromtimestamp(d.variables['time'][-1]);
print(f'{ti.year}{ti.month:02}' == f'{tf.year}{tf.month:02}' == sys.argv[1].split('.')[-2] and ti.hour == 0 and tf.hour == 23)" "$1"
}

# Sort files given
if [[ $# = 0 ]]; then
	echo "Give the files to be processed as arguments to the script."
	exit
fi

files=( $(sort <(printf "%s\n" "$@")) )

for (( i=1 ; i<${#files[@]} ; i++ )); do
	if [[ $(basename ${files[$i-1]} | cut -d. -f1) != $(basename ${files[$i]} | cut -d. -f1) ]]; then
		continue # skip these files since they dont have the same variable
	fi
	echo Processing $i/$((${#files[@]}-1)) -- ${files[$i-1]}   ${files[$i]}

	# COMPARE ENDING AND START OF BOTH FILES TO SEE IF THEY OVERLAP
	comp=$(check_start_end_times_overlap ${files[$i-1]} ${files[$i]})
	if [[ $comp =~ "True" ]]; then
		echo -e "  \033[33m==\033[m Times match ${comp##True }. Deleting on ${files[$i-1]}..."
		ncks -O -d time,0,-2 "${files[$i-1]}" "/tmp/$(basename ${files[$i-1]}).tmp" # delete and save a tmp file
		mv "/tmp/$(basename ${files[$i-1]}).tmp" "${files[$i-1]}" # overwrite original
	fi

	# COMPARE ENDING AND START OF BOTH FILES TO SEE IF THEY ARE CONSECUTIVE
	nmov=$(check_end_and_start_are_consecutive ${files[$i-1]} ${files[$i]})
	if [[ $nmov != 0 ]]; then
		echo -e "  \033[33m==\033[m Times out of place. Moving $nmov timesteps in ${files[$i-1]} to ${files[$i]}..."
		ncks -O -d time,-$nmov ${files[$i-1]} "/tmp/$(basename ${files[$i-1]}).tmp" # Move selected times to a new file
		ncrcat -O "/tmp/$(basename ${files[$i-1]}).tmp" ${files[$i]} "/tmp/$(basename ${files[$i]}).tmp" # concatenate with second file in a tmp file
		mv "/tmp/$(basename ${files[$i]}).tmp" ${files[$i]}  # ovewrite second file
		ncks -O -d time,0,-$(($nmov+1)) "${files[$i-1]}" "/tmp/$(basename ${files[$i-1]}).tmp" # delete times moved and save tmp file
		mv "/tmp/$(basename ${files[$i-1]}).tmp" "${files[$i-1]}" # overwrite first file
	fi

	# VERIFY IF THE FILE IS CORRECT
	if [[ $(verify_start_end ${files[$i-1]}) == 'False' ]];then
		echo -e "  \033[31mXX\033[m File ${files[$i-1]} still has problems."
	fi
done

