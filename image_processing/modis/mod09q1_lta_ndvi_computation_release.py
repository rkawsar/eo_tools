# coding: utf-8
# Author: R.Kawsar
# E-mail: r.kawsar@spatial-business-integration.com
# Date: 3-June 2015
# MOD09Q LONG TERM AVERAGE computation


import os, sys, time, numpy, fnmatch
from osgeo import gdal
from osgeo.gdalconst import *


input_dir = '/media/Arc/eo_archive_proc/MOD09Q1/output/h18v03/ndvi'
output_dir = '/media/Arc/eo_archive_proc/MOD09Q1/output/h18v03/ndvi_lta'
# start timing
startTime = time.time()
# information on MOD09Q1 file
ncol = 4800
nrow = 4800
fillval = 255
doy_s = [1,9,17,25,33,41,49,57,65,73,81,89,97,105,113,121,129,
         137,145,153,161,169,177,185,193,201,209,217,225,233,
         241,249,257,265,273,281,289,297,305,313,321,329,337,345,353,361]

# finding all the hdf files in the mentioned root directories 
def list_files_acc_to_doy(input_dir, doy):
    toprocess = []
    for root,dir,files in os.walk(input_dir):
        for name in sorted(files):
            if fnmatch.fnmatch(name,'*ndvi.tif'):
                if int(os.path.basename(name)[13:16]) == doy:
                    toprocess.append( os.path.join(root, name) )
    return toprocess



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
    band = band.astype(numpy.float32)
    return band,geoTransform,proj,ncol,nrow
    dataset = None
    band = None


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


def doit(input_dir):

    dic = {}
    for i in doy_s:
        dic['doy_' + str(i)] = list_files_acc_to_doy(input_dir, i)
        
    for doy, img_list in dic.items():
        print 'computing LTA for ' + doy + ' ...'
        sum_doy = numpy.zeros((4800,4800), dtype=numpy.float32)
        count_doy = numpy.zeros((4800,4800), dtype=numpy.float32)

        # defining output name
        name = os.path.basename(img_list[0])
        img_date = name.split('.')[1]
        year = img_date[1:5]
        doy = img_date[5:8]
        out_img_name = name.split('.')[0] + '.' + 'A' + doy + '.' + name.split('.')[2] + '.ndvi.lta.tif'
        out_img_name = os.path.join(output_dir, out_img_name)
        
        for i in img_list:
            band,geoTransform,proj,ncol,nrow = return_band(i, 1)
            # replace the no data value with '0'
            band[band == 255] = 0
            sum_doy += band
            # replace all the value with 1 to create the count raster.
            band[band != 0] = 1
            count_doy += band
        avg_doy = sum_doy/count_doy
        # writing LTA raster...
        output_file(out_img_name,avg_doy,geoTransform,proj,ncol,nrow)

if __name__ == '__main__':

    doit(input_dir)
