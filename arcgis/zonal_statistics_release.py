#!/usr/bin/python
# Script devised for MAGIC PROJECT
# Author Riazuddin Kawsar
# email: r.kawsar@spatial-business-integration
# date: 27th April 2015
# ---------------------------------------------------------------------------


import arcpy
from arcpy import env
import os, sys, string, glob, time, fnmatch
arcpy.CheckOutExtension("spatial")



# input variable
site_name = 'Laubach'
# ----------------------------------------------------------------------------



## yyyy/mm/dd_"%I-%M-%S"
time_stamp = time.strftime("%Y%m%d_%H%M%S")
temp = "X:\\temp"
in_dir = "X:\\150301_BASF_MAGIC\\Germany\\site_specific_analysis"
in_raster_dir = os.path.join(in_dir, site_name, 'rasters')
out_raster_stat_dir = os.path.join(in_dir, site_name, 'FYPM', 'raster_stats')
in_shp_dir = os.path.join(in_dir, site_name, 'shpfiles')



def CreateDirectory(DBF_dir):
    if not os.path.exists(DBF_dir):
        os.mkdir(DBF_dir)
        print "created directory {0}".format(DBF_dir)
        

def find_shp_files(input_dir):
    toprocess = []
    for root,dir,files in os.walk(input_dir):
        for name in sorted(files):
            if fnmatch.fnmatch(name,'*.shp'):
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
        table = table.split('.')[0]
        dbf_file = os.path.join(DBF_dir, table + '.dbf')
        xml_file = os.path.join(DBF_dir, table + '.dbf.xml')
        cpg_file = os.path.join(DBF_dir, table + '.cpg')
        os.remove(dbf_file)
        os.remove(xml_file)
        os.remove(cpg_file)

        

if __name__ == "__main__":
    DBF_dir = temp + os.sep + "DBFile"
    shp_file = find_shp_files(in_shp_dir)
    rasters = find_raster_files(in_raster_dir)
    zoneField = "field_name"
    CreateDirectory(DBF_dir)

    for i in shp_file:
        for j in rasters:
            
            name =  os.path.basename(j)
            date = name.split('_')[2]
            date = date[0:8]
            day = date[0:2]
            month = date[3:5]
            year = date[6:8]
            date = day + month + year
            band = name.split('_')[1]
            ZonalStasAsTable(i,DBF_dir,j,band,date,zoneField)

    zstat_table = DBF_dir + os.sep + "Site_{0}_zonalstat.dbf".format(site_name)
    MergeTables(DBF_dir,zstat_table)

'''

'''
