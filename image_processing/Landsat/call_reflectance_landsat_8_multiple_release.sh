#!/bin/bash
# Author Riazuddin Kawsar
# email: r.kawsar@spatial-business-integration
# date: 30th july 2015

## Parameters to be provided to the python script
#data_folder = sys.argv[2] #'LC81970302014029LGN00'
#wrd_dir = sys.argv[3] #'/media/Num/wrk_dir/landsat'

# Input variables
WRK_DIR="/media/Num/PhD/LANDSAT8/N0"

# to unzip use the following command tar zxvf fileNameHere.tgz
for file in $WRK_DIR"/"*.tgz
do
out_dir=${file%%.*}
if [ ! -d "$out_dir" ] #if out_dir doesnot exists then extract of pass
then
echo "extracting ... "${file%%.*}
mkdir $out_dir
tar zxvf $file -C $out_dir
fi
done

# gathring folders to be processed
DIRS=`ls -l $WRK_DIR | egrep '^d' | awk '{print $9}'`

#DIRS=`ls -l $MYDIR | egrep '^d' | awk '{print $8}'`
# "ls -l $MYDIR"      = get a directory listing
# "| egrep '^d'"           = pipe to egrep and select only the directories
# "awk '{print $8}'" = pipe the result from egrep to awk and print only the 8th field

# call python script for each folders and calculate TOA
for DIR in $DIRS
do
echo  ${DIR}
python /media/Num/eo_tools/bin/Image_processing/landsat/reflectance_landsat_8_multiple_release.py ${DIR} ${WRK_DIR}
done
