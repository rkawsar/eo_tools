#!/usr/bin/python
# Script devised for MAGIC PROJECT
# Author Riazuddin Kawsar
# email: r.kawsar@spatial-business-integration
# date: 18th may 2015
# ---------------------------------------------------------------------------


# Import system modules
import arcpy
from arcpy import env
from arcpy.sa import *
import os, sys, string, glob, time, fnmatch
arcpy.CheckOutExtension("spatial")
arcpy.env.workspace = 'X:\\WORKSPACE'
#arcpy.env.overwriteOutput = True


# Aschersleben, Dohndorf, Elmshorn, Grossalsleben, Laubach
# Lechfeld, Mannheim, Oschersleben, Straubing, Wittingen

# input variable
site_name = 'Laubach'
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
t1 = time.time()
time_stamp = time.strftime("%Y%m%d_%H%M%S")
wrk_dir = 'X:\\WORKSPACE'
wrk_Geodatabase = 'X:\\WORKSPACE\\wrk_Geodatabase.gdb'
in_dir = "X:\\150301_BASF_MAGIC\\Germany\\site_specific_analysis"
in_raster_dir = os.path.join(in_dir, site_name, 'rasters')
in_shp_dir = "X:\\150301_BASF_MAGIC\\Germany\\shpfile"
out_raster_stat_dir = os.path.join(in_dir, site_name, 'FYPM', 'raster_stats')



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


# Description: Converts a raster dataset to point features.
def raster_to_point(in_raster, in_shp):
    
    out_point = os.path.basename(in_raster)
    out_point = out_point.split('_')[0]
    cliped_raster = os.path.join(wrk_dir,'rasters', out_point + '_clip.tif')
    out_point = os.path.join(wrk_Geodatabase, out_point + '_points')
    #out_point = out_point.replace('X', 'C')
    print out_point
    
    if os.path.exists(cliped_raster):
        arcpy.Delete_management(cliped_raster)
    if os.path.exists(out_point):
        arcpy.Delete_management(out_point)
        
    print 'Clipping Raster Dataset with feature geometry...'
    arcpy.Clip_management(in_raster, "#", cliped_raster, in_shp, "0", "ClippingGeometry")
    
    print 'Executeing RasterToPoint conversion...'
    field = "VALUE"
    arcpy.RasterToPoint_conversion(cliped_raster, out_point, field)
    arcpy.Delete_management(cliped_raster)

    return out_point



def extract_multiValues_to_points(raster_list, in_shp):
    
    list_to_process = []
    for i in raster_list:
        name = os.path.basename(i)
        date = name.split('_')[2]
        date = date[0:8]
        day = date[0:2]
        month = date[3:5]
        date = day + month
        band = name.split('_')[1]
        name = band + '_' + date
        x = i + ' ' + name + ';'
        list_to_process.append(x)
    list_to_process = ''.join(list_to_process)

    print 'Execute ExtractValuesToPoints ....'
    ExtractMultiValuesToPoints(in_shp, list_to_process, "NONE")





def calculate_vi_index(in_shp):

    # Execute AddField
    fieldList = arcpy.ListFields(in_shp)
    field_name_list = []
    band_list = []
    date_list = []
    for field in fieldList:
        if fnmatch.fnmatch(field.name, 'B*'):
            name = field.name
            band = name.split('_')[0]
            date = name.split('_')[1]
            field_name_list.append(name)
            band_list.append(band)
            date_list.append(date)

    field_name_list = set(field_name_list)
    band_list = set(band_list)
    date_list = set(date_list)
    
    # field.type, field.length
    for date in date_list:
        print 'Started VI computation for date ...' + date
        for field in fieldList:
            if fnmatch.fnmatch(field.name, 'B*'):


                if fnmatch.fnmatch(field.name.split('_')[1], date):
                    if fnmatch.fnmatch(field.name, 'B1_*'):
                        blue = field.name
                    elif fnmatch.fnmatch(field.name, 'B2_*'):
                        green = field.name
                    elif fnmatch.fnmatch(field.name, 'B3_*'):
                        red = field.name
                    elif fnmatch.fnmatch(field.name, 'B4_*'):
                        re = field.name
                    elif fnmatch.fnmatch(field.name, 'B5_*'):
                        nir = field.name

                        
                        

                        print 'Available Bands are Blue: {0}, green: {1}, red: {2}, re: {3}, nir: {4}'.format(blue, green, red, re, nir)
                        time_stamp = red.split('_')[1]
                        nn = float(1.0)
                        ndvi_field_name = 'nd_' + time_stamp
                        sipi_field_name = 'si_' + time_stamp
                        chl_field_name = 'ch_' + time_stamp
                        msavi_field_name = 'ms_' + time_stamp
                        
                        ndvi_expression = "( !" + nir + "! - !" + red + "! ) /( !" + nir + "! + !" + red + "! )"
                        sipi_expression = "( !" + nir + "! - !" + blue + "! ) /( !" + nir + "! - !" + red + "! )"
                        chl_expression = "(( !" + nir + "! / !" + re + "!) - 1)"
                        msavi_expression = "0.5*(2*!" +nir+ "!+1-math.sqrt(math.pow((2*!" +nir+ "!+1),2 )-8*(!" +nir+ "!-!"+red+"!)))"

                        print 'Computing NDVI ..'
                        arcpy.AddField_management(in_shp, '' + ndvi_field_name + '', "DOUBLE", "","","","","NULLABLE","NON_REQUIRED","")
                        arcpy.CalculateField_management(in_shp, '' + ndvi_field_name + '', ndvi_expression, "PYTHON")

                        print 'Computing SIPI ..'
                        arcpy.AddField_management(in_shp, '' + sipi_field_name + '', "DOUBLE", "","","","","NULLABLE","NON_REQUIRED","")
                        arcpy.CalculateField_management(in_shp, '' + sipi_field_name + '', sipi_expression, "PYTHON")

                        print 'Computing CHL ..'
                        arcpy.AddField_management(in_shp, '' + chl_field_name + '', "DOUBLE", "","","","","NULLABLE","NON_REQUIRED","")
                        arcpy.CalculateField_management(in_shp, '' + chl_field_name + '', chl_expression, "PYTHON")

                        print 'Computing MSAVI ..'
                        arcpy.AddField_management(in_shp, '' + msavi_field_name + '', "DOUBLE", "","","","","NULLABLE","NON_REQUIRED","")
                        arcpy.CalculateField_management(in_shp, '' + msavi_field_name + '', msavi_expression, "PYTHON")


def field_mapping(in_shp):
    
    field_patterns = ['field_*', 'crop', 'B*', 'nd_*', 'si_*', 'ch_*', 'ms_*' ]
    fieldmap = []
    fieldList = arcpy.ListFields(in_shp)
    
    # POINTID \"POINTID\" true true false 6 Long 0 6 ,First,#,elmshorn_points,POINTID,-1,-1;
    for field in fieldList:
        for patterns in field_patterns:
            if fnmatch.fnmatch(field.name, patterns):
                x = field.name+' \"'+field.name+'\"'+' true'+' true'+' false '+str(field.length)+' '+ field.type + ' 0 0 ' + ',First,#,'+in_shp+','+field.name+',-1,-1'
                fieldmap.append(x)
    
    return fieldmap
 


def poly_point_intersect(in_poly, in_point, out_point):

    fieldmap_poly = field_mapping(in_poly)
    fieldmap_point = field_mapping(in_point)
    fieldmap = fieldmap_poly + fieldmap_point
    fieldmap = set(fieldmap)
    fieldmapping = ';'.join(fieldmap)
    #print fieldmapping

    print 'Executing Spatial Join Field Boundary and Raster Points .....'
    arcpy.SpatialJoin_analysis(in_point, in_poly, out_point, "JOIN_ONE_TO_ONE", "KEEP_ALL", fieldmapping, "INTERSECT", "", "")


def generate_field_stat(in_shp, out_dbf):
    
    vi_patterns = ['B*', 'nd_*', 'si_*', 'ch_*', 'ms_*' ]
    fieldmap = []
    fieldList = arcpy.ListFields(in_shp)
    
    for field in fieldList:
        for patterns in vi_patterns:
            if fnmatch.fnmatch(field.name, patterns):
                i_mean = field.name + ' ' + 'MEAN'
                i_max = field.name + ' ' + 'MAX'
                i_min = field.name + ' ' + 'MIN'
                i_std = field.name + ' ' + 'STD'
                fieldmap.extend((i_mean, i_max, i_min, i_std))
    
    fieldmap = set(fieldmap)
    fieldmapping = ';'.join(fieldmap)
    print 'Gathering Field Statistics ....'
    arcpy.Statistics_analysis(in_shp, out_dbf, fieldmapping, "field_name;crop;field_id")




if __name__ == "__main__":

    # gather the raster files in a list
    raster_list = find_raster_files(in_raster_dir)
    
    # gather shpfiles in a list and find the field boundaries
    shp_file = find_shp_files(in_shp_dir, site_name, utm_zones)

    for i in shp_file:
        print 'Clipping shpfiles ... ' + i
        whereClause_site = "site ='%s'" % site_name
        whereClause_crop = "crop_id ='%s'" % crop_code
        #user selects tract, Select by Attribute tool runs
        arcpy.MakeFeatureLayer_management(i, "field_boundaries")
        arcpy.SelectLayerByAttribute_management ("field_boundaries", "NEW_SELECTION", whereClause_site)
        arcpy.SelectLayerByAttribute_management("field_boundaries", "SUBSET_SELECTION", whereClause_crop)

        # define the raster point output file
        out_spatial_join_point = os.path.join(in_dir, site_name, shpfiles)
        out_spatial_join_point = out_spatial_join_point + '_' + site_name + '_' + crop_code + '_points.shp'
        if os.path.exists(out_spatial_join_point):
            arcpy.Delete_management(out_spatial_join_point)

        # convert the raster (1st one from the raster_list)
        raster_points = raster_to_point(raster_list[0], "field_boundaries")

        # executing extract_multiValues_to_points which will populate the raster_points attributes
        extract_multiValues_to_points(raster_list, raster_points)

        # do some attribute calculation....
        calculate_vi_index(raster_points)
        
        #Executing the spatial join....
        poly_point_intersect("field_boundaries", raster_points, out_spatial_join_point)

        # deleting the files....
        arcpy.Delete_management(raster_points)

        # Gathering Field Statistics ....
        field_stat_out_name = os.path.basename(out_spatial_join_point).split('.')[0]
        field_stat_out_name = os.path.join(out_raster_stat_dir, field_stat_out_name + '.dbf')
        if os.path.exists(field_stat_out_name):
            arcpy.Delete_management(field_stat_out_name)
        generate_field_stat(out_spatial_join_point, field_stat_out_name)

    t2 = time.time()
    print 'Processing Finished and it took: ' + str((t2-t1)/60) + ' min'

