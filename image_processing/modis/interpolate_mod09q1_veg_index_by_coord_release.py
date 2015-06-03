#!/usr/bin/python

# Extract Ndvi data from modis Image according to Lattitude/longitude list
# Author Riazuddin Kawsar
# email: r.kawsar@spatial-business-integration
# date: 24th july 2014


import os, sys, time, gdal, fnmatch
import glob, numpy, csv
from osgeo import osr
from gdalconst import *
import pylab as plt
from scipy import interpolate
from scipy.optimize import fmin



# input parameters -------------------------------------------------------------------------------------

x = 11.377
y = 52.011
year = '2015'
tile = 'h18v03'
v_index = 'ndvi' # 'msavi', 'ndvi'





# -----------------------------------------------------------------------------------------------------
startdate = year + '001'
enddate = year + '366'
raster_file_path = '/media/Arc/eo_archive_proc/MOD09Q1/output/' + tile + '/ndvi'
startTime = time.time()
# creating the output list.
output_list = []
out_list = []
out_list_without_nan = []


def doit(v_index, x, y, raster_file_path):
    
    node_code = 'node_code'
    print 'data extraction started for : ' + str(x), str(y)
    modis_x, modis_y, modis_z = wgs84_to_modissinu( x, y )

    filelist = findfiles(raster_file_path)

    for files in filelist:
        doy, ndvi, msavi = extract_value_from_raster(files, modis_x, modis_y)
        output_seq = [node_code, x, y, doy, ndvi, msavi]
        output_list.append(output_seq)

    for i in output_list:
        data =  [i[3], i[4], i[5]]
        out_list.append(data)

    for i in output_list:
        if i[4] != 255.0 and i[4] > 0.01 and i[5] != 255.0 and i[5] > 0.01:
            data =  [i[3], i[4], i[5]]
            out_list_without_nan.append(data)
    data = numpy.asarray(out_list_without_nan)
    print data

    x = data[:,0]
    if v_index == 'ndvi':
        y = data[:,1]
    elif v_index == 'msavi':
        y = data[:,2]
    else:
        'VI index input value was not found'

    f = interpolate.interp1d(x, y, kind='linear', bounds_error=False) # linear, cubic

    xnew = numpy.arange(1.,366.)
    ynew = f(xnew)

    # a simple box smoothing filter (filter width 31)
    w = numpy.ones(15)
    # normalise
    w = w/w.sum()
    # half width
    n = len(w)/2
    # Take the linear interpolation of the LAI above as the signal linear interpolation
    x = xnew
    y = f(x)

    # where we will put the result
    z = numpy.zeros_like(y)

    # This is a straight implementation of the equation above
    for j in xrange(n,len(y)-n):
        for i in xrange(-n,n+1):
            z[j] += w[n+i] * y[j+i]
            
    plt.plot(x,y,'k--',label='y')
    plt.plot(x,z,'r',label='z')
    plt.xlim(x[0],x[-1])
    plt.legend(loc='best')
    plt.title('smoothing with filter width %d'%len(w))
    plt.show()



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
    
    return  doy_value, ndvi_value, msavi_value


def wgs84_to_modissinu ( lon, lat ):
	wgs84 = osr.SpatialReference( )
	wgs84.ImportFromEPSG( 4326 )
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


if __name__ == "__main__":
    
    doit(v_index, x, y, raster_file_path)


# figure out how long the script took to run
endTime = time.time()
print 'The script took ' + str(endTime - startTime) + ' seconds'
