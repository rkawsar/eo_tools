#!/usr/bin/env python
# Riazuddin Kawsar
# 9th Feb 2015

# unzip the downlodeded file and rename the raster files as per 'SST' and 'NSST'
# and removing the *.bz2 files

import os, fnmatch, bz2, fnmatch
from osgeo import gdal


input_dir = '/media/Arc/oceancolor_data/L2_sst_untar'

for(dirpath,dirnames,files)in os.walk(input_dir):
    
    for file in files:
        if fnmatch.fnmatch(file,'*SST.bz2'):
            filepath = os.path.join(dirpath,file)
            print filepath
            
            zipfile = bz2.BZ2File(filepath)
            data = zipfile.read()
            newfilepath = filepath[:-7]
            open(newfilepath, 'wb').write(data)
            
            hdf_file = gdal.Open(newfilepath,gdal.GA_ReadOnly)
            metadata = hdf_file.GetMetadata()
            DayOrNight = metadata['Day or Night'][0:1]

            if DayOrNight =='N':
                new_newfilepath = newfilepath + 'NSST'
            elif DayOrNight =='M':
                new_newfilepath = newfilepath + 'MSST'
            else:
                new_newfilepath = newfilepath + 'SST'
            print new_newfilepath
                
            os.rename(newfilepath, new_newfilepath)
            os.remove(filepath)
