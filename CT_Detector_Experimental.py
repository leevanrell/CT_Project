#!/usr/bin/python

import threading
import time
import serial
import sqlite3
import os

# Configures Sim900 
# Sets to Engineering mode     
def setup_SIM():
    SIM_Serial.open()
    
    # Sends Command to SIM Unit, configures Engineering mode
    # AT+CENG=<mode>.<Ncell> : mode = switch on engineering mode, Ncell = display neighbor cell ID
    SIM_Serial.write('AT+CENG=1,1' + '\r\n')
    time.sleep(.5) # Need to wait for device to receive commands
    
    SIM_Serial.close()

# Returns Array of Strings
# Each string represents a cell tower and contains the cell tower's Metadata
def getCellTowers():
    SIM_Serial.open()
    
    # Sends Command to Display current engineering mode settings, serving cell and neighboring cells
    # We only care about the serving cell and neighboring cell data; We'll cut the rest
    SIM_Serial.write('AT+CENG?' + '\r\n')
    time.sleep(.5) # Need to wait for device to receive commands 

    # Reads in SIM900 output
    global SIM_Output
    SIM_Output = ''
    while SIM_Serial.inWaiting() > 0:
        SIM_Output += SIM_Serial.read(6) 
    SIM_Serial.close()

    # Removes Excess Lines and packs into array
    SIM_Output = SIM_Output.split('\n')
    SIM_Output = SIM_Output[4:11]

# Returns a String
# Contains GPS data 
def getLocation():
    GPS_Serial.open()

    global GPS_Output
    GPS_Output = GPS_Serial.readline()
    while isValidLocation(GPS_Output) == False:
        print '\t\tNo Fix'
        time.sleep(.5) # Need to wait before collecting data
        GPS_Output = GPS_Serial.readline()
    GPS_Serial.close()
    print '\t\tFix'

# Returns bool 
# Only returns true if output contains valid gps data
def isValidLocation(output):
    check = output.split(',')
    # We only want GPGGA sentences;
    # Checks to see if we have a fix; 1 is fix, 2 is a differential fix.
    return len(output) != 0 and check[0] == '$GPGGA' and (int(check[6]) == 2 or int(check[6]) == 1)
    
class GPS_Poller(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        print '\tGPS Thread Started:'
        getLocation();
        print '\tGPS Thread Finished'

class SIM_Poller(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        print '\tSIM Thread Started:'
        getCellTowers();
        print '\tSIM Thread Finished'

def main():
    #Creates DB for Cell Towers and GPS coords
    conn = sqlite3.connect('CellTowers.db')
    cursor = conn.cursor() 
    cursor.execute('''CREATE TABLE IF NOT EXISTS DetectorData(t text, arfcn integer, rxl integer, bsic integer, Cell_ID text, MCC integer, MNC integer, LAC text, lat real, lon real, satellites integer, gps_quality integer, altitude real, altitude_units text);''')
    conn.commit()

    setup_SIM() # Configures SIM module to output Cell Tower Meta Data
    GPS_Thread = GPS_Poller()
    SIM_Thread = SIM_Poller()

    run = True;
    while(run == True):
        try: 
            #Starts Threads
            print 'Starting Threads:'
            GPS_Thread.start()
            SIM_Thread.start()

            #Waits for Threads to finish
            GPS_Thread.join()
            SIM_Thread.join()

            location = GPS_Output # Gets Location data.
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
            
            cell_towers = SIM_Output # Gets Array of Cell tower data
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
                print t, ': Added Entry to Database'
        
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
        # Can also configure port accordingly
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

