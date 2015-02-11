#!/usr/bin/env python

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

geotransform = ds_sst.GetGeoTransform ()

ncols = ds_sst.RasterXSize
nrows = ds_sst.RasterYSize
xmin = float(ds_sst.GetMetadataItem('geospatial_lon_min'))
ymin = float(ds_sst.GetMetadataItem('geospatial_lat_min'))
xmax = float(ds_sst.GetMetadataItem('geospatial_lon_max'))
ymax = float(ds_sst.GetMetadataItem('geospatial_lat_max'))


