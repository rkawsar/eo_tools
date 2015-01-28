#!/usr/bin/python
# Riazuddin Kawsar

import os, sys, glob, time, datetime, math, numpy, fnmatch
from osgeo import gdal
from osgeo.gdalconst import *

# input variable
folder_name = '054084822010_01'

min_ndvi= 0.01
max_ndvi = 1.0
fillval = 255

# for Multispectral
# input and output files and dirs (generated automatically upon providing the folder name
sub_folder = folder_name.split('_', 1)[0] + '_01_P001_MUL'
data_dir = '/media/Arc/eo_archive_proc/VHR_SAT_IMAGE/WV2/' + folder_name + '/' + sub_folder
os.chdir(img_imd_folder)

for files in glob.glob('*.TIF'):
    image_file_name = files
    image_file_path = os.path.join(img_imd_folder, image_file_name)
    print 'input img file: ' + image_file_name

for files in glob.glob('*.IMD'):
    imd_file_name = files
    imd_file_path = os.path.join(img_imd_folder, imd_file_name)
    metadata_file = imd_file_path
    print 'input metadata file: ' + imd_file_name

product='binned'
output_dir = os.path.join(data_dir, product)
if not os.path.exists(output_dir):
    os.makedirs(output_dir)
print 'output folder: ' + output_dir


#Loop thru and parse the IMD file, extract and store in a dictionary
def getimddata(f):
    lines=iter(open(f).readlines())
    imddata={}
    bands=[]
    line=lines.next()
    while line:
        line=[item.strip() for item in line.replace('"','').split('=')]
        group=line[0]
        if group == 'END;':break
        value=line[1]
        if group == 'BEGIN_GROUP':
            group=value
            subdata={}
            if 'BAND_' in group:bands.append(group)
            while line:
                line=lines.next()
                line = [l.replace('"','').strip() for l in line.split('=')]
                subgroup=line[0]
                subvalue=line[1]
                if subgroup == 'END_GROUP':break
                elif line[1] == '(':
                    while line:
                        line=lines.next()
                        line = line.replace('"','').strip()
                        subvalue+=line
                        if line[-1:]==';':
                            subvalue=eval(subvalue.strip(';'))
                            break
                else:subvalue=subvalue.strip(';')
                subdata[subgroup]=subvalue
            imddata[group]=subdata
        else: imddata[group]=value.strip(');')
        line=lines.next()
    imddata['bands']=bands
    imddata['nbands']=len(bands)
    return imddata

# run function and loop through IMD file and read data into dictionay
imddata = getimddata(metadata_file)

#WV-2 Band-Averaged Solar Spectral Irradiance Table
ESUN = {'BAND_P': 1580.8140,
    'BAND_C': 1758.2229,
    'BAND_B': 1974.2416,
    'BAND_G': 1856.4104,
    'BAND_Y': 1738.4791,
    'BAND_R': 1559.4555,
    'BAND_RE': 1342.0695,
    'BAND_N': 1069.7302,
    'BAND_N2': 861.2866}

# Take a string date as input and converts it to the Julian day and
# returns the Earth-Sun Distance for that day

def EarthSunDistance(date):
    acqTime = datetime.datetime.strptime(date, "%Y-%m-%dT%H:%M:%S.%fZ")
    #acqTime = time.strptime(date, "%Y-%m-%dT%H:%M:%S.%fZ")
    if acqTime.month == 1 or acqTime.month == 2:
        month = acqTime.month + 12
        year = acqTime.year - 1
    else:
        month = acqTime.month
        year = acqTime.year
    
    secondsMicro = acqTime.second + (acqTime.microsecond / 1000000.0)
    UT = acqTime.hour + (acqTime.minute / 60.0) + (secondsMicro / 3600.0)
    A = int(year / 100)
    B = 2 - A + int(A / 4)
    JD = int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + \
        acqTime.day + (UT / 24.0) + B - 1524.5
    D = JD - 2451545.0
    g = math.radians(357.529 + 0.98560028 * D)
    
    return 1.00014 - 0.01671 * math.cos(g) - 0.00014 * math.cos(2 * g)


# extracting necessary values from the Dictionary
# absCalFactor(absCF_B) = ACF,effectiveBandwidth (effBW_B)= EBW
def acquireMetadata(band):
    
    ACF = float(imddata['BAND_' + str(band)]['absCalFactor'][0:15])
    EBW = float(imddata['BAND_' + str(band)]['effectiveBandwidth'][0:15])
    
    metadatalist = [ACF, EBW]
    
    return metadatalist

# extracting other information...
imgdate = imddata['MAP_PROJECTED_PRODUCT']['earliestAcqTime'][0:30]
EarthSunDistance = float (EarthSunDistance(imgdate))
SunEl = imddata['IMAGE_1']['meanSunEl'][0:30]
solar_zenith_angle = 90.00 - float(SunEl)
solar_zenith_angle_radians = math.radians(solar_zenith_angle)

print 'image date: ' + imgdate
print 'EarthSunDistance: ' + str(EarthSunDistance)
print 'SunEl: ' + str (SunEl)
print 'solar_zenith_angle: ' + str(solar_zenith_angle)
print 'solar_zenith_angle_radians: ' + str(solar_zenith_angle_radians)



######## raster processing functions ---------------------
#----------------------------------------------------------

# function to  the raster based on the raster index
def return_band(image_file_name, band_number):
    image = image_file_name
    dataset = gdal.Open(image,GA_ReadOnly)  
    if dataset is None:
        print "Could not open " + dataset
        sys.exit(1)
    geoTransform = dataset.GetGeoTransform()
    proj = dataset.GetProjection()
    rasterband = dataset.GetRasterBand(band_number)
    type(rasterband)
    ncol = dataset.RasterXSize
    nrow = dataset.RasterYSize
    band = rasterband.ReadAsArray(0,0,ncol,nrow)
    band = band.astype(numpy.uint16)
    return band,geoTransform,proj,ncol,nrow
    dataset = None
    band = None

# dfunction to efine the output name
def product_output_name(out_put_dir,product,Product_name):
    product_dir = os.path.join(out_put_dir,product)
    product_output_name = Product_name+'.'+product+'.tif'
    product_path_file = os.path.join(product_dir,product_output_name)
    return product_path_file

# function to define the output file
def output_file(output_name,output_array,geoTransform,proj,ncol,nrow):
    format = "GTiff"
    driver = gdal.GetDriverByName( format )
    outDataset = driver.Create(output_name,ncol,nrow,1,GDT_Float32)
    outBand = outDataset.GetRasterBand(1)
    outBand.WriteArray(output_array,0,0)
    outBand.FlushCache()
    outDataset.SetGeoTransform(geoTransform )
    outDataset.SetProjection(proj)

# function to calculate NDVI
def normalize(band1,band2):
    var1 = numpy.subtract(band1,band2)
    var2 = numpy.add(band1,band2)
    numpy.seterr(all='ignore')
    ndvi = numpy.divide(var1,var2)
    return ndvi


# reading DN bands, extracting metadata and calculating radiance and reflactance and writing it to the folder
def calculate_reflectance(band_name, DN, EarthSunDistance, solar_zenith_angle_radians, output_dir):
    
    img_name = 'Band_' + band_name
    print 'reading....' +  img_name

    print 'extracting the band metadata...'
    band_metadata = acquireMetadata (band_name)
    ACF = float(band_metadata[0])
    EBW = float(band_metadata[1])
    print ACF, EBW

    print 'calculating Rediance...'
    rediance = (DN * ACF )/ EBW

    ESUNVAL = float(ESUN['BAND_' + str(band_name)])
    print ESUNVAL

    print 'calculating Reflectance...'
    reflectance = (math.pi * rediance * math.pow(EarthSunDistance, 2)) / (ESUNVAL * math.cos(solar_zenith_angle_radians)

    reflectance_name = product_output_name(data_dir,product,band_name)
    
    print 'Writing output...'
    output_file(reflectance_name,reflectance,geoTransform,proj,ncol,nrow)
    print reflectance_name

    reflactance = None
    rediance = None


# calculating the ndvi
def calculate_ndvi(EarthSunDistance, solar_zenith_angle_radians, output_dir):

    print 'extracting the band metadata and calculating RED band Reflactance...'
    Band_R,geoTransform,proj,ncol,nrow  = return_band(image_file_path,5)
    band_metadata = acquireMetadata ('R')
    ACF_R = float(band_metadata[0])
    EBW_R = float(band_metadata[1])
    rediance_R = (Band_R * ACF_R )/ EBW_R
    ESUNVAL_R = float(ESUN['BAND_' + str('R')])
    reflectance_R = (math.pi * rediance_R * math.pow(EarthSunDistance, 2)) / (ESUNVAL_R * math.cos(solar_zenith_angle_radians))
    Band_R = None
    rediance_R = None

    print 'extracting the band metadata and calculating NIR1 band Reflactance...'
    Band_N,geoTransform,proj,ncol,nrow  = return_band(image_file_path,7)
    band_metadata = acquireMetadata ('N')
    ACF_N = float(band_metadata[0])
    EBW_N = float(band_metadata[1])
    rediance_N = (Band_N * ACF_N )/ EBW_N
    ESUNVAL_N = float(ESUN['BAND_' + str('N')])
    reflectance_N = (math.pi * rediance_N * math.pow(EarthSunDistance, 2)) / (ESUNVAL_N * math.cos(solar_zenith_angle_radians))
    Band_N = None
    rediance_N = None

    ndvi_name = product_output_name(data_dir,product,'ndvi')

    print "processing ndvi...."
    ndvi = normalize(reflectance_N, reflectance_R)
    min_ndvi_mask = numpy.where(ndvi < min_ndvi, 1, 0)
    max_ndvi_mask = numpy.where(ndvi > max_ndvi, 1, 0)

    numpy.putmask(ndvi, min_ndvi_mask, min_ndvi)
    numpy.putmask(ndvi, max_ndvi_mask, max_ndvi)

    output_file(ndvi_name,ndvi,geoTransform,proj,ncol,nrow)

    reflectance_R = None
    reflectance_N = None
    mdvi = None


'''
if __name__ == "__main__":
    calculate_ndvi(EarthSunDistance, solar_zenith_angle_radians, output_dir)
'''


if __name__ == "__main__":

    Band_C,geoTransform,proj,ncol,nrow  = return_band(image_file_path,1)
    calculate_reflectance('C', Band_C, EarthSunDistance, solar_zenith_angle_radians, output_dir)
    Band_C = None

    Band_B,geoTransform,proj,ncol,nrow  = return_band(image_file_path,2)
    calculate_reflectance('B', Band_B, EarthSunDistance, solar_zenith_angle_radians, output_dir)
    Band_B = None

    Band_G,geoTransform,proj,ncol,nrow  = return_band(image_file_path,3)
    calculate_reflectance('G', Band_G, EarthSunDistance, solar_zenith_angle_radians, output_dir)
    Band_G = None
    
    Band_Y,geoTransform,proj,ncol,nrow  = return_band(image_file_path,4)
    calculate_reflectance('Y', Band_Y, EarthSunDistance, solar_zenith_angle_radians, output_dir)
    Band_Y = None

    Band_R,geoTransform,proj,ncol,nrow  = return_band(image_file_path,5)
    calculate_reflectance('R', Band_R, EarthSunDistance, solar_zenith_angle_radians, output_dir)
    Band_R = None

    Band_RE,geoTransform,proj,ncol,nrow  = return_band(image_file_path,6)
    calculate_reflectance('RE', Band_RE, EarthSunDistance, solar_zenith_angle_radians, output_dir)
    Band_RE = None

    Band_N,geoTransform,proj,ncol,nrow  = return_band(image_file_path,7)
    calculate_reflectance('N', Band_N, EarthSunDistance, solar_zenith_angle_radians, output_dir)
    Band_N = None

    Band_N2,geoTransform,proj,ncol,nrow  = return_band(image_file_path,8)
    calculate_reflectance('N2', Band_N2, EarthSunDistance, solar_zenith_angle_radians, output_dir)
    Band_N2 = None

    calculate_ndvi(EarthSunDistance, solar_zenith_angle_radians, output_dir)
