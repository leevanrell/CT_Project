#!/usr/bin/python

import time
import serial
import sqlite3
import os

# Configures Sim900 
# Sets to Engineering mode     
def setup_SIM():   
    SIM_Serial.open()
    
    # AT+CENG=<mode>.<Ncell> : mode = switch on engineering mode, Ncell = display neighbor cell ID
    SIM_Serial.write('AT+CENG=1,1' + '\r\n')
    time.sleep(.5) # Need to wait for device to receive commands
    
    SIM_Serial.close()

# Returns Array of Strings
# Each string represents a cell tower and contains the cell tower's Metadata
def getCellTowers():
    SIM_Serial.open()
    
    # Displays current engineering mode settings, serving cell and neighboring cells
    # We only care about the serving cell and neighboring cell data; We'll cut the rest
    SIM_Serial.write('AT+CENG?' + '\r\n')
    time.sleep(.5) # Need to wait for device to receive commands 

    # Reads in Sim900 output
    SIM_Output = ''
    while SIM_Serial.inWaiting() > 0:
        SIM_Output += SIM_Serial.read(6) 
    SIM_Serial.close()

    # Removes Excess Lines and packs into array
    SIM_Output = SIM_Output.split('\n')
    SIM_Output = SIM_Output[4:11]

    return SIM_Output

# Returns a String
# Contains GPS data 
def getLocation():
    GPS_Serial.open()

    GPS_Output = GPS_Serial.readline()
    while isValidLocation(GPS_Output) == False:
        print 'No Fix'
        time.sleep(.5) # Need to wait before collecting data
        GPS_Output = GPS_Serial.readline()
    GPS_Serial.close()
    print 'Fix'
    return GPS_Output

# Returns bool 
# Only returns true if output contains valid gps data
def isValidLocation(output):
    check = output.split(',')
    # We only want GPGGA sentences;
    # Checks to see if we have a fix; 1 is fix, 2 is a differential fix.
    return len(output) != 0 and check[0] == '$GPGGA' and int(check[6]) != 0
    
def main():
    #Creates DB for towers and GPS coords
    conn = sqlite3.connect('CellTowers.db')
    cursor = conn.cursor() 
    cursor.execute('''CREATE TABLE IF NOT EXISTS DetectorData(t text, arfcn integer, rxl integer, bsic integer, Cell_ID text, MCC integer, MNC integer, LAC text, lat real, lon real, satellites integer, gps_quality integer, altitude real, altitude_units text);''')
    conn.commit()

    setup_SIM() # Configures SIM module to output Cell Tower Meta Data
    
    run = True;
    while(run == True):
        try: 
            location = getLocation() # Gets Location data.
            location = location.split(',')

            # Now we need to process some of the data
            t = location[1]
            # N, E is positive
            # S, W is negative
            if(location[3] == 'N'):
                lat = float(location[2])
            else:
                lat = float(location[2]) * -1
            if(location[5] == 'E'):
                lon = float(location[4])
            else:
                lon = float(location[4]) * -1
            gps_quality = int(location[6])
            satellites = int(location[7])
            altitude = float(location[8])
            altitude_units = location[9]
            
            cell_towers = getCellTowers() # Gets Array of Cell tower data
            for i in range(len(cell_towers)):
               
                # Data in first (serving) cell is ordered differently than first cell,
                # +CENG:0, '<arfcn>, <rxl>, <rxq>, <mcc>, <mnc>, <bsic>, <cellid>, <rla>, <txp>, <lac>, <TA>'
                cell = cell_towers[i]
                cell = cell.split(',')

                arfcn = int(cell[1][1:])    # Absolute radio frequency channel number
                rxl = int(cell[2])          # Receive level (signal stregnth)
                  
                if(i == 0):
                    bsic = int(cell[6])     # Base station identity code
                    Cell_ID = cell[7]       # Unique Identifier
                    MCC = int(cell[4])      # Mobile Country Code
                    MNC = int(cell[5])      # Mobile Network Code
                    LAC = cell[10]          # Location Area code

                # +CENG:1+,'<arfcn>, <rxl>, <bsic>, <cellid>, <mcc>, <mnc>, <lac>'    
                else:
                    bsic = int(cell[3])     # Base station identity code
                    Cell_ID = cell[4]       # Unique Identifier
                    MCC = int(cell[5])      # Mobile Country Code
                    MNC = int(cell[6])      # Mobile Network Code
                    LAC = cell[7][:-1]      # Location Area code

                # Adds Cell Tower info along with GPS info
                cursor.execute('INSERT INTO DetectorData(t, arfcn, rxl, bsic, Cell_ID, MCC, MNC, LAC, lat, lon, satellites, gps_quality, altitude, altitude_units) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', 
                    (t, arfcn, rxl, bsic, Cell_ID, MCC, MNC, LAC, lat, lon, satellites, gps_quality, altitude, altitude_units))
                conn.commit()
                print '%s: Added Entry to Database' % strtime('%Y-%m-%d %H:%M:%S', gmtime())
        
        # Loops until detects keyboard input
        except KeyboardInterrupt as e:
            print '\nQuiting Program: '
            run = False
            continue
    conn.close()
    print('Exit complete')

if __name__ == '__main__':
    # Exception handling in case the devices aren't plugged in or the units get disconnected
    try:
        # Plug in the SIM unit first or the program won't work
        SIM_Serial = serial.Serial(port='/dev/ttyUSB0', baudrate=115200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=0)
        SIM_Serial.close()
    except serial.SerialException as e:
        print 'SIM is not plugged in!'
        print 'Quiting Program.'
        quit()

    try:
        # Plug in the GPS unit last!
        GPS_Serial = serial.Serial(port='/dev/ttyUSB1', baudrate=9600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=0)  
        GPS_Serial.close()
    except serial.SerialException as e:
        print 'GPS is not plugged in!'
        print 'Quiting Program.'
        quit()
    
    try:
        main()
    except serial.SerialException as e:
        print 'Something Got unplugged!'
        print 'Quitting Program.'
        quit()

