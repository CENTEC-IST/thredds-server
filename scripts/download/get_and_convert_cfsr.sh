#! /bin/bash

# ================================================================================
#
# Download CFSR FILES script
# Give URLs with the following format to download:
# https://rda.ucar.edu/data/ds093.1/${year}/${variable}.gdas.${year}${month}.grb2
# eg:
# https://rda.ucar.edu/data/ds093.1/1988/wnd10m.gdas.198809.grb2
#
# ================================================================================

set -e

email="fabio4335@gmail.com"
passwd="frac4ever"

cert_opt=""
# If you get a certificate verification error (version 1.10 or higher),
# uncomment the following line:
#cert_opt="--no-check-certificate"

echo -e "\033[32mAuthenticating https://rda.ucar.edu ...\033[m"
wget -q --show-progress $cert_opt -O auth_status.rda.ucar.edu --save-cookies auth.rda.ucar.edu.$$ --post-data="email=${email}&passwd=${passwd}&action=login" https://rda.ucar.edu/cgi-bin/login

for url in $@ ; do
	filename=${url##*/}
	wget -q --show-progress $cert_opt --load-cookies auth.rda.ucar.edu.$$ -O $filename $url

	echo -e "\033[32mConverting $filename to netcdf...\033[m"

	wgrib2 $filename -netcdf "${filename%.*}.nc" >/dev/null &
done

wait 

# clean up
rm auth.rda.ucar.edu.$$ auth_status.rda.ucar.edu
