
# coding: utf-8
# Author: Riazuddin Kawsar
# E-mail: r.kawsar@spatial-business-integration.com
# Date: 11-May 2015
# Vegiation Index Computation (for 250 meters pixel)
# using MOD09Q1 and MOD09A1
'''
scrpit description: Uses the Natural Jenks Breaks Algorithom to get the break intervals
and then reclass the Jenks classes (equal interval between 2nd and 9th item in the breaks)
and then use the reclass Jenks to classify the input image and 
'''



import numpy, math
from osgeo import gdal
import ogr
import sys, os, fnmatch, csv, time
import matplotlib.pylab as plt
from operator import itemgetter
import xml.etree.cElementTree as ET
import multiprocessing


# input variable
site_name = 'Aschersleben' # Lechfeld, Aschersleben, Oschersleben , Steinburg , Limburgerhof, Elmshorn, Grossalsleben, Laubach
crop_to_process = 'ww' # ww, wrs, cr, all
submission_version = 1



# parmanent for MAGIC 2 project
startTime = time.time()
project_path = '/media/SBIProject/150301_BASF_MAGIC/Germany/site_specific_analysis'
in_rster_dir= os.path.join(project_path, site_name, 'FA')
in_shp_path = os.path.join(project_path, site_name, 'shpfiles')

numClass = 10
#classification_values = [0.00001, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
classification_output_values = [1,2,3,4,5,6,7,8,9,10]
fill_value = 0


def find_shp_files(input_dir):
    toprocess = []
    for root,dir,files in os.walk(input_dir):
        for name in sorted(files):
            if fnmatch.fnmatch(name, '*_utm_to_clip.shp'): 
                toprocess.append( os.path.join(root, name) )
    return toprocess

def findfiles(input_dir):
    toprocess = [] 
    for root,dir,files in os.walk(input_dir):
        for name in sorted(files):
            if fnmatch.fnmatch(name,'*_avg.*.tif'): 
                toprocess.append( os.path.join(root, name) )             
    return toprocess

def return_raster(in_file, band_number):
    dataset = gdal.Open(in_file)
    band = dataset.GetRasterBand(band_number)
    ncol = dataset.RasterXSize # xsize
    nrow = dataset.RasterYSize # ysize
    block_sizes = band.GetBlockSize()
    x_block = block_sizes[0]
    y_block = block_sizes[1]
    return dataset, band, ncol, nrow, x_block, y_block

def remove_values_from_list(the_list, val):
    return [value for value in the_list if value != val]

def get_raster_array(in_raster, band_number):
    dataset = gdal.Open(in_raster)
    band = dataset.GetRasterBand(band_number)
    ncol = dataset.RasterXSize
    nrow = dataset.RasterYSize
    noDataValue = band.GetNoDataValue()
    numarray = band.ReadAsArray(0,0,ncol,nrow)
    numarray = numpy.ma.masked_values (numarray, noDataValue)
    print "reading bands as array....."
    dataList = []
    for x in xrange(numarray.shape[0]):
      for y in xrange(numarray.shape[1]):
        dataList.append(numarray[x][y])
    dataList = remove_values_from_list(dataList, noDataValue)
    return dataList


def get_jenks_breaks (dataList, numClass):
    dataList.sort()
    mat1 = []
    for i in range(0,len(dataList)+1):
      temp = []
      for j in range(0,numClass+1):
        temp.append(0)
      mat1.append(temp)
    mat2 = []
    for i in range(0,len(dataList)+1):
      temp = []
      for j in range(0,numClass+1):
        temp.append(0)
      mat2.append(temp)
    print "Itaration 1 .... ( mat1 and mat 2 )...."
    for i in range(1,numClass+1):
      mat1[1][i] = 1
      mat2[1][i] = 0
      for j in range(2,len(dataList)+1):
        mat2[j][i] = float('inf')
    print "Itaration 2 .... ( mat1 and mat 2 )...."
    v = 0.0
    for l in range(2,len(dataList)+1):
      s1 = 0.0
      s2 = 0.0
      w = 0.0
      for m in range(1,l+1):
        i3 = l - m + 1
        val = float(dataList[i3-1])
        s2 += val * val
        s1 += val
        w += 1
        v = s2 - (s1 * s1) / w
        i4 = i3 - 1
        if i4 != 0:
          for j in range(2,numClass+1):
            if mat2[l][j] >= (v + mat2[i4][j - 1]):
              mat1[l][j] = i3
              mat2[l][j] = v + mat2[i4][j - 1]
      mat1[l][1] = 1
      mat2[l][1] = v
    k = len(dataList)
    kclass = []
    for i in range(0,numClass+1):
      kclass.append(0)
    kclass[numClass] = float(dataList[len(dataList) - 1])
    countNum = numClass
    while countNum >= 2:
      id = int((mat1[k][countNum]) - 2)
      kclass[countNum - 1] = dataList[id]
      k = int((mat1[k][countNum] - 1))
      countNum -= 1
    return kclass


def reclass_jenks_class(jenks_class, classes):
    min_value = jenks_class[1]
    max_value = jenks_class[9]
    unit = (max_value - min_value) / classes
    reclass = [min_value + k*unit for k in range(classes+1)]
    reclass[0] = 0.00001
    reclass[10] = 1
    return reclass

def gather_raster_stat(band):
    max_value = band.GetMaximum()
    min_value = band.GetMinimum()
    if max_value == None or min_value == None:
        stats = band.GetStatistics(0, 1)
        max_value = stats[1]
        min_value = stats[0]
    return max_value, min_value


# this function is dependent on other functions:
def classify_raster(class_in_values, class_out_values, in_raster, out_name):
    dataset, band, ncol, nrow, x_block, y_block = return_raster(in_raster, 1)
    max_value, min_value = gather_raster_stat(band)
    name = os.path.basename(in_raster)
    format = "GTiff"
    driver = gdal.GetDriverByName( format )
    out_dataset = driver.Create(out_name, ncol, nrow, 1 )
    out_dataset.SetGeoTransform(dataset.GetGeoTransform())
    out_dataset.SetProjection(dataset.GetProjection())
    out_dataset.GetRasterBand(1).SetNoDataValue(fill_value)
    for i in range(0, nrow, y_block):
        if i + y_block < nrow:
            rows = y_block
        else:
            rows = nrow - i
        for j in range(0, ncol, x_block):
            if j + x_block < ncol:
                cols = x_block
            else:
                cols = ncol
            data = band.ReadAsArray(j, i, cols, rows)
            r = numpy.zeros((rows, cols), numpy.uint8)
            for k in range(len(class_in_values) - 1):
                if class_in_values[k] < max_value and (class_in_values[k + 1] > min_value ):
                    r = r + class_out_values[k] * numpy.logical_and(data >= class_in_values[k], data < class_in_values[k + 1])
            if class_in_values[k + 1] < max_value:
                r = r + class_out_values[k] * (data >= class_in_values[k + 1])
            out_dataset.GetRasterBand(1).WriteArray(r,j,i)
    band = None
    dataset = None
    #return out_dataset


def raster_class_stat_dict(in_raster):
    in_raster, band, ncol, nrow, x_block, y_block = return_raster(in_raster, 1)
    xsize = in_raster.RasterXSize
    ysize = in_raster.RasterYSize
    bands = in_raster.RasterCount
    for i in xrange(1, bands + 1):
        band_i = in_raster.GetRasterBand(i)
        raster = band_i.ReadAsArray()
    count = {}
    for col in range( xsize ):
        for row in range( ysize ):
            cell_value = raster[row, col]
            if math.isnan(cell_value):
                cell_value = 'Null'
            if cell_value <= 0.0:
                cell_value = 'Null'
            try:
                count[cell_value] += 1
            except:
                count[cell_value] = 1
    #total number of pixels
    keys, values = zip(*sorted(count.items(), key=itemgetter(1)))
    total = sum(values)
    # total number of useable pixels
    sums = 0
    for (key, value) in count.items():
        if key!= 'Null':
            sums = sums + value
    #print 'total number useable pixels: ' + str(sums)
    sums = None
    return count


def manage_list(jenks_class, count_dic):
    vvi = 0.50
    i_list = []
    j_list = []
    k_list = []
    for i in range(len(jenks_class)-1):
        if i == 0:
            value = jenks_class[i+1]
            value = "%.3f" % value
            vi = vvi
            vi = "%.2f" % vi
        else:
            value = jenks_class[i]
            value = "%.3f" % value
            vi = vvi + 0.05*i
            vi = "%.2f" % vi
        x = [i+1, vi, value]
        i_list.append(x)
    for (key, value) in count_dic.items():
        x = [key, value]
        j_list.append(x)
    for i in i_list:
        for j in j_list:
            if i[0] == j[0]:
                x = [i[0], i[1], i[2], j[1]]
            if x not in k_list:
                k_list.append(x)
    return k_list



def create_list_to_xml(k_list, xml_out):
    csvimport = ET.Element("csvimport")
    for i in range(len(k_list)):
        row = ET.SubElement(csvimport,"row")
        i_class = ET.SubElement(row,"class")
        i_value = ET.SubElement(row,"value")
        i_vi = ET.SubElement(row,"vi")
        i_count = ET.SubElement(row,"pixel_count")
        
        i_class.text = str(k_list[i][0])
        i_vi.text = str(k_list[i][2])
        i_value.text = str(k_list[i][1])
        i_count.text = str(k_list[i][3])
    tree = ET.ElementTree(csvimport)
    tree.write(xml_out)
    return tree


def extract_crop_type_info(in_shp_path):
    crop_list = []
    for inshape in find_shp_files(in_shp_path):
        ds = ogr.Open(inshape)
        lyr = ds.GetLayer(0)
        lyr.ResetReading()
        ft = lyr.GetNextFeature()
        while ft:
            field_name = ft.GetFieldAsString('field_name')
            field_name = field_name.replace('_', '')
            field_name = field_name.replace('.', '')
            crop_type = ft.GetFieldAsString('crop')
            x = [field_name, crop_type]
            if x not in crop_list:
                crop_list.append(x)
            ft = lyr.GetNextFeature()
        ds = None
    return crop_list


def return_field_crop_info(field_name, crop_list):
    for i in crop_list:
        if field_name == i[0]:
            x = i[1]
    return x


def uniq(i_list):
    last = object()
    for item in i_list:
        if item == last:
            continue
        yield item
        last = item

# accumulating the processing 
def doprocess(raster):
    filename = raster.split('/')[-1]
    out_dir = raster.replace(filename, '')
    print 'Reclassification Process Started for ... ' + filename
    filename = filename.replace('.tif', '')
    filename = filename.split('_')[0]
    filename = filename.replace('_', '')
    filename = filename.replace('.', '')
    siteCode = site_name.lower()[0:3]
    crop_list = extract_crop_type_info(in_shp_path)
    crop_list = uniq(crop_list)
    crop = return_field_crop_info(filename, crop_list)
    if crop == crop_to_process:
        print crop
        out_file = 'fypm_' + str(submission_version) + '_' + crop + '_' + siteCode + '_' + filename + '.tif'
        print out_file
        out_file = os.path.join(out_dir, out_file)
        xml_out_file = os.path.join(out_dir, out_file + '.xml')
        xml_out_file = xml_out_file.replace('.tif', '')
        if os.path.exists(out_file):
            os.remove(out_file)
        if os.path.exists(xml_out_file):
            os.remove(xml_out_file)
        datalist = get_raster_array(raster, 1)
        jenks_class = get_jenks_breaks (datalist, numClass)
        re_jenks_class = reclass_jenks_class(jenks_class, numClass)
        print re_jenks_class
        classify_raster(re_jenks_class, classification_output_values, raster, out_file)
        count = raster_class_stat_dict(out_file)    
        complete_list = manage_list(re_jenks_class, count)
        xml_file = create_list_to_xml(complete_list, xml_out_file)


def main(in_rster_dir):
    input_dir = in_rster_dir
    filelist = findfiles(input_dir)
    pool = multiprocessing.Pool(processes=multiprocessing.cpu_count())
    #pool = multiprocessing.Pool(processes=1)
    pool.map(doprocess,filelist)
    pool.close()
    pool.join()
    print 'Using ' +str(multiprocessing.cpu_count())+' cores.'
    

if __name__ == "__main__":
    main(in_rster_dir)
    endTime = time.time()
    print '\n\nThe script took ' +str(endTime - startTime)+ ' seconds'

