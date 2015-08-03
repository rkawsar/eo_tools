#!/usr/bin/python

# Landsat 8 TOA reflactance and brightness temparature calculation
# Author Riazuddin Kawsar
# email: r.kawsar@spatial-business-integration
# date: 30th july 2015


# Landsat 8 bands
#---------------------------------------------------------
#Band 1 - Coastal aerosol 	0.43 - 0.45 	30
#Band 2 - Blue 	                0.45 - 0.51 	30
#Band 3 - Green 	        0.53 - 0.59 	30
#Band 4 - Red 	                0.64 - 0.67 	30
#Band 5 - Near Infrared (NIR) 	0.85 - 0.88 	30
#Band 6 - SWIR 1 	        1.57 - 1.65 	30
#Band 7 - SWIR 2 	        2.11 - 2.29 	30
#Band 8 - Panchromatic 	        0.50 - 0.68 	15
#Band 9 - Cirrus 	        1.36 - 1.38 	30
#Band 10 - Thermal Infrared (TIRS) 1 	10.60 - 11.19 	100 * (30)
#Band 11 - Thermal Infrared (TIRS) 2 	11.50 - 12.51 	100 * (30)

# http://landsat.usgs.gov/band_designations_landsat_satellites.php
# reflectance algorithm source: http://landsat.usgs.gov/Landsat8_Using_Product.php




import xml.dom.minidom as minidom
from collections import defaultdict
import csv
import os, glob, sys, time, datetime, math, numpy, fnmatch
from osgeo import gdal
from osgeo.gdalconst import *
#import multiprocessing
import matplotlib.pylab as plt
#from decimal import *



# input variables ---- user input ----
wrd_dir = '/media/Num/PhD/LANDSAT8/N0'
data_folder = 'LC81970302014029LGN00'


min_ndvi= 0.01
max_ndvi = 1.0
fillval = 9999

# input files (automatically generated)
data_dir = os.path.join(wrd_dir, data_folder)
os.chdir(data_dir)

for meta_file in glob.glob('*_MTL.txt'):
    metadata_file = os.path.join(data_dir, meta_file)
    print 'metadata_file: ' + metadata_file


# Quality pixel flag ( from Landsat 8 Quality Assessment band)
#BQF = [61440,59424,57344,56320,53248,39936,36896,36864,
#       31744,28672,28590,26656,24576,23552,20516,20512,20480]

BQF = [1, 61440,59424,57344,56320,53248,39936,36896,36864]

#---------------------------- collecting all the necessary input files -------------------
# ----------------------------------------------------------------------------------------

def findfiles(input_dir, file_type):  # file_type = '*.tif'
    toprocess = []
    for root,dir,files in os.walk(input_dir):
        for name in sorted(files):
            if fnmatch.fnmatch(name,file_type): 
                toprocess.append( os.path.join(root, name) )
    return toprocess


# finding different bands for calculation
for raster_files in findfiles(data_dir, '*.TIF'):
    raster_path = raster_files
    raster_name = os.path.basename(raster_path)
    band_name = raster_name.split('_', 1)[1]
    band_name = band_name.split('.', 1)[0]
    if band_name == 'B1':
        Band_B1 = raster_path
    if band_name == 'B2':
        Band_B2 = raster_path
    if band_name == 'B3':
        Band_B3 = raster_path
    if band_name == 'B4':
        Band_B4 = raster_path
    if band_name == 'B5':
        Band_B5 = raster_path
    if band_name == 'B6':
        Band_B6 = raster_path
    if band_name == 'B7':
        Band_B7 = raster_path
    if band_name == 'B10':
        Band_B10 = raster_path
    if band_name == 'B11':
        Band_B11 = raster_path
    if band_name == 'BQA':
        Band_BQA = raster_path
        print 'Band_BQA = ' + Band_BQA 



####### extracting metadata ---------------------------
#------------------------------------------------------
# function to read the metadata (works for landsat MTL and Digitalglobe IMD metadata)
def read_metadata(f):
    lines=iter(open(f).readlines())
    hdrdata={}
    line=lines.next()
    while line:
        line=[item.strip() for item in line.replace('"','').split('=')]
        group=line[0].upper()
        if group in ['END;','END']:break
        value=line[1]
        if group in ['END_GROUP']:pass
        elif group in ['BEGIN_GROUP','GROUP']:
            group=value
            subdata={}
            while line:
                line=lines.next()
                line = [l.replace('"','').strip() for l in line.split('=')]
                subgroup=line[0]
                subvalue=line[1]
                if subgroup == 'END_GROUP':
                    break
                elif line[1] == '(':
                    while line:
                        line=lines.next()
                        line = line.replace('"','').strip()
                        subvalue+=line
                        if line[-1:]==';':
                            subvalue=eval(subvalue.strip(';'))
                            break
                else:subvalue=subvalue.strip(';')
                subdata[subgroup]=subvalue
            hdrdata[group]=subdata
        else: hdrdata[group]=value.strip(');')
        line=lines.next()
    return hdrdata


# reading the metadata in a dictionary
imddata = read_metadata (metadata_file)


def acquireMetadata(band):
    ref_MRF = float(imddata['RADIOMETRIC_RESCALING']['REFLECTANCE_MULT_BAND_' + str(band)])
    ref_AMF = float(imddata['RADIOMETRIC_RESCALING']['REFLECTANCE_ADD_BAND_' + str(band)])
    metadatalist = [0, 0, ref_MRF, ref_AMF]
    return metadatalist

def acquireThrmalMetadata(band):
    radi_MRF = float(imddata['RADIOMETRIC_RESCALING']['RADIANCE_MULT_BAND_' + str(band)])
    radi_AMF = float(imddata['RADIOMETRIC_RESCALING']['RADIANCE_ADD_BAND_' + str(band)])  
    K1 = float(imddata['TIRS_THERMAL_CONSTANTS']['K1_CONSTANT_BAND_' + str(band)])
    K2 = float(imddata['TIRS_THERMAL_CONSTANTS']['K2_CONSTANT_BAND_' + str(band)])
    acquireThrmalMetadata = [radi_MRF, radi_AMF, K1, K2]
    return acquireThrmalMetadata


SunElevation  = float(imddata['IMAGE_ATTRIBUTES']['SUN_ELEVATION'])
img_date = imddata['PRODUCT_METADATA']['DATE_ACQUIRED']
img_time = imddata['PRODUCT_METADATA']['SCENE_CENTER_TIME']
solar_zenith_angle = float(90.00) - SunElevation
solar_zenith_angle_radians = math.radians(solar_zenith_angle)
SunElevation_radians = math.radians(SunElevation)

print 'Acquisition date : ' + img_date
print 'Acquisition time : ' + img_time
print 'SunElevation :' + str(SunElevation)


# creating the product name and output dir
year = img_date.split('-', 1)[0]
month = img_date.split('-', 1)[1]
month = month.split('-', 1)[0]
day = img_date.split('-', 1)[1]
day = day.split('-', 1)[1]

product_date = day + '.' + month + '.' +  year[2:4]
product = 'binned_' + product_date
output_dir = os.path.join (data_dir, product)
print output_dir

if not os.path.exists(output_dir):
   os.makedirs(output_dir)




######## raster processing functions ---------------------
#----------------------------------------------------------


# function to read the image bands
def return_band(image_file_name, band_number):
    image = image_file_name
    dataset = gdal.Open(image,GA_ReadOnly)  
    if dataset is None:
        print "Could not open " + dataset
        sys.exit(1)
    geoTransform = dataset.GetGeoTransform()
    proj = dataset.GetProjection()
    rasterband = dataset.GetRasterBand(band_number)
    type(rasterband)
    ncol = dataset.RasterXSize
    nrow = dataset.RasterYSize
    band = rasterband.ReadAsArray(0,0,ncol,nrow)
    band = band.astype(numpy.uint16)
    return band,geoTransform,proj,ncol,nrow
    dataset = None
    band = None



# will return '/media/Arc/eo_archive_proc/VHR_SAT_IMAGE/SPOT6/20140704_SPOT/binned_SPOT6_20140704/B0.binned_SPOT6_20140704.tif'
# the function input defined in the beginining: out_put_dir, product just we have to change the product name.....
def product_output_name(out_put_dir,product,Product_name):
    product_dir = os.path.join(out_put_dir,product)
    product_output_name = Product_name+'.'+product+'.tif'
    product_path_file = os.path.join(product_dir,product_output_name)
    return product_path_file


def output_file(output_name,output_array,geoTransform,proj,ncol,nrow):
    format = "GTiff"
    driver = gdal.GetDriverByName( format )
    outDataset = driver.Create(output_name,ncol,nrow,1,GDT_Float32)
    outBand = outDataset.GetRasterBand(1)
    outBand.WriteArray(output_array,0,0)
    outBand.FlushCache()
    outBand.SetNoDataValue(fillval)
    outDataset.SetGeoTransform(geoTransform )
    outDataset.SetProjection(proj)


def normalize(band1,band2):
    var1 = numpy.subtract(band1,band2)
    var2 = numpy.add(band1,band2)
    numpy.seterr(all='ignore')
    ndvi = numpy.divide(var1,var2)
    return ndvi


# reading DN bands, extracting metadata and calculating radiance and reflactance and writing it to the folder
# i.e, band_name = B1
def calculate_reflectance(band_name, solar_zenith_angle_radians, DN, output_dir):
    img_name = 'Band_' + band_name
    band_metadata = acquireMetadata (band_name[1:])
    ref_MRF = float(band_metadata[2])
    ref_AMF = float(band_metadata[3])
    print 'calculating ' + band_name + ' reflactance...'
    reflectance = (ref_MRF * DN + ref_AMF) / (math.cos(solar_zenith_angle_radians))
    reflectance_name = product_output_name(data_dir,product,band_name)
    print 'Masking with Quality flag...'
    band_BQA,geoTransform,proj,ncol,nrow  = return_band(Band_BQA,1)
    for i in BQF:
        qc = numpy.where(band_BQA==i,1,0)
        numpy.putmask(reflectance, qc, fillval)
    output_file(reflectance_name,reflectance,geoTransform,proj,ncol,nrow)
    reflactance = None
    band_BQA = None


# calculating the ndvi
def calculate_ndvi(solar_zenith_angle_radians, red, nir, output_dir):
    print 'reading RED band....'
    band_metadata_B4 = acquireMetadata(4)
    ref_MRF_B4 = float(band_metadata_B4[2])
    ref_AMF_B4 = float(band_metadata_B4[3])
    print 'calculating reflactance...'
    reflectance_B4 = (ref_MRF_B4 * Band_B4 + ref_AMF_B4) / (math.cos(solar_zenith_angle_radians))
    print 'reading NIR band....'
    band_metadata_B5 = acquireMetadata(5)
    ref_MRF_B5 = float(band_metadata_B5[2])
    ref_AMF_B5 = float(band_metadata_B5[3])
    print 'calculating reflactance...'
    reflectance_B5 = (ref_MRF_B5 * Band_B5 + ref_AMF_B5) / (math.cos(solar_zenith_angle_radians))
    ndvi_name = product_output_name(data_dir,product,'ndvi')
    print "Calculating ndvi...."
    ndvi = normalize(reflectance_B5, reflectance_B4)
    min_ndvi_mask = numpy.where(ndvi < min_ndvi, 1, 0)
    max_ndvi_mask = numpy.where(ndvi > max_ndvi, 1, 0)
    numpy.putmask(ndvi, min_ndvi_mask, min_ndvi)
    numpy.putmask(ndvi, max_ndvi_mask, max_ndvi)
    #print 'Masking with Quality flag...'
    band_BQA,geoTransform,proj,ncol,nrow  = return_band(Band_BQA,1)
    for i in BQF:
        qc = numpy.where(band_BQA==i,1,0)
        numpy.putmask(ndvi, qc, fillval)
    output_file(ndvi_name,ndvi,geoTransform,proj,ncol,nrow)
    reflectance_B4 = None
    reflectance_B5 = None
    mdvi = None
    band_BQA = None


# Conversion to At-Satellite Brightness Temperature (K)
def calculate_brightness_temperature(band_name, solar_zenith_angle_radians, DN, output_dir):

    img_name = 'Band_' + band_name
    print 'reading....' +  img_name
    band_metadata = acquireThrmalMetadata (band_name[1:])
    radi_MRF = float(band_metadata[0])
    radi_AMF = float(band_metadata[1])
    K1 = float(band_metadata[2])
    K2 = float(band_metadata[3])
    print 'calculating Radiance...'
    radiance = (DN * radi_MRF) + radi_AMF
    print 'calculating Satellite Brightness Temperature...'
    TB = K2 / (numpy.log((K1 / radiance) +1))
    print 'Masking with Quality flag...'
    band_BQA,geoTransform,proj,ncol,nrow  = return_band(Band_BQA,1)
    for i in BQF:
        qc = numpy.where(band_BQA==i,1,0)
        numpy.putmask(TB, qc, fillval)
    print 'writing output...'
    reflectance_name = product_output_name(data_dir,product,band_name)
    output_file(reflectance_name,TB,geoTransform,proj,ncol,nrow)
    radiance = None




if __name__ == "__main__":

    Band_B1,geoTransform,proj,ncol,nrow  = return_band(Band_B1,1)
    calculate_reflectance('B1', solar_zenith_angle_radians, Band_B1, output_dir)
    Band_B1 = None

    Band_B2,geoTransform,proj,ncol,nrow  = return_band(Band_B2,1)
    calculate_reflectance('B2', solar_zenith_angle_radians, Band_B2, output_dir)
    Band_B2 = None

    Band_B3,geoTransform,proj,ncol,nrow  = return_band(Band_B3,1)
    calculate_reflectance('B3', solar_zenith_angle_radians, Band_B3, output_dir)
    Band_B3 = None

    Band_B4,geoTransform,proj,ncol,nrow  = return_band(Band_B4,1)
    calculate_reflectance('B4', solar_zenith_angle_radians, Band_B4, output_dir)

    Band_B5,geoTransform,proj,ncol,nrow  = return_band(Band_B5,1)
    calculate_reflectance('B5', solar_zenith_angle_radians, Band_B5, output_dir)
    
    Band_B6,geoTransform,proj,ncol,nrow  = return_band(Band_B6,1)
    calculate_reflectance('B6', solar_zenith_angle_radians, Band_B6, output_dir)
    Band_B6 = None

    Band_B7,geoTransform,proj,ncol,nrow  = return_band(Band_B7,1)
    calculate_reflectance('B7', solar_zenith_angle_radians, Band_B7, output_dir)
    Band_B7 = None

    calculate_ndvi(solar_zenith_angle_radians, Band_B4, Band_B5, output_dir)
    Band_B5 = None
    Band_B4 = None

    Band_B10,geoTransform,proj,ncol,nrow  = return_band(Band_B10,1)
    calculate_brightness_temperature('B10', solar_zenith_angle_radians, Band_B10, output_dir)
    Band_B10 = None

    Band_B11,geoTransform,proj,ncol,nrow  = return_band(Band_B11,1)
    calculate_brightness_temperature('B11', solar_zenith_angle_radians, Band_B11, output_dir)
    Band_B11 = None

    print 'GAME OVER .... '
