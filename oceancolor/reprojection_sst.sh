#!/bin/bash

#infile="/media/Arc/oceancolor_data/euro_coasts/SST/A2014002165500.L2_LAC_SST"
#outfile="/media/Arc/oceancolor_data/euro_coasts/SST/A2014002165500_SST.tif"
#qual_outfile="/media/Num/eo_tools/testData/raster/qual_sst.tif"

data_dir="/media/Arc/oceancolor_data/euro_coasts/test"

for infile in $data_dir/*.L2_LAC_NSST
do

fname=$(basename $in_file)
#fbname=${fname%.*}
#echo $fbname

xmin=`gdalinfo $infile | grep geospatial_lon_min | awk -F= '{print $2}' | sed 's/ //g'`
ymin=`gdalinfo $infile | grep geospatial_lat_min | awk -F= '{print $2}' | sed 's/ //g'`
xmax=`gdalinfo $infile | grep geospatial_lon_max | awk -F= '{print $2}' | sed 's/ //g'`
ymax=`gdalinfo $infile | grep geospatial_lat_max | awk -F= '{print $2}' | sed 's/ //g'`

gdalwarp -geoloc -of GTIFF -t_srs EPSG:4326 \
	-r near -srcnodata -32767.0 -dstnodata -32767.0 \
	-te $xmin $ymin $xmax $ymax \
	HDF4_SDS:UNKNOWN:"$infile":15 $infile.tif

done

#gdalinfo $infile >> /media/Num/eo_tools/testData/raster/info.txt
