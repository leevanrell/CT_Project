#!/usr/bin/python
SIM_TTY = '/dev/ttyUSB1' # sim serial address (dmesg | grep tty or)
GPS_TTY = '/dev/ttyUSB0' # gps serial address
HTTP_SERVER = 'http://localhost:80' # server address 
LED_gpio = 3 # GPIO pin for LED 
button_gpio = 23 # GPIO pin for Button
RATE = 5 # time delay between successfully adding a document to queue and trying to get another data sample

import threading # used for threads
import serial # used for serial connection
import Queue # used for queue for threads
import os # 
import sys # used to check for sudo
import socket # used to test connectivity
#import RPi.GPIO as GPIO # used to control the Pi's GPIO pins
import requests # used for POST requests
import json # used for making jason object (json.dumps)
import time # 
import pynmea2 # used for parsing gps/nmea sentences
from time import sleep # used to sleep

q = Queue.Queue() # Using queue to share data between two threads

import logging
log = logging.getLogger()
log.setLevel('DEBUG')
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('[%(asctime)s] [Detector.%(message)s'))
log.addHandler(handler)

def setup_check():
    log.info('setup] checking TTY connections')

    try:
        Serial = serial.Serial(port=SIM_TTY, baudrate=115200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=0)
        Serial.write('AT' + '\r\n') # sends AT command
        sleep(.5)
        for i in range(0, 5):
            if(i == 2):
                check = Serial.readline() # gets response
            else: 
                Serial.readline()
        if check != 'OK\r\n': # should be 'OK' if not, tty address is incorrect and quits
            log.info('setup] Error: SIM_TTY misconfigured') 
            quit()       

    except serial.SerialException as e:
        if not os.geteuid() == 0:
            log.info('setup] Error: Script must be run as root!')
            quit()
        else:
            log.info('setup] Error: SIM unit not plugged in')
            quit()

    try:
        Serial = serial.Serial(port=GPS_TTY, baudrate=9600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=0)
        '''
        sleep(.5)
        check = Serial.readline() 
        if check[:1] != '$': 
            log.info('setup] Error: GPS_TTY misconfigured') # checking for incorrect address again may be redundant (not sure if there is a scenario in which only one address may be incorrect)
            quit()
        '''
    except serial.SerialException as e:
        log.info('setup] Error: GPS unit not plugged in')
        quit()

def setup_SIM():
    log.info('setup] configuring SIM')
    try:
        SIM_Serial = serial.Serial(port=SIM_TTY, baudrate=115200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=0)
        SIM_Serial.write('AT+CENG=1,1' + '\r\n') # Configures SIM unit to Engineering mode
        sleep(.5) # Need to wait for device to receive commands
        SIM_Serial.close()
    except serial.SerialException as e:
        log.info('setup] Error: lost connection to SIM unit')
        quit()

def setup_GPS():
    log.info('setup] configuring GPS')
    try:
        GPS_Serial = serial.Serial(port=GPS_TTY, baudrate=9600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=0)  
        sleep(.5)
        GPS_Serial.write('$PMTK314,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0*29<CR><LF> ' + '\r\n') #Configures GPS to only output GPGGA Sentences
        sleep(.5) # Need to wait for device to receive commands
        GPS_Serial.write('$PMTK220,100*2F<CR><LF>' + '\r\n') # Configures Fix interval to 100 ms
        sleep(.5)
        GPS_Serial.write('$PMTK251,115200*1F<CR><LF>' + '\r\n') # Configures Baud Rate to 115200
        sleep(.5)
        GPS_Serial.close() 
    except serial.SerialException as e:
        log.info('setup] Error: lost connection to GPS unit')
        quit()  

class Data_Thread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.running = True
        self.GPS_Thread = self.GPS_Poller()
        self.SIM_Thread = self.SIM_Poller()
    
    def run(self):
        self.GPS_Thread.start()
        self.SIM_Thread.start()
        while self.running:
            # Only runs when the GPS and SIM Thread are finished    
            if not self.GPS_Thread.go and not self.SIM_Thread.go:
                # ensures the gps and sim data are collected around the same time
                if abs(self.GPS_Thread.run_time - self.SIM_Thread.run_time) < .4:
                    log.info('Data] GPS runtime: %.2f, SIM runtime: %.2f' % (self.GPS_Thread.run_time, self.SIM_Thread.run_time))
                    cell_towers = self.SIM_Thread.SIM_Output # Gets Array of Cell tower data (contains ~5-6 lines each representing a cell tower in the surrounding area)
                    location = pynmea2.parse(self.GPS_Thread.GPS_Output) # converts GPS data to nmea object 
                    for i in range(len(cell_towers)):
                        # Data in first (serving) cell is ordered differently than first cell,
                        # +CENG:0, '<arfcn>, <rxl>, <rxq>, <mcc>, <mnc>, <bsic>, <cellid>, <rla>, <txp>, <lac>, <TA>'
                        cell_tower = cell_towers[i].split(',')
                        #cell_tower = cell_tower.split(',')
                        arfcn = cell_tower[1][1:]         # Absolute radio frequency channel number
                        rxl = cell_tower[2]               # Receive level (signal stregnth)
                        if(i == 0):
                            bsic = cell_tower[6]          # Base station identity code
                            Cell_ID = cell_tower[7]       # Unique Identifier
                            MCC = cell_tower[4]           # Mobile Country Code
                            MNC = cell_tower[5]           # Mobile Network Code
                            LAC = cell_tower[10]          # Location Area code
                        # +CENG:1+,'<arfcn>, <rxl>, <bsic>, <cellid>, <mcc>, <mnc>, <lac>'    
                        else:
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
                        # Filters out data points with lower receive strengths, the data tends to get 'dirty' when the rxl is < 5~10
                        if(rxl > 7 and rxl != 255 and MCC != '0'):
                            log.info('Data] added document to queue')
                            q.put(document)
                            sleep(RATE)
                        else:
                            log.info('Data] dropped bad document: %s %s %s %s %s' % (MCC, MNC, LAC, Cell_ID, rxl))
                else:
                    # gps couldn't get a fix (timed out) or data wasn't collected simultenously 
                    log.info('Data] TIMEOUT: GPS runtime: %.2f, SIM runtime: %.2f' % (self.GPS_Thread.run_time, self.SIM_Thread.run_time))

                # Tells SIM and GPS thread to start again
                self.GPS_Thread.go = True
                self.SIM_Thread.go = True
        # Kills subthreads when data thread stops 
        self.GPS_Thread.running = False
        self.SIM_Thread.running = False

    class GPS_Poller(threading.Thread):
        def __init__(self):
            threading.Thread.__init__(self)
            self.GPS_Serial = serial.Serial(port=GPS_TTY, baudrate=115200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=0)  
            self.GPS_Serial.close() 
            self.running = True # Set to false when data thread stops
            self.go = True # Set to False after it runs once, starts again after data thread finishes handling data
            self.run_time = 0.0 #  time it takes to collect data
            self.GPS_Output = '' # output of gps unit; contains lat, lon, alt, etc..

        def run(self):
            while self.running:
                # Runs when Data thread tells it to
                if self.go:
                    try:
                        start = time.time()
                        self.GPS_Serial.open()
                        sleep(.1)
                        self.GPS_Output = self.GPS_Serial.readline()
                        # Loops until has a valid GPS fix or until run time is more than 10 sec
                        while not self.isValidLocation(self.GPS_Output) and time.time() - start < 10.0:
                            sleep(.1) # Need to wait before collecting data
                            self.GPS_Output = self.GPS_Serial.readline()
                        self.GPS_Serial.close()
                        self.run_time = time.time() - start # calculates run time
                        self.go = False # stops running until data thread is ready
                    except serial.SerialException as e:
                        log.info('GPS] Error: something got unplugged!') # error handling encase connection to sim unit is lost
                        Data.running = False
                        Logger.running = False
                        Data.join()
                        Logger.join()
                        #quit()

        def isValidLocation(self, output):
            check = output.split(',')
            return len(output) != 0 and check[0] == '$GPGGA' and int(check[6]) != 0 # We only want GPGGA sentences with an Actual Fix (Fix != 0)

    class SIM_Poller(threading.Thread):
        def __init__(self):
            threading.Thread.__init__(self)
            self.SIM_Serial = serial.Serial(port=SIM_TTY, baudrate=115200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=0)
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
                        log.info('SIM] Error: something got unplugged!') # error handling encase connection to gps unit is lost
                        Data.running = False
                        Logger.running = False
                        Data.join()
                        Logger.join()
                        #quit() # not sure if needed

class Logging_Thread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.running = True
    
    def run(self):
        while self.running:
            self.send_Data()
        sleep(5)
        self.send_Data() # makes sure queue is empty before finishing
    
    def send_Data(self):
        while not q.empty():
            # ensures there is a connection to internet/server
            if self.isConnected():
                document = q.get() # gets data
                r = requests.post(HTTP_SERVER, data=json.dumps(document)) # converts to json and sends post request
                if r.status_code != 200:
                    q.add(document) # add back to queue if post fails
                    log.info('Logger] Error: status code: %s' % r.status_code)
                else:
                    log.info('Logger] uploaded document')
            else:
               log.info('Logger] Error: no internet connection')
               sleep(1)
        sleep(2) # Wait for queue to fill

    def isConnected(self):
        try:
            socket.create_connection(('www.google.com', 80)) # connect to the host -- tells us if the host is actually reachable
            return True
        except OSError:
            pass
        return False

def main():
    setup_check() # Ensures correct TTY/Serial setup
    setup_SIM() # Configures SIM module to output Cell Tower Meta Data
    setup_GPS() # Configures GPS module to only output GPGGA Sentences and increase's GPS speed
    global Data, Logger 
    Data = Data_Thread() # Thread collects GPS and SIM data and adds to queue
    Logger = Logging_Thread() # Thread waits for Wifi connection and posts data to server
    log.info('main] starting threads')
    Data.start() # Get this ish running
    Logger.start()
    try:        

        '''
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Sets GPIO LED_gpio as LED output
        GPIO.setup(LED_gpio, GPIO.OUT)
        GPIO.output(LED_gpio, GPIO.LOW)

        # Sets GPIO 2LED_gpio as Button input
        GPIO.setup(button_gpio, GPIO.IN, pull_up_down = GPIO.PUD_UP)


        # this code is bad and will not work as intended (start/stop threads)
        run = True
        while run:
            if(GPIO.input(button_gpio)):
                log.info('Detected GPIO Button Press: Killing Threads')
                GPIO.output(LED_gpio, GPIO.LOW)
                Data.running = False
                Logger.running = False
                run = False
                Data.join() # wait for the thread to finish what it's doing
                Logger.join()
                exitBlink() # blinks to indicate threads are finished
            else:
                GPIO.output(LED_gpio, GPIO.HIGH)
                sleep(.7)
                GPIO.output(LED_gpio,GPIO.LOW)
                sleep(.7)
        '''
        while Data.running and Logger.running:
            sleep(.5)

    except (KeyboardInterrupt, SystemExit): # when you press ctrl+c
        log.info('main] detected KeyboardInterrupt: killing threads.')
        Data.running = False
        Logger.running = False
        Data.join() # wait for the thread to finish what it's doing
        Logger.join()

    log.info('main] exiting.')
'''
def exitBlink():
    for i in range(0,9):
        GPIO.output(LED_gpio, GPIO.HIGH)
        sleep(.1)
        GPIO.output(LED_gpio, GPIO.LOW)
        sleep(.5)
    GPIO.output(LED_gpio, GPIO.LOW)
    GPIO.cleanup()
'''

if __name__ == '__main__':
    main()