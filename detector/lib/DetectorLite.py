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

Class DetectoryLite():

    __init__(self, log, HTTP_SERVER SIM_TTY, GPS_TTY, RATE):
        self.run = True
        self.log = log
        self.HTTP_SERVER = HTTP_SERVER
        self.SIM_TTY = SIM_TTY
        self.GPS_TTY = GPS_TTY
        self.RATE = RATE

    def start(self):
        while self.run:
            try:
                location = pynmea2.parse(getLocation())
                cell_towers = self.getCell() 
                for i in range(len(cell_towers)):
                    document = self.getDocument(cell_towers, location)
                    if(rxl > 7 and rxl != 255 and MCC != '0'): 
                        self.log.info('Data] added document to queue')
                        self.update_local(document)
                        q.put(document)
                        if q.qsize() >= QUEUE_SIZE:
                            self.update_remote()
                        sleep(RATE)
                    else:
                        self.log.info('Data] dropped bad document: %s %s %s %s %s' % (MCC, MNC, LAC, Cell_ID, rxl))
            except (KeyboardInterrupt, SystemExit):
                run = False:
        update_remote()
            
    def getCell():
        try:
            SIM_Serial = serial.Serial(port=SIM_TTY, baudrate=115200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=0)
            SIM_Serial.write('AT+CENG?' + '\r\n')  
            sleep(.1)  
            SIM_Output = ''
            while SIM_Serial.inWaiting() > 0:
                SIM_Output += SIM_Serial.read(6)
            SIM_Serial.close()
            SIM_Output = SIM_Output.split('\n')[4:11] 
            return SIM_Output
        except serial.SerialException as e:
            log.error('SIM] something got unplugged!')
            quit()

    def getLocation():
        try
            GPS_Serial = serial.Serial(port=GPS_TTY, baudrate=115200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=0)     
            sleep(.1)
            GPS_Output = GPS_Serial.readline()
            while not self.isValidLocation(self.GPS_Output): 
                sleep(.1) 
                self.GPS_Output = GPS_Serial.readline()
            GPS_Serial.close()
            return GPS_Output
        except serial.SerialException as e:
            log.error('GPS] something got unplugged!')
            quit()

    def isValidLocation(output):
        check = output.split(',')
        return len(output) != 0 and check[0] == '$GPGGA' and len(check[6]) != 0 and int(check[6]) != 0 # we only want GPGGA sentences with an actual fix (Fix != 0)

    def getDocument(cell_towers, location):
        cell_tower = cell_towers[i].split(',')
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

    def update_local(document):
            FOLDER = 'data/' + str(datetime.date.today())
            FILE = FOLDER  + '/table.csv'
            if not os.path.exists(FOLDER):
                os.makedirs(FOLDER)
            with open(FILE, 'a') as f:
                writer = csv.writer(f)
                writer.writerow(document)

    def update_remote():
        start = time.time()
        while not q.empty() and  time.time() - start < 10:
            if self.isConnected():
                try:
                    document = q.get()
                    r = requests.post(HTTP_SERVER, data=json.dumps(document), headers={'content-type': 'application/json'})
                    if r.status_code != 200:
                        q.add(document) 
                        log.error('Logger] status code: %s' % r.status_code)
                    else:
                        log.info('Logger] uploaded document')
                except OSError
                    log.error('Logger] lost connection')
            else:
               log.error('Logger] no internet connection')
               sleep(1)

    def isConnected(self):
        try:
            socket.create_connection((HTTP_SERVER, 3000))
            return True
        except OSError:
            pass
        return False
