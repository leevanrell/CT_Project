#!/usr/bin/python
LED_gpio = 3 # GPIO pin for LED 
button_gpio = 23 # GPIO pin for Button
SIM_TTY = '' # sim serial address 
GPS_TTY = '' # gps serial address

import serial 
import argparse 
import threading 
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

q = Queue.Queue() # Using queue to share data between two threads

os.chdir(os.path.dirname(os.path.abspath(__file__))) # changes working directory to script location incase running from crontab or seomthing similar

import logging
log = logging.getLogger()
log.setLevel('DEBUG')
handler = logging.FileHandler('data/log.log')
handler.setFormatter(logging.Formatter('[%(asctime)s] [Detector.%(message)s'))
log.addHandler(handler)


def setup_TTY(): # finds the TTY addresses for SIM and GPS unit if available 
    log.info('setup] setting TTY connections')
    retry = 0 
    configured_SIM = setup_SIM_TTY() # tries to figure out tty address for SIM
    while not configured_SIM and retry < 5: # setup_SIM_TTY is buggy so its worth trying again to find the correct address
        retry += 1
        #log.debug('setup] retrying SIM TTY config')
        configured_SIM = setup_SIM_TTY() 
    retry = 0
    configured_GPS = setup_GPS_TTY()
    while not configured_GPS and retry < 5: # setup_SIM_TTY is also inconsistent -- running a few times guarantees finding the correct address if its exists
        retry += 1
        #log.debug('setup] retrying GPS TTY config')
        configured_GPS = setup_GPS_TTY() 
    if not configured_GPS or not configured_SIM: # if gps or sim fail then program gives up
        log.error('setup] failed to configure TTY: GPS - %s, SIM - %s' % (configured_GPS, configured_SIM))
        quit()

def setup_SIM_TTY(): # finds the correct tty address for the sim unit 
    count = 0
    global SIM_TTY
    while count < 10: # iterates through the first 10 ttyUSB# addresses until it finds the correct address
        SIM_TTY = '/dev/ttyUSB%s' % count 
        try:
            Serial = serial.Serial(port=SIM_TTY, baudrate=115200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=0)
            Serial.write('AT' + '\r\n') # sends AT command
            sleep(.5)
            for i in range(0, 5):
                check = Serial.readline()
                if check == 'OK\r\n':
                    log.info('setup] set SIM_TTY to ' + SIM_TTY)
                    return True
            Serial.close()
        except serial.SerialException as e:# throws exception if there is no tty device on the current address
                count += 1
        count += 1  
    return False

def setup_GPS_TTY(): # finds the correct tty address for the GPS unit
    count = 0
    global GPS_TTY
    while count < 10:
        GPS_TTY = '/dev/ttyUSB%s' % count
        try:
            check = test_GPS(9600) # tries default baud rate first         
            if check:
                return True
            else:
                check = test_GPS(115200) # tries configured baud rate 
                if check: 
                    return True
                else:
                    count += 1
        except serial.SerialException as e:
            count += 1 
    return False

def test_GPS(baudrate):
    Serial = serial.Serial(port=GPS_TTY, baudrate=baudrate, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=0)
    sleep(.5)
    check = Serial.readline()
    Serial.close()
    if check[:1] == '$': # looks for $
        log.info('setup] set GPS_TTY to ' + GPS_TTY)
        return True
    return False

def setup_SIM(): # configures sim unit to engineering mode -- outputs cell tower meta data
    log.info('setup] configuring SIM')
    try:
        SIM_Serial = serial.Serial(port=SIM_TTY, baudrate=115200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=0)
        SIM_Serial.write('AT+CENG=1,1' + '\r\n') # command to set to eng mode
        sleep(.5) # need to wait for device to receive commands
        SIM_Serial.close()
    except serial.SerialException as e:
        log.error('setup] lost connection to SIM unit')
        quit()

def setup_GPS(): # configures gps unit; increase baudrate, output fmt, and output interval
    log.info('setup] configuring GPS')
    try:
        GPS_Serial = serial.Serial(port=GPS_TTY, baudrate=9600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=0)  
        sleep(.5)
        GPS_Serial.write('$PMTK314,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0*29<CR><LF> ' + '\r\n') #Configures GPS to only output GPGGA Sentences
        sleep(.5) # need to wait for device to receive commands
        GPS_Serial.write('$PMTK220,100*2F<CR><LF>' + '\r\n') # configures fix interval to 100 ms
        sleep(.5)
        GPS_Serial.write('$PMTK251,115200*1F<CR><LF>' + '\r\n') # configures Baud Rate to 115200
        sleep(.5)
        GPS_Serial.close() 
    except serial.SerialException as e:
        log.error('setup] lost connection to GPS unit')
        quit()  

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
                    log.info('Data] GPS runtime: %.2f, SIM runtime: %.2f' % (self.GPS_Thread.run_time, self.SIM_Thread.run_time))
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
                         'MCC': MCC,
                         'MNC': MNC,
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
                            log.info('Data] added document to queue')
                            update_local(document)
                            q.put(document)
                            sleep(RATE)
                        else:
                            log.info('Data] dropped bad document: %s %s %s %s %s' % (MCC, MNC, LAC, Cell_ID, rxl))
                else: # gps couldn't get a fix (timed out) or data points weren't taken close enough together
                    log.error('Data] GPS runtime: %.2f, SIM runtime: %.2f' % (self.GPS_Thread.run_time, self.SIM_Thread.run_time))

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
            self.GPS_Serial = serial.Serial(port=GPS_TTY, baudrate=115200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=0)  
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
                        log.error('GPS] something got unplugged!') # error handling encase connection to sim unit is lost
                        Data.running = False
                        Logger.running = False
                        self.running = False # is this necessary? 
                        Data.join()
                        Logger.join()
                     
        def isValidLocation(self, output): # checks string to confirm it contains valid coordinates
            check = output.split(',')
            return len(output) >= 6 and check[0] == '$GPGGA' and int(check[6]) != 0 # we only want GPGGA sentences with an actual fix (Fix != 0)

    class SIM_Poller(threading.Thread): # thread responsible for collecting data from sim unit
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
                        log.error('SIM] something got unplugged!') # error handling encase connection to gps unit is lost
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
        while not q.empty(): # ensures there is a connection to internet/server
            if self.isConnected():
                document = q.get()
                headers = {'content-type': 'application/json'}
                r = requests.post(HTTP_SERVER, data=json.dumps(document), headers=headers)
                #r = requests.post(HTTP_SERVER + '/data', data=json.dumps(document)) # converts to json and sends post request
                if r.status_code != 200:
                    q.add(document) # add back to queue if post fails
                    log.error('Logger] status code: %s' % r.status_code)
                else:
                    log.info('Logger] uploaded document')
            else:
               log.error('Logger] no internet connection')
               sleep(1)
        sleep(2) # Wait for queue to fill

    def isConnected(self): # checks to see if detector can connect to the http server
        try:
            socket.create_connection((HTTP_SERVER, 3000)) # connect to the host -- tells us if the host is actually reachable
            return True
        except OSError:
            pass
        return False

def main():
    setup_TTY() # configures TTY addresses for SIM and GPS
    setup_SIM() # configures SIM module to output cell tower meta data
    setup_GPS() # configures GPS module to only output GPGGA Sentences and increases operating speed
    global Data, Logger 
    Data = Data_Thread() # thread collects GPS and SIM data and adds to queue
    Logger = Logging_Thread() # Thread waits for Wifi connection and posts data to server
    log.info('main] starting threads')
    Data.start() 
    Logger.start()
    try:        
        if MODE:
            pi()
        else:
            laptop()
    except (KeyboardInterrupt, SystemExit): 
        log.info('main] detected KeyboardInterrupt: killing threads.')
        Data.running = False
        Logger.running = False
        Data.join() # wait for the threads to finish what it's doing
        Logger.join()
    log.info('main] exiting.')

def laptop():
    while Data.running and Logger.running:
        sleep(.5)

def pi():
    import RPi.GPIO as GPIO # used to control the Pi's GPIO pins
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(LED_gpio, GPIO.OUT)
    GPIO.output(LED_gpio, GPIO.LOW)
    GPIO.setup(button_gpio, GPIO.IN, pull_up_down = GPIO.PUD_UP)
    run = True
    while run:
        if not GPIO.input(button_gpio):
            log.info('pi] detected GPIO button press: killing threads')
            GPIO.output(LED_gpio, GPIO.LOW)
            Data.running = False
            Logger.running = False
            run = False
            Data.join() # wait for the thread to finish what it's doing
            Logger.join()
            sleep(1)
            exitBlink() # blinks to indicate threads are finished
        else:
            GPIO.output(LED_gpio, GPIO.HIGH)
            sleep(.7)
            GPIO.output(LED_gpio,GPIO.LOW)
            sleep(.7)

def exitBlink():
    for i in range(0,9):
        GPIO.output(LED_gpio, GPIO.HIGH)
        sleep(.1)
        GPIO.output(LED_gpio, GPIO.LOW)
        sleep(.5)
    GPIO.output(LED_gpio, GPIO.LOW)
    GPIO.cleanup()

if __name__ == '__main__':
    if not os.geteuid() == 0:
        log.error('setup] script must be run as root!')
        quit()
    parser = argparse.ArgumentParser(description='SIR Detector')
    parser.add_argument('-m', '--mode', default='pi', help='configures detector to run on laptop/pi; options: pi/laptop') #, action='store', dest='mode')
    parser.add_argument('-s', '--server', default="http://localhost:3000/data", help='sets address and port of http server;') #, action='store', dest='mode')
    parser.add_argument('-r', '--rate', default=5, help='delay between successfully finding a data point and attempting to find another') #, action='store', dest='mode')  
    args = parser.parse_args()
    HTTP_SERVER = 'http://%s:3000/data' % args.server if(args.server[:4] != 'http') else args.server
    MODE = True if args.mode == 'pi'else False
    RATE = args.rate
    log.info('setup] running as: %s, server: %s' % (args.mode, HTTP_SERVER))
    main()