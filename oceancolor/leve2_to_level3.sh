#!/bin/bash
# Riazuddin kawsar
# 9th Feb 2015
# about l2bin and l3bin details : http://oceancolor.gsfc.nasa.gov/forum/oceancolor/topic_show.pl?tid=2931


## l2bin_sst_default_parfile.par used for both l2bin and l3bin 
# flaguse=LAND,HISOLZ
# l3bprod=sst
# prodtype=regional
# rowgroup=270 
# qual_prod=qual_sst
# qual_max=2
# resolve=H
# verbose=1

l2bin_parfile="/media/Num/eo_tools/oceancolour/l2bin_sst_default_parfile.par"

# in_file="/media/Num/eo_tools/testData/raster/A2014001000000.L2_LAC_SST"
in_dir="/media/Num/eo_tools/testData/raster"

#Define variables read in from master_script.sh.
spatial_bin=H #(H=0.5, 1, 2, 4, 9, or 36)
sensor="A"
year="2014"


#Spatially bin the L2_LAC_SST files "l2bin".
for files in $in_dir/A*.L2_LAC_SST
do
base=$(echo $files | awk -F. '{ print $1 }')
l2_out_file=${base}_${spatial_bin}.L2b
l2bin infile=$files ofile=$l2_out_file parfile=$l2bin_parfile
done


#Temporally bin the "*.L2b" files using l3bin.
pwidth=3
for i in {1..365}
do
doy=$(printf "%0*d\n" $pwidth $i)
ls $in_dir/${sensor}${year}${doy}*.L2b | tee -a $in_dir/l3bin_DAYlist.txt
l3_out_file=${sensor}${year}${doy}_${spatial_bin}_${doy}.L3
l3bin in=$in_dir/l3bin_DAYlist.txt out=$l3_out_file parfile=$l2bin_parfile
rm $in_dir/l3bin_DAYlist.txt
done


#Remove the spatially binned Level-2 files.
rm $in_dir/*.L2b
