#!/bin/bash
set -e

DATA=/media/degas/model/ECMWF/ERA5/

process() {
	files=`find $DATA -name "$1*.nc" -not -path "*testes*" | sort`
	total=`find $DATA -name "$1*.nc" -not -path "*testes*" | wc -l`
	n=1
	for f in $files; do 
		echo ">> [$n/$total] $f ${f/${1}/${2}}"
		ncrename -v $1,$2 "$f"
		mv "$f" "${f/${1}/${2}}"
		n=$((n+1))
	done
}

process "10u" "uwnd"
process "10v" "vwnd"
process "2d" "dewp"
process "2t" "atmp"

