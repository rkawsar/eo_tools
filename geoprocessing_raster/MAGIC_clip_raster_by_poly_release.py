# coding: utf-8
# Author: Riazuddin Kawsar
# E-mail: r.kawsar@spatial-business-integration.com
# Date: 28-May 2015
# Clipping rasters based on polygon geometry in the shp file
# usualls gdalwarp or gdal_translate produces a shift in the image
# but this script solves that problem. Cliping image without shift.

from osgeo import gdal, gdalnumeric, ogr, osr
import Image, ImageDraw
import os, sys, fnmatch
from matplotlib import path
import numpy
gdal.UseExceptions()

# Aschersleben, Dohndorf, Elmshorn, Grossalsleben
# Laubach, Lechfeld, Mannheim, Straubing, Wittingen

# input variable
site_name = 'Wittingen'
crop = ['ww', 'wrs'] #cr

#------------------------------------------------------------------------------------------

# parmanent for MAGIC 2 project
project_path = '/media/SBIProject/150301_BASF_MAGIC/Germany/site_specific_analysis'
site_path = os.path.join(project_path, site_name)
in_rst_path = os.path.join(project_path, site_name, 'rasters')
in_shp = '/media/SBIProject/150301_BASF_MAGIC/Germany/shpfile/Germany_all_fields_v01_wgs84.shp'
fillvalue = 255.0

def findfiles(input_dir, file_type):
    toprocess = []
    for root,dir,files in os.walk(input_dir):
        for name in sorted(files):
            if fnmatch.fnmatch(name,file_type): 
                toprocess.append( os.path.join(root, name) )
    return toprocess

def imageToArray(i):
    a=gdalnumeric.fromstring(i.tostring(),'b')
    a.shape=i.im.size[1], i.im.size[0]
    return a

def world2Pixel(geoMatrix, x, y):
  ulX = geoMatrix[0]
  ulY = geoMatrix[3]
  xDist = geoMatrix[1]
  yDist = geoMatrix[5]
  rtnX = geoMatrix[2]
  rtnY = geoMatrix[4]
  pixel = int((x - ulX) / xDist)
  line = int((ulY - y) / xDist)
  return (pixel, line)

def OpenArray( array, prototype_ds = None, xoff=0, yoff=0 ):
    ds = gdal.Open( gdalnumeric.GetArrayFilename(array) )
    band = ds.GetRasterBand(1)
    band.SetNoDataValue(fillvalue)
    if ds is not None and prototype_ds is not None:
        if type(prototype_ds).__name__ == 'str':
            prototype_ds = gdal.Open( prototype_ds )
        if prototype_ds is not None:
            gdalnumeric.CopyDatasetInfo( prototype_ds, ds, xoff=xoff, yoff=yoff )
    return ds


def main( shapefile_path, raster_path ):

    siteCode = site_name.lower()[0:3]
    shapef = ogr.Open(shapefile_path)
    lyr = shapef.GetLayer( os.path.split( os.path.splitext( shapefile_path )[0] )[1] )
    id = []
    for f in lyr:
        field_id = f.GetFieldAsString('field_id')
        crop_id = f.GetFieldAsString('crop_id')
        field_id_siteCode = field_id.split('_')[0]
        if field_id_siteCode == siteCode and crop_id in crop :
            id.append(f.GetFID())
    for i in id:
        feat=lyr.GetFeature(i)
        field_name = feat.GetFieldAsString('field_name')
        print 'cliping images for field ' + field_name
        # Convert the geometry extent to image pixel coordinates
        geom = feat.GetGeometryRef()
        f_coord = geom.GetEnvelope()
        minX, maxX, minY, maxY = f_coord
        
        out_rst_path = os.path.join(project_path, site_name, 'FA', field_name, 'rasters')
        if not os.path.exists(out_rst_path):
            os.makedirs(out_rst_path)

        rasters_list = findfiles(raster_path, '*_wgs84_*.tif')
        for inraster in rasters_list:
            name = os.path.basename(inraster)
            name = name.split('.tif', 1)[0]
            image_date = name.split('_', 1)[1]
            print 'image date ' + image_date
            name = None
            outraster = os.path.join(out_rst_path, field_name + '_' + image_date + '.tif')

            srcArray = gdalnumeric.LoadFile(inraster)
            srcImage = gdal.Open(inraster)
            geoTrans = srcImage.GetGeoTransform()

            ulX, ulY = world2Pixel(geoTrans, minX, maxY)
            lrX, lrY = world2Pixel(geoTrans, maxX, minY)
            #print ulX, ulY, lrX, lrY 

            # Calculate the pixel size of the new image
            pxWidth = int(lrX - ulX)
            pxHeight = int(lrY - ulY)
            clip = srcArray[ulY:lrY, ulX:lrX]

            # EDIT: create pixel offset to pass to new image Projection info
            xoffset =  ulX
            yoffset =  ulY

            # Create a new geomatrix for the image
            geoTrans = list(geoTrans)
            geoTrans[0] = minX
            geoTrans[3] = maxY

            # Map points to pixels for drawing the boundary on a blank 8-bit, black and white, mask image.
            points = []
            pixels = []
            pts = geom.GetGeometryRef(0)

            for p in range(pts.GetPointCount()):
                points.append((pts.GetX(p), pts.GetY(p)))

            for p in points:
                pixels.append(world2Pixel(geoTrans, p[0], p[1]))

            #print points

            rasterPoly = Image.new("L", (pxWidth, pxHeight), 1)
            rasterize = ImageDraw.Draw(rasterPoly)
            rasterize.polygon(pixels, 0)
            mask = imageToArray(rasterPoly)
            # Clip the image using the mask
            clip = gdalnumeric.choose(mask, (clip, 255.0)).astype(numpy.float)

            if os.path.exists(outraster):
                os.remove(outraster)
            gtiffDriver = gdal.GetDriverByName( 'GTiff' )
            if gtiffDriver is None:
                raise ValueError("Can't find GeoTiff Driver")
            gtiffDriver.CreateCopy( outraster, OpenArray( clip, prototype_ds=inraster, xoff=xoffset, yoff=yoffset ))

if __name__ == '__main__':
    main(in_shp, in_rst_path)

