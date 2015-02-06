#!/usr/bin/env python
# Riazuddin Kawsar
# 5th Feb 2015


import os
from osgeo import gdal
from osgeo import osr
import matplotlib.pyplot as plt
import numpy as np

# def array2raster(newRasterfn,rasterOrigin,pixelWidth,pixelHeight,array):
#   cols = array.shape[1]
#   rows = array.shape[0]
#   originX = rasterOrigin[0]
#   originY = rasterOrigin[1]
#   driver = gdal.GetDriverByName('GTiff')
#   outRaster = driver.Create(newRasterfn, cols, rows, 1, gdal.GDT_Byte)
#   outRaster.SetGeoTransform((originX, pixelWidth, 0, originY, 0, pixelHeight))
#   outband = outRaster.GetRasterBand(1)
#   outband.WriteArray(array)
#   outRasterSRS = osr.SpatialReference()
#   outRasterSRS.ImportFromEPSG(4326)
#   outRaster.SetProjection(outRasterSRS.ExportToWkt())
#   outband.FlushCache()



hdf_file = '/media/Num/eo_tools/testData/raster/A2014001000000.L2_LAC_SST'
out_sst = '/media/Num/eo_tools/testData/raster/sst.tif'



# function to generate nodecode from lattitude and longitude
def code_node_code(lat, lon):

    if lon > 180 or lon < -180:
        print ' Longitude out of range ...'
        sys.exit(1)

    if lat > 90 or lat < -90:
        print ' latitude out of range ...'
        sys.exit(1)

    lat_p = "%02d" % (abs(lat))
    lat_t = format(lat, '.3f')
    lat_l = str(lat_t).split(".")[1]
    lon_p = "%03d" % (abs(lon))
    lon_t = format(lon, '.3f')
    lon_l = str(lon_t).split(".")[1]

    if lat > 0:
        lat_code = 'N' + lat_p + '.' + lat_l
    elif lat == 0:
        lat_code = 'N' + lat_p + '.' + lat_l
    else:
        lat_code = 'S' + lat_p + '.' + lat_l

    if lon > 0:
        lon_code = 'E' + lon_p + '.' + lon_l
    elif lon == 0:
        lon_code = 'E' + lon_p + '.' + lon_l
    else:
        lon_code = 'W' + lon_p + '.' + lon_l

    node_code =  lon_code + '_' +  lat_code

    #print node_code
    return node_code
  



# function to generate nodecode from lattitude and longitude
def decode_node_code(node_code):

    if node_code[9:10] =='N':
        lat = float(node_code[10:16])    
    else:
        lat = '-' + node_code[10:16]
        lat = float(lat)

    if node_code[:1] =='E':
        lon = float(node_code[1:8])
    else:
        lon = '-' + node_code[1:8]
        lon = float(lon)

    print lat, lon
    return lat, lon





def return_sst_band_arrays(hdf_file):
  
  ff_name = os.path.basename(hdf_file)
  ff_name = os.path.splitext(ff_name)[0]
  
  hdf_file = gdal.Open(hdf_file,gdal.GA_ReadOnly)
  subdatasets = hdf_file.GetSubDatasets()
  variables = []
  for subdataset in subdatasets:
    variables.append(subdataset[1].split(" ")[1])
  print 'available layers: ' + str(variables)


  print 'reading longitude, latitude sst and qual_sst layers ...'
  ds_lon = gdal.Open(subdatasets[0][0])
  ds_lat = gdal.Open(subdatasets[1][0])
  ds_sst = gdal.Open(subdatasets[2][0])
  ds_quality = gdal.Open(subdatasets[3][0])

  geo_transform = ds_sst.GetGeoTransform ()
  print geo_transform
  print ds_sst.RasterXSize, ds_sst.RasterYSize


  print 'coverting layers into numpy arrays ...'
  longs = ds_lon.GetRasterBand(1).ReadAsArray()
  lats = ds_lat.GetRasterBand(1).ReadAsArray()
  sst = ds_sst.GetRasterBand(1).ReadAsArray()
  quality = ds_quality.GetRasterBand(1).ReadAsArray()


  print 'extracting meatadata ... '
  metadata = hdf_file.GetMetadata()
  DayOrNight = metadata['Day or Night'][0:1]
  lat = (round(float(metadata['Scene Center Latitude']), 3))
  lon = (round(float(metadata['Scene Center Longitude']), 3))
  node_code = code_node_code(lat, lon)
  out_dataset_name = ff_name + '_' + DayOrNight + '_' + node_code 
  print out_dataset_name
  

  print 'Scaling and adjusting NaN values...'
  sst_nan = float(ds_sst.GetMetadataItem('bad_value_scaled'))
  sst_intercept = float(ds_sst.GetMetadataItem('intercept'))
  sst_slope = float(ds_sst.GetMetadataItem('slope'))

  # Create NoData value mask
  mask = sst == sst_nan
  qual_mask_4 = quality == 4 # 0 = best, 1 = good, 2 = questionable quality
  qual_mask_3 = quality == 3

  # Scale values
  sst = sst_intercept + sst_slope * sst
  
  # Apply mask
  sst[mask] = np.nan
  sst[qual_mask_4] = np.nan
  sst[qual_mask_3] = np.nan
  #sst[np.isnan(sst)] = -9999

  ul_x = longs.min()
  ul_y = lats.max()
  #geotransform = (upperleft_x, pixelsize, rotation, upperleft_y, pixelsize, rotation)
  geoTransform = (ul_x, 0.011, 0, ul_y, 0, -0.011)
  ncols = sst.shape[1]
  nrows = sst.shape[0]

  ds_lon, ds_lat, ds_sst, ds_quality = None, None, None, None
  mask, qual_mask_4, qual_mask_3 = None, None, None

  return sst, quality, geoTransform, ncols, nrows




def output_file(output_name,output_array):
  
    driver = gdal.GetDriverByName("GTiff")
    outDataset = driver.Create(output_name, ncols, nrows, 1, gdal.GDT_Float32)
    
    outBand = outDataset.GetRasterBand(1)
    outBand.WriteArray(output_array,0,0)
    
    outBand.SetNoDataValue(np.nan)

    outDataset.SetGeoTransform(geoTransform)

    wgs84 = osr.SpatialReference()
    wgs84.ImportFromEPSG(4326)
    outDataset.SetProjection(wgs84.ExportToWkt())
    outBand.FlushCache()




sst, quality, geoTransform, ncols, nrows = return_sst_band_arrays(hdf_file)
output_file(out_sst, sst)



'''

imgplot2 = plt.imshow(quality)
plt.show()
'''
