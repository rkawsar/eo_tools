#!/usr/bin/env python
# interpolation source:
# http://gis.stackexchange.com/questions/7611/bilinear-interpolation-of-point-data-on-a-raster-in-python

import os
from osgeo import gdal
from osgeo import osr
import matplotlib.pyplot as plt
import numpy as np
import fnmatch

hdf_file = 'C:\\R.Kawsar\\WORKSPACE\\Python\\data\\hdf\\T2015001000000.L2_LAC_SST'
out_sst = 'C:\\R.Kawsar\\WORKSPACE\\Python\\data\\hdf\\sst.tif'
data_dir = 'C:\\R.Kawsar\\WORKSPACE\\Python\\data\\hdf'


hdf_file = 'C:\\R.Kawsar\\WORKSPACE\\Python\\data\\hdf\\T2015001000000.L2_LAC_SST'
hdf_file = gdal.Open(hdf_file,gdal.GA_ReadOnly)
subdatasets = hdf_file.GetSubDatasets()
ds_sst = gdal.Open(subdatasets[2][0])

nx = ds_sst.RasterXSize # ncols
ny = ds_sst.RasterYSize # nrows
xmin = float(ds_sst.GetMetadataItem('geospatial_lon_min'))
ymin = float(ds_sst.GetMetadataItem('geospatial_lat_min'))
xmax = float(ds_sst.GetMetadataItem('geospatial_lon_max'))
ymax = float(ds_sst.GetMetadataItem('geospatial_lat_max'))

xres=(xmax-xmin)/float(nx) # ncol_new = (xmax - xmin) / float(0.11)
yres=(ymax-ymin)/float(ny) # nrow_new = (ymax - ymin) / float(0.11)

new_nx = (xmax-xmin)/0.011
new_ny = (ymax-ymin)/0.011 

print nx, ny
print new_nx, new_ny

yres=(ymax-ymin)/float(ny)
geotransform = ds_sst.GetGeoTransform ()
print geotransform
new_geotransform=(xmin,xres,0,ymax,0, -yres)
print new_geotransform
