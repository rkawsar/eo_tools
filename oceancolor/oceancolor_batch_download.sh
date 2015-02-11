#!/bin/bash

param=".L2_LAC_SST.bz2"
year=2014



cd /media/Arc/oceancolor_data/L2_sst

for i in {1..366}
do
wget -q -O - http://oceandata.sci.gsfc.nasa.gov/MODISA/L2/"$year"/$(printf '%0.3d\n' $i)/ |grep "$param"|wget -N --wait=0.5 --random-wait --force-html -i -
done
