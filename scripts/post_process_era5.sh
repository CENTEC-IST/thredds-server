#!/bin/bash

# This script performs a bunch of renaming and attribute editing depending on the config file, renaming_config.conf
# Namely it does the following:
#   Rename variable (account for problem where z850 is named as var129 incorrectly)
#   Add long_name attribute
#   Add units attribute
#   Rename the file to match the variable name

list_variables() {
    local f
    for f in "$@" ; do
        ncks -mq "$f" | grep 'variables:' -A100 | grep '(.*,.*)' | awk '{gsub("\\(.*", "", $2);gsub("\\\\","",$2);print $2}'
    done
}

rename_variables() {
    if [[ $# == 1 ]] ; then
        echo "No config file exists, renaming not performed."
        return
    else [[ $# != 2 ]] && { echo "function must be given 2 values." ; exit 1 ;}
    fi

    # rename inputs
    local original_filename="$1"
    local conf_file="$2"

    local filename="/dev/shm/$(basename $original_filename)"
    cp "$original_filename" "$filename" # copy the file into memory to speedup the process

    [[ ! -f "$conf_file" ]] && { echo "$conf_file does not exist, renaming not performed"; return; }

    local variables=( $(list_variables $filename) )
    local rename_args=""

    # XXX To solve the issue where z850 has the same varXXX name as mwp3
    if [[ "${filename}" =~ "z850" ]] && [[ " $variables " == " var129 " ]] ; then
        ncrename -v var129,var999 "${filename}"
        local variables=( $(list_variables $filename) )
    fi
    # XXX

    while IFS=';' read var_name new_var_name long_name units ; do
        var_name="$(echo $var_name | xargs)"
        if [[ " ${variables[@]} " =~ " $var_name " ]] ; then
            new_var_name="$(echo $new_var_name | xargs)"
            rename_args="${rename_args} -v .$var_name,$new_var_name"
            long_name="$(echo $long_name | xargs)"
            units="$(echo $units | xargs)"
            break
        fi
    done <<< $(grep -v "^\ *#\|^\ *$" "$conf_file")

    # # if there is something to rename, rename it
    if [[ ! -z ${rename_args} ]] ; then
        echo "$filename  >   $rename_args"
        ncrename $rename_args "${filename}"
        ncatted -O -a long_name,$new_var_name,o,c,"$long_name" "${filename}"
        ncatted -O -a units,$new_var_name,o,c,"$units" "${filename}"

        sudo mv "$filename" "$original_filename" # move the file from memory back into disk
        sudo chown root:wheel "$original_filename"

        # rename the file
        fname_sufix=$(basename ${original_filename%%.*})
        if [[ "$original_filename" != "${original_filename/$fname_sufix/$new_var_name}" ]] ; then
            sudo mv "$original_filename" "${original_filename/$fname_sufix/$new_var_name}"
        fi
    fi

    [[ -f "${filename}" ]] && rm "${filename}"
}

# MAIN

NJOBS=${NJOBS:=20}

set -u

# prompt for sudo password so that its not requested inside a job later
sudo echo

for f in $* ; do
    [[ $(jobs -p|wc -l) -gt $((${NJOBS}-1)) ]] && wait -n # manage running jobs
    rename_variables $f renaming_config.conf &
done

wait
