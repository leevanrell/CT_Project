import time
import serial
import sqlite3
import os

def main():
    conn = sqlite3.connect('test.db')
    cursor = conn.cursor() 
    cursor.execute("CREATE TABLE IF NOT EXISTS CellTowerData(t text, arfcn integer, rxl integer, bsic integer, Cell_ID text, MCC integer, MNC integer, LAC text, lat real, lon real, satellites integer, gps_quality integer, altitude real, altitude_units text)")
   
    conn.commit()

    t = "1230.1234"
    arfcn = 1234
    rxl = 12345
    bsic = 1234
    Cell_ID = "8e9"
    MCC = 1234
    MNC = 1234
    LAC = "12341"
    lat = 12.123
    lon = 12.123
    satellites = 3
    gps_quality = 2
    altitude = 13.01
    altitude_units = "M"

    cursor.execute("INSERT INTO CellTowerData(t, arfcn, rxl, bsic, Cell_ID, MCC, MNC, LAC, lat, lon, satellites, gps_quality, altitude, altitude_units) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", 
    	(t, arfcn, rxl, bsic, Cell_ID, MCC, MNC, LAC, lat, lon, satellites, gps_quality, altitude, altitude_units))

	# cur.execute("insert into contacts (name, phone, email) values (?, ?, ?)",
    #       (name, phone, email))

    conn.commit()


if __name__ == "__main__":
	main();