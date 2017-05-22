import sqlite3

def main():
    conn = sqlite3.connect('test.db')
    cursor = conn.cursor() 
    cursor.execute("CREATE TABLE IF NOT EXISTS CellTowerData(t text, arfcn integer, rxl integer, bsic integer, Cell_ID text, MCC integer, MNC integer, LAC text, lat real, lon real, satellites integer, gps_quality integer, altitude real, altitude_units text)")
    conn.commit()

    location = "$GPGGA,195718.000,3236.3567,N,08529.2146,W,1,05,1.47,180.6,M,-29.4,M,,*53"
    location = location.split(',')
    t = location[1]       
    if(location[3] == 'N'):
    	lat = float(location[2])
    else:
		lat = float(location[2]) * -1
    if(location[5] == 'E'):
        lon = float(location[4])
    else:
        lon = float(location[4]) * -1   
    satellites = int(location[7])
    gps_quality = int(location[6])
    altitude = float(location[8])
    altitude_units = location[9]

    cell = "+CENG:1,\"0612,26,56,4577,310,260,8e2\""
    cell = cell.split(',')
    arfcn = int(cell[1][1:]) 
    rxl = int(cell[2]) 
    bsic = int(cell[3])     
    Cell_ID = cell[4]       
    MCC = int(cell[5])      
    MNC = int(cell[6])   
    LAC = cell[7][:-1]

    cursor.execute("INSERT INTO CellTowerData(t, arfcn, rxl, bsic, Cell_ID, MCC, MNC, LAC, lat, lon, satellites, gps_quality, altitude, altitude_units) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", 
    	(t, arfcn, rxl, bsic, Cell_ID, MCC, MNC, LAC, lat, lon, satellites, gps_quality, altitude, altitude_units))
    conn.commit()

    conn.close()


if __name__ == "__main__":
	main();