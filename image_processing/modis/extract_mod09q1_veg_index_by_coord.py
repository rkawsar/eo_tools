#!/usr/bin/python

# Extract Ndvi data from modis Image according to Lattitude/longitude list
# Author Riazuddin Kawsar
# email: r.kawsar@spatial-business-integration
# date: 10th April 2015


import os, sys, time, gdal, fnmatch
from osgeo import osr
from gdalconst import *
import glob
import numpy
import csv
import multiprocessing

startTime = time.time()




# input parameters -------------------------------------------------------------------------------------
coord_file = '/media/neel/Num/eo_data/MODIS_GRID/MOD09Q1/Germany/Germany_mod09q1_h18v04_arable_land_point_v01_test_v02.csv'
raster_file_path = glob.glob('/media/Arc/eo_archive_proc/MOD09Q1/output/h18v03/ndvi' + '/*.tif')

# out_file = '/media/neel/Num/eo_data/MODIS_GRID/MOD09Q1/Germany/ndvi_Germany_mod09q1_h18v04_arable_land_point_v01.csv'
out_dir = '/media/neel/Num/eo_data/MODIS_GRID/MOD09Q1/Germany'




# reading the coordinate list as an arry
coord_data = numpy.genfromtxt(coord_file, dtype=None, delimiter=',', skip_header=1) #coord_data.dtype.names


def doit(coord_data, raster_file_path):
    prepare_county_list(coord_data)
    

def prepare_county_list(coord_data):
    
    krs_list = []
    
    for i in range(len(coord_data)):
        krs = coord_data[i][4]
        krs_list.append(krs)
    uniq_krs_list = list(set(krs_list))
    print uniq_krs_list

    coord_list = []
    
    for i in range(len(coord_data)):
        node_code = coord_data[i][0]
        x = float (coord_data[i][1])
        y = float (coord_data[i][2])
        mod09_tile = coord_data[i][3]
        krs = coord_data[i][4]
        out_seq = [node_code, x, y, mod09_tile, krs]
        coord_list.append(out_seq)

    all_list_name = []
 
    for i in uniq_krs_list:
        temp_list = []
        for j in range(len(coord_list)):
            if i == coord_list[j][4]:
                out_seq_1 = [coord_list[j][0], coord_list[j][1], coord_list[j][2], coord_list[j][3],coord_list[j][4]]
                temp_list.append(out_seq_1)
        all_list_name.append(temp_list)

    # print all_list_name

    for records in all_list_name:
        # print records
        # creating the output list
        output_list = []
        list_out = ['node_code', 'x', 'y', 'date', 'doy', 'ndvi', 'msavi']
        output_list.append(list_out)

        for i in range(len(records)):
            node_code = records[i][0]
            x = float (records[i][1])
            y = float (records[i][2])
            mod09 = str (records[i][3])
            krs = str (records[i][4])
            print 'data extraction started for : ' + str(x), str(y)
            modis_x, modis_y, modis_z = wgs84_to_modissinu( x, y )

            for files in raster_file_path:
                date, doy, ndvi, msavi = extract_value_from_raster(files, modis_x, modis_y)
                output_seq = [node_code, x, y, date, doy, ndvi, msavi]
                output_list.append(output_seq)
        out_file = os.path.join(out_dir, 'out_' + krs + '_' + mod09 + '.csv')
        print 'writing extraction results for  krs:   ' + out_file
        write_output(out_file, output_list)
        


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
	wgs84.ImportFromEPSG( 4326 ) # And set it to WGS84 using the EPSG code
	# Define the modis data projection, sinusoidal #sinu_modis.ImportFromEPSG( 27700)
	modis_sinu = osr.SpatialReference() 
	modis_sinu.ImportFromProj4 ( "+proj=sinu +lon_0=0 +x_0=0 +y_0=0 " + \
                      "+a=6371007.181 +b=6371007.181 " + \
                      "+units=m +no_defs" )
	# Define a coordinate transformtion object, from wgs84 to sinu_modis
	tx = osr.CoordinateTransformation(wgs84, modis_sinu)
	# Actually do the transformation using the TransformPoint method
	modis_x, modis_y, modis_z = tx.TransformPoint ( lon, lat )
	#print "converted to modis coordinate:", lon, lat, modis_x, modis_y
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
	#print "converted to wgs84 coordinate:", modis_x, modis_y, lon, lat



def write_output(out_file, output_list):
    with open(out_file, "wb") as f:
        writer = csv.writer(f)
        writer.writerows(output_list)



if __name__ == "__main__":
    doit(coord_data, raster_file_path)
    #pool = multiprocessing.Pool(processes=multiprocessing.cpu_count())
    #pool = multiprocessing.Pool(processes=1)
    #pool.map(doit(coord_data, raster_file_path))
    #pool.close()
    #pool.join()
    #print 'Using ' +str(multiprocessing.cpu_count())+' cores.'


# figure out how long the script took to run
endTime = time.time()
print 'The script took ' + str(endTime - startTime) + ' seconds'
