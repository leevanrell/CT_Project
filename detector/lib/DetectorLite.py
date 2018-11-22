#!/usr/bin/python
import serial
import os
import Queue
import sys
import socket
import requests
import json
import csv
import pynmea2
import datetime
import time
from time import sleep

import lib.Helper as Helper
from lib.Setup import Setup
sys.path.append('../')

QUEUE_SIZE = 10


class DetectorLite():

    def __init__(self, log, HTTP_SERVER, SIM_TTY, GPS_TTY, TIMEOUT, RATE):
        self.run = True
        self.q = Queue.Queue()
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
                    for cell_tower in cell_towers:
                        document = Helper.getDocument(cell_tower, location)
                        if document['GPS_quality'] != 0 and document['rxl'] > 7 and document['rxl'] != 255: 
                            self.log.info('Data] added document to queue')
                            Helper.update_local(document)
                            self.q.put(document)
                            if self.q.qsize() >= QUEUE_SIZE:
                                self.update_remote()
                            sleep(self.RATE)
                        else:
                            self.log.debug('Data] dropped bad document: %s %s %s %s %s %s' % (document['GPS_quality'], document['MCC'], document['MNC'], document['LAC'], document['Cell_ID'], document['rxl']))
            except (KeyboardInterrupt, SystemExit):
                self.run = False
        self.update_remote()

    def getCell(self):
        try:
            SIM_Serial = serial.Serial(port=self.SIM_TTY, baudrate=115200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=0)
            SIM_Serial.write('AT+CENG?\r\n')  
            sleep(.1)  
            SIM_Output = ''
            while SIM_Serial.inWaiting() > 0:
                SIM_Output += SIM_Serial.read(6)
            SIM_Serial.close()
            SIM_Output = SIM_Output.split('\n')[4:11] 
            return SIM_Output
        except serial.SerialException as e:
            self.log.error('SIM] something got unplugged!') 
            sleep(1)
            setup = Setup(self.log)
            setup.setup_TTY()
            count = 0
            while not setup.configured and count < 10:
                setup.setup_TTY()
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
            while not Helper.isValidLocation(GPS_Output) and time.time() - start < self.TIMEOUT: 
                sleep(.1) 
                self.GPS_Output = GPS_Serial.readline()
            GPS_Serial.close()
            if Helper.isValidLocation(GPS_Output):
                return GPS_Output
            return 'error: bad gps data'
        except serial.SerialException as e:
            self.log.error('GPS] something got unplugged!') 
            sleep(1)
            setup = Setup(self.log)
            setup.setup_TTY()
            count = 0
            while not setup.configured and count < 10:
                setup.setup_TTY()
                count += 0
                self.log.error('GPS] Retrying setup: %s', count)
            if not setup.configured:
                self.log.error('GPS] setup failed')
                self.run = False
            else:
                self.SIM_TTY = setup.SIM_TTY
                self.GPS_TTY = setup.GPS_TTY
            return 'error'

    def update_remote(self):
        start = time.time()
        while not self.q.empty() and time.time() - start < 10:
            if Helper.isConnected():
                try:
                    document = self.q.get()
                    r = requests.post(self.HTTP_SERVER, data=json.dumps(document), headers={'content-type': 'application/json'})
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
