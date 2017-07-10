#!/usr/bin/python
SIM_TTY = '/dev/ttyUSB1' # sim serial address (dmesg | grep tty or)
GPS_TTY = '/dev/ttyUSB0' # gps serial address
HTTP_SERVER = 'http://localhost:80' # server address 
LED_gpio = 3 # GPIO pin for LED 
button_gpio = 23 # GPIO pin for Button
RATE = 15 # rate (per second) that detector attempts to collect data 

import threading # used for threads
import serial # used for serial connection
import Queue # used for queue for threads
import os # ?
import socket # used to test connectivity
import pymongo # used for db
#import RPi.GPIO as GPIO # used to control the Pi's GPIO pins
import requests # used for POST requests
import json # used for making jason object (json.dumps)
import time # ?
from time import sleep # used to sleep

q = Queue.Queue() # Using queue to share data between two threads

import logging
log = logging.getLogger()
log.setLevel('DEBUG')
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('[%(asctime)s] Detector.%(message)s'))
log.addHandler(handler)

def setupSIM():
    try:
        SIM_Serial = serial.Serial(port=SIM_TTY, baudrate=115200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=0)
        SIM_Serial.write('AT+CENG=1,1' + '\r\n') # Configures SIM unit to Engineering mode
        sleep(.5) # Need to wait for device to receive commands
        SIM_Serial.close()
    except serial.SerialException as e:
        log.info('Error: SIM is not plugged in or the SIM_TTY is Incorrect!')
        quit()

def setupGPS():
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
        log.info('Error: GPS is not plugged in or the GPS_TTY is Incorrect!')
        quit()  

class Data_Thread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.running = True
        self.GPS_Thread = self.GPS_Poller()
        self.SIM_Thread = self.SIM_Poller()
    
    def run(self):
        # Starts Threads
        self.GPS_Thread.start()
        self.SIM_Thread.start()
        while self.running:
            # Only runs when the GPS and SIM Thread are finished    
            if not self.GPS_Thread.go and not self.SIM_Thread.go:
                # ensures the gps and sim data are collect around the same time
                if abs(self.GPS_Thread.run_time - self.SIM_Thread.run_time) < .4:
                    log.info('Data: GPS Runtime: %s, SIM Runtime: %s' % (self.GPS_Thread.run_time, self.SIM_Thread.run_time))

                    cell_towers = self.SIM_Thread.SIM_Output # Gets Array of Cell tower data
                    location = self.GPS_Thread.GPS_Output.split(',') # Gets string of GPS data and split into array
                    time = location[1]
                    # N, E is positive; S, W negative;
                    lat = float(location[2]) if location[3] == 'N' else (float(location[2]) * -1)
                    lon = float(location[4]) if location[5] == 'E' else (float(location[4]) * -1)
                    lat = lat / 100.0
                    lon = lon / 100.0
                    '''
                    if(location[3] == 'N'):
                        lat = float(location[2] # N, E is positive
                    else:
                        lat = float(location[2] * -1 # S, W is negative
                    if(location[5] == 'E'):
                        lon = float(location[4]
                    else:
                        lon = float(location[4] * -1
                    '''
                    GPS_quality = location[6]
                    Satellites = location[7]
                    Altitude = location[8]
                    Altitude_units = location[9]      
                    for i in range(len(cell_towers)):
                        # Data in first (serving) cell is ordered differently than first cell,
                        # +CENG:0, '<arfcn>, <rxl>, <rxq>, <mcc>, <mnc>, <bsic>, <cellid>, <rla>, <txp>, <lac>, <TA>'
                        cell_tower = cell_towers[i]
                        cell_tower = cell_tower.split(',')
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
                            LAC = cell_tower[7][:-1]      # Location Area code
                        # puts data into json compatible format
                        document = {'time': time,
                         'MCC': int(MCC),
                         'MNC': int(MNC),
                         'LAC': LAC, 
                         'Cell_ID': Cell_ID,
                         'rxl': int(rxl), 
                         'arfcn': arfcn,
                         'bsic': bsic, 
                         'lat': float(lat),
                         'lon': float(lon), 
                         'satellites': int(Satellites),
                         'GPS_quality': int(GPS_quality),
                         'altitude': float(Altitude),
                         'altitude_units': Altitude_units
                        }
                        # Filters out data points with lower receive strengths,
                        # The data tends to be bad when the rxl is < 5~10
                        if(rxl > 9):
                            log.info('Data: Added Document to queue')
                            q.put(document)
                            sleep(RATE)
                else:
                    # gps couldn't get a fix or data was taken close at close enough intervaltx
                    log.info('Data: TIMEOUT: GPS Runtime: %s, SIM Runtime: %s' % (self.GPS_Thread.run_time, self.SIM_Thread.run_time))

                # Tells SIM and GPS thread to start again
                self.GPS_Thread.go = True
                self.SIM_Thread.go = True
        self.GPS_Thread.running = False
        self.SIM_Thread.running = False

    class GPS_Poller(threading.Thread):
        def __init__(self):
            threading.Thread.__init__(self)
            self.GPS_Serial = serial.Serial(port=GPS_TTY, baudrate=115200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=0)  
            self.GPS_Serial.close()
            self.running = True
            self.go = True
            self.run_time = 0.0
            self.GPS_Output = ''

        def run(self):
            while self.running:
                # Runs when Data thread tells it to
                if self.go:
                    start = time.time()
                    self.GPS_Serial.open()
                    sleep(.1)
                    self.GPS_Output = self.GPS_Serial.readline()
                    # Loops until has a valid GPS fix or until script has run 10 secs (~50 loops)
                    while not self.isValidLocation(self.GPS_Output) and time.time() - start < 10.0:
                        sleep(.1) # Need to wait before collecting data
                        self.GPS_Output = self.GPS_Serial.readline()
                    self.GPS_Serial.close()
                    #self.GPS_Output = self.GPS_Output.split(',')
                    self.go = False;
                    self.run_time = time.time() - start

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
            self.SIM_Output = ''
        
        def run(self):
            while self.running:
                if self.go:
                    start = time.time()
                    self.SIM_Serial.open() 
                    self.SIM_Serial.write('AT+CENG?' + '\r\n')  # Sends Command to Display current engineering mode settings, serving cell and neighboring cells
                    sleep(.1) # Need to wait for device to receive commands 
                    # Reads in SIM900 output
                    self.SIM_Output = ''
                    while self.SIM_Serial.inWaiting() > 0:
                        self.SIM_Output += self.SIM_Serial.read(6) 
                    self.SIM_Serial.close()
                    # Removes Excess Lines and packs into array
                    self.SIM_Output = self.SIM_Output.split('\n')
                    self.SIM_Output = self.SIM_Output[4:11]
                    self.go = False
                    self.run_time = time.time() - start

class Logging_Thread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.running = True
    
    def run(self):
        while self.running:
            self.sendData()
        sleep(1)
        self.sendData()
    
    def sendData(self):
        while not q.empty():
            if self.isConnected():
                document = q.get()
                r = requests.post(HTTP_SERVER, data=json.dumps(document))
                if r.status_code != 200:
                    q.add(document)
                    log.info('Logger: ERROR: Status code: %s' % r.status_code)
                else:
                    log.info('Logger: Uploaded Document')
            else:
               log.info('Logger: ERROR: No Internet Connection')
               sleep(1)
        sleep(1)

    def isConnected(self):
        try:
            socket.create_connection(('www.google.com', 80)) # connect to the host -- tells us if the host is actuallyreachable
            return True
        except OSError:
            pass
        return False

def main():
    setupSIM() # Configures SIM module to output Cell Tower Meta Data
    setupGPS() # Configures GPS module to only output GPGGA Sentences and increase's GPS speed
    try:
        Data = Data_Thread() # Thread collects GPS and SIM data and adds to queue
        Logger = Logging_Thread() # Thread waits for Wifi connection and posts data to server
        
        Data.start() # Get this ish running
        Logger.start()

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
        while True:
            if(GPIO.input(button_gpio) == 0 and run == True):
                log.info('Detected GPIO Button Press: Killing Threads')
                GPIO.output(LED_gpio, GPIO.LOW)
                Data.running = False
                Logger.running = False
                run = False
                Data.join() # wait for the thread to finish what it's doing
                Logger.join()
                exitBlink() # blinks to indicate threads are finished
            elif(GPIO.input(button_gpio) == 0 and run == False)
                log.info('Detected GPIO Button Press: Starting Threads')
                Data.running = True
                Logger.running = False
                run = True
                GPIO.output(LED_gpio, GPIO.HIGH)
                sleep(.7)
                GPIO.output(LED_gpio,GPIO.LOW)
                sleep(.7)
            elif(run == True):
                GPIO.output(LED_gpio, GPIO.HIGH)
                sleep(.7)
                GPIO.output(LED_gpio,GPIO.LOW)
                sleep(.7)
            else:
                # Not running so don't blink
                GPIO.output(LED_gpio,GPIO.LOW)
                sleep(.5)
        '''
        while True:
            sleep(.5)

    except (KeyboardInterrupt, SystemExit): # when you press ctrl+c
        log.info('Detected KeyboardInterrupt: Killing Threads.')
        Data.running = False
        Logger.running = False
        Data.join() # wait for the thread to finish what it's doing
        Logger.join()
    except serial.SerialException as e:
        log.info('Error: Something Got Unplugged!')
        Data.running = False
        Logger.running = False
        Logger.join()
        log.info('Quiting Program.')
        #exitBlink()
        quit()

    #exitBlink()
    log.info('Exiting.')
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