#!/usr/bin/python
LED_gpio = 3 # GPIO pin for LED 
button_gpio = 23 # GPIO pin for Button

import argparse 
import os  
import sys 
import datetime 
import time 
from time import sleep 

os.chdir(os.path.dirname(os.path.abspath(__file__))) 

q = Queue.Queue() 

import logging
log = logging.getLogger()
log.setLevel('DEBUG')
file_handler = logging.FileHandler('data/log/log.log')
file_handler.setFormatter(logging.Formatter('[%(asctime)s] [Detector.%(message)s'))
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter('[%(asctime)s] [Detector.%(message)s'))
log.addHandler(file_handler)
log.addHandler(stream_handler)

def main():
    global Data, Logger
    setup = Setup(log);
    setup.setup_TTY();
    if not setup.configured:
        log.info('main] setup failed. exiting')
        quit()
    Data = Data_Thread(log, setup. SIM_TTY, GPS_TTY) 
    Logger = Logging_Thread(log, HTTP_SERVER) 
    log.info('main] starting threads')
    Data.start(log, GPS_TTY, SIM_TTY) 
    Logger.start(log)
    try:        
        if MODE:
            pi() 
        else:
            laptop()
    except (KeyboardInterrupt, SystemExit): 
        log.info('main] detected KeyboardInterrupt: killing threads.')
        Data.running = False
        Logger.running = False
        Data.join() 
        Logger.join()
    log.info('main] exiting.')



def laptop():
    while Data.running and Logger.running:
        pass

def pi():
    import RPi.GPIO as GPIO 
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(LED_gpio, GPIO.OUT)
    GPIO.output(LED_gpio, GPIO.LOW)
    GPIO.setup(button_gpio, GPIO.IN, pull_up_down = GPIO.PUD_UP)

    while Data.running and Logger.running:
        if not GPIO.input(button_gpio):
            log.info('pi] detected GPIO button press: killing threads')
            GPIO.output(LED_gpio, GPIO.LOW)
            Data.running = False
            Logger.running = False
            
            Data.join() 
            Logger.join()
            sleep(1)
            exitBlink() 
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

def isPi():
    try:
        import RPi.GPIO as GPIO
        return True
    except ImportError:
        return False

if __name__ == '__main__':
    if not os.geteuid() == 0:
        log.error('setup] script must be run as root!')
        quit()
    parser = argparse.ArgumentParser(description='SIR Detector')
    parser.add_argument('-s', '--server', default="http://localhost:3000/data", help='sets address and port of http server;') #, action='store', dest='mode')
    parser.add_argument('-r', '--rate', default=5, help='delay between successfully finding a data point and attempting to find another') #, action='store', dest='mode')  
    args = parser.parse_args()
    HTTP_SERVER = 'http://%s:3000/data' % args.server if(args.server[:4] != 'http') else args.server
    MODE = isPi()
    RATE = args.rate
    SIM_TTY = '' 
    GPS_TTY = '' 
    log.info('setup] running as: %s, server address: %s' % (args.mode, HTTP_SERVER))
    main()
