#!/usr/bin/python
QUEUE_SIZE = 10

import serial 
import argparse
import Queue 
import os  
import sys 
import socket 
import requests 
import json 
import csv 
import pynmea2
import datetime 
import time  
from time import sleep
from lib.Setup import Setup
sys.path.append('../')

class DetectorLite():

    def __init__(self, log, HTTP_SERVER, SIM_TTY, GPS_TTY, TIMEOUT, RATE):
        self.run = True
        self.log = log
        self.HTTP_SERVER = HTTP_SERVER
        self.SIM_TTY = SIM_TTY
        self.GPS_TTY = GPS_TTY
        self.TIMEOUT = TIMEOUT
        self.RATE = RATE

    def start(self):
        while self.run:
            try:
                location = self.getLocation()
                cell_towers = self.getCell()
                if location[:5] != "error" and cell_towers[:5] != "error":
                    location = pynmea2.parse(location)
                    for i in range(len(cell_towers)):
                        document = self.getDocument(cell_towers[i], location)
                        if(document['GPS_quality'] != 0 and document['rxl'] > 7 and document['rxl'] != 255 and document['MCC'] != '0'): 
                            self.log.info('Data] added document to queue')
                            self.update_local(document)
                            q.put(document)
                            if q.qsize() >= QUEUE_SIZE:
                                self.update_remote()
                            sleep(self.RATE)
                        else:
                            self.log.debug('Data] dropped bad document: %s %s %s %s %s %s' % (document['GPS_quality'], document['MCC'], document['MNC'], document['LAC'], document['Cell_ID'], document['rxl']))
            except (KeyboardInterrupt, SystemExit):
                self.run = False
        update_remote()
            
    def getCell(self):
        try:
            SIM_Serial = serial.Serial(port=self.SIM_TTY, baudrate=115200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=0)
            SIM_Serial.write('AT+CENG?' + '\r\n')  
            sleep(.1)  
            SIM_Output = ''
            while SIM_Serial.inWaiting() > 0:
                SIM_Output += SIM_Serial.read(6)
            SIM_Serial.close()
            SIM_Output = SIM_Output.split('\n')[4:11] 
            return SIM_Output
        except serial.SerialException as e:
            self.log.error('SIM] something got unplugged!') 
            # TODO: make execution control and error checking not terrible; implement semaphores better
            sleep(1)
            setup = Setup(self.log)
            setup.setup_TTY();
            count = 0
            while not setup.configured and count < 10:
                setup.setup_TTY();
                count += 0
                self.log.error('SIM] Retrying setup: %s', count)
            if not setup.configured:
                self.log.error('SIM] setup failed')
                self.run = False
            else:
                self.SIM_TTY = setup.SIM_TTY
                self.GPS_TTY = setup.GPS_TTY
            return "error"

    def getLocation(self):
        try:
            GPS_Serial = serial.Serial(port=self.GPS_TTY, baudrate=115200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=0)     
            sleep(.1)
            GPS_Output = ""
            GPS_Output = GPS_Serial.readline()
            start = time.time()
            while not self.isValidLocation(GPS_Output) and time.time() - start < self.TIMEOUT: 
                sleep(.1) 
                self.GPS_Output = GPS_Serial.readline()
            GPS_Serial.close()
            if self.isValidLocation(GPS_Output):
                return GPS_Output
            else:
                return 'error: bad gps data'
        except serial.SerialException as e:
            self.log.error('GPS] something got unplugged!') 
            # TODO: make execution control and error checking not terrible; implement semaphores better
            sleep(1)
            setup = Setup(self.log)
            setup.setup_TTY();
            count = 0
            while not setup.configured and count < 10:
                setup.setup_TTY();
                count += 0
                self.log.error('GPS] Retrying setup: %s', count)
            if not setup.configured:
                log.error('GPS] setup failed')
                self.run = False
            else:
                self.SIM_TTY = setup.SIM_TTY
                self.GPS_TTY = setup.GPS_TTY
            return 'error'

    def isValidLocation(self, output):
        check = output.split(',')
        return len(output) != 0 and check[0] == '$GPGGA' and len(check[6]) != 0 and int(check[6]) != 0 # we only want GPGGA sentences with an actual fix (Fix != 0)

    def getDocument(self, cell_tower, location):
        cell_tower = cell_tower.split(',')
        if len(cell_tower) > 6:
            arfcn = cell_tower[1][1:]         # Absolute radio frequency channel number
            rxl = cell_tower[2]               # Receive level (signal stregnth)
            if(len(cell_tower) > 9): # +CENG:0, '<arfcn>, <rxl>, <rxq>, <mcc>, <mnc>, <bsic>, <cellid>, <rla>, <txp>, <lac>, <TA>'
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
        return {'time': time.strftime('%m-%d-%y %H:%M:%S'), 'MCC': MCC, 'MNC': MNC, 'LAC': LAC, 'Cell_ID': Cell_ID, 'rxl': int(rxl), 'arfcn': arfcn, 'bsic': bsic, 'lat': location.latitude, 'lon': location.longitude, 'satellites':  int(location.num_sats), 'GPS_quality': int(location.gps_qual), 'altitude': location.altitude, 'altitude_units': location.altitude_units}

    def update_local(self, document):
            FOLDER = 'data/backup/' 
            FILE = FOLDER  + str(datetime.date.today())+ '.csv'
            fieldnames = ['MCC','MNC','LAC','Cell_ID','rxl','arfcn','bsic','lat','lon','satellites','GPS_quality','altitude','altitude_units']
            if not os.path.exists(FOLDER):
                os.makedirs(FOLDER)
            with open(FILE, 'a') as f:
                writer = csv.Dictwriter(f, fieldnames = fieldnames)
                writer.writerow(dictionary.values())

    def update_remote(self):
        start = time.time()
        while not self.q.empty() and  time.time() - start < 10:
            if self.isConnected():
                try:
                    document = self.q.get()
                    r = requests.post(HTTP_SERVER, data=json.dumps(document), headers={'content-type': 'application/json'})
                    if r.status_code != 200:
                        self.q.add(document) 
                        self.log.error('Logger] status code: %s' % r.status_code)
                    else:
                        self.log.info('Logger] uploaded document')
                except OSError:
                    self.log.error('Logger] lost connection')
            else:
               self.log.error('Logger] no internet connection')
               sleep(1)

    def isConnected(self):
        try:
            socket.create_connection((HTTP_SERVER, 3000))
            return True
        except OSError:
            pass
        return False
