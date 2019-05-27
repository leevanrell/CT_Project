#!/usr/bin/python3

import serial
import os
import sys
import socket
import pynmea2
import datetime
import time
import sqlite3
from time import sleep
from pynmea2 import ParseError

from .TTY import TTY


class DetectorLite():

    def __init__(self, log, HTTP_SERVER, DB_FILE, TABLE):
        self.run = True
        self.log = log
        self.TTY = TTY(log)
        self.HTTP_SERVER = HTTP_SERVER
        self.DB_FILE = DB_FILE
        self.TABLE = TABLE
        self.TIMEOUT = 5
        self.RATE = 0.5
        self.QUEUE_SIZE = 10
        if not self.TTY.configured:
            self.log.info('setup failed. exiting.')
            self.run = False

    def start(self):
        docs = []
        self.log.info('starting data collection')
        while self.run:
            try:
                location = self.getLocation()
                cell_towers = self.getCell()
                if location and cell_towers:
                    location = pynmea2.parse(location)
                    for cell_tower in cell_towers:
                        try:
                            document = self.getDocument(cell_tower, location)
                            if document and document[11] != 0 and document[5] > 7 and document[5] != 255: 
                                docs.append(document)
                                self.log.debug('added document to queue')
                                #self.log.info(document)
                                if len(docs) > self.QUEUE_SIZE:
                                    self.log.info('making bulk upload')
                                    self.update_local_db(docs)
                                    del docs[:]
                                sleep(self.RATE)
                            else:
                                self.log.debug(f"dropped bad document: {cell_tower}")
                        except ValueError as e:
                            self.log.debug(f"dropped bad document: {cell_tower} {e}")

            except (KeyboardInterrupt, SystemExit):
                self.run = False
        self.update_local_db(docs)

    def getDocument(self, cell_tower, location):
        cell_tower = cell_tower.split(',')
        self.log.debug(cell_tower)
        if len(cell_tower) >= 8:
            arfcn = cell_tower[1][1:]         # Absolute radio frequency channel number
            rxl = cell_tower[2]               # Receive level (signal stregnth)
            if(len(cell_tower) >= 11): # +CENG:0, '<arfcn>, <rxl>, <rxq>, <mcc>, <mnc>, <bsic>, <cellid>, <rla>, <txp>, <lac>, <TA>'
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
            if arfcn and rxl and bsic and Cell_ID and MCC and MNC and LAC:
                return (time.strftime('%m-%d-%y %H:%M:%S'),int(MCC),int(MNC),int(LAC, 16),int(Cell_ID, 16),int(rxl),arfcn,bsic,location.latitude,location.longitude,int(location.num_sats),location.gps_qual,location.altitude,location.altitude_units)
            else:
                return False
        return False

    def getCell(self):
        try:
            SIM_Serial = serial.Serial(port=self.TTY.SIM_TTY, baudrate=115200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=0)
            SIM_Serial.write(b'AT+CENG?\r\n')  
            sleep(.1)  
            SIM_Output = ''
            while SIM_Serial.inWaiting() > 0:
                SIM_Output += SIM_Serial.readline().decode('ascii').strip('\r')
            SIM_Serial.close()
            SIM_Output = filter(None, SIM_Output.split('\n'))
            self.log.debug(SIM_Output)
            return SIM_Output
        except serial.SerialException as e:
            #self.log.error('SIM, something got unplugged!') 
            sleep(1)
            self.TTY.reset()
            for c in range(0, 5):
                if self.TTY.configured:
                    break
                self.TTY.reset()
                self.log.warning(f'SIM, Retrying setup: {count}')
            if not self.TTY.configured:
                self.log.error('SIM, setup failed')
                self.run = False
            return False

    def getLocation(self):
        try:
            GPS_Serial = serial.Serial(port=self.TTY.GPS_TTY, baudrate=115200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=0)     
            sleep(.1)
            GPS_Output = ""
            start = time.time()
            while not self.isValidLocation(GPS_Output) and time.time() - start < self.TIMEOUT: 
                sleep(.1) 
                try:
                    GPS_Output = GPS_Serial.readline().decode('ascii').strip()
                except UnicodeDecodeError:
                    GPS_Output = ""
            GPS_Serial.close()
            if self.isValidLocation(GPS_Output):
                self.log.debug(GPS_Output)
                return GPS_Output
            return False
        except serial.SerialException as e:
            self.log.error('GPS, something got unplugged!') 
            sleep(1)
            self.TTY.reset()
            for c in range(0, 5):
                if self.TTY.configured:
                    break
                self.TTY.reset()
                self.log.warning(f'GPS, Retrying setup: {count}')
            if not self.TTY.configured:
                self.log.error('GPS, setup failed')
                self.run = False
            return False

    def update_local_db(self, docs):
        conn = sqlite3.connect(self.DB_FILE)
        c = conn.cursor()
        c.executemany(f"INSERT INTO {self.TABLE} VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", docs)
        conn.commit()
        conn.close()

    def update_remote_db(self, docs):
        try:
            requests.post(self.HTTP_SERVER + '/update', json=docs, timeout=1)
        except requests.ConnectionError:
            self.log.warning('error: connection error')
        except requests.HTTPError:
            self.log.warning('error: http error')
        except requests.Timeout:
            self.log.warning('error: timeout error')

    def isValidLocation(self, output):
        check = output.split(',')
        if len(output) != 0 and len(check) >= 6 and check[0] == '$GPGGA':
            try:
                location = pynmea2.parse(output)
                if int(location.num_sats) and int(location.gps_qual) and float(location.altitude) and float(location.latitude) and float(location.longitude):
                    return True
                return False
            except ParseError:
                return False
            except ValueError:
                return False
            except AttributeError:
                return False
            except KeyError:
                return False
        return False 