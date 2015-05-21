#!/usr/bin/python
# Script devised for MAGIC PROJECT
# Author Riazuddin Kawsar
# email: r.kawsar@spatial-business-integration
# date: 18th May 2015
# ---------------------------------------------------------------------------


import arcpy
from arcpy import env
import os, sys, string, glob, time, fnmatch
arcpy.CheckOutExtension("spatial")


# Aschersleben, Dohndorf, Elmshorn, Grossalsleben, Laubach
# Lechfeld, Mannheim, Oschersleben, Straubing, Wittingen



# input variable
site_name = 'Elmshorn'
crop_code = 'ww'


# ----------------------------------------------------------------------------

utm_zones = {'asc':'utm32',
             'don':'utm32',
             'elm':'utm32',
             'gro':'utm32',
             'lau':'utm32',
             'lec':'utm32',
             'man':'utm32',
             'osc':'utm32',
             'str':'utm33',
             'wit':'utm32'}

## yyyy/mm/dd_"%I-%M-%S"
time_stamp = time.strftime("%Y%m%d_%H%M%S")
temp = "X:\\temp"
in_dir = "X:\\150301_BASF_MAGIC\\Germany\\site_specific_analysis"
in_raster_dir = os.path.join(in_dir, site_name, 'rasters')
out_raster_stat_dir = os.path.join(in_dir, site_name, 'FYPM', 'raster_stats')
in_shp_dir = "X:\\150301_BASF_MAGIC\\Germany\\shpfile"



def CreateDirectory(DBF_dir):
    if not os.path.exists(DBF_dir):
        os.mkdir(DBF_dir)
        print "created directory {0}".format(DBF_dir)
        

def find_shp_files(in_shp_dir, site_name, utm_zones):
    toprocess = []
    
    site_code = (site_name.lower())[0:3]
    zone = utm_zones.get(str(site_code),"None")
    shp_pattern = '*_' + zone + '.shp'

    for root,dir,files in os.walk(in_shp_dir):
        for name in sorted(files):
            if fnmatch.fnmatch(name, shp_pattern):
                toprocess.append( os.path.join(root, name) )
    return toprocess


def find_raster_files(input_dir):
    toprocess = []
    for root,dir,files in os.walk(input_dir):
        for name in sorted(files):
            if fnmatch.fnmatch(name,'*_B*.tif'):
                toprocess.append( os.path.join(root, name) )
    return toprocess

 
def ZonalStasAsTable(fc,DBF_dir,raster,band,date,zoneField):
    tempTable = DBF_dir + os.sep + "stat_{0}_{1}.dbf".format(band,date)
    print "Calculating Raster stat for Band {0} and Date {1}...".format(band,date)
    arcpy.gp.ZonalStatisticsAsTable_sa(fc, zoneField, raster, tempTable, "DATA", "ALL")                              

        
def MergeTables(DBF_dir,zstat_table):
    arcpy.env.workspace = DBF_dir
    tableList = arcpy.ListTables()
    
    for table in tableList:
        date = table.split('_')[-1]
        date = date.split('.')[0]
        band = table.split('_')[1]
        print "Creating and populating Fields for Band {0} and Date {1}...".format(band,date)

        # add new fields to the *.dbf tables
        arcpy.AddField_management(table, "Band", "TEXT", "", "", "100")
        arcpy.AddField_management(table, "date", "TEXT", "", "", "100")
        # populate the fields
        arcpy.CalculateField_management(table, "date", '"' + date + '"',"PYTHON")
        arcpy.CalculateField_management(table, "Band", '"' + band + '"',"PYTHON")

    arcpy.Merge_management(tableList,zstat_table)
    print "Merged tables. Final zonalstat table {0} created. Located at {1}".format(zstat_table,DBF_dir)

    # remove all the intermediate files
    for table in tableList:
        arcpy.Delete_management(table, "")



if __name__ == "__main__":
    DBF_dir = temp + os.sep + "DBFile"
    shp_file = find_shp_files(in_shp_dir, site_name, utm_zones)
    print shp_file
    site_code = (site_name.lower())[0:3]
    rasters = find_raster_files(in_raster_dir)
    zoneField = "field_id"
    CreateDirectory(DBF_dir)
    
    for i in shp_file:
        print 'Clipping shpfiles ... ' + i
        whereClause_site = "site ='%s'" % site_name
        whereClause_crop = "crop_id ='%s'" % crop_code
        #user selects tract, Select by Attribute tool runs
        arcpy.MakeFeatureLayer_management(i, "lyr")
        arcpy.SelectLayerByAttribute_management ("lyr", "NEW_SELECTION", whereClause_site)
        arcpy.SelectLayerByAttribute_management("lyr", "SUBSET_SELECTION", whereClause_crop)
        
        for j in rasters:
            
            name =  os.path.basename(j)
            date = name.split('_')[2]
            date = date[0:8]
            day = date[0:2]
            month = date[3:5]
            year = date[6:8]
            date = day + month + year
            band = name.split('_')[1]
            ZonalStasAsTable("lyr",DBF_dir,j,band,date,zoneField)

    zstat_table = DBF_dir + os.sep + "Site_{0}_{1}_zonalstat.dbf".format(site_name, crop_code)
    MergeTables(DBF_dir,zstat_table)
    
    zstat_table_name = os.path.basename(zstat_table)
    zstat_table_xml_name = zstat_table + '.xml'
    zstat_table_xml_name_1 = zstat_table_name + '.xml'
    zstat_table_new_xml_name = os.path.join(out_raster_stat_dir, zstat_table_xml_name_1)
    zstat_table_new_name = os.path.join(out_raster_stat_dir, zstat_table_name)
    if os.path.exists(zstat_table_new_name):
        os.remove(zstat_table_new_name)
        print 'deleting old *.dbf files'
    if os.path.exists(zstat_table_new_xml_name):
        print 'deleting old *.xml files'
        os.remove(zstat_table_new_xml_name)
    os.rename(zstat_table, zstat_table_new_name)
    os.rename(zstat_table_xml_name, zstat_table_new_xml_name)
    # Execute Copy
    # arcpy.Copy_management(in_data, out_data, data_type)

