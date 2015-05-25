from osgeo import gdal, gdalnumeric, ogr, osr
from PIL import Image, ImageDraw
import os, sys
from matplotlib import path
import numpy
gdal.UseExceptions()


in_shp = "/Users/neel/eo_tools/data/shpfiles/shp_to_clip.shp"
in_rst = "/Users/neel/eo_tools/data/rasters/spot_raster.tif"
out_rst = "/Users/neel/eo_tools/data/rasters/spot_raster_clip.tif"
fillvalue = 0.0


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

    srcArray = gdalnumeric.LoadFile(raster_path)
    srcImage = gdal.Open(raster_path)
    geoTrans = srcImage.GetGeoTransform()
    
    shapef = ogr.Open(shapefile_path)
    lyr = shapef.GetLayer( os.path.split( os.path.splitext( shapefile_path )[0] )[1] )
    poly = lyr.GetNextFeature()
    
    # Convert the layer extent to image pixel coordinates
    minX, maxX, minY, maxY = lyr.GetExtent()
    ulX, ulY = world2Pixel(geoTrans, minX, maxY)
    lrX, lrY = world2Pixel(geoTrans, maxX, minY)
    # Calculate the pixel size of the new image
    pxWidth = int(lrX - ulX)
    pxHeight = int(lrY - ulY)
    clip = srcArray[ulY:lrY, ulX:lrX]
    # EDIT: create pixel offset to pass to new image Projection info
    xoffset =  ulX
    yoffset =  ulY
    print "Xoffset, Yoffset = ( %f, %f )" % ( xoffset, yoffset )
    # Create a new geomatrix for the image
    geoTrans = list(geoTrans)
    geoTrans[0] = minX
    geoTrans[3] = maxY
    
    # Map points to pixels for drawing the boundary on a blank 8-bit, black and white, mask image.
    points = []
    pixels = []
    geom = poly.GetGeometryRef()
    pts = geom.GetGeometryRef(0)
    for p in range(pts.GetPointCount()):
      points.append((pts.GetX(p), pts.GetY(p)))
    for p in points:
      pixels.append(world2Pixel(geoTrans, p[0], p[1]))    
    rasterPoly = Image.new("L", (pxWidth, pxHeight), 1)
    rasterize = ImageDraw.Draw(rasterPoly)
    rasterize.polygon(pixels, 0)
    mask = imageToArray(rasterPoly)
    # Clip the image using the mask
    clip = gdalnumeric.choose(mask, (clip, 0)).astype(gdalnumeric.uint8)

    # gdalnumeric.SaveArray(clip, "OUTPUT.tif", format="GTiff", prototype=raster_path)
    if os.path.exists(out_rst):
        os.remove(out_rst)
    gtiffDriver = gdal.GetDriverByName( 'GTiff' )
    if gtiffDriver is None:
        raise ValueError("Can't find GeoTiff Driver")
    gtiffDriver.CreateCopy( out_rst, OpenArray( clip, prototype_ds=raster_path, xoff=xoffset, yoff=yoffset ))


if __name__ == '__main__':
    main(in_shp, in_rst)
