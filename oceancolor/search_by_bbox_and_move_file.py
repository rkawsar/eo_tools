#!/usr/bin/env python
# Riazuddin Kawsar
# 9th March 2015

# bounding box
# bbox = left,bottom,right,top
# bbox = min Longitude , min Latitude , max Longitude , max Latitude
# OR bbbox = south Latitude, north Latitude, west Longitude, east Longitude
lim_euro_coast = [ -26, 30, 57, 72 ]
# ['-80.42581177', '-27.22232819', '-54.37218857', '-6.238492012']


import os, fnmatch, bz2, fnmatch
from osgeo import gdal

in_dir = '/media/Arc/oceancolor_data/L2_sst_untar'
euro_coasts_dir = '/media/Arc/oceancolor_data/euro_coasts'


# check if the image intersect with the bounding box limit
def check_bbox_intersect(bbox1, bbox2):
     xmin1, xmax1, ymin1, ymax1 = float(bbox1[0]), float(bbox1[1]), float(bbox1[2]), float(bbox1[3])
     xmin2, xmax2, ymin2, ymax2 = float(bbox2[0]), float(bbox2[1]), float(bbox2[2]), float(bbox2[3])
     xdist = abs( (xmin1 + xmax1) / 2.0 - (xmin2 + xmax2) / 2.0 )
     ydist = abs( (ymin1 + ymax1) / 2.0 - (ymin2 + ymax2) / 2.0 )
     xwidth = (xmax1 - xmin1 + xmax2 - xmin2) / 2.0
     ywidth = (ymax1 - ymin1 + ymax2 - ymin2) / 2.0
     out = str((xdist <= xwidth) and (ydist <= ywidth))
     return out



for(dirpath,dirnames,files)in os.walk(in_dir):
     for file in files:
          filepath = os.path.join(dirpath,file)

          hdf_file = gdal.Open(filepath,gdal.GA_ReadOnly)
          metadata = hdf_file.GetMetadata()

          min_lon = metadata['geospatial_lon_min']
          min_lat = metadata['geospatial_lat_min']
          max_lon = metadata['geospatial_lon_max']
          max_lat = metadata['geospatial_lat_max']
          img_bbbox = [min_lon, min_lat, max_lon, max_lat]
          #print img_bbbox

          check_result = check_bbox_intersect(lim_euro_coast, img_bbbox)
          if check_result == 'True':
               sst_type = file.split('_')[-1]
               new_filepath = os.path.join(euro_coasts_dir, sst_type, file)
               print 'moving file ' + file
               os.rename(filepath, new_filepath) 


               
