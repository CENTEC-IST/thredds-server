#!/bin/bash


# This scripts sends an alert if space in disk gets too low

set -e

send_mail() {
	/usr/bin/mutt fabio4335@gmail.com -s "$1" <<< "$2"
	/usr/bin/mutt ricardo.campos@centec.tecnico.ulisboa.pt -s "$1" <<< "$2"
}

send_notification() {
	local KEY=$(cat /home/eximus/simplepush_key)
	local data="key=${KEY}&title=${1}&msg=${2}"
	curl -s --data "$data" https://api.simplepush.io/send 
}

check_free_space() {
	free_space=$(df "$1" | tail -n1 | awk '{print $4}')

	if [[ $free_space -lt 70000000 ]]; then
		send_notification "CENTEC: $1  Low free space." "$(df -h $1 | tail -n1 | awk '{print $4}')"
		if [[ $free_space -lt 30000000 ]]; then
			send_mail "CENTEC: $1  Low free space." "$(df -h $1)"
		fi
	fi
}

check_free_space /media/monet
check_free_space /media/degas

