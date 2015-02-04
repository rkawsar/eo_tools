#!/usr/bin/env python
# Riazuddin Kawsar
# 5th Feb 2015


import os, sys, time, numpy, fnmatch
from osgeo import gdal
from osgeo.gdalconst import *
import multiprocessing
import matplotlib.pyplot as plt


#fillval_sst =




startdate = '2014000'

input_dir = '/media/Arc/eo_archive_proc/MOD09Q1/downloads/h18v03'
output_dir = '/media/Arc/eo_archive_proc/MOD09Q1/output/h18v03'

hdf_file = '/media/Num/eo_tools/testData/raster/A2014001000000.L2_LAC_SST'

# function to read specific band
def return_band(hdf_file, band_number):
    
    if band_number == 3:
        print 'Get sst band (16-bit integer) ...'
        hdf_file = 'HDF4_SDS:UNKNOWN:'+ hdf_file +':15'

    elif band_number == 4:
        print 'Get qual_sst band (8-bit integer) ...'
        hdf_file = 'HDF4_SDS:UNKNOWN:'+ hdf_file +':16'

    elif band_number == 8:
        print 'Get l2_flags band (32-bit integer) ...'
        hdf_file = 'HDF4_SDS:UNKNOWN:'+ hdf_file +':20'

    else:
        print 'Band number out of range ...'
        sys.exit(1)


    dataset = gdal.Open(hdf_file,gdal.GA_ReadOnly)
    if dataset is None:
        print "Could not open " + hdf_file
        sys.exit(1)
    geoTransform = dataset.GetGeoTransform()
    proj = dataset.GetProjection()
    ncols = dataset.RasterXSize
    nrows = dataset.RasterYSize
    nbands = dataset.RasterCount
    print ncols, nrows, nbands

    
    rasterband = dataset.GetRasterBand(1)
    NoDataValue = rasterband.GetNoDataValue()
    print 'NoDataValue : ' + str (NoDataValue)
    GetMinimum = rasterband.GetMinimum()
    GetMaximum = rasterband.GetMaximum()

    stats = rasterband.GetStatistics( True, True )
    print "BandStatistics =  Min=%.3f, Max=%.3f, Mean=%.3f, StdDev=%.3f" % ( \
                stats[0], stats[1], stats[2], stats[3] )
    
    type(rasterband)
    rasterband = rasterband.ReadAsArray(0, 0, ncols, nrows)

    if band_number == 3:
        rasterband = rasterband.astype(numpy.uint16)
    elif band_number == 4:
        rasterband = rasterband.astype(numpy.uint8)
    elif band_number == 8:
        rasterband = rasterband.astype(numpy.uint32)
    else:
        print 'Band number out of range'
        sys.exit(1)
        
    return rasterband,geoTransform,proj
    dataset = None
    rasterband = None



# define the otput file
def output_file(output_name,output_array,geoTransform,proj):
    format = "GTiff"
    driver = gdal.GetDriverByName( format )
    outDataset = driver.Create(output_name,ncol,nrow,1,GDT_Int16)
    outBand = outDataset.GetRasterBand(1)
    outBand.WriteArray(output_array,0,0)
    outBand.FlushCache()
    outBand.SetNoDataValue(fillval_sst)
    outDataset.SetGeoTransform(geoTransform )
    outDataset.SetProjection(proj)



# finding all the hdf files in the mentioned root directories 
def findfiles(input_dir):
    toprocess = []
    for root,dir,files in os.walk(input_dir):
        for name in sorted(files):
            if fnmatch.fnmatch(name,'*.hdf'):
                if name[1:8] > startdate:
                    #if name[1:8] == startdate:
                    toprocess.append( os.path.join(root, name) )
               #print os.path.join(root, name)
    return toprocess



# define the product output name
def product_output_name(output_dir,sst_name,product):
    product_dir = os.path.join(output_dir,product)
    product_output_name = sst_name +'.'+product+'.tif'
    product_path_file = os.path.join(product_dir,product_output_name)
    return product_path_file

    

rasterband,geoTransform,proj = return_band(hdf_file, 8)


'''
# data printing
imgplot2 = plt.imshow(rasterband)
plt.show()
'''


