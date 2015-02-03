#!/usr/bin/env python

# python script to download SST data for the year 2012

import re
import os
import urllib, urllib2
import datetime, time

pram = 'SST'
OUT_DIR = "C:\R.Kawsar\WORKSPACE\Data\oceancolour"

year = '2012'
day = '01'
month = '01'

basetime= time.time()
user_TInput = month + '/' + day + '/' + year[2:]
d1 = datetime.datetime.strptime(user_TInput, "%m/%d/%y")
d0 = datetime.datetime.strptime('01/01/70', "%m/%d/%y")
start_day =(d1 - d0).days
end_day = start_day + 365 

#for i in range(start_day, end_day):
#    print i


INPUTS = {
    'sub': 'level1or2list',
    'per': 'DAY', 
    'day': 16393, #day=15390 refers to number of elapsed days since 1 Jan 1970
    'prm': pram,
    'ndx': 0,
    'mon': 16375,
    'sen': 'am',
    'dnm': 'D', # D for daytime image anf for both day and night D@N
    'rad': 0,
    'frc': 0,
    'set': 10,
    'n': 50,
    'w': -100,
    'e': -95,
    's': 40,}

URL_FIND = "http://oceancolor.gsfc.nasa.gov/cgi/browse.pl/"
URL_GET = "http://oceandata.sci.gsfc.nasa.gov/cgi/getfile/%s"
PATT = "A\d*\.L2_LAC_" + pram

def http_post(url, args):
    data = urllib.urlencode(args)
    req = urllib2.Request(url, data)
    response = urllib2.urlopen(req)
    page = response.read()
    return page

if __name__ == "__main__":
    page = http_post(URL_FIND, INPUTS)
    scenes = re.findall(PATT, page)
    scenes = list(set(scenes))
    for scene in scenes:
        filename = scene + ".bz2"
        outpath = os.path.join(OUT_DIR, filename)
        url = URL_GET % filename
        urllib.urlretrieve(url, outpath)
