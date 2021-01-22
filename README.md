# CENTEC Thredds Data Server


![centeclogo](http://www.centec.tecnico.ulisboa.pt/renew2020/App_Themes/Renew2020/Images/IST_logo.jpg)

This repository contains the configuration of a thredds dataserver running on a docker image.

The server acts as an interface to hindcast and forecast data contained in the CENTEC database.

### Check out this repository [wiki](https://github.com/CENTEC-IST/centec-db/wiki) for more information.


[UNIDATA - Thredds Data Server](https://www.unidata.ucar.edu/software/tds/)

## Usage

Run `./init.sh` to initialize some paths and setup the docker images

```
$ docker-compose start
```

The `docker-compose.yml` file contains the path specification for the current server, and must be tweaked if the data paths change.

The `catalog*.xml` files inside `thredds/` contain the specification for each individual dataset and must also be tweaked if anything changes.
