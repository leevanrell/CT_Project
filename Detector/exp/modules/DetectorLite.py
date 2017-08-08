#!/usr/bin/python
from time import sleep # used to sleep
import serial # used for serial connection
import os # 
import socket # used to test connectivity
import requests # used for POST requests
import json # used for making jason object (json.dumps)
import csv # used for creating csv
import pynmea2 # used for parsing gps/nmea sentences
import datetime # used for creating csv
import time # 
import shutil

class Detector(object):
    def __init__(self, log, HTTP_SERVER, SIM_TTY, GPS_TTY, RATE):
        self.log = log
        self.HTTP_SERVER = HTTP_SERVER
        self.SIM_TTY = SIM_TTY # sim serial address 
        self.GPS_TTY = GPS_TTY # gps serial address
        self.RATE = RATE

    def run():
        running = True
        while running:
            try:
                parse_data()
            except (KeyboardInterrupt, SystemExit):
                running = False
        update_remote()

    def parse_data():
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
             'MCC': int(MCC),
             'MNC': int(MNC),
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
                sleep(self.RATE)
            else:
                log.info('Data] dropped bad document: %s %s %s %s %s' % (MCC, MNC, LAC, Cell_ID, rxl))
                
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
        try:
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
        return len(output) != 0 and check[0] == '$GPGGA' and len(check) >= 6 and int(check[6]) != 0 # we only want GPGGA sentences with an actual fix (Fix != 0)

    def update_local(document):
            FOLDER = 'data/' + str(datetime.date.today())
            FILE = FOLDER  + '/table.csv'
            if not os.path.exists(FOLDER):
                os.makedirs(FOLDER)
                clean_data()
                with open(FILE, 'w') as f:
                    writer = csv.writer(f)
                    writer.writerow(['time', 'MCC', 'MNC', 'LAC', 'Cell_ID', 'rxl', 'arfcn', 'bsic', 'lat', 'lon', 'satellites', 'GPS_quality', 'altitude', 'altitude_units']) # header row
                    writer.writerow(document)
            else:
                with open(FILE, 'a') as f:
                    writer = csv.writer(f)
                    writer.writerow(document)
    def clean_data():
        for FOLDER in os.listdir('data/'):
            FILE = 'data/' + FOLDER + '/table.csv'
            difference = datetime.datetime.now() - datetime.datetime.fromtimestamp(os.path.getmtime(FILE)) # gets time when table.csv was last edited
            if difference.days > 5:
                shutil.rmtree('data/' + FOLDER)

    def update_remote(document):
        start = time.time()
        while not q.empty() and  time.time() - start < 10: 
            if self.isConnected(): # ensures there is a connection to internet/server
                r = requests.post(HTTP_SERVER, data=json.dumps(document)) # converts to json and sends post request
                if r.status_code != 200:
                    q.add(document) # add back to queue if post fails
                    log.info('Logger] Error: status code: %s' % r.status_code)
                else:
                    log.info('Logger] uploaded document')
            else:
               log.info('Logger] Error: no internet connection')
               sleep(.5)

    def isConnected(self): # checks to see if detector can connect to the http server
        try:
            socket.create_connection((HTTP_SERVER, 80)) # connect to the host -- tells us if the host is actually reachable
            return True
        except OSError:
            pass
        return False