
# Stratified random sampling script
# source: http://arizona.openrepository.com/arizona/bitstream/10150/311667/1/azu_etd_13118_sip1_m.pdf

import arcpy
arcpy.CheckOutExtension("spatial")

#This run number eliminates the need to go back and delete files if executing this script multiple times
rr = raw_input("Give this run a number")
r = str(rr)
print "This is now run " + r
raw_input("Press enter to continue")

#Reset these parameters accordingly. Remember to use \\ instead of \ in file paths
#base directory, needs an "outputs" folder and a "scratch" folder and a "final_merge" folder
d = "I:\\accuracy_assessment\\" 

#training polygons shapefile
training_poly = "I:\\training_sites.shp"
 #number of points
POINTS = "50"

#input land cover map
landcover_in = "I:\\post_process_r7\\r7_final"

#Minimum distance between randomized points in meters. Can be 0 if desired
rand_space = "90"

#Highest land cover class grid code. Land cover raster must contain all sequential values between 1 and lc_count.
lc_count = 10 

#Variables. Leave these unmodified:
outputs = d + "outputs"
focal_stats_run_img = d + "scratch\\focal_stats_run" + r + ".img"
reclass_run_img = d + "scratch\\reclass_run" + r + ".img"
raster_point_run_shp = d + "scratch\\raster_point_run" + r + ".shp"
value_to_point_run_shp = d + "scratch\\value_to_point_run" + r + ".shp"

#to convert points to squares:
point_merge_buffer_run_shp = d + "scratch\\point_merge_buffer_run" + r + ".shp"
point_erase_run_shp = d + "scratch\\point_erase_run" + r + ".shp"
mergestring = ""
run_point_merge_shp = d + "final_merge\\run" + r + "_point_merge.shp"

#this is the final output of the stratified random sampling
assessment_squares_run_shp = d + "final_merge\\assessment_squares_run" + r + ".shp" 

# Process: Focal Statistics- targets center pixels of homogenous land cover 
# arcpy.gp.FocalStatistics_sa(landcover_in, focal_stats_run_img, 
# "Rectangle 3 3 CELL", "VARIETY", "DATA") print "focal stats finished"

# Process: Reclassify- eliminates all pixels not surrounded by homogenous 
# lc arcpy.gp.Reclassify_sa(focal_stats_run_img, "VALUE", "1 1", reclass_run_img, "NODATA")

print "reclassify done"
# Process: Raster to Point
arcpy.RasterToPoint_conversion(reclass_run_img, raster_point_run_shp, "VALUE")
print "raster to point done"
#Erase overlapping training points with possible AA points
arcpy.Erase_analysis(raster_point_run_shp, training_poly, point_erase_run_shp, "")
# Process: Extract Values to Points
arcpy.gp.ExtractValuesToPoints_sa( point_erase_run_shp, landcover_in, value_to_point_run_shp, "NONE", "VALUE_ONLY")
print "extract value to point done"
#loops through the grid codes and generates random points. A range of (1,n+1) will yield values 1 to n for intx in range(1,lc_count + 1):
Thesis Overview 91
￼
x = str(intx)
#grabs points of

class_run_all_shp = d + "scratch\\class" + x + "_run" + r + "_all.shp" arcpy.Select_analysis(value_to_point_run_shp, class_run_all_shp, "\"RASTERVALU\" = " + x) 

each land cover class
print "class " + x + "has been selected"
out = "class" + x + "_run" + r + "_points"
arcpy.CreateRandomPoints_management(outputs, out, class_run_all_shp, "0 0 250 250", POINTS, rand_space +
" Meters", "POINT", "0") if intx == 10:
mergestring = mergestring + outputs + "\\" + out + ".shp" else:
mergestring = mergestring + outputs + "\\" + out + ".shp;" print "random points for class " + x + "have been created"
print "Random points have been created. Now merging them together and outlining landcover pixels" arcpy.Merge_management(mergestring, run_point_merge_shp) #merges all randomized points together
# This will create boxes around each point so that the pixel's boundaries can be assessed
# Process: Buffer- 15 meters here to create a final box outlining the 30m*30m pixel arcpy.Buffer_analysis(run_point_merge_shp, point_merge_buffer_run_shp, "15 Meters", "FULL", "ROUND", "NONE", "")
# Process: Feature Envelope To Polygon arcpy.FeatureEnvelopeToPolygon_management(point_merge_buffer_run_shp, assessment_squares_run_shp, "SINGLEPART")
print "Finished"
