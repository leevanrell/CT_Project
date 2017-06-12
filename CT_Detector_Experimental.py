#!/usr/bin/python
SIM_TTY = '/dev/ttyUSB0'
GPS_TTY = '/dev/ttyUSB1'
DB_URL = 'mongodb://localhost:27017/'

import threading
import serial
#import os
import Queue
import pymongo
import socket
from time import sleep
def setupTTY(SIM_TTY, GPS_TTY):
    try:
        # Plug in the SIM unit first or the program won't work
        # Can also configure TTY port accordingly
        global SIM_Serial
        SIM_Serial = serial.Serial(port=SIM_TTY, baudrate=115200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=0)
        SIM_Serial.close()
    except serial.SerialException as e:
        print 'SIM is not plugged in!'
        print 'Quiting Program.'
        quit()
    try:
        # Plug in the GPS unit last!
        global GPS_Serial
        GPS_Serial = serial.Serial(port=GPS_TTY, baudrate=9600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=0)  
        GPS_Serial.close()
    except serial.SerialException as e:
        print 'GPS is not plugged in!'
        print 'Quiting Program.'
        quit()

# Configures SIM900 to Engineering mode   
def setupSIM():
    SIM_Serial.open()
    # AT+CENG=<mode>.<Ncell> : mode = switch on engineering mode, Ncell = display neighbor cell ID
    SIM_Serial.write('AT+CENG=1,1' + '\r\n') # Configures SIM unit to Engineering mode
    sleep(.5) # Need to wait for device to receive commands
    SIM_Serial.close()

#Configures GPS Unit
def setupGPS():
    GPS_Serial.open()
    sleep(5)
    ser.write('$PMTK314,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0*29<CR><LF> ' + '\r\n') #Configures GPS to only output GPGGA Sentences
    sleep(1) # Need to wait for device to receive commands
    ser.write('$PMTK220,100*2F<CR><LF>' + '\r\n') # Configures Fix interval to 100 ms
    sleep(1)
    ser.write('$PMTK251,115200*1F<CR><LF>' + '\r\n') # Configures Baud Rate to 115200
    sleep(1)
    GPS_Serial = serial.Serial(port=GPS_TTY, baudrate=115200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=0)  
    GPS_Serial.close()   

class DataThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.running = True
    def run(self):
        GPS_Thread = GPS_Poller()
        SIM_Thread = SIM_Poller()
        while self.running:
            # Starts Threads
            GPS_Thread.start()
            SIM_Thread.start()
            # Waits for Threads to finish
            GPS_Thread.join()
            SIM_Thread.join()

            location = GPS_Thread.GPS_Output # Gets Location data.
            #location = location.split(',')
            # Now we need to process some of the data
            time = location[1]
            if(location[3] == 'N'):
                Lat = float(location[2]) # N, E is positive
            else:
                Lat = float(location[2]) * -1 # S, W is negative
            if(location[5] == 'E'):
                Lon = float(location[4])
            else:
                Lon = float(location[4]) * -1
            GPS_quality = int(location[6])
            Satellites = int(location[7])
            Altitude = float(location[8])
            Altitude_units = location[9]
            
            cell_towers = SIM_Thread.SIM_Output # Gets Array of Cell tower data
            #for i in range(len(cell_towers)):
            for cell_tower in cell_towers  
                # Data in first (serving) cell is ordered differently than first cell,
                # +CENG:0, '<arfcn>, <rxl>, <rxq>, <mcc>, <mnc>, <bsic>, <cellid>, <rla>, <txp>, <lac>, <TA>'
                # cell = cell_towers[i]
                cell_tower = cell.split(',')
                arfcn = int(cell_tower[1][1:])    # Absolute radio frequency channel number
                rxl = int(cell_tower[2])          # Receive level (signal stregnth)
                if(i == 0):
                    bsic = int(cell_tower[6])     # Base station identity code
                    Cell_ID = cell_tower[7]       # Unique Identifier
                    MCC = int(cell_tower[4])      # Mobile Country Code
                    MNC = int(cell_tower[5])      # Mobile Network Code
                    LAC = cell_tower[10]          # Location Area code
                # +CENG:1+,'<arfcn>, <rxl>, <bsic>, <cellid>, <mcc>, <mnc>, <lac>'    
                else:
                    bsic = int(cell_tower[3])     # Base station identity code
                    Cell_ID = cell_tower[4]       # Unique Identifier
                    MCC = int(cell_tower[5])      # Mobile Country Code
                    MNC = int(cell_tower[6])      # Mobile Network Code
                    LAC = cell_tower[7][:-1]      # Location Area code
                entry = {'time': time,
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
                if(rxl > 1):
                    q.put(entry)

    class GPS_Poller(threading.Thread):
        def __init__(self):
            threading.Thread.__init__(self)
            self.GPS_Output

        def run(self):
            GPS_Serial.open()
            GPS_Output = GPS_Serial.readline()
            while not isValidLocation(GPS_Output):
                sleep(.1) # Need to wait before collecting data
                GPS_Output = GPS_Serial.readline()
            GPS_Serial.close()
            GPS_Output = GPS_Output.split(',')
            self.GPS_Output = GPS_Output

        def isValidLocation(output):
            check = output.split(',')
            return len(output) != 0 and check[0] == '$GPGGA' and int(check[6]) != 0 # We only want GPGGA sentences with an Actual Fix (Fix != 0)

    class SIM_Poller(threading.Thread):
        def __init__(self):
            threading.Thread.__init__(self)
            self.SIM_Output
        def run(self):
            SIM_Serial.open() 
            SIM_Serial.write('AT+CENG?' + '\r\n')  # Sends Command to Display current engineering mode settings, serving cell and neighboring cells
            sleep(.1) # Need to wait for device to receive commands 
            # Reads in SIM900 output
            SIM_Output = ''
            while SIM_Serial.inWaiting() > 0:
                SIM_Output += SIM_Serial.read(6) 
            SIM_Serial.close()
            # Removes Excess Lines and packs into array
            SIM_Output = SIM_Output.split('\n')
            SIM_Output = SIM_Output[4:11]
            self.SIM_Output = SIM_Output

class LoggingThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.client = MongoClient(DB_URL)
        self.db = client.CellTower_DB 
        self.collection = db.CellTower_Collection
        self.running = True
    def run(self):
        while self.running:
            while isConnected() and not q.empty():
                collection.insert_one(q.get())
            sleep(.5)
    def isConnected():
        try:
            socket.create_connection(("www.google.com", 80)) # connect to the host -- tells us if the host is actuallyreachable
            return True
        except OSError:
            pass
        return False


def main():
    setupTTY(SIM_TTY, GPS_TTY)
    setupSIM() # Configures SIM module to output Cell Tower Meta Data
    setupGPS() # Configures GPS module to only output GPGGA Sentences, also makes GPS Hella Fast
    global q
    q = Queue.Queue()
    Data = DataThread()
    Log = LoggingThread()
    try:
        Data.start() # Get this ish running
        Log.start()
        while True 
            sleep(.5)
    except (KeyboardInterrupt, SystemExit): # when you press ctrl+c
        print '\nKilling Thread...'
        Data.running = False
        Log.running = False
        Data.join() # wait for the thread to finish what it's doing
        Log.join()
    print 'Done.\nExiting.'

if __name__ == '__main__':
    main()