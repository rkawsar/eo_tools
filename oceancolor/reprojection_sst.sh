#!/bin/bash

infile="/media/Num/eo_tools/testData/raster/A2014001000000.L2_LAC_SST"
outfile="/media/Num/eo_tools/testData/raster/sst_cubic.tif"
qual_outfile="/media/Num/eo_tools/testData/raster/qual_sst.tif"

#gdalinfo $infile >> /media/Num/eo_tools/testData/raster/info.txt


xmin=`gdalinfo $infile | grep geospatial_lon_min | awk -F= '{print $2}' | sed 's/ //g'`
ymin=`gdalinfo $infile | grep geospatial_lat_min | awk -F= '{print $2}' | sed 's/ //g'`
xmax=`gdalinfo $infile | grep geospatial_lon_max | awk -F= '{print $2}' | sed 's/ //g'`
ymax=`gdalinfo $infile | grep geospatial_lat_max | awk -F= '{print $2}' | sed 's/ //g'`

echo $xmin
echo $xmax
echo $ymin
echo $ymax

  #sst_nan = float(ds_sst.GetMetadataItem('bad_value_scaled'))
  #sst_intercept = float(ds_sst.GetMetadataItem('intercept'))
  #sst_slope = float(ds_sst.GetMetadataItem('slope'))


#gdalwarp -geoloc -of GTIFF -t_srs EPSG:4326 \
#	-r near -srcnodata -32767.0 -dstnodata -32767.0 \
#	-te 13.39145756 52.11008835 75.31025696 75.28180695 \
#	HDF4_SDS:UNKNOWN:"$infile":15 $outfile


#gdalwarp -geoloc -of GTIFF -t_srs EPSG:4326 \
#	-r near \
#	-te 13.39145756 52.11008835 75.31025696 75.28180695 \
#	HDF4_SDS:UNKNOWN:"$infile":16 $qual_outfile
