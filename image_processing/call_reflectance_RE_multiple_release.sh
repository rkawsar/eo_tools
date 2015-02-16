#!/bin/bash
# Riazuddin Kawsar

MYDIR="/media/Arc/eo_archive_proc/VHR_SAT_IMAGE/RE5/SBCP_BASF"

DIRS=`ls -l $MYDIR | egrep '^d' | awk '{print $9}'`


# and now loop through the directories:
for DIR in $DIRS
do
echo  ${DIR}
python /media/Num/eo_tools/bin/Image_processing/reflectance_RE_multiple_release.py ${DIR}
done
