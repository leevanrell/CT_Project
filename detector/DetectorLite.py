#!/usr/bin/python
LED_gpio = 3 # GPIO pin for LED 
button_gpio = 23 # GPIO pin for Button
import serial # used for serial connection
import argparse # handles args
import Queue # used for queue for threads
import os # 
import sys # used to check for sudo
import socket # used to test connectivity
import requests # used for POST requests
import json # used for making jason object (json.dumps)
import csv # used for creating csv
import pynmea2 # used for parsing gps/nmea sentences
import datetime # used for creating csv
import time # 
from time import sleep # used to sleep

import logging
log = logging.getLogger()
log.setLevel('DEBUG')
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('[%(asctime)s] [Detector.%(message)s'))
log.addHandler(handler)


def setup_TTY(): # finds the TTY addresses for SIM and GPS unit if available 
    log.info('setup] setting TTY connections')
    retry = 0 
    configured_SIM = setup_SIM_TTY() # tries to figure out tty address for SIM
    while not configured_SIM and retry < 5: # setup_SIM_TTY is buggy so its worth trying again to find the correct address
        retry += 1
        log.info('setup] retrying SIM TTY config')
        configured_SIM = setup_SIM_TTY() 
    retry = 0
    configured_GPS = setup_GPS_TTY()
    while not configured_GPS and retry < 5: # setup_SIM_TTY is also inconsistent -- running a few times guarantees finding the correct address if its exists
        retry += 1
        log.info('setup] retrying GPS TTY config')
        configured_GPS = setup_GPS_TTY() 
    if not configured_GPS or not configured_SIM: # if gps or sim fail then program gives up
        log.info('setup] Error: failed to configure TTY: GPS - %s, SIM - %s' % (configured_GPS, configured_SIM))
        quit()

def setup_SIM_TTY(): # finds the correct tty address for the sim unit 
    count = 0
    global SIM_TTY
    while count < 10: # iterates through the first 10 ttyUSB# addresses until it finds the correct address
        SIM_TTY = '/dev/ttyUSB%s' % count 
        try:
            Serial = serial.Serial(port=SIM_TTY, baudrate=115200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=0)
            Serial.write('AT' + '\r\n') # sends AT command
            sleep(.5)
            for i in range(0, 5):
                check = Serial.readline()
                if check == 'OK\r\n':
                    log.info('setup] set SIM_TTY to ' + SIM_TTY)
                    return True
            Serial.close()
        except serial.SerialException as e:# throws exception if there is no tty device on the current address
                count += 1
        count += 1  
    return False

def setup_GPS_TTY(): # finds the correct tty address for the GPS unit
    count = 0
    global GPS_TTY
    while count < 10:
        GPS_TTY = '/dev/ttyUSB%s' % count
        try:
            check = test_GPS(9600) # tries default baud rate first         
            if check:
                return True
            else:
                check = test_GPS(115200) # tries configured baud rate 
                if check: 
                    return True
                else:
                    count += 1
        except serial.SerialException as e:
            count += 1 
    return False

def test_GPS(baudrate):
    Serial = serial.Serial(port=GPS_TTY, baudrate=baudrate, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=0)
    sleep(.5)
    check = Serial.readline()
    Serial.close()
    if check[:1] == '$': # looks for $
        log.info('setup] set GPS_TTY to ' + GPS_TTY)
        return True
    return False

def setup_SIM(): # configures sim unit to engineering mode -- outputs cell tower meta data
    log.info('setup] configuring SIM')
    try:
        SIM_Serial = serial.Serial(port=SIM_TTY, baudrate=115200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=0)
        SIM_Serial.write('AT+CENG=1,1' + '\r\n') # command to set to eng mode
        sleep(.5) # need to wait for device to receive commands
        SIM_Serial.close()
    except serial.SerialException as e:
        log.info('setup] Error: lost connection to SIM unit')
        quit()

def setup_GPS(): # configures gps unit; increase baudrate, output fmt, and output interval
    log.info('setup] configuring GPS')
    try:
        GPS_Serial = serial.Serial(port=GPS_TTY, baudrate=9600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=0)  
        sleep(.5)
        GPS_Serial.write('$PMTK314,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0*29<CR><LF> ' + '\r\n') #Configures GPS to only output GPGGA Sentences
        sleep(.5) # need to wait for device to receive commands
        GPS_Serial.write('$PMTK220,100*2F<CR><LF>' + '\r\n') # configures fix interval to 100 ms
        sleep(.5)
        GPS_Serial.write('$PMTK251,115200*1F<CR><LF>' + '\r\n') # configures Baud Rate to 115200
        sleep(.5)
        GPS_Serial.close() 
    except serial.SerialException as e:
        log.info('setup] Error: lost connection to GPS unit')
        quit()  

def start():
    run = True
    while run:
        try:
            cell_towers = getCell() # gets array of Cell tower data (contains ~5-6 lines each representing a cell tower in the surrounding area)
            location = pynmea2.parse(getLocation()) # converts GPS data to nmea object 
            for i in range(len(cell_towers)):
                cell_tower = cell_towers[i].split(',')
                arfcn = cell_tower[1][1:]         # Absolute radio frequency channel number
                rxl = cell_tower[2]               # Receive level (signal stregnth)
                # data in first (serving) cell is ordered differently than first cell,
                if(i == 0): # +CENG:0, '<arfcn>, <rxl>, <rxq>, <mcc>, <mnc>, <bsic>, <cellid>, <rla>, <txp>, <lac>, <TA>'
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
                # puts data into json compatible format
                document = {'time': time.strftime('%m-%d-%y %H:%M:%S'),
                 'MCC': MCC,
                 'MNC': MNC,
                 'LAC': LAC, 
                 'Cell_ID': Cell_ID,
                 'rxl': int(rxl), 
                 'arfcn': arfcn,
                 'bsic': bsic, 
                 'lat': location.latitude,
                 'lon': location.longitude, 
                 'satellites':  int(location.num_sats),
                 'GPS_quality': int(location.gps_qual),
                 'altitude': location.altitude,
                 'altitude_units': location.altitude_units
                }
                if(rxl > 7 and rxl != 255 and MCC != '0'): # filters out data points with lower receive strengths -- the data tends to get 'dirty' when the rxl is < 5~10
                    log.info('Data] added document to queue')
                    q.add(document)
                    update_local(document)
                    update_remote()
                    sleep(RATE)
                else:
                    log.info('Data] dropped bad document: %s %s %s %s %s' % (MCC, MNC, LAC, Cell_ID, rxl))
        except (KeyboardInterrupt, SystemExit):
            run = False:
    update_remote()
        
def getCell():
    try:
        SIM_Serial = serial.Serial(port=SIM_TTY, baudrate=115200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=0)
        SIM_Serial.write('AT+CENG?' + '\r\n')  # Sends Command to Display current engineering mode settings, serving cell and neighboring cells
        sleep(.1) # Need to wait for device to receive commands 
        SIM_Output = ''
        while SIM_Serial.inWaiting() > 0:
            SIM_Output += SIM_Serial.read(6) # Reads in SIM900 output
        SIM_Serial.close()
        SIM_Output = SIM_Output.split('\n')[4:11] # \Removes Excess Lines
        return SIM_Output
    except serial.SerialException as e:
        log.info('GPS] Error: something got unplugged!') # error handling encase connection to sim unit is lost
        quit()

def getLocation():
    try
        GPS_Serial = serial.Serial(port=GPS_TTY, baudrate=115200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=0)     
        sleep(.1)
        GPS_Output = GPS_Serial.readline()
        while not isValidLocation(self.GPS_Output): # loops until has a valid GPS fix or until run time is more than 10 sec
            sleep(.1) # Need to wait before collecting data
            self.GPS_Output = GPS_Serial.readline()
        GPS_Serial.close()
        return GPS_Output
    except serial.SerialException as e:
        log.info('GPS] Error: something got unplugged!') # error handling encase connection to sim unit is lost
        quit()

def isValidLocation(output): # checks string to confirm it contains valid coordinates
    check = output.split(',')
    return len(output) != 0 and check[0] == '$GPGGA' and len(check[6]) != 0 and int(check[6]) != 0 # we only want GPGGA sentences with an actual fix (Fix != 0)

def update_local(document):
        FOLDER = 'data/' + str(datetime.date.today())
        FILE = FOLDER  + '/table.csv'
        if not os.path.exists(FOLDER):
            os.makedirs(FOLDER)
            with open(FILE, 'w') as f:
                writer = csv.writer(f)
                writer.writerow(['time', 'MCC', 'MNC', 'LAC', 'Cell_ID', 'rxl', 'arfcn', 'bsic', 'lat', 'lon', 'satellites', 'GPS_quality', 'altitude', 'altitude_units']) # header row
                writer.writerow(document)
        else:
            with open(FILE, 'a') as f:
                writer = csv.writer(f)
                writer.writerow(document)

def update_remote():
    start = time.time()
    while not q.empty() and  time.time() - start < 10: # ensures there is a connection to internet/server
        if self.isConnected():
            document = q.get()
            headers = {'content-type': 'application/json'}
            r = requests.post(HTTP_SERVER, data=json.dumps(document), headers=headers)
            #r = requests.post(HTTP_SERVER, data=json.dumps(document)) # converts to json and sends post request
            if r.status_code != 200:
                q.add(document) # add back to queue if post fails
                log.info('Logger] Error: status code: %s' % r.status_code)
            else:
                log.info('Logger] uploaded document')
        else:
           log.info('Logger] Error: no internet connection')
           sleep(1)

def isConnected(self): # checks to see if detector can connect to the http server
    try:
        socket.create_connection((HTTP_SERVER, 3000)) # connect to the host -- tells us if the host is actually reachable
        return True
    except OSError:
        pass
    return False

def main():
    setup_TTY() # configures TTY addresses for SIM and GPS
    setup_SIM() # configures SIM module to output cell tower meta data
    setup_GPS() # configures GPS module to only output GPGGA Sentences and increases operating speed
    start()

if __name__ == '__main__':
    if not os.geteuid() == 0:
        log.info('setup] Error: script must be run as root!')
        quit()
    parser = argparse.ArgumentParser(description='SIR Detector')
    parser.add_argument('-m', '--mode', default=False, help='configures detector to run on laptop/pi; options: pi/laptop') #, action='store', dest='mode')
    parser.add_argument('-s', '--server', default="http://localhost:3000/data", help='sets address and port of http server;') #, action='store', dest='mode')
    parser.add_argument('-r', '--rate', default=5, help='delay between successfully finding a data point and attempting to find another') #, action='store', dest='mode')  
    args = parser.parse_args()
    HTTP_SERVER = 'http://%s:3000/data' % args.server if(args.server[:4] != 'http') else args.server
    MODE = True if args.mode == 'pi'else False
    RATE = args.rate
    SIM_TTY = '' # sim serial address 
    GPS_TTY = '' # gps serial address
    q = Queue.Queue() # Using queue to share data between two threads
    main()