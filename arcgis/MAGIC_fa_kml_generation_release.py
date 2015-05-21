#!/usr/bin/python
# Script devised for MAGIC PROJECT
# Author Riazuddin Kawsar
# email: r.kawsar@spatial-business-integration
# date: 18th may 2015
# ---------------------------------------------------------------------------

import arcpy
import os, time


# Aschersleben, Dohndorf, Elmshorn, Grossalsleben, Laubach
# Lechfeld, Mannheim, Oschersleben, Straubing, Wittingen

# input variable
site_name = 'Lechfeld'
mxd_type = 'FA'       # FA, FA_SG
#crop_code = 'ww'



# ----------------------------------------------------------------------------
mxd_name = site_name + '_v01_' + mxd_type + '.mxd'
t1 = time.time()
# MXD file locaiton:
in_dir = "X:\\150301_BASF_MAGIC\\Germany\\site_specific_analysis"
input_mxd = os.path.join(in_dir, site_name,mxd_name )
output_path = os.path.join(in_dir, site_name, 'FA')


# All Fields
mxd = arcpy.mapping.MapDocument(input_mxd)
alldf = arcpy.mapping.ListDataFrames(mxd, "")


for dataframe in alldf:
    
    if dataframe.name != 'All Fields':
        print 'Preparing KmZ files for ' + dataframe.name + ' field'
        if mxd_type == 'FA':
            out_kmz = os.path.join(output_path, dataframe.name)
            out_kmz = out_kmz + ".kmz"
        elif mxd_type == 'FA_SG':
            out_kmz = os.path.join(output_path, 'SG_KMZ', dataframe.name)
            out_kmz = out_kmz + ".kmz"
        else:
            print 'MXD file is not found'
            
        if os.path.exists(out_kmz):
            arcpy.Delete_management(out_kmz)
            
        arcpy.MapToKML_conversion(input_mxd, dataframe.name, out_kmz,"0", "NO_COMPOSITE", "VECTOR_TO_IMAGE", "DEFAULT", "1024", "150", "CLAMPED_TO_GROUND")

print 'Processing COMPLETED ...'
t2 = time.time()
print 'Processing Finished and it took: ' + str((t2-t1)/60) + ' min'


