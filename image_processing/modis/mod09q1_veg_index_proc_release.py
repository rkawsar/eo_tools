# coding: utf-8
# Author: R.Kawsar
# E-mail: r.kawsar@spatial-business-integration.com
# Date: 8-April 2015
# Vegiation Index Computation (for 250 meters pixel)
# using MOD09Q1 and MOD09A1

import os, sys, time, numpy, fnmatch
from osgeo import gdal
from osgeo.gdalconst import *
import multiprocessing

startdate='2005001'

# start timing
startTime = time.time()

# information on MOD09Q1 file
ncol = 4800
nrow = 4800 

fillval_band = -28672
fillval_qc = 65535

fillval = 255

min_ndvi= -0.2
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
        fn_mod09q1 = 'HDF4_EOS:EOS_GRID:'+fn_mod09q1+':MOD_Grid_250m_Surface_Reflectance:sur_refl_b0'+str(band_number)

    elif band_number < 8 and band_number > 2:
        fn_mod09a1 = 'HDF4_EOS:EOS_GRID:'+fn_mod09a1+':MOD_Grid_500m_Surface_Reflectance:sur_refl_b0'+str(band_number)

    elif band_number == 33:
        fn_mod09q1 = 'HDF4_EOS:EOS_GRID:'+fn_mod09q1+':MOD_Grid_250m_Surface_Reflectance:sur_refl_qc_250m'

    elif band_number == 11:
        fn_mod09a1 = 'HDF4_EOS:EOS_GRID:'+fn_mod09a1+':MOD_Grid_500m_Surface_Reflectance:sur_refl_state_500m'

    elif band_number == 12:
        fn_mod09a1 = 'HDF4_EOS:EOS_GRID:'+fn_mod09a1+':MOD_Grid_500m_Surface_Reflectance:sur_refl_day_of_year'

        
    else:
        print 'Band number out of range'
        sys.exit(1)
    
    if band_number < 3 and band_number > 0 or band_number == 33:
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
	
    if band_number < 8 and band_number > 2 or band_number == 11 or band_number == 12:
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
        band = band.astype(numpy.uint16)
        return band,geoTransform,proj
        ds_mod09a1 = None
        band = None



# define the otput file
def output_file(output_name,output_array,geoTransform,proj):
    format = "GTiff"
    driver = gdal.GetDriverByName( format )
    outDataset = driver.Create(output_name,ncol,nrow,1,GDT_Float32)
    outBand = outDataset.GetRasterBand(1)
    outBand.WriteArray(output_array,0,0)
    outBand.FlushCache()
    outBand.SetNoDataValue(fillval)
    outDataset.SetGeoTransform(geoTransform )
    outDataset.SetProjection(proj)



# finding all the hdf files in the mentioned root directories 
def findfiles(input_dir):
    toprocess = []
    for root,dir,files in os.walk(input_dir):
        for name in sorted(files):
            if fnmatch.fnmatch(name,'*.hdf'):
                if name[9:-11] > startdate:
                    toprocess.append( os.path.join(root, name) )
    return toprocess




# define the product output name
def product_output_name(output_dir,mod09q1_name,product):
    product_dir = os.path.join(output_dir,product)
    product_output_name = mod09q1_name[:-4]+'.'+product+'.tif'
    product_path_file = os.path.join(product_dir,product_output_name)
    # print 'Output file:   ',product_path_file
    return product_path_file




# processign NDVI
def process_ndvi(mod09q1_file_name,ndvi_output_name):
    fn_mod09q1 = mod09q1_file_name
    fn_mod09a1 = mod09q1_file_name
    
    red,geoTransform,proj  = return_band(fn_mod09q1,1)
    nir1 = return_band(fn_mod09q1,2)[0]
    # the scale factor of the data is 0.0001
    red = red * 0.0001
    nir1 = nir1 * 0.0001
    
    print 'Calculating NDVI... '
    ndvi = (nir1 - red) / (red + nir1 + 0.00000000001)
    
    # MOD09q1 quality mask preparation
    qc = return_band(fn_mod09q1,33)[0]
    mask011 = 0b11111111111
    qc011 = (qc & mask011)
    qc011 = numpy.where(qc011>0,1,0)
    
    # cloud mask from MOD09A1 
    stateflags = return_band(fn_mod09a1,11)[0]
    mask02 = 0b0000000000000111
    qc02 = (stateflags & mask02)
    qc02 = numpy.where(qc02>0,1,0)
    
    # water mask preparation
    water = numpy.right_shift(stateflags,3)
    water = numpy.bitwise_and(water,7)
    water_mask = numpy.where(water == 1 , 0, 1)
    
    # bad ndvi value mask (ndvi out of normal range
    min_ndvi_mask = numpy.where(ndvi < min_ndvi, 1, 0)
    max_ndvi_mask = numpy.where(ndvi > max_ndvi, 1, 0)
    
    # apply all the masks
    numpy.putmask(ndvi, qc011, fillval)
    numpy.putmask(ndvi, qc02, fillval)
    
    numpy.putmask(ndvi, water_mask, fillval)
    
    numpy.putmask(ndvi, min_ndvi_mask, fillval)
    numpy.putmask(ndvi, max_ndvi_mask, fillval)
    
    output_file(ndvi_output_name,ndvi,geoTransform,proj)
    
    red = None
    nir1 = None
    

    qc = None
    mask011 = None
    qc011 = None

    stateflags = None
    mask02 = None
    qc02 = None
    
    water = None
    water_mask = None
    
    ndvi = None
    
    min_ndvi_mask = None
    max_ndvi_mask = None




# processign MSAVI
def process_msavi(mod09q1_file_name,msavi_output_name):
    fn_mod09q1 = mod09q1_file_name
    fn_mod09a1 = mod09q1_file_name
    
    red,geoTransform,proj  = return_band(fn_mod09q1,1)
    nir1 = return_band(fn_mod09q1,2)[0]
    # the scale factor of the data is 0.0001
    red = red * 0.0001
    nir1 = nir1 * 0.0001
    
    print 'Calculating MSAVI....'
    msavi =  0.5*( 2*nir1 + 1 - ( (2*nir1 + 1)**2 - 8*(nir1 - red) )**0.5 )
    
    
    # MOD09q1 quality mask preparation
    qc = return_band(fn_mod09q1,33)[0]
    mask011 = 0b11111111111
    qc011 = (qc & mask011)
    qc011 = numpy.where(qc011>0,1,0)
    
    # cloud mask from MOD09A1 
    stateflags = return_band(fn_mod09a1,11)[0]
    mask02 = 0b0000000000000111
    qc02 = (stateflags & mask02)
    qc02 = numpy.where(qc02>0,1,0)
    
    # water mask preparation
    water = numpy.right_shift(stateflags,3)
    water = numpy.bitwise_and(water,7)
    water_mask = numpy.where(water == 1 , 0, 1)
    
    # bad ndvi value mask (ndvi out of normal range
    min_ndvi_mask = numpy.where(msavi < min_ndvi, 1, 0)
    max_ndvi_mask = numpy.where(msavi > max_ndvi, 1, 0)
    
    # apply all the masks
    
    numpy.putmask(msavi, qc011, fillval)
    numpy.putmask(msavi, qc02, fillval)
    
    numpy.putmask(msavi, water_mask, fillval)
    
    numpy.putmask(msavi, min_ndvi_mask, fillval)
    numpy.putmask(msavi, max_ndvi_mask, fillval)
    
    output_file(msavi_output_name,msavi,geoTransform,proj)
    
    
    red = None
    nir1 = None

    qc = None
    mask011 = None
    qc011 = None

    stateflags = None
    mask02 = None
    qc02 = None
    
    water = None
    water_mask = None
    
    msavi = None
    
    min_ndvi_mask = None
    max_ndvi_mask = None




def process_chl(mod09q1_file_name,chl_output_name):
	
    fn_mod09q1 = mod09q1_file_name
    fn_mod09a1 = mod09q1_file_name
    
    nir1,geoTransform,proj  = return_band(fn_mod09q1,2)
    green = return_band(fn_mod09a1,4)[0]
    
    nir1_mask = numpy.where(nir1 == -28672, 1, 0)
    green_mask = numpy.where(green == -28672, 1, 0)
    
    nir1 = nir1 * 0.0001
    green = green * 0.0001
    
    print 'Calculating CHL....'
    #chl = nir
    chl = (nir1 / (green + 0.000000001)) - 1
    
    min_chl_mask = numpy.where(chl < -0.2, 1, 0)
    max_chl_mask = numpy.where(chl > 20, 1, 0)
    
    # MOD09q1 quality mask preparation
    qc = return_band(fn_mod09q1,33)[0]
    mask011 = 0b11111111111
    qc011 = (qc & mask011)
    qc011 = numpy.where(qc011>0,1,0)
    
    # cloud mask from MOD09A1 
    stateflags = return_band(fn_mod09a1,11)[0]
    mask02 = 0b0000000000000111
    qc02 = (stateflags & mask02)
    qc02 = numpy.where(qc02>0,1,0)
    
    # water mask preparation
    water = numpy.right_shift(stateflags,3)
    water = numpy.bitwise_and(water,7)
    water_mask = numpy.where(water == 1 , 0, 1)
    
    # apply all the masks
    numpy.putmask(chl, nir1_mask, fillval)
    numpy.putmask(chl, green_mask, fillval)
    
    numpy.putmask(chl, qc011, fillval)
    numpy.putmask(chl, qc02, fillval)
    
    numpy.putmask(chl, min_chl_mask, fillval)
    numpy.putmask(chl, max_chl_mask, fillval)
    
    numpy.putmask(chl, water_mask, fillval)
    
    output_file(chl_output_name,chl,geoTransform,proj)
    
    
    green = None
    nir1 = None
    nir1_mask = None
    green_mask = None

    qc = None
    mask011 = None
    qc011 = None

    stateflags = None
    mask02 = None
    qc02 = None
    
    water = None
    water_mask = None
    
    chl = None
    



def process_doy(mod09q1_file_name,doy_output_name):
	
    fn_mod09a1 = mod09q1_file_name
    fn_mod09q1 = mod09q1_file_name
    
    red,geoTransform,proj  = return_band(fn_mod09a1,2)
    doy  = return_band(fn_mod09a1,12)[0]
    
    print 'processing DOY....'
    doy = doy * 1.0
    
    
    # MOD09q1 quality mask preparation
    qc = return_band(fn_mod09q1,33)[0]
    mask011 = 0b11111111111
    qc011 = (qc & mask011)
    qc011 = numpy.where(qc011>0,1,0)
    
    # cloud mask from MOD09A1 
    stateflags = return_band(fn_mod09a1,11)[0]
    mask02 = 0b0000000000000111
    qc02 = (stateflags & mask02)
    qc02 = numpy.where(qc02>0,1,0)
    
    # water mask preparation
    water = numpy.right_shift(stateflags,3)
    water = numpy.bitwise_and(water,7)
    water_mask = numpy.where(water == 1 , 0, 1)
    
    # apply all the masks
    
    numpy.putmask(doy, qc011, fillval)
    numpy.putmask(doy, qc02, fillval)
    
    numpy.putmask(doy, water_mask, fillval)
    
    output_file(doy_output_name,doy,geoTransform,proj)
    
    red = None

    qc = None
    mask011 = None
    qc011 = None

    stateflags = None
    mask02 = None
    qc02 = None
    
    water = None
    water_mask = None
    
    doy = None



def process_sipi(mod09a1_file_name,sipi_output_name):
    #open mod09a1
    fn_mod09a1 = mod09a1_file_name
    
    red,geoTransform,proj  = return_band(fn_mod09a1,1) # band 1 -- red		(620 - 670nm)
    nir1 = return_band(fn_mod09a1,2)[0] # band 2 -- nir1	(841 - 875 nm)
    blue = return_band(fn_mod09a1,3)[0] # band 3 -- blue	(459 - 479 nm)    

    ocean_mask = numpy.where(red == -28672, 1, 0)
    red_mask = numpy.where(red <= 1 , 1, 0)
    nir1_mask = numpy.where(nir1 <= 1, 1, 0)
    blue_mask = numpy.where(blue <= 1, 1, 0)
    
    
    cloud = process_cloudmask(fn_mod09a1)
    cloud_mask = numpy.where(cloud > 1, 1, 0)

    sipi = (nir1 - blue) / (nir1 - red)
    



def process_sipi(mod09q1_file_name,ndwi_output_name):

    fn_mod09a1 = mod09q1_file_name
    fn_mod09q1 = mod09q1_file_name
    
    nir1,geoTransform,proj  = return_band(fn_mod09q1,2)
    red  = return_band(fn_mod09q1,1)[0]
    blue  = return_band(fn_mod09a1,3)[0]
    
    print 'processing SIPI....'
    sipi = (nir1 - blue) / (nir1 - red + 0.00000000001)
        
    # MOD09q1 quality mask preparation
    qc = return_band(fn_mod09q1,33)[0]
    mask011 = 0b11111111111
    qc011 = (qc & mask011)
    qc011 = numpy.where(qc011>0,1,0)
    
    # cloud mask from MOD09A1 
    stateflags = return_band(fn_mod09a1,11)[0]
    mask02 = 0b0000000000000111
    qc02 = (stateflags & mask02)
    qc02 = numpy.where(qc02>0,1,0)
    
    # water mask preparation
    water = numpy.right_shift(stateflags,3)
    water = numpy.bitwise_and(water,7)
    water_mask = numpy.where(water == 1 , 0, 1)
    
    
    # apply all the masks
    
    numpy.putmask(sipi, qc011, fillval)
    numpy.putmask(sipi, qc02, fillval)
    
    numpy.putmask(sipi, water_mask, fillval)
    
    output_file(ndwi_output_name,sipi,geoTransform,proj)
    
    nir1 = None
    red = None
    blue = None

    qc = None
    mask011 = None
    qc011 = None

    stateflags = None
    mask02 = None
    qc02 = None
    
    water = None
    water_mask = None
    
    sipi = None
    




# accumulating the processing    
def doprocess(path):
	
    mod09q1_dir = os.path.dirname(path)
    t1 = time.time()
    name = os.path.basename(path)
    mod09q1 = os.path.join(mod09q1_dir,name)
    print 'processing started ... ', name
    
    ndvi = product_output_name(output_dir,name,'ndvi')
    process_ndvi(mod09q1,ndvi)

    msavi = product_output_name(output_dir,name,'msavi')
    process_msavi(mod09q1,msavi)

    chl = product_output_name(output_dir,name,'chl')
    process_chl(mod09q1,chl)

    #sipi = product_output_name(output_dir,name,'sipi')
    #process_sipi(mod09q1,sipi)
        
    doy = product_output_name(output_dir,name,'doy')
    process_doy(mod09q1,doy)
    
    print '\n'
     

# main function what requires two input: the input path and the output path
def main(input_dir,output_dir):
    
    input_dir = input_dir
    output_dir = output_dir
    filelist = findfiles(input_dir)

    pool = multiprocessing.Pool(processes=multiprocessing.cpu_count())
    # pool = multiprocessing.Pool(processes=1)
    pool.map(doprocess,findfiles(input_dir))
    pool.close()
    pool.join()
    print 'Using ' +str(multiprocessing.cpu_count())+' cores.'
    

if __name__ == '__main__':
    main(input_dir,output_dir)
    
    endTime = time.time()
    print '\n\nThe script took ' +str(endTime - startTime)+ ' seconds'
