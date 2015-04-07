#!/bin/bash
# Author Riazuddin Kawsar
# email: r.kawsar@spatial-business-integration
# date: 18th March 2015

# location: /media/Num/eo_tools/bin/Image_processing/call_reflectance_RE_multiple_release.sh
# Dependency : /media/Num/eo_tools/bin/Image_processing/reflectance_RE_multiple_release.py

# input value
MYDIR="/media/Arc/eo_archive_proc/VHR_SAT_IMAGE/RE5/150301_MAGIC"

# extract the project name information
project_name=`echo "$MYDIR" | cut -d '/' -f 7`

# list all the folders and save it in a list
DIRS=`ls -l $MYDIR | egrep '^d' | awk '{print $9}'`


# and now loop through the directories:
for DIR in $DIRS
do
# check if the folder is already processed?
processing_status=`echo "$DIR" | cut -d'_' -f1`
if [ $processing_status != "P" ]
	then
	echo  "processing folder ..."${DIR}
	
	python /media/Num/eo_tools/bin/Image_processing/reflectance_RE_multiple_release.py ${DIR} ${project_name}
	
	folder_name=$MYDIR"/"$DIR
	new_folder_name=$MYDIR"/P_"$DIR
	
	# rename the folder after processing
	mv $folder_name $new_folder_name
fi
done
