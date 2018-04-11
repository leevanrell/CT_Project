#!/usr/bin/python

LOCAL_BACKUP_LOCATION = 'data/backup/' 
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
from lib.Setup import Setup
sys.path.append('../')

class Data_Thread(threading.Thread): 

    def __init__(self, log, q, SIM_TTY, GPS_TTY, TIMEOUT, RATE):
        threading.Thread.__init__(self)
        self.running = True
        self.log = log
        self.q = q
        self.GPS_Thread = self.GPS_Poller(log, SIM_TTY)
        self.SIM_Thread = self.SIM_Poller(log, GPS_TTY)
        self.TIMEOUT = TIMEOUT
        self.RATE = RATE
    
    def run(self):
        self.start_GPS_and_SIM()
        # TODO: make execution control and error checking not terrible
        while self.running and self.GPS_Thread.running and self.SIM_Thread.running: # breaks execution if gps or sim crashes   
            if not self.GPS_Thread.go and not self.SIM_Thread.go: # only runs when the GPS and SIM Thread are finished 
                self.log.debug('Data] GPS runtime: %.2f, SIM runtime: %.2f' % (self.GPS_Thread.run_time, self.SIM_Thread.run_time))
                if self.GPS_Thread.run_time < self.TIMEOUT and abs(self.GPS_Thread.run_time - self.SIM_Thread.run_time) < .4 and self.GPS_Thread.isValidLocation(self.GPS_Thread.GPS_Output): 
                    cell_towers = self.SIM_Thread.SIM_Output 
                    location = pynmea2.parse(self.GPS_Thread.GPS_Output)
                    for i in range(len(cell_towers)):
                        document = self.getDocument(cell_towers, location)
                        if(document['rxl'] != 255 and document['rxl'] > 7 and document['MCC'] = '0'): # filters out data points with lower receive strengths -- the data tends to get 'dirty' when the rxl is < 5~10
                            self.log.info('Data] added document to queue')
                            self.update_local(document)
                            self.q.put(document)
                            sleep(self.RATE)
                        else:
                            self.log.info('Data] dropped bad document: %s %s %s %s %s' % (MCC, MNC, LAC, Cell_ID, rxl))
                self.resume_GPS_and_SIM()
        self.stop_GPS_and_SIM()

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
                        
    def start_GPS_and_SIM(self):
        self.GPS_Thread.start()
        self.SIM_Thread.start()

    def stop_GPS_and_SIM(self):
        self.GPS_Thread.running = False
        self.SIM_Thread.running = False

    def resume_GPS_and_SIM(self):
        self.GPS_Thread.go = True
        self.SIM_Thread.go = True

    def update_local(self, document):
        FOLDER = 'data/backup/' 
        FILE = FOLDER  + str(datetime.date.today())+ '.csv'
        if not os.path.exists(FOLDER):
            os.makedirs(FOLDER)
        with open(FILE, 'a') as f:
            writer = csv.writer(f)
            writer.writerow(document)

    class GPS_Poller(threading.Thread):

        def __init__(self, log, GPS_TTY):
            threading.Thread.__init__(self)
            self.log = log
            self.GPS_TTY = GPS_TTY
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
                        while not self.isValidLocation(self.GPS_Output) and time.time() - start < 10.0: # loops until has a valid GPS fix or until run time is more than 10 sec
                            sleep(.1) 
                            self.GPS_Output = self.GPS_Serial.readline()
                        self.GPS_Serial.close()
                        self.run_time = time.time() - start 
                        self.go = False 
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
                        if not setup.configured:
                            self.log.error('GPS] setup failed')
                            self.running = False
                        else:
                            self.GPS_TTY = setup.GPS_TTY
                            #TODO: Possibly need to set SIM TTY aswell somehow getInstance() 
                
                else:
                    sleep(.1)
                     
        def isValidLocation(self, output):
            check = output.split(',')
            return len(output) >= 6 and check[0] == '$GPGGA' and int(check[6]) != 0 # we only want GPGGA sentences with an actual fix (Fix != 0)

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
                        self.SIM_Serial.write('AT+CENG?' + '\r\n')  
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
                        # TODO: make execution control and error checking not terrible; implement semaphores better
                        sleep(1)
                        setup = Setup(self.log)
                        setup.setup_TTY();
                        count = 0
                        while not setup.configured and count < 10:
                            setup.setup_TTY();
                            count += 0
                        if not setup.configured:
                            self.log.error('SIM] setup failed')
                            self.running = False
                        else:
                            self.SIM_TTY = setup.SIM_TTY
                            #TODO: Possibly need to set GPS TTY aswell somehow getInstance() 
                else:
                    sleep(.1)