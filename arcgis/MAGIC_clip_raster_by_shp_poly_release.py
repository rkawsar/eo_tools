#!/usr/bin/python
# -*- coding: cp1252 -*-
# Script devised for MAGIC PROJECT
# Author Riazuddin Kawsar
# email: r.kawsar@spatial-business-integration
# date: 21th May 2015
# ---------------------------------------------------------------------------


import arcpy
import os, time
import fnmatch
import subprocess


# Aschersleben, Dohndorf, Elmshorn, Grossalsleben, Laubach
# Lechfeld, Mannheim, Oschersleben, Straubing, Wittingen


# input variable ------------------------------------------------------------
site_name = 'Lechfeld'
# crop_code = 'ww'
#product = 'fypm'



# ----------------------------------------------------------------------------
t1 = time.time()
# parmanent for MAGIC 3 project
project_path = "X:\\150301_BASF_MAGIC\\Germany\\site_specific_analysis"
in_shp = "X:\\150301_BASF_MAGIC\\Germany\\shpfile\\Germany_all_fields_v01_wgs84.shp"
site_path = os.path.join(project_path, site_name)
in_rst_path = os.path.join(project_path, site_name, 'rasters')



def find_rst_files(in_rst_dir):
    toprocess = []
    rst_pattern = '*_wgs84_*.tif'
    for root,dir,files in os.walk(in_rst_dir):
        for name in sorted(files):
            if fnmatch.fnmatch(name, rst_pattern):
                toprocess.append( os.path.join(root, name) )
    return toprocess


def raster_clip():
    
    raster_list = find_rst_files(in_rst_path)
    
    print 'Slecting shpfiles ... '
    whereClause_site = "site ='%s'" % site_name
    #user selects tract, Select by Attribute tool runs
    arcpy.MakeFeatureLayer_management(in_shp, "field_boundaries")
    arcpy.SelectLayerByAttribute_management ("field_boundaries", "NEW_SELECTION", whereClause_site)


    for raster in raster_list:

        # Create search cursor
        rows = arcpy.SearchCursor("field_boundaries")
        # Create a list of string fields
        fields = arcpy.ListFields("field_boundaries", "", "String")
        
        for row in rows:
            for field in fields:
                if field.name == 'field_name':
                    field_name = row.getValue("field_name")
                    feat = row.Shape
                    
                    out_rst_path = os.path.join(site_path, 'FA', field_name, 'rasters')
                    if not os.path.exists(out_rst_path):
                        os.makedirs(out_rst_path)

                    rst_name = os.path.basename(raster)
                    rst_name = rst_name.split('.tif', 1)[0]
                    image_date = rst_name.split('_', 1)[1]

                    out_rst_name = os.path.join(out_rst_path, field_name + '_' + image_date + '.tif')
                    if os.path.exists(out_rst_name):
                        arcpy.Delete_management(out_rst_name)

                    print 'cliping {0} with {1} ...'.format(rst_name, field_name)
                    arcpy.Clip_management(raster, "#", out_rst_name, feat, "255", "ClippingGeometry")



if __name__ == "__main__":
    raster_clip()
    t2 = time.time()
    print 'Processing Finished and it took: ' + str((t2-t1)/60) + ' min'

