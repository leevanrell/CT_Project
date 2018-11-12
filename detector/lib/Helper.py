#!/usr/bin/python
import datetime
import time
import csv
import urllib2
import os


def isValidLocation(output):
    check = output.split(',')
    return len(output) != 0 and check[0] == '$GPGGA' and len(check[6]) != 0 and int(check[6]) != 0 # we only want GPGGA sentences with an actual fix (Fix != 0)


def getDocument(cell_tower, location):
    cell_tower = cell_tower.split(',')
    if len(cell_tower) > 6:
        arfcn = cell_tower[1][1:]         # Absolute radio frequency channel number
        rxl = cell_tower[2]               # Receive level (signal stregnth)
        if(len(cell_tower) > 9): # +CENG:0, '<arfcn>, <rxl>, <rxq>, <mcc>, <mnc>, <bsic>, <cellid>, <rla>, <txp>, <lac>, <TA>'
            bsic = cell_tower[6]          # Base station identity code
            Cell_ID = cell_tower[7]       # Unique Identifier
            MCC = cell_tower[4]           # Mobile Country Code
            MNC = cell_tower[5]           # Mobile Network Code
            LAC = cell_tower[10]          # Location Area code
        else: # +CENG:1+,'<arfcn>, <rxl>, <bsic>, <cellid>, <mcc>, <mnc>, <lac>'    
            bsic = cell_tower[3]          # Base station identity code
            Cell_ID = cell_tower[4]       # Unique Identifier
            MCC = cell_tower[5]           # Mobile Country Code
            MNC = cell_tower[6]           # Mobile Network Code
            LAC = cell_tower[7][:-2]      # Location Area code
    return {'time': time.strftime('%m-%d-%y %H:%M:%S'), 'MCC': MCC, 'MNC': MNC, 'LAC': LAC, 'Cell_ID': Cell_ID, 'rxl': int(rxl), 'arfcn': arfcn, 'bsic': bsic, 'lat': location.latitude, 'lon': location.longitude, 'satellites':  int(location.num_sats), 'GPS_quality': int(location.gps_qual), 'altitude': location.altitude, 'altitude_units': location.altitude_units}


def update_local(document):
    FOLDER = 'data/backup/' 
    FILE = FOLDER  + str(datetime.date.today())+ '.csv'
    if not os.path.exists(FOLDER):
        os.makedirs(FOLDER)
    with open(FILE, 'a') as f:
        writer = csv.DictWriter(f, document.keys())
        writer.writerow(document)


def isConnected(HTTP_SERVER): 
    try:
        if HTTP_SERVER.lower().startswith('http'):
            urllib2.urlopen(HTTP_SERVER, timeout=1)
        else:
            raise ValueError from None
        return True
    except urllib2.URLError as err:
        return False
