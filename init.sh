#!/bin/bash

# Initialize paths
logs="./logs"
[ ! -d $logs ] && mkdir $logs
[ ! -d $logs/tomcat ] && mkdir $logs/tomcat
[ ! -d $logs/thredds ] && mkdir $logs/thredds

docker network create centec-network
# Initialize docker network and images
docker-compose up -d
