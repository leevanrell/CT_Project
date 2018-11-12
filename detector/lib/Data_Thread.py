#!/usr/bin/python
import threading
import Queue
import json
import csv
import serial
import pynmea2
import os
import sys
import datetime
import time
import logging
from time import sleep

import lib.Helper as Helper
from lib.Setup import Setup

LOCAL_BACKUP_LOCATION = 'data/backup/'
sys.path.append('../')


class Data_Thread(threading.Thread): 

    def __init__(self, log, q, SIM_TTY, GPS_TTY, TIMEOUT, RATE):
        threading.Thread.__init__(self)
        self.running = True
        self.log = log
        self.q = q
        self.GPS_Thread = self.GPS_Poller(log, GPS_TTY, TIMEOUT)
        self.SIM_Thread = self.SIM_Poller(log, SIM_TTY)
        self.TIMEOUT = TIMEOUT
        self.RATE = RATE

    def run(self):
        self.start_GPS_and_SIM()
        while self.running and self.GPS_Thread.running and self.SIM_Thread.running:  
            if not self.GPS_Thread.go and not self.SIM_Thread.go: 
                self.log.debug('Data] GPS runtime: %.2f, SIM runtime: %.2f' % (self.GPS_Thread.run_time, self.SIM_Thread.run_time))
                if self.GPS_Thread.run_time < self.TIMEOUT and abs(self.GPS_Thread.run_time - self.SIM_Thread.run_time) < .4 and Helper.isValidLocation(self.GPS_Thread.GPS_Output): 
                    cell_towers = self.SIM_Thread.SIM_Output 
                    location = pynmea2.parse(self.GPS_Thread.GPS_Output)
                    for cell_tower in cell_towers:
                        document = Helper.getDocument(cell_tower, location)
                        if document['GPS_quality'] != 0 and document['rxl'] != 255 and document['rxl'] > 7 and document['Cell_ID'] != 'ffff' and document['MCC'] != 0: # filters out data points with lower receive strengths -- the data tends to get 'dirty' when the rxl is < 5~10
                            self.log.info('Data] added document to queue')
                            Helper.update_local(document)
                            self.q.put(document)
                            sleep(self.RATE)
                        else:
                            self.log.debug('Data] dropped bad document: %s %s %s %s %s' % (document['MCC'], document['MNC'], document['LAC'], document['Cell_ID'], document['rxl']))
                self.resume_GPS_and_SIM()
        self.stop_GPS_and_SIM()

    def start_GPS_and_SIM(self):
        self.GPS_Thread.start()
        self.SIM_Thread.start()

    def stop_GPS_and_SIM(self):
        self.GPS_Thread.running = False
        self.SIM_Thread.running = False

    def resume_GPS_and_SIM(self):
        self.GPS_Thread.go = True
        self.SIM_Thread.go = True

    class GPS_Poller(threading.Thread):

        def __init__(self, log, GPS_TTY, TIMEOUT):
            threading.Thread.__init__(self)
            self.log = log
            self.GPS_TTY = GPS_TTY
            self.TIMEOUT = TIMEOUT
            self.running = True
            self.go = True
            self.run_time = 0.0
            self.GPS_Output = ''

        def run(self):
            while self.running:
                if self.go:
                    try:
                        self.GPS_Serial = serial.Serial(port=self.GPS_TTY, baudrate=115200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=0)  
                        start = time.time()
                        sleep(.1)
                        self.GPS_Output = self.GPS_Serial.readline()
                        while not Helper.isValidLocation(self.GPS_Output) and time.time() - start < self.TIMEOUT: # loops until has a valid GPS fix or until run time is more than 10 sec
                            sleep(.1)
                            self.GPS_Output = self.GPS_Serial.readline()
                        self.GPS_Serial.close()
                        self.run_time = time.time() - start
                        self.go = False
                    except serial.SerialException as e:
                        self.log.error('GPS] something got unplugged!')
                        sleep(1)
                        setup = Setup(self.log)
                        setup.setup_TTY()
                        count = 0
                        while not setup.configured and count < 10:
                            setup.setup_TTY()
                            count += 0
                        if not setup.configured:
                            self.log.error('GPS] setup failed')
                            self.running = False
                        else:
                            self.GPS_TTY = setup.GPS_TTY
                            #TODO: Possibly need to set SIM TTY aswell somehow getInstance() 
                else:
                    sleep(.1)

    class SIM_Poller(threading.Thread):

        def __init__(self, log, SIM_TTY):
            threading.Thread.__init__(self)
            self.log = log
            self.SIM_TTY = SIM_TTY
            self.running = True
            self.go = True
            self.run_time = 0.0
            self.SIM_Output = ''

        def run(self):
            while self.running:
                if self.go:
                    try:
                        self.SIM_Serial = serial.Serial(port=self.SIM_TTY, baudrate=115200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=0)
                        start = time.time()
                        self.SIM_Serial.write('AT+CENG?\r\n')
                        sleep(.1)
                        self.SIM_Output = ''
                        while self.SIM_Serial.inWaiting() > 0:
                            self.SIM_Output += self.SIM_Serial.read(6)
                        self.SIM_Serial.close()
                        self.SIM_Output = self.SIM_Output.split('\n')[4:11]
                        self.run_time = time.time() - start
                        self.go = False
                    except serial.SerialException as e:
                        self.log.error('SIM] something got unplugged!')
                        sleep(1)
                        setup = Setup(self.log)
                        setup.setup_TTY()
                        count = 0
                        while not setup.configured and count < 10:
                            setup.setup_TTY()
                            count += 0
                        if not setup.configured:
                            self.log.error('SIM] setup failed')
                            self.running = False
                        else:
                            self.SIM_TTY = setup.SIM_TTY
                else:
                    sleep(.1)
