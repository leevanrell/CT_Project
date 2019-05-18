#!/usr/bin/python3

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
import sqlite3
from time import sleep

from Setup import Setup

QUEUE_SIZE = 25

class DetectorLite():

    def __init__(self, log, DB_FILE, TABLE, SIM_TTY, GPS_TTY):
        self.run = True
        self.log = log
        self.DB_FILE = FILE
        self.TABLE = TABLE
        self.SIM_TTY = SIM_TTY
        self.GPS_TTY = GPS_TTY
        self.TIMEOUT = 5
        self.RATE = 1
        self.QUEUE_SIZE = 25

    def start(self):
        while self.run:
            try:
                docs = []
                cell_towers = self.getCell()
                location = self.getLocation()
                if location[:5] != "error" and cell_towers[:5] != "error":
                    location = pynmea2.parse(location)
                    for cell_tower in cell_towers:
                        document = self.getDocument(cell_tower, location)
                        if document['GPS_quality'] != 0 and document['rxl'] > 7 and document['rxl'] != 255: 
                            docs.append(document)
                            self.log.info('added document to queue')
                            if len(docs) >= self.QUEUE_SIZE:
                                 self.update_db(docs)
                                 del doc[:]
                            sleep(self.RATE)
                        else:
                            self.log.debug('dropped bad document: %s %s %s %s %s %s' % (document['GPS_quality'], document['MCC'], document['MNC'], document['LAC'], document['Cell_ID'], document['rxl']))
            except (KeyboardInterrupt, SystemExit):
                self.run = False

    def getDocument(cell_tower, location):
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
        return (time.strftime('%m-%d-%y %H:%M:%S'),int(MCC),int(MNC),LAC,Cell_ID,int(rxl),arfcn,bsic,location.latitude,location.longitude,int(location.num_sats),int(location.gps_qual),location.altitude,location.altitude_units)

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
            self.log.error('SIM, something got unplugged!') 
            sleep(1)
            setup = Setup(self.log)
            setup.setup_TTY()
            count = 0
            while not setup.configured and count < 10:
                setup.setup_TTY()
                count += 0
                self.log.error('SIM, Retrying setup: %s', count)
            if not setup.configured:
                self.log.error('SIM, setup failed')
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
            return 'error: bad gps data'
        except serial.SerialException as e:
            self.log.error('GPS, something got unplugged!') 
            sleep(1)
            setup = Setup(self.log)
            setup.setup_TTY()
            count = 0
            while not setup.configured and count < 10:
                setup.setup_TTY()
                count += 0
                self.log.error('GPS, Retrying setup: %s', count)
            if not setup.configured:
                self.log.error('GPS, setup failed')
                self.run = False
            else:
                self.SIM_TTY = setup.SIM_TTY
                self.GPS_TTY = setup.GPS_TTY
            return 'error'

    def update_db(self, docs):
        conn = sqlite3.connect(self.DB_FILE)
        c = conn.cursor()
        c.executemany("""INSERT INTO %s VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""" % self.TABLE, docs)
        conn.commit()
        conn.close()

    def isValidLocation(self, output):
        check = output.split(',')
        return len(output) != 0 and check[0] == '$GPGGA' and len(check[6]) != 0 and int(check[6]) != 0 # we only want GPGGA sentences with an actual fix (Fix != 0)
