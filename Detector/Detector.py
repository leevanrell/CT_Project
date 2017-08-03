#!/usr/bin/python

import serial 
import threading 
import Queue 
import os  
#import sys 
import socket 
import requests 
import json 
import csv 
import pynmea2 
import datetime 
import time 
#import logging
from time import sleep 

class Detector(object):
    def __init__(self, log, HTTP_SERVER, SIM_TTY, GPS_TTY):
        self.log = log
        self.SIM_TTY = SIM_TTY # sim serial address 
        self.GPS_TTY = GPS_TTY # gps serial address
        self.LED_gpio = LED_gpio
        self.button_gpio = button_gpio
        self.HTTP_SERVER = HTTP_SERVER
        self.q = Queue.Queue() # Using queue to share data between two threads
        self.Data = self.Data_Thread() # thread collects GPS and SIM data and adds to queue
        self.Logger = self.Logging_Thread() # Thread waits for Wifi connection and posts data to server

    def run(self):
        self.log.info('main] starting threads')
        Data.start() 
        Logger.start()
        try:        
            while Data.running and Logger.running:
                sleep(.5)
        except (KeyboardInterrupt, SystemExit): 
            self.log.info('main] detected KeyboardInterrupt: killing threads.')
            Data.running = False
            Logger.running = False
            Data.join() # wait for the threads to finish what it's doing
            Logger.join()
        self.log.info('main] exiting.')

    class Data_Thread(threading.Thread): # thread handles data collection
        def __init__(self):
            threading.Thread.__init__(self)
            self.running = True
            self.GPS_Thread = self.GPS_Poller()
            self.SIM_Thread = self.SIM_Poller()
        
        def run(self):
            self.GPS_Thread.start()
            self.SIM_Thread.start()
            while self.running and self.GPS_Thread.running and self.SIM_Thread.running: # ensures that the GPS and SIM thread hasn't crashed    
                if not self.GPS_Thread.go and not self.SIM_Thread.go: # only runs when the GPS and SIM Thread are finished 
                    if self.GPS_Thread.run_time < 10.0 and abs(self.GPS_Thread.run_time - self.SIM_Thread.run_time) < .4: # ensures the gps and sim data are collected around the same time
                        self.log.info('Data] GPS runtime: %.2f, SIM runtime: %.2f' % (self.GPS_Thread.run_time, self.SIM_Thread.run_time))
                        cell_towers = self.SIM_Thread.SIM_Output # gets array of Cell tower data (contains ~5-6 lines each representing a cell tower in the surrounding area)
                        location = pynmea2.parse(self.GPS_Thread.GPS_Output) # converts GPS data to nmea object 
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
                                self.log.info('Data] added document to queue')
                                update_local(document)
                                q.put(document)
                                sleep(RATE)
                            else:
                                self.log.info('Data] dropped bad document: %s %s %s %s %s' % (MCC, MNC, LAC, Cell_ID, rxl))
                    else: # gps couldn't get a fix (timed out) or data points weren't taken close enough together
                        self.log.info('Data] TIMEOUT: GPS runtime: %.2f, SIM runtime: %.2f' % (self.GPS_Thread.run_time, self.SIM_Thread.run_time))

                    # tells SIM and GPS thread get more data
                    self.GPS_Thread.go = True
                    self.SIM_Thread.go = True
            # kills subthreads when data thread stops 
            self.GPS_Thread.running = False
            self.SIM_Thread.running = False

        def update_local(self, document):
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

        class GPS_Poller(threading.Thread): # thread repsonsible for collecting data from gps unit
            def __init__(self):
                threading.Thread.__init__(self)
                self.GPS_Serial = serial.Serial(port=self.GPS_TTY, baudrate=115200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=0)  
                self.GPS_Serial.close() 
                self.running = True # set to false when data thread stops
                self.go = True # set to False after it runs once, starts again after data thread finishes handling data
                self.run_time = 0.0 #  time it takes to collect data
                self.GPS_Output = '' # output of gps unit; contains lat, lon, alt, etc..

            def run(self):
                while self.running: # runs when data thread tells it to
                    if self.go:
                        try:
                            start = time.time()
                            self.GPS_Serial.open()
                            sleep(.1)
                            self.GPS_Output = self.GPS_Serial.readline()
                            while not self.isValidLocation(self.GPS_Output) and time.time() - start < 10.0: # loops until has a valid GPS fix or until run time is more than 10 sec
                                sleep(.1) # Need to wait before collecting data
                                self.GPS_Output = self.GPS_Serial.readline()
                            self.GPS_Serial.close()
                            self.run_time = time.time() - start # calculates run time
                            self.go = False # stops running until data thread is ready
                        except serial.SerialException as e:
                            self.log.info('GPS] Error: something got unplugged!') # error handling encase connection to sim unit is lost
                            Data.running = False
                            Logger.running = False
                            self.running = False # is this necessary? 
                            Data.join()
                            Logger.join()
                         
            def isValidLocation(self, output): # checks string to confirm it contains valid coordinates
                check = output.split(',')
                return len(output) != 0 and check[0] == '$GPGGA' and len(check[6]) != 0 and int(check[6]) != 0 # we only want GPGGA sentences with an actual fix (Fix != 0)

        class SIM_Poller(threading.Thread): # thread responsible for collecting data from sim unit
            def __init__(self):
                threading.Thread.__init__(self)
                self.SIM_Serial = serial.Serial(port=self.SIM_TTY, baudrate=115200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=0)
                self.SIM_Serial.close()
                self.running = True
                self.go = True
                self.run_time = 0.0
                self.SIM_Output = '' # output of sim unit; contains cellid, lac, mnc, mcc, etc for multiple cell towers
            
            def run(self):
                while self.running:
                    if self.go:
                        try:
                            start = time.time()
                            self.SIM_Serial.open() 
                            self.SIM_Serial.write('AT+CENG?' + '\r\n')  # Sends Command to Display current engineering mode settings, serving cell and neighboring cells
                            sleep(.1) # Need to wait for device to receive commands 
                            self.SIM_Output = ''
                            while self.SIM_Serial.inWaiting() > 0:
                                self.SIM_Output += self.SIM_Serial.read(6) # Reads in SIM900 output
                            self.SIM_Serial.close()
                            self.SIM_Output = self.SIM_Output.split('\n')[4:11] # \Removes Excess Lines
                            self.run_time = time.time() - start # calculates run time
                            self.go = False
                        except serial.SerialException as e:
                            self.log.info('SIM] Error: something got unplugged!') # error handling encase connection to gps unit is lost
                            Data.running = False
                            Logger.running = False
                            self.running = False # is this necessary?
                            Data.join()
                            Logger.join()

    class Logging_Thread(threading.Thread): # thread responsible for sending data to server
        def __init__(self):
            threading.Thread.__init__(self)
            self.running = True
        
        def run(self):
            while self.running:
                self.send_Data()
            Data.join() # waits for data thread to stop
            sleep(2)
            self.send_Data() # makes sure queue is empty before finishing
        
        def send_Data(self):
            while not q.empty(): 
                if self.isConnected(): # ensures there is a connection to internet/server
                    r = requests.post(self.HTTP_SERVER, data=json.dumps(document)) # converts to json and sends post request
                    if r.status_code != 200:
                        q.add(document) # add back to queue if post fails
                        self.log.info('Logger] Error: status code: %s' % r.status_code)
                    else:
                        self.log.info('Logger] uploaded document')
                else:
                   self.log.info('Logger] Error: no internet connection')
                   sleep(1)
            sleep(2) # Wait for queue to fill

        def isConnected(self): # checks to see if detector can connect to the http server
            try:
                socket.create_connection((self.HTTP_SERVER, 80)) # connect to the host -- tells us if the host is actually reachable
                return True
            except OSError:
                pass
            return False