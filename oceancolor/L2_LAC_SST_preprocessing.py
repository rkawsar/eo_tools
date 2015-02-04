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




# function to generate nodecode from lattitude and longitude
def code_node_code(lat, lon):
  
  lat_p = "%03d" % (abs(lat))
  lat_l = str(lat).split(".")[1]
  lon_p = "%03d" % (abs(lon))
  lon_l = str(lon).split(".")[1]

  if lat > 0:
    lat_code = 'W' + lat_p + '.' + lat_l
  else:
    lat_code = 'E' + lat_p + '.' + lat_l

  if lon < 0:
    lon_code = 'N' + lon_p + '.' + lon_l
  else:
    lon_code = 'S' + lon_p + '.' + lon_l

  node_code = lat_code + '_' + lon_code
  print node_code
  return node_code
  




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
  out_dataset_name = ff_name + '_' + node_code + '_' + DayOrNight
  print out_dataset_name
  

  # Scaling and NaN values
  sst_nan = float(ds_sst.GetMetadataItem('bad_value_scaled'))
  sst_intercept = float(ds_sst.GetMetadataItem('intercept'))
  sst_slope = float(ds_sst.GetMetadataItem('slope'))
  # Create mask
  mask = sst == sst_nan
  # Scale values
  sst = sst_intercept + sst_slope * sst
  # Apply mask
  sst[mask] = np.nan

  # free datasets
  ds_lon, ds_lat, ds_sst, ds_quality = None, None, None, None

  return lats, longs, sst, quality






lats, longs, sst, quality = return_sst_band_arrays(hdf_file)
gdal_dtype = gdal.GDT_Float32
out_fn = '/media/Num/eo_tools/testData/raster/foo.tif'
driver_name = 'GTiff'
resolution_out = 1000
ncols = sst.shape[1]
nrows = sst.shape[0]
n_px = ncols * nrows
ul_x = longs.min()
ul_y = lats.max()



# Define projections (from and to)
wgs84 = osr.SpatialReference()
wgs84.ImportFromEPSG(4326)
polar = osr.SpatialReference()
polar.ImportFromEPSG(3031)

#
# ## Create SST daatset in memory
# mem = gdal.GetDriverByName( 'MEM' )
# ds_sst = mem.Create('', ncols, nrows, 1, gdal_dtype)
# ds_sst.SetGeoTransform( (ul_x, 0.01, 0, ul_y, 0, 0.01) )
# # Select output band
# band_sst = ds_sst.GetRasterBand(1)
# # Write array into output band
# band_sst.WriteArray(sst)
# # Set NoData value
# band_sst.SetNoDataValue(np.nan)
# # Set projection of output raster
# ds_sst.SetProjection( wgs84.ExportToWkt() )
#
# ## REPROJECT DATA TO EPSG:3031
# tx = osr.CoordinateTransformation (wgs84, polar)
#
# # GeoTransform vector of SST data
# gt = [ float(x) for x in (ul_x, 0.01, 0, ul_y, 0, 0.01) ]
# # Work out the boundaries of the new dataset in the target projection
# (ulx, uly, ulz ) = tx.TransformPoint( gt[0], gt[3] )
# (lrx, lry, lrz ) = tx.TransformPoint( gt[0] + gt[1] * ncols, gt[3] + gt[5] * nrows )
#
# # Now, we create an in-memory raster
# driver = gdal.GetDriverByName( driver_name )
# # The size of the raster is given the new projection and pixel spacing
# # Using the values we calculated above. Also, setting it to store one band
# # and to use Float32 data type.
# ds_out = driver.Create(out_fn, int( abs(lrx - ulx) / resolution_out ), int( abs(uly - lry) / resolution_out ), 1, gdal_dtype )
# # Calculate the new geotransform
# out_gt = ( ulx, resolution_out, gt[2], uly, gt[4], -resolution_out )
# # Set the geotransform
# ds_out.SetGeoTransform( out_gt )
# ds_out.SetProjection ( polar.ExportToWkt() )
# # Perform the projection/resampling
# res = gdal.ReprojectImage( ds_sst, ds_out, wgs84.ExportToWkt(), polar.ExportToWkt(), gdal.GRA_Bilinear )
#




'''

imgplot2 = plt.imshow(quality)
plt.show()
'''

def output_file(output_name,output_array):
    format = "GTiff"
    driver = gdal.GetDriverByName( format )
    outDataset = driver.Create(output_name, ncols, nrows, 1, GDT_Int16)
    outBand = outDataset.GetRasterBand(1)
    outBand.WriteArray(output_array,0,0)
    outBand.FlushCache()
    outBand.SetNoDataValue(0)
    out.SetGeoTransform( (ul_x, 0.01, 0, ul_y, 0, 0.01) )
    out.SetProjection( wgs84.ExportToWkt() )


#output_file(out_fn, sst)

'''
## WRITE FILE

# Get driver
driver = gdal.GetDriverByName('GTiff')
# Create output raster file
out = driver.Create(out_fn, ncols, nrows, 1, gdal_dtype)
# Set the affine transformation coefficients
print ul_x, ul_y, ncols, nrows
out.SetGeoTransform( (ul_x, 0.01, 0, ul_y, 0, 0.01) )
# Select output band
outband = out.GetRasterBand(1)
# Write array into output band
outband.WriteArray(sst)
# Set NoData value
outband.SetNoDataValue(np.nan)
# Set projection of output raster
out.SetProjection( wgs84.ExportToWkt() )
# Flush cache
outband.FlushCache()
'''
