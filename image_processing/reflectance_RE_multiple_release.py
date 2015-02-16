#!/usr/bin/python

# RapidEye 5 ORTHO PMS images are in 16bit and the value are Raw radiometric counts (DN)
# Author Riazuddin Kawsar
# email: r.kawsar@spatial-business-integration
# date: 21st july 2014


##### RE bands and indexes
#Band Nr 1 = Blue
#Band Nr 2 = Green
#Band Nr 3 = Red
#Band Nr 4 = Red Edge
#Band Nr 5 = Near IR


import xml.dom.minidom as minidom
from collections import defaultdict
import csv
import os, sys, time, datetime, math, numpy, fnmatch
from osgeo import gdal
from osgeo.gdalconst import *
import multiprocessing
import matplotlib.pylab as plt


# input variables (sub_folder_name should be the name of the image folder and
# main folder name should be the folder name the iamge folders are in...


# primary input
sub_folder_name = sys.argv[1]
#sub_folder_name = '3358305_2014-07-04_RE3_3A_294600'


# secondary input
main_folder = 'SBCP_BASF'



# input files (automatically generated
image_file_name = '/media/Arc/eo_archive_proc/VHR_SAT_IMAGE/RE5/' + main_folder + '/' + sub_folder_name + '/' + sub_folder_name + '.tif'
metadata_file='/media/Arc/eo_archive_proc/VHR_SAT_IMAGE/RE5/' + main_folder + '/' + sub_folder_name + '/' + sub_folder_name + '_metadata.xml'

Esdistance_file="/media/Arc/eo_archive_proc/VHR_SAT_IMAGE/bin/earth_sun_distance.csv"
out_put_dir = '/media/Arc/eo_archive_proc/VHR_SAT_IMAGE/RE5/' + main_folder + '/' + sub_folder_name


min_ndvi= 0.01
max_ndvi = 1.0

# Exo Atmospheric Irradiance for RapidEye bands (effective on or after April 27, 2010)
B1_irradiance = 1997.80
B2_irradiance = 1863.50
B3_irradiance = 1560.40
B4_irradiance = 1395.00
B5_irradiance = 1124.40



# creating the product name based on date (automatically generated)
product_tmp = sub_folder_name.split('_', 1)[1]
product_tmp = product_tmp.split('_', 1)[0]

year = product_tmp.split('-', 1)[0]
month = product_tmp.split('-', 1)[1]
month = month.split('-', 1)[0]
day = product_tmp.split('-', 1)[1]
day = day.split('-', 1)[1]

product_date = day + '.' + month + '.' +  year[2:4]
product = 'binned_' + product_date
product_out_path = os.path.join (out_put_dir, product)

if not os.path.exists(product_out_path):
    os.makedirs(product_out_path)



# main function
def doit(image_file_name, metadata_file, Esdistance_file, B1_irradiance, B2_irradiance, B3_irradiance, B4_irradiance, B5_irradiance):    
    B1_ScaleFactor, B2_ScaleFactor, B3_ScaleFactor, B4_ScaleFactor, B5_ScaleFactor = return_band_radiance(metadata_file)
    solar_zenith_angle_radians = return_located_geometric_values(metadata_file)
    Esdistance = return_strip_source(metadata_file, Esdistance_file)
    B1,geoTransform,proj,ncol,nrow  = return_band(image_file_name,1)
    B2,geoTransform,proj,ncol,nrow  = return_band(image_file_name,2)
    B3,geoTransform,proj,ncol,nrow  = return_band(image_file_name,3)
    B4,geoTransform,proj,ncol,nrow  = return_band(image_file_name,4)
    B5,geoTransform,proj,ncol,nrow  = return_band(image_file_name,5)
    B1_TOA_radiance, B2_TOA_radiance, B3_TOA_radiance, B4_TOA_radiance, B5_TOA_radiance = calculate_toa_radiance(B1, B2, B3, B4, B5, B1_ScaleFactor, B2_ScaleFactor, B3_ScaleFactor, B4_ScaleFactor, B5_ScaleFactor)
    calculate_toa_reflectance(out_put_dir,product,B1_TOA_radiance, B2_TOA_radiance, B3_TOA_radiance, B4_TOA_radiance, B5_TOA_radiance, B1_irradiance, B2_irradiance, B3_irradiance, B4_irradiance, B5_irradiance, Esdistance, solar_zenith_angle_radians)



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
    outDataset.SetGeoTransform(geoTransform )
    outDataset.SetProjection(proj)


def normalize(band1,band2):
    var1 = numpy.subtract(band1,band2)
    var2 = numpy.add(band1,band2)
    numpy.seterr(all='ignore')
    ndvi = numpy.divide(var1,var2)
    return ndvi


# extracting the band raiance information (band gain and bias) (watt/m2/steradians/micrometers)
def return_band_radiance(metadata_file):
    doc = minidom.parse(metadata_file)
    radiometricScaleFactor = doc.getElementsByTagName('re:bandSpecificMetadata')
    for node in radiometricScaleFactor:
        band=node.getElementsByTagName('re:bandNumber')
        ScaleFactor=node.getElementsByTagName('re:radiometricScaleFactor')
        for a in band:
            band= a.firstChild.data
            for b in ScaleFactor:
                ScaleFactor= b.firstChild.data
        ScaleFactor = [band, ScaleFactor]
        if ScaleFactor[0] == '1':
            B1_ScaleFactor = float(ScaleFactor[1])
            print 'B1_ScaleFactor: ' + str(B1_ScaleFactor)
        elif ScaleFactor[0] == '2':
            B2_ScaleFactor = float(ScaleFactor[1])
            print 'B2_ScaleFactor: ' + str(B2_ScaleFactor)
        elif ScaleFactor[0] == '3':
            B3_ScaleFactor = float(ScaleFactor[1])
            print 'B3_ScaleFactor: ' + str(B3_ScaleFactor)
        elif ScaleFactor[0] == '4':
            B4_ScaleFactor = float(ScaleFactor[1])
            print 'B4_ScaleFactor: ' + str(B4_ScaleFactor)
        elif ScaleFactor[0] == '5':
            B5_ScaleFactor = float(ScaleFactor[1])
            print 'B5_ScaleFactor: ' + str(B5_ScaleFactor)

    return B1_ScaleFactor, B2_ScaleFactor, B3_ScaleFactor, B4_ScaleFactor, B5_ScaleFactor





# central solar zenith angle ( 90.00 - center_sun_elevation )
def return_located_geometric_values(metadata_file):
    doc = minidom.parse(metadata_file)
    Acquisition = doc.getElementsByTagName('re:Acquisition')
    for node in Acquisition:
        illuminationElevationAngle = node.getElementsByTagName('opt:illuminationElevationAngle')
        for a in illuminationElevationAngle:
            illuminationElevationAngle = float(a.firstChild.data)
            solar_zenith_angle = float(90.00) - float(illuminationElevationAngle)
            solar_zenith_angle_radians = math.radians(solar_zenith_angle)
            print 'sun_elevation: ' + str(illuminationElevationAngle)
            print 'solar_zenith_angle: ' + str(solar_zenith_angle)
            print 'solar_zenith_angle_radians: ' + str(solar_zenith_angle_radians)
    return solar_zenith_angle_radians





# Earth-Sun distance (d) in astronomical units for Day of the Year (DOY); DOY, Esdistance

def return_strip_source(metadata_file, Esdistance_file):
    doc = minidom.parse(metadata_file)
    DownlinkInformation = doc.getElementsByTagName('eop:DownlinkInformation')
    for node in DownlinkInformation:
        acquisitionDate = node.getElementsByTagName('eop:acquisitionDate')
        for a in acquisitionDate:
            acquisitionDate = a.firstChild.data
            year = int(acquisitionDate[0:4])
            month = int(acquisitionDate[5:7])
            day = int(acquisitionDate[8:10])
            d=datetime.date(year=year, month=month, day=day)
            yday = d.toordinal() - datetime.date(d.year, 1, 1).toordinal() + 1
            print 'acquisitionDate :' + str(acquisitionDate)
            print 'Day Of Year :' + str(yday)
            # Earth- sun distance calculation
            with open(Esdistance_file) as f:
                reader = csv.DictReader(f)
                rows = [row for row in reader if row['DOY'] == str(yday)]
                Esdistance = float(rows[0]['Esdistance'])
                print 'Esdistance: ' + str(Esdistance)
    return Esdistance





# Band specific TOA Rediance Estimation

def calculate_toa_radiance(B1, B2, B3, B4, B5, B1_ScaleFactor, B2_ScaleFactor, B3_ScaleFactor, B4_ScaleFactor, B5_ScaleFactor):
    B1_TOA_radiance = B1 * B1_ScaleFactor
    print 'B1_TOA_radiance: ' + str(B1_TOA_radiance)
    B2_TOA_radiance = B2 * B2_ScaleFactor
    print 'B2_TOA_radiance: ' + str(B2_TOA_radiance)
    B3_TOA_radiance = B3 * B3_ScaleFactor
    print 'B3_TOA_radiance: ' + str(B3_TOA_radiance)
    B4_TOA_radiance = B4 * B4_ScaleFactor
    print 'B4_TOA_radiance: ' + str(B4_TOA_radiance)
    B5_TOA_radiance = B5 * B5_ScaleFactor
    print 'B5_TOA_radiance: ' + str(B5_TOA_radiance)
    return B1_TOA_radiance, B2_TOA_radiance, B3_TOA_radiance, B4_TOA_radiance, B5_TOA_radiance



# Band specific TOA Reflectation Estimation
def calculate_toa_reflectance(out_put_dir,product,B1_TOA_radiance, B2_TOA_radiance, B3_TOA_radiance, B4_TOA_radiance, B5_TOA_radiance, B1_irradiance, B2_irradiance, B3_irradiance, B4_irradiance, B5_irradiance, Esdistance, solar_zenith_angle_radians):

    B1_TOA_reflectance = (math.pi * B1_TOA_radiance * math.pow(Esdistance, 2)) / (B1_irradiance * math.cos(solar_zenith_angle_radians))
    print 'B1_TOA_reflectance: ' + str(B1_TOA_reflectance)

    B2_TOA_reflectance = (math.pi * B2_TOA_radiance * math.pow(Esdistance, 2)) / (B2_irradiance * math.cos(solar_zenith_angle_radians))
    print 'B2_TOA_reflectance: ' + str(B2_TOA_reflectance)

    B3_TOA_reflectance = (math.pi * B3_TOA_radiance * math.pow(Esdistance, 2)) / (B3_irradiance * math.cos(solar_zenith_angle_radians))
    print 'B3_TOA_reflectance: ' + str(B3_TOA_reflectance)

    B4_TOA_reflectance = (math.pi * B4_TOA_radiance * math.pow(Esdistance, 2)) / (B4_irradiance * math.cos(solar_zenith_angle_radians))
    print 'B4_TOA_reflectance: ' + str(B4_TOA_reflectance)

    B5_TOA_reflectance = (math.pi * B5_TOA_radiance * math.pow(Esdistance, 2)) / (B5_irradiance * math.cos(solar_zenith_angle_radians))
    print 'B5_TOA_reflectance: ' + str(B5_TOA_reflectance)

    Band,geoTransform,proj,ncol,nrow  = return_band(image_file_name,2)

    B1_name = product_output_name(out_put_dir,product,'B1')
    B2_name = product_output_name(out_put_dir,product,'B2')
    B3_name = product_output_name(out_put_dir,product,'B3')
    B4_name = product_output_name(out_put_dir,product,'B4')
    B5_name = product_output_name(out_put_dir,product,'B5')
    ndvi_name = product_output_name(out_put_dir,product,'ndvi')

    print "Processing B1_name ... "
    output_file(B1_name,B1_TOA_reflectance,geoTransform,proj,ncol,nrow)
    print "Processing B2_name ... "
    output_file(B2_name,B2_TOA_reflectance,geoTransform,proj,ncol,nrow)
    print "Processing B3_name ... "
    output_file(B3_name,B3_TOA_reflectance,geoTransform,proj,ncol,nrow)
    print "Processing B4_name ... "
    output_file(B4_name,B4_TOA_reflectance,geoTransform,proj,ncol,nrow)
    print "Processing B5_name ... "
    output_file(B5_name,B5_TOA_reflectance,geoTransform,proj,ncol,nrow)

    print "processing ndvi...."
    ndvi = normalize(B5_TOA_reflectance,B3_TOA_reflectance)
    min_ndvi_mask = numpy.where(ndvi < min_ndvi, 1, 0)
    max_ndvi_mask = numpy.where(ndvi > max_ndvi, 1, 0)

    numpy.putmask(ndvi, min_ndvi_mask, min_ndvi)
    numpy.putmask(ndvi, max_ndvi_mask, max_ndvi)

    output_file(ndvi_name,ndvi,geoTransform,proj,ncol,nrow)
    band = None
    ndvi = None

            

if __name__ == "__main__":
    doit(image_file_name, metadata_file, Esdistance_file, B1_irradiance, B2_irradiance, B3_irradiance, B4_irradiance, B5_irradiance)
