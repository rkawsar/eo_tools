#!/usr/bin/python

# Extract Ndvi data from modis Image according to Lattitude/longitude list
# Author Riazuddin Kawsar
# email: r.kawsar@spatial-business-integration
# date: 24th july 2014


import os, sys, time, gdal, fnmatch
from osgeo import osr
from gdalconst import *
import glob
import numpy
import csv
import multiprocessing



# input parameters -------------------------------------------------------------------------------------
coord_file = '/media/Arc/eo_archive_proc/MOD09Q1/wrkdir/input_coord_file/MOD09Q1_H18V04.csv'
out_file = '/media/Arc/eo_archive_proc/MOD09Q1/wrkdir/output_coord_file/mod09q1_h18v04_2015_121_129_test.csv'

startdate = '2015115'
enddate = '2015130'


raster_file_path = '/media/Arc/eo_archive_proc/MOD09Q1/output/h18v04/ndvi'
startTime = time.time()


# reading the coordinate list as an arry
coord_data = numpy.genfromtxt(coord_file, dtype=None, delimiter=',', skip_header=1) #coord_data.dtype.names


# creating the output list.
output_list = []
list_out = ['node_code', 'x', 'y', 'date', 'doy', 'ndvi', 'msavi']
output_list.append(list_out)


# finding all the hdf files in the mentioned root directories 
def findfiles(input_dir):
    toprocess = []
    for root,dir,files in os.walk(input_dir):
        for name in sorted(files):
            if fnmatch.fnmatch(name,'*.tif'):
                if name[9:-11] > startdate and name[9:-11] < enddate :
                    toprocess.append( os.path.join(root, name) )
    return toprocess




def extract_value_from_raster(ds_file, modis_x, modis_y):
    
    name = os.path.basename(ds_file)
    date = name[9:16]
    
    gdal.AllRegister()
    
    ds_ndvi = gdal.Open(ds_file, GA_ReadOnly)
    ds_doy = ds_file.replace("ndvi","doy")
    ds_doy = gdal.Open(ds_doy, GA_ReadOnly)
    ds_msavi = ds_file.replace("ndvi","msavi")
    ds_msavi = gdal.Open(ds_msavi, GA_ReadOnly)
    
    rows = ds_ndvi.RasterYSize
    cols = ds_ndvi.RasterXSize
    transform = ds_ndvi.GetGeoTransform()
    xOrigin = transform[0]
    yOrigin = transform[3]
    pixelWidth = transform[1]
    pixelHeight = transform[5]
    xOffset = int((modis_x - xOrigin) / pixelWidth)
    yOffset = int((modis_y - yOrigin) / pixelHeight)
    
    ndvi_band = ds_ndvi.GetRasterBand(1)
    doy_band = ds_doy.GetRasterBand(1)
    msavi_band = ds_msavi.GetRasterBand(1)
    
    ndvi_data = ndvi_band.ReadAsArray(xOffset, yOffset, 1, 1)
    doy_data = doy_band.ReadAsArray(xOffset, yOffset, 1, 1)
    msavi_data = msavi_band.ReadAsArray(xOffset, yOffset, 1, 1)
    
    ndvi_value = ndvi_data[0,0]
    doy_value = doy_data[0,0]
    msavi_value = msavi_data[0,0]

    ds_ndvi = None
    ds_doy = None
    ds_msavi = None

    ndvi_band = None
    doy_band = None
    msavi_band = None

    ndvi_data = None
    doy_data = None
    msavi_data = None
    
    return date, doy_value, ndvi_value, msavi_value


def wgs84_to_modissinu ( lon, lat ):
	wgs84 = osr.SpatialReference( )  # Define a SpatialReference object
	wgs84.ImportFromEPSG( 4326 )
	# Define the modis data projection, sinusoidal #sinu_modis.ImportFromEPSG( 27700)
	modis_sinu = osr.SpatialReference() 
	modis_sinu.ImportFromProj4 ( "+proj=sinu +lon_0=0 +x_0=0 +y_0=0 " + \
                      "+a=6371007.181 +b=6371007.181 " + \
                      "+units=m +no_defs" )
	tx = osr.CoordinateTransformation(wgs84, modis_sinu)
	modis_x, modis_y, modis_z = tx.TransformPoint ( lon, lat )
	return modis_x, modis_y, modis_z


def modissinu_to_wgs84 ( modis_x, modis_y ):
	from osgeo import osr
	wgs84 = osr.SpatialReference( )
	wgs84.ImportFromEPSG( 4326 )
	modis_sinu = osr.SpatialReference() 
	modis_sinu.ImportFromProj4 ( "+proj=sinu +lon_0=0 +x_0=0 +y_0=0 " + \
                      "+a=6371007.181 +b=6371007.181 " + \
                      "+units=m +no_defs" )
	tx = osr.CoordinateTransformation(modis_sinu, wgs84)
	lon, lat, modis_z = tx.TransformPoint ( modis_x, modis_y )



def write_output(out_file, output_list):
    with open(out_file, "wb") as f:
        writer = csv.writer(f)
        writer.writerows(output_list)



def doit(coord_data, raster_file_path):
    mod_coord_list =[]
    for i in range(len(coord_data)):
        node_code = coord_data[i][0]
        x = float (coord_data[i][1])
        y = float (coord_data[i][2])
        
        modis_x, modis_y, modis_z = wgs84_to_modissinu( x, y )
        nn = [node_code, x, y, modis_x, modis_y]
        mod_coord_list.append(nn)
    return mod_coord_list


def main(raster_file, node_code, x, y, modis_x, modis_y):
    #print 'data extraction started for : ' + str(x), str(y)
    date, doy, ndvi, msavi = extract_value_from_raster(raster_file, modis_x, modis_y)
    output_seq = [node_code, x, y, date, doy, ndvi, msavi]
    return output_seq


# auxiliary funciton to make it work
def job_helper(args):
    return main(*args)


def process_tuples(raster_file_path, coord_data):
    parallal_args = []
    filelist = findfiles(raster_file_path)
    mod_coord_list = doit(coord_data, raster_file_path)
    for i in filelist:
        for j in mod_coord_list:
            nn = (str(i), j[0], j[1], j[2], j[3], j[4])
            parallal_args.append(nn)
    return parallal_args



if __name__ == "__main__":
    
    parallal_args = process_tuples(raster_file_path, coord_data)
    pool = multiprocessing.Pool(processes=multiprocessing.cpu_count())
    #pool = multiprocessing.Pool(processes=1)
    output_seq = pool.map(job_helper, parallal_args)
    pool.close()
    pool.join()
    write_output(out_file, output_seq)
    print 'Using ' +str(multiprocessing.cpu_count())+' cores.'
    endTime = time.time()
    print 'The script took ' + str(endTime - startTime) + ' seconds'
