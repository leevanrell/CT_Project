#!/usr/bin/python

import sqlite3
from urllib2 import Request, urlopen, URLError

def main():
    conn = sqlite3.connect('CellTowers.db')
    c1= conn.cursor()
    c1.execute('SELECT * FROM DetectorData')

    c2 = conn.cursor() 
    # Creates table to store rogue cell tower's data
    c2.execute('''CREATE TABLE IF NOT EXISTS RogueData(t text, arfcn integer, rxl integer, bsic integer, Cell_ID text, MCC integer, MNC integer, LAC text, lat real, lon real, satellites integer, gps_quality integer, altitude real, altitude_units text);''')
    c2.commit()

    # Iterates through DetectorData table
    for row in c1:
        cellid = row[4]
        mcc = row[5]
        mnc = row[6]
        lac = row[7]
		
		# Makes API request
        request_str = 'https://api.mylnikov.org/geolocation/cell?v=1.1&data=open&mcc=%s&mnc=%s&lac=%s&cellid=%s' % (mcc, mnc, lac, cellid)
        request = Request(request_str)
        try:
            response = urlopen(request)
            check = response.read()
			# Gets code from API response
			# 200 = Tower is in DB and 404 = Tower is not found
            code = int(check[14:18])
            if(code == 404) :
				# adds row to Rogue Cell Tower DB
                print "Tower Added to Rogue DB:"
                print "\tCell id : %s" $ cellid
                c2.execute('INSERT INTO RogueData(t, arfcn, rxl, bsic, Cell_ID, MCC, MNC, LAC, lat, lon, satellites, gps_quality, altitude, altitude_units) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', row)
        except URLError, e:
            print 'URL Error: ', e
            quit()
    conn.close()

if __name__ == "__main__":
    main()