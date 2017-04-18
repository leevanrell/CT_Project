import time
import serial
import sqlite3
import gps
import os

# Configures Sim900 
# Sets to Engineering mode     
def setup_SIM():

    SIM_Serial.open()

    # AT+CENG=<mode>.<Ncell> : mode = switch on engineering mode, Ncell = display neighbor cell ID
    SIM_Serial.write('AT+CENG=1,1' + '\r\n')

    # Need to wait for device to receive commands
    time.sleep(.5) 

    SIM_Serial.close()


# Returns Array of Strings
# Each string represents a cell tower and contains the cell tower's Metadata
def getCellTowers():
    
    SIM_Serial.open()

    # Displays current engineering mode settings, serving cell and neighboring cells
    # We only care about the serving cell and neighboring cell data; We'll cut the res
    SIM_Serial.write('AT+CENG?' + '\r\n')
    
    # Need to wait for device to receive commands
    time.sleep(.5) 

    # Reads in Sim900 output
    SIM_Output = ''
    while SIM_Serial.inWaiting() > 0:
        SIM_Output += SIM_Serial.read(6) 
    
    SIM_Serial.close()

    # Removes Excess Lines and packs into array
    SIM_Output = SIM_Output.split('\n')
    SIM_Output = SIM_Output[4:11]

    return SIM_Output

# Returns an String
# Contains GPS data 
def getLocation():
    GPS_Serial.open()

    GPS_Output = ''
    while isValidLocation(GPS_Output) == False:
        GPS_Output = GPS_Serial.readline()
        print GPS_Output # This is just for debugging
    
    GPS_Serial.close()

    return GPS_Output

# Returns bool 
# Only returns true if output contains valid gps data
def isValidLocation(output):
    if(len(output) == 0):
        return "Invalid Location" # Debug
        return False

    check = output.split(',')
    # We only want GPGGA sentences;
    if(output[0] == "$GPGGA"):
        # Checks to see if we have a fix; 1 is fix, 2 is a differential fix.
        return output[6] == 1 or output[6] == 2
    else:
        print "Invalid Location" # Debug
        return False

def main():
    #Creates DB for towers and Gps coords
    conn = sqlite3.connect('celltowers.db')
    cursor = conn.cursor() 
    cursor.execute('''CREATE TABLE IF NOT EXISTS CellTowerData(
        t text, 
        arfcn integer, 
        rxl integer,
        bsic integer,
        Cell_ID text, 
        MCC integer,
        MNC integer,
        LAC integer,
        lat real,
        lon real,
        satellites integer, 
        gps_quality integer, 
        altitude integer,
        altitude_units text
        );''')
    conn.commit()

    # Configures SIM module to output Cell Tower Meta Data
    setup_SIM()


    # IMMPLEMENT LOOP
    # I need a way to loop infinitely until a key is pressed and then exits gracefully


    # Gets Location data.
    # $GPGGA, time, lat, N or S, lon, E or W, Quality Indicator, No. of Satellites, 
    # Precision, Altitude, Units, Separation, Units, Age, Differential reference station ID, 
    location = getLocation();
    
    # Now we need to process some of the data
    t = location[1]
    # We need to convert lat and lon
    # N, E are positive
    # S, W are negative
    if(location[3] == 'N'):
        lat = float(location[2])
    else:
        lat = float(location[2]) * -1
    if(location[5] == 'E'):
        lon = float(location[4])
    else:
        lon = float(ocation[4]) * -1
    satellites = location[7]
    gps_quality = location[6]
    altitude = location[8]
    altitude_units = location[9]
    
    # Gets Array of Cell tower data
    # Each indices contains data on a single Tower
    cell_towers = getCellTowers()

    for i in range(len(cell_towers)):
       
        # Data in first (serving) cell is ordered differently than first cell,
        # +CENG:0, "<arfcn>, <rxl>, <rxq>, <mcc>, <mnc>, <bsic>, <cellid>, <rla>, <txp>, <lac>, <TA>"
        cell = cell_towers[i]
        cell = s.split(',')

        if(i == 0):
            arfcn = int(cell[1])
            rxl = int(cell[2])
            bsic = int(cell[6])
            Cell_ID = int(cell[7])
            MCC = int(cell[4])
            MNC = int(cell[5])
            LAC = int(cell[10])

        # +CENG:1+,"<arfcn>, <rxl>, <bsic>, <cellid>, <mcc>, <mnc>, <lac>"    
        else:
            arfcn = int(cell[1])
            rxl = int(cell[2])
            bsic = int(cell[3])
            Cell_ID = int(cell[4])
            MCC = int(cell[5])
            MNC = int(cell[6])
            LAC = int(cell[7])
    cursor.execute('''INSERT INTO CellTowerData(t, arfcn, rxl, 
            bsic, Cell_ID, MCC, MNC, LAC, lat, lon, satellites,
            gps_quality, altitude, altitude_units) ''', (t, arfcn, rxl, 
            bsic, Cell_ID, MCC, MNC, LAC, lat, lon, satellites,
            gps_quality, altitude, altitude_units))
    conn.commit()



    conn.close()


if __name__ == "__main__":
    # Exception handling in case the devices aren't plugged in or the units get disconnected
    try:
        # Plug in the SIM unit first or the program won't work
        SIM_Serial = serial.Serial(
            port='/dev/ttyUSB0',
            baudrate=9600,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=0
        )
        SIM_Serial.close()
    except serial.SerialException as e:
        print "SIM is not plugged in!"
        print "Quiting Program."
        quit()

    try:
        # Plug in the GPS unit last!
        GPS_Serial = serial.Serial(
            port='/dev/ttyUSB1',
            baudrate=9600,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=0
        )
        GPS_Serial.close()
    except serial.SerialException as e:
        print "GPS is not plugged in!"
        print "Quiting Program."
        quit()
    
    try:
        main()
    except serial.SerialException as e:
        print "Something Got unplugged!"
        print "Quitting Program."
        quit()

