import os, sys, time, numpy, fnmatch
from osgeo import gdal
from osgeo.gdalconst import *
import multiprocessing

startdate='2014240'

# information on MOD09Q1 file
ncol = 4800
nrow = 4800 
fillval_band = -28672
fillval_qc = 65535
fillval_ndvi = 255
# valid range -0.2 to 1.0
min_ndvi= 0 #-0.2
max_ndvi = 1.0

#directories
input_dir = '/media/Arc/eo_archive_proc/MOD09Q1/downloads/h18v03'
output_dir = '/media/Arc/eo_archive_proc/MOD09Q1/output/h18v03'
#filename= '/media/Arc/eo_archive_proc/MOD09Q1/downloads/h08v06/MOD09Q1/MOD09Q1.A2014081.h08v06.005.2014090090436.hdf'

# function to read specific band
def return_band(mod09q1_file_name, band_number):
    fn_mod09q1 = mod09q1_file_name
    fn_mod09a1 = fn_mod09q1.replace("MOD09Q1","MOD09A1")
    if band_number < 3 and band_number > 0:
        print 'Get band: ' + str(band_number) # String (converts any Python object using str()).
        fn_mod09q1 = 'HDF4_EOS:EOS_GRID:'+fn_mod09q1+':MOD_Grid_250m_Surface_Reflectance:sur_refl_b0'+str(band_number)
        #print fn_mod09q1
    elif band_number == 3:
        print 'Get band: ' + str(band_number)
        fn_mod09q1 = 'HDF4_EOS:EOS_GRID:'+fn_mod09q1+':MOD_Grid_250m_Surface_Reflectance:sur_refl_qc_250m'
        #print fn_mod09q1
    elif band_number == 11:
		print 'Get band: ' + str(band_number)
		fn_mod09a1 = 'HDF4_EOS:EOS_GRID:'+fn_mod09a1+':MOD_Grid_500m_Surface_Reflectance:sur_refl_state_500m'
		#print fn_mod09a1
    else:
        print 'Band number out of range'
        sys.exit(1)
    
    if band_number < 4 and band_number > 0:
		ds_mod09q1 = gdal.Open(fn_mod09q1,GA_ReadOnly)
		if ds_mod09q1 is None:
			print "Could not open " + fn_mod09q1
			sys.exit(1) 
		geoTransform = ds_mod09q1.GetGeoTransform()
		proj = ds_mod09q1.GetProjection()        
		rasterband = ds_mod09q1.GetRasterBand(1)
		type(rasterband)
		band = rasterband.ReadAsArray(0,0,ncol,nrow)
		band = band.astype(numpy.uint16)
		return band,geoTransform,proj
		ds_mod09q1 = None
		band = None
	
    if band_number == 11:
		ds_mod09a1 = gdal.Open(fn_mod09a1,GA_ReadOnly)
		if ds_mod09a1 is None:
			print "Could not open " + fn_mod09a1
			sys.exit(1) 
		geoTransform = ds_mod09a1.GetGeoTransform()
		proj = ds_mod09a1.GetProjection()        
		rasterband = ds_mod09a1.GetRasterBand(1)
		type(rasterband)
		band = rasterband.ReadAsArray(0,0,2400,2400)
		band = numpy.repeat(band, 2, axis=1)
		band = numpy.repeat(band, 2, axis=0)
		#print band.shape
		band = band.astype(numpy.uint16)
		return band,geoTransform,proj
		ds_mod09a1 = None
		band = None
