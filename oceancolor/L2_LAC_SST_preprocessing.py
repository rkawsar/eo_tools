import os, sys, time, numpy, fnmatch
from osgeo import gdal
from osgeo.gdalconst import *
import multiprocessing


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
        print 'Band number out of range'
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
    GetNoDataValue = rasterband.GetNoDataValue()
    GetMinimum = rasterband.GetMinimum()
    GetMaximum = rasterband.GetMaximum()

    print   'MaxValue: ' + str(GetMaximum) + ' , ' \
          + 'MinValue: ' + str(GetMinimum) + ' , ' \
            'NoDataValue: ' + str(GetNoDataValue)

    # stats = rasterband.GetStatistics (true, true)
    # print "[ STATS ] =  Minimum=%.3f, Maximum=%.3f, Mean=%.3f, StdDev=%.3f" % ( \
    #            stats[0], stats[1], stats[2], stats[3] )
    
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
 

return_band(hdf_file, 3)
return_band(hdf_file, 4)
return_band(hdf_file, 8)
