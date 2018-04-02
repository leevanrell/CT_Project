#!/usr/bin/python
LED_gpio = 3 # GPIO pin for LED 
button_gpio = 23 # GPIO pin for Button

import argparse 
import configparser
import os  
import sys 
import datetime
import time 
import Queue
from lib.Setup import Setup
from time import sleep 

os.chdir(os.path.dirname(os.path.abspath(__file__))) 

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
    setup = Setup(log);
    setup.setup_TTY();
    if not setup.configured:
        log.info('main] setup failed. exiting')
        quit()        
    if MODE:
        pi() 
    else:
        laptop()
    log.info('main] exiting')



def laptop():
    from lib.Logging_Thread import Logging_Thread
    from lib.Data_Thread import Data_Thread

    q = Queue.Queue() 
    Data = Data_Thread(log, q, setup.SIM_TTY, setup.GPS_TTY, RATE) 
    Logger = Logging_Thread(log, q, HTTP_SERVER) 
    log.info('main] starting threads')
    Data.start() 
    Logger.start()

    try:
        while Data.running and Logger.running:
            pass
        Data.running = False
        Logger.running = False
        Data.join()
        Logger.join()
    except (KeyboardInterrupt, SystemExit): 
        log.info('main] detected KeyboardInterrupt: killing threads.')
        Data.running = False
        Logger.running = False
        Data.join() 
        Logger.join()

def pi():
    import RPi.GPIO as GPIO 
    import lib.DetectorLite as Detector

    detector = Detector.Detector(log, HTTP_SERVER, setup.SIM_TTY, setup.GPS_TTY, RATE)
    try:
        detector.start()
    except (KeyboardInterrupt, SystemExit):
        log.info('main] detected KeyboardInterrupt: stopping job')
        detector.run = False


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
    config = configparser.ConfigParser()
    config.read('config.txt')
    HTTP_SERVER = config['DEFAULT']['HTTP_Server']
    RATE = int(config['DEFAULT']['Rate'])
    MODE = isPi()
    parser = argparse.ArgumentParser(description='SIR Detector')
    parser.add_argument('-s', '--server', default=HTTP_SERVER, help='sets address and port of http server;') #, action='store', dest='mode')
    parser.add_argument('-r', '--rate', default=RATE, help='delay between successfully finding a data point and attempting to find another') #, action='store', dest='mode')  
    args = parser.parse_args()
    HTTP_SERVER = 'http://%s:3000/data' % args.server if(args.server[:4] != 'http') else args.server
    RATE = args.rate
    log.info('setup] running as: %s, server address: %s' % (MODE, HTTP_SERVER))
    main()
