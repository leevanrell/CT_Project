#!/usr/bin/python

DB_URL = 'mongodb://localhost:27017/'
 
import requests
import pymongo
from pymonogo import MongoClient

def main():
    client = MongoClient(DB_URL)
    db = client['CellTower_DB']
    collection = db['CellTower_Collection']
    rogue_db = client['Rogue_DB']
    rogue_collection = rogue_db['Rogue_Collection']
    findRogueTowers()


def findRogueTowers():
    # Iterates through DetectorData table
    cursor = collection.find()
    while cursor.hasNext() :
        document = cursor.next()
        cellid = row[4]
        mcc = row[5]
        mnc = row[6]
        lac = row[7]
        
        # Makes API request
        request = 'https://api.mylnikov.org/geolocation/cell?v=1.1&data=open&mcc=%s&mnc=%s&lac=%s&cellid=%s' % (mcc, mnc, lac, cellid)
        r = requests.get(request)
        if(r.status_code == 404) :
            print "Document Added to Rogue DB: %s" % cellid
            rogue_collection.insert_one(document)

def listCellTowers():
    print collection.distinct('Cell_ID')

#def maponeCellTower():
#def mapallCellTowers_Together():
#def mappallCellTowers_Individually():


            

if __name__ == "__main__":
    main()


'''
document = {'time': time,
 'arfcn': arfcn,
 'rxl': rxl, 
 'bsic': bsic, 
 'Cell_ID': Cell_ID,
 'MCC': MCC,
 'MNC': MNC,
 'LAC': LAC, 
 'Lat': Lat,
 'Lon': Lon, 
 'Satellites': Satellites,
 'GPS_quality': GPS_quality,
 'Altitude': Altitude,
 'Altitude_units': Altitude_units
}
'''